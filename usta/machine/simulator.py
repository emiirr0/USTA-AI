"""Fiziğe yakın enjeksiyon presi simülatörü.

Rastgele sayı üreteci değil, küçük bir süreç modeli:
  • Kovan bölgeleri setpoint'e birinci derece gecikmeyle yaklaşır
    (setpoint değişince sıcaklık birden zıplamaz, rampa yapar).
  • Enjeksiyon basıncı eriyik sıcaklığına bağlıdır (soğuk eriyik = yüksek basınç).
  • Fire olasılığı süreç sapmalarından doğar ve türü sapmaya göre seçilir
    (sıcak + yüksek tutma → çapak; soğuk + düşük tutma → eksik dolum ...).
  • Alarmlar sabit bir listeden değil, ölçülen değerlerdeki koşullardan doğar
    ve koşul kalkınca kendiliğinden temizlenir.
  • Arıza senaryoları (rezistans arızası, huni boşalması ...) fiziksel olarak
    enjekte edilir; alarm, verideki etkiden kendiliğinden çıkar.
"""
from __future__ import annotations

import random
import threading
from collections import deque
from datetime import datetime
from typing import Callable, Deque, Dict, List, Optional

from .base import MachineAdapter, MachineError

FAZLAR = [("KAPANMA", 0.10), ("ENJEKSİYON", 0.10), ("TUTMA", 0.25),
          ("SOĞUTMA", 0.40), ("AÇMA·ÇIKARMA", 0.15)]

SENARYOLAR = {
    "rezistans_b2": ("Bölge 2 rezistans arızası", 90),
    "huni_bos": ("Besleme hunisi boşalıyor", 60),
    "yag_sicak": ("Hidrolik yağ soğutması zayıfladı", 80),
    "kalip_koruma": ("Kalıp arasında engel", 8),
}


def _simdi() -> str:
    return datetime.now().strftime("%H:%M:%S")


class SimulatedMachine(MachineAdapter):
    salt_okunur = False

    def __init__(self, ad: str, hiz: float = 1.0, tohum: Optional[int] = None,
                 alarm_kaydedici: Optional[Callable[[Dict], None]] = None):
        self.ad = ad
        self.hiz = hiz                      # 1.0 = gerçek zaman; testlerde hızlandırılır
        self.rng = random.Random(tohum)
        self._kilit = threading.RLock()
        self._dur = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.alarm_kaydedici = alarm_kaydedici
        self.sp = {"z1": 218.0, "z2": 221.0, "z3": 224.0, "nozul": 230.0, "tutmaPress": 45.0}
        self.pv = dict(self.sp)
        self.pv.update(enjPress=82.0, cevrim=24.0, yastik=6.2, yag=44.0, huni=80.0)
        self.is_bilgi = {"urun": "Konnektör Gövdesi", "kalip": "K-114", "malzeme": "ABS",
                         "cevrim_hedef": 24.0}
        self.baski = 14382
        self.uretim = {"saglam": 0, "fire": 0, "turler": {}}
        self.trend: Deque[Dict] = deque(maxlen=60)
        self.faz_i = 0
        self._faz_t = 0.0
        self._alarmlar: List[Dict] = []
        self._alarm_sayac = 300
        self._kosul_sure: Dict[str, float] = {}
        self._ariza: Dict[str, float] = {}   # senaryo -> bitiş zamanı (sim saniyesi)
        self._t = 0.0                         # simülasyon saati

    # ── yaşam döngüsü ────────────────────────────────────────────────
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._dur.clear()
        self._thread = threading.Thread(target=self._dongu, name="usta-sim", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._dur.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _dongu(self) -> None:
        adim = 0.25
        while not self._dur.wait(adim):
            self.tick(adim * self.hiz)

    # ── süreç modeli ─────────────────────────────────────────────────
    def tick(self, dt: float) -> None:
        """dt saniye ilerlet (testler bunu doğrudan çağırır)."""
        with self._kilit:
            self._t += dt
            r = self.rng
            # arıza senaryolarının fiziksel etkisi
            for s, bitis in list(self._ariza.items()):
                if self._t >= bitis:
                    del self._ariza[s]
            b2_kayip = 16.0 if "rezistans_b2" in self._ariza else 0.0

            k = min(1.0, 0.12 * dt * 4)        # birinci derece yaklaşım katsayısı
            for z in ("z1", "z2", "z3", "nozul"):
                hedef = self.sp[z] - (b2_kayip if z == "z2" else 0.0)
                self.pv[z] += (hedef - self.pv[z]) * k + r.gauss(0, 0.35)
            self.pv["tutmaPress"] += (self.sp["tutmaPress"] - self.pv["tutmaPress"]) * min(1.0, 0.6 * dt * 4) \
                + r.gauss(0, 0.25)
            # soğuk eriyik daha viskoz → daha yüksek enjeksiyon basıncı
            eriyik = (self.pv["z3"] + self.pv["nozul"]) / 2
            hedef_bas = 82.0 + (228.0 - eriyik) * 0.55 + (self.pv["tutmaPress"] - 45) * 0.15
            self.pv["enjPress"] += (hedef_bas - self.pv["enjPress"]) * 0.2 + r.gauss(0, 0.4)
            yag_hedef = 58.0 if "yag_sicak" in self._ariza else 44.0
            self.pv["yag"] += (yag_hedef - self.pv["yag"]) * 0.05 + r.gauss(0, 0.1)
            if "huni_bos" in self._ariza:
                self.pv["huni"] = max(0.0, self.pv["huni"] - 2.5 * dt)
            else:
                self.pv["huni"] = min(80.0, self.pv["huni"] + 4.0 * dt)
            self.pv["yastik"] = max(0.5, min(9.0, self.pv["yastik"] + r.gauss(0, 0.05)
                                    + (-0.15 * dt if self.pv["huni"] < 15 else (6.2 - self.pv["yastik"]) * 0.05)))

            # çevrim faz makinesi (kalıp koruma arızasında makine bekler)
            if "kalip_koruma" not in self._ariza:
                cevrim = self.is_bilgi["cevrim_hedef"] + (self.pv["yag"] - 44) * 0.05
                self.pv["cevrim"] = round(cevrim + r.gauss(0, 0.15), 1)
                sure = max(4.0, self.pv["cevrim"]) / 6.0   # demo: çevrim 6x hızlı oynar
                self._faz_t += dt
                if self._faz_t >= FAZLAR[self.faz_i][1] * sure:
                    self._faz_t = 0.0
                    self.faz_i += 1
                    if self.faz_i >= len(FAZLAR):
                        self.faz_i = 0
                        self._cevrim_bitti()
            self._alarm_kosullari(dt)

    def _sapma(self, z: str) -> float:
        return self.pv[z] - self.sp[z]

    def _cevrim_bitti(self) -> None:
        self.baski += 1
        sic = sum(self._sapma(z) for z in ("z1", "z2", "z3", "nozul")) / 4
        tutma = self.pv["tutmaPress"] - 45
        p = 0.015 + 0.004 * abs(sic) ** 1.3 + 0.006 * max(0.0, abs(tutma) - 3)
        if self.pv["yastik"] < 2.0:
            p += 0.35
        tur = None
        if self.rng.random() < min(0.9, p):
            if self.pv["yastik"] < 2.0 or (sic < -4 and tutma < 0):
                tur = "eksik_dolum"
            elif sic > 4 or tutma > 6:
                tur = "capak"
            elif tutma < -4:
                tur = "cokuntu"
            else:
                tur = self.rng.choice(["cizik", "leke", "capak", "cokuntu"])
        if tur:
            self.uretim["fire"] += 1
            self.uretim["turler"][tur] = self.uretim["turler"].get(tur, 0) + 1
        else:
            self.uretim["saglam"] += 1
        self.trend.append({"t": _simdi(), "cevrim": self.pv["cevrim"],
                           "yastik": round(self.pv["yastik"], 2),
                           "enjPress": round(self.pv["enjPress"], 1),
                           "fire": bool(tur)})

    # ── alarmlar: koşul → alarm, koşul kalkınca temizlenir ───────────
    def _alarm_kosullari(self, dt: float) -> None:
        kosullar = {
            "ALM-2xx-z1": (abs(self._sapma("z1")) > 6, abs(self._sapma("z1")) < 3, "warn",
                           "Bölge 1 sıcaklık sapması", "Ölçülen değer setpoint'ten 6 °C'den fazla uzaklaştı."),
            "ALM-2xx-z2": (abs(self._sapma("z2")) > 6, abs(self._sapma("z2")) < 3, "warn",
                           "Bölge 2 sıcaklık sapması", "Ölçülen değer setpoint'ten 6 °C'den fazla uzaklaştı."),
            "ALM-2xx-z3": (abs(self._sapma("z3")) > 6, abs(self._sapma("z3")) < 3, "warn",
                           "Bölge 3 sıcaklık sapması", "Ölçülen değer setpoint'ten 6 °C'den fazla uzaklaştı."),
            "ALM-2xx-noz": (abs(self._sapma("nozul")) > 6, abs(self._sapma("nozul")) < 3, "warn",
                            "Nozul sıcaklık sapması", "Nozul ölçümü setpoint'ten uzaklaştı."),
            "ALM-104": (self.pv["enjPress"] > 92, self.pv["enjPress"] < 88, "warn",
                        "Enjeksiyon basıncı üst sınıra yakın", "Basınç 92 bar eşiğini aştı."),
            "ALM-310": (self.pv["yag"] > 52, self.pv["yag"] < 49, "warn",
                        "Hidrolik yağ sıcaklığı yüksek", "Yağ sıcaklığı 52 °C üst eşiğini aştı."),
            "ALM-120": (self.pv["huni"] < 20, self.pv["huni"] > 30, "warn",
                        "Besleme hunisi seviyesi düşük", "Granül seviyesi düşük; besleme kesilebilir."),
            "ALM-090": ("kalip_koruma" in self._ariza, "kalip_koruma" not in self._ariza, "crit",
                        "Kalıp koruma tetiklendi", "Kalıp kapanırken engel algılandı, çevrim durdu."),
        }
        for anahtar, (tetik, temiz, sev, baslik, detay) in kosullar.items():
            aktif = self._aktif_alarm(anahtar)
            if tetik:
                self._kosul_sure[anahtar] = self._kosul_sure.get(anahtar, 0.0) + dt
                # 2 sn süren koşul alarm olur (anlık gürültü alarm üretmez)
                if not aktif and self._kosul_sure[anahtar] >= 2.0:
                    self._alarm_ac(anahtar, sev, baslik, detay)
            else:
                self._kosul_sure[anahtar] = 0.0
                if aktif and temiz:
                    aktif["active"] = False
                    aktif["end"] = _simdi()
                    if self.alarm_kaydedici:
                        self.alarm_kaydedici(dict(aktif))

    def _aktif_alarm(self, anahtar: str) -> Optional[Dict]:
        for a in self._alarmlar:
            if a["key"] == anahtar and a["active"]:
                return a
        return None

    def _alarm_ac(self, anahtar: str, sev: str, baslik: str, detay: str) -> None:
        if anahtar.startswith("ALM-2xx"):
            self._alarm_sayac += 1
            kod = f"ALM-{200 + self._alarm_sayac % 100:03d}"
        else:
            kod = anahtar
        a = {"id": f"{kod}#{int(self._t * 1000)}", "code": kod, "key": anahtar, "sev": sev,
             "title": baslik, "detail": detay, "start": _simdi(), "end": None,
             "active": True, "ack": False, "ack_by": None}
        self._alarmlar.insert(0, a)
        del self._alarmlar[100:]
        if self.alarm_kaydedici:
            self.alarm_kaydedici(dict(a))

    # ── MachineAdapter ───────────────────────────────────────────────
    def snapshot(self) -> Dict:
        with self._kilit:
            pv = {k: round(v, 1) for k, v in self.pv.items()}
            for z in ("z1", "z2", "z3", "nozul"):
                pv[z] = int(round(self.pv[z]))
            pv["tutmaPress"] = int(round(self.pv["tutmaPress"]))
            pv["enjPress"] = int(round(self.pv["enjPress"]))
            return {
                "makine": self.ad, "baglanti": "simülasyon", "durum":
                    "BEKLİYOR" if "kalip_koruma" in self._ariza else "ÇALIŞIYOR",
                "pv": pv, "sp": {k: round(v, 1) for k, v in self.sp.items()},
                "is": dict(self.is_bilgi), "baski": self.baski,
                "faz": FAZLAR[self.faz_i][0], "faz_i": self.faz_i,
                "fazlar": [f for f, _ in FAZLAR],
                "uretim": {"saglam": self.uretim["saglam"], "fire": self.uretim["fire"],
                           "turler": dict(self.uretim["turler"])},
                "trend": list(self.trend),
                "senaryolar": sorted(self._ariza),
            }

    def alarms(self) -> List[Dict]:
        with self._kilit:
            return [dict(a) for a in self._alarmlar]

    def ack_alarm(self, alarm_id: str, kim: str) -> bool:
        with self._kilit:
            for a in self._alarmlar:
                if a["id"] == alarm_id:
                    a["ack"], a["ack_by"] = True, kim
                    return True
        return False

    def write_setpoint(self, alan: str, deger: float) -> None:
        with self._kilit:
            if alan not in self.sp:
                raise MachineError(f"'{alan}' bu makinede yazılabilir bir setpoint değil.")
            self.sp[alan] = float(deger)

    def load_job(self, ayarlar: Dict, bilgi: Dict) -> None:
        with self._kilit:
            for k in self.sp:
                if k in ayarlar:
                    self.sp[k] = float(ayarlar[k])
            self.is_bilgi = {"urun": bilgi.get("urun", ""), "kalip": bilgi.get("kalip", ""),
                             "malzeme": bilgi.get("malzeme", ""),
                             "cevrim_hedef": float(ayarlar.get("cevrim", 24) or 24)}

    def inject_fault(self, tur: str) -> str:
        if tur == "rastgele":
            tur = self.rng.choice(list(SENARYOLAR))
        if tur not in SENARYOLAR:
            raise MachineError(f"Bilinmeyen senaryo: {tur}")
        ad, sure = SENARYOLAR[tur]
        with self._kilit:
            self._ariza[tur] = self._t + sure
        return ad
