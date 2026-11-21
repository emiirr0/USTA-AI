"""USTA·AI uygulama çekirdeği — HTTP'den bağımsız iş mantığı.

Sunucu yalnızca bu sınıfı çağırır; testler de doğrudan bunu kullanır.
Güvenlik varsayılanları:
  • Her açılışta panel DANIŞMAN modunda ve OPERATÖR rolüyle başlar.
  • Danışman modunda makineye hiçbir değer yazılmaz (iş değişimi dahil).
  • Her yazma tek kullanımlık onay belirteci ister ve kayıt defterine düşer.
"""
from __future__ import annotations

import re
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from . import __version__, gozcu_bridge, knowledge
from .ai import AIAracisi
from .config import ROL_TR, YETKI, Ayarlar
from .machine import SENARYOLAR, MachineError, olustur
from .safety import GuvenlikKapisi, ayarlari_sinirla
from .storage import Depo

MALZEMELER = ["ABS", "PP (Polipropilen)", "PC (Polikarbonat)", "POM (Asetal)",
              "PA6 (Naylon)", "PS (Polistiren)", "PETG"]
ETLER = ["İnce (<2 mm)", "Orta (2–4 mm)", "Kalın (>4 mm)"]
TOHUM_ISLER = [
    {"id": "JOB-K512", "urun": "Peynir Üçgen Kutu", "kalip": "K-512", "malzeme": "PP (Polipropilen)",
     "ayarlar": {"z1": 206, "z2": 212, "z3": 216, "nozul": 222, "enjPress": 72, "tutmaPress": 40, "cevrim": 18}},
    {"id": "JOB-K114", "urun": "Konnektör Gövdesi", "kalip": "K-114", "malzeme": "ABS",
     "ayarlar": {"z1": 218, "z2": 221, "z3": 224, "nozul": 230, "enjPress": 82, "tutmaPress": 45, "cevrim": 24}},
    {"id": "JOB-K330", "urun": "Redüktör Dişlisi", "kalip": "K-330", "malzeme": "PA6 (Naylon)",
     "ayarlar": {"z1": 250, "z2": 255, "z3": 258, "nozul": 262, "enjPress": 95, "tutmaPress": 55, "cevrim": 31}},
]


class Hata(Exception):
    """Kullanıcıya gösterilecek, beklenen hata (HTTP 400/403/404)."""

    def __init__(self, mesaj: str, kod: int = 400):
        super().__init__(mesaj)
        self.kod = kod


def vardiya(saat: Optional[int] = None) -> str:
    h = datetime.now().hour if saat is None else saat
    return "Gece Vardiyası" if h < 8 else "Vardiya 1" if h < 16 else "Vardiya 2"


def _metin(v, ad: str, azami: int) -> str:
    s = (v or "").strip() if isinstance(v, str) else ""
    if not s:
        raise Hata(f"{ad} boş olamaz.")
    if len(s) > azami:
        raise Hata(f"{ad} en fazla {azami} karakter olabilir.")
    return s


class Usta:
    def __init__(self, ayarlar: Optional[Ayarlar] = None, makine=None, ai=None):
        self.ayarlar = ayarlar or Ayarlar()
        self.depo = Depo(self.ayarlar.veri / "usta.db")
        self._tohumla()
        self.kapi = GuvenlikKapisi(self.ayarlar.alanlar)
        self.ai = ai or AIAracisi(self.ayarlar)
        self.makine = makine or olustur(self.ayarlar)
        self.makine.alarm_kaydedici = self._alarm_kaydet
        self._kilit = threading.RLock()
        self.oturum = {"kullanici": self.ayarlar.kullanicilar()[0], "mod": "danisman"}
        self.aktif_is_id: Optional[str] = self.depo.durum_al("aktif_is", "JOB-K114")
        self._gozcu_onbellek = (0.0, None)
        self._yorumlar: Dict[str, Dict] = {}
        self._bekleyen_kaynak: Dict[str, str] = {}

    # ── yaşam döngüsü ────────────────────────────────────────────────
    def baslat(self) -> None:
        self.makine.start()
        j = self.depo.is_getir(self.aktif_is_id or "")
        if j and not self.makine.salt_okunur:
            # açılışta makine zaten bu işte çalışıyor kabul edilir (simülasyon)
            self.makine.load_job(j["ayarlar"], j)

    def durdur(self) -> None:
        self.makine.stop()
        self.depo.kapat()

    def _tohumla(self) -> None:
        if not self.depo.durum_al("tohumlandi"):
            for j in TOHUM_ISLER:
                self.depo.is_kaydet(j)
            for b in knowledge.TOHUM:
                self.depo.bilgi_ekle(dict(b, kaynak="örnek tesis verisi"))
            self.depo.durum_yaz("tohumlandi", True)

    def _alarm_kaydet(self, a: Dict) -> None:
        try:
            self.depo.alarm_kaydet(a)
        except Exception:
            pass   # alarm akışı kayıt hatası yüzünden asla durmamalı

    # ── oturum / yetki ───────────────────────────────────────────────
    def yetkili(self, eylem: str) -> bool:
        return self.oturum["kullanici"]["rol"] in YETKI.get(eylem, ())

    def _zorunlu(self, eylem: str, mesaj: str) -> None:
        if not self.yetkili(eylem):
            raise Hata(mesaj, 403)

    def kullanici_sec(self, kid: str, pin: str = "") -> Dict:
        u = next((u for u in self.ayarlar.kullanicilar() if u["id"] == kid), None)
        if not u:
            raise Hata("Kullanıcı bulunamadı.", 404)
        beklenen = self.ayarlar.pin(u["rol"])
        if beklenen and str(pin) != beklenen:
            raise Hata("PIN hatalı.", 403)
        with self._kilit:
            self.oturum["kullanici"] = u
            if u["rol"] not in YETKI["yaz"]:
                self.oturum["mod"] = "danisman"
        return self.oturum_bilgisi()

    def mod_sec(self, mod: str) -> Dict:
        if mod not in ("danisman", "yazma"):
            raise Hata("Geçersiz mod.")
        if mod == "yazma":
            self._zorunlu("yaz", "Onaylı yazma moduna yalnız usta/mühendis geçebilir.")
            if self.makine.salt_okunur:
                raise Hata("Makine bağlantısı salt okunur; yazma modu kullanılamaz.", 403)
        self.oturum["mod"] = mod
        return self.oturum_bilgisi()

    def oturum_bilgisi(self) -> Dict:
        u = self.oturum["kullanici"]
        return {"kullanici": u, "rol_ad": ROL_TR.get(u["rol"], u["rol"]), "mod": self.oturum["mod"],
                "vardiya": vardiya(),
                "yetki": {e: u["rol"] in r for e, r in YETKI.items()},
                "pin_gerekli": {r: bool(self.ayarlar.pin(r)) for r in ROL_TR}}

    # ── okuma ────────────────────────────────────────────────────────
    def meta(self) -> Dict:
        return {"surum": __version__, "makine": self.ayarlar.makine_adi,
                "alanlar": self.ayarlar.alanlar, "malzemeler": MALZEMELER, "etler": ETLER,
                "kullanicilar": self.ayarlar.kullanicilar(), "roller": ROL_TR,
                "ai": self.ai.bilgi(), "uyarilar": self.ayarlar.uyarilar,
                "senaryolar": {k: v[0] for k, v in SENARYOLAR.items()},
                "salt_okunur": self.makine.salt_okunur,
                "gozcu_ayarli": bool(self.ayarlar.d["gozcu"]["klasor"])}

    def gozcu(self) -> Optional[Dict]:
        zaman, veri = self._gozcu_onbellek
        if time.monotonic() - zaman > 3:
            veri = gozcu_bridge.oku(self.ayarlar.d["gozcu"]["klasor"])
            self._gozcu_onbellek = (time.monotonic(), veri)
        return veri

    def durum(self) -> Dict:
        return {"makine": self.makine.snapshot(), "alarmlar": self.makine.alarms()[:30],
                "oturum": self.oturum_bilgisi(), "aktif_is": self.aktif_is_id,
                "gozcu": self.gozcu(), "zaman": datetime.now().strftime("%H:%M:%S")}

    # ── AI ───────────────────────────────────────────────────────────
    def sohbet(self, gecmis: List[Dict]) -> Dict:
        if not isinstance(gecmis, list) or not gecmis:
            raise Hata("Soru boş.")
        temiz = []
        for m in gecmis[-20:]:
            if isinstance(m, dict) and isinstance(m.get("content"), str) and m["content"].strip():
                temiz.append({"role": "assistant" if m.get("role") == "assistant" else "user",
                              "content": m["content"].strip()[:4000]})
        if not temiz or temiz[-1]["role"] != "user":
            raise Hata("Son mesaj bir soru olmalı.")
        return self.ai.sohbet(temiz, self.makine.snapshot(), self.depo.bilgi_listesi(), self.gozcu())

    def alarm_yorumu(self, alarm_id: str) -> Dict:
        a = next((a for a in self.makine.alarms() if a["id"] == alarm_id), None)
        if not a:
            raise Hata("Alarm bulunamadı.", 404)
        if alarm_id in self._yorumlar:
            return self._yorumlar[alarm_id]
        y = self.ai.alarm_yorumu(a, self.makine.snapshot(), self.depo.bilgi_listesi())
        if not y.get("yedek"):
            self._yorumlar[alarm_id] = y
        return y

    def alarm_gordum(self, alarm_id: str) -> Dict:
        if not self.makine.ack_alarm(alarm_id, self.oturum["kullanici"]["ad"]):
            raise Hata("Alarm bulunamadı.", 404)
        return {"tamam": True}

    def senaryo(self, tur: str) -> Dict:
        try:
            return {"ad": self.makine.inject_fault(tur or "rastgele")}
        except MachineError as e:
            raise Hata(str(e))

    def recete(self, malzeme: str, et: str) -> Dict:
        return self.ai.recete(_metin(malzeme, "Malzeme", 60), _metin(et, "Et kalınlığı", 40),
                              self.depo.bilgi_listesi())

    def sonuc_kaydet(self, malzeme: str, et: str, sonuc: str, recete: Dict) -> Dict:
        if sonuc not in ("iyi", "fire"):
            raise Hata("Sonuç 'iyi' ya da 'fire' olmalı.")
        self.depo.sonuc_ekle(_metin(malzeme, "Malzeme", 60), _metin(et, "Et", 40), sonuc,
                             recete if isinstance(recete, dict) else {})
        return {"sonuclar": self.depo.sonuclar()}

    # ── işler ────────────────────────────────────────────────────────
    def is_ekle(self, urun, kalip, malzeme) -> Dict:
        self._zorunlu("is_duzenle", "İş eklemek için usta/mühendis girişi gerekir.")
        j = {"id": "JOB-" + format(int(time.time() * 1000), "x").upper(),
             "urun": _metin(urun, "Ürün adı", 80), "kalip": _metin(kalip, "Kalıp kodu", 30),
             "malzeme": _metin(malzeme, "Malzeme", 40),
             "ayarlar": {"z1": 210, "z2": 215, "z3": 220, "nozul": 225, "enjPress": 80,
                         "tutmaPress": 45, "cevrim": 22}}
        self.depo.is_kaydet(j)
        return j

    def is_guncelle(self, is_id: str, ayarlar: Dict) -> Dict:
        self._zorunlu("is_duzenle", "İş değerlerini değiştirmek için usta/mühendis girişi gerekir.")
        j = self.depo.is_getir(is_id)
        if not j:
            raise Hata("İş bulunamadı.", 404)
        if not isinstance(ayarlar, dict):
            raise Hata("Ayarlar bir nesne olmalı.")
        s = ayarlari_sinirla(ayarlar, self.ayarlar.alanlar)
        j["ayarlar"].update(s["degerler"])
        self.depo.is_kaydet(j)
        return {"is": j, "uyarilar": s["uyarilar"]}

    def is_sil(self, is_id: str) -> Dict:
        self._zorunlu("is_duzenle", "İş silmek için usta/mühendis girişi gerekir.")
        if is_id == self.aktif_is_id:
            raise Hata("Aktif iş silinemez; önce başka bir işi aktif yap.")
        if not self.depo.is_sil(is_id):
            raise Hata("İş bulunamadı.", 404)
        return {"tamam": True}

    def is_oner(self, is_id: str) -> Dict:
        j = self.depo.is_getir(is_id)
        if not j:
            raise Hata("İş bulunamadı.", 404)
        r = self.ai.recete(j["malzeme"], "Orta (2–4 mm)", self.depo.bilgi_listesi(),
                           f"Ürün: {j['urun']}, Kalıp: {j['kalip']}.")
        return r

    def is_aktif(self, is_id: str) -> Dict:
        self._zorunlu("is_sec", "İş seçimi için usta/mühendis girişi gerekir.")
        j = self.depo.is_getir(is_id)
        if not j:
            raise Hata("İş bulunamadı.", 404)
        yazildi = False
        if self.oturum["mod"] == "yazma" and not self.makine.salt_okunur:
            sorunlar = []
            for k, v in j["ayarlar"].items():
                t = self.ayarlar.alanlar.get(k)
                if t and t.get("yazilabilir") and not (t["aralik"][0] <= v <= t["aralik"][1]):
                    sorunlar.append(f"{t['etiket']} {v} {t['birim']} güvenli aralık dışında")
            if sorunlar:
                raise Hata("İş makineye yüklenemedi: " + "; ".join(sorunlar) + ".")
            eski = self.makine.snapshot().get("sp", {})
            self.makine.load_job(j["ayarlar"], j)
            u = self.oturum["kullanici"]
            for k, v in j["ayarlar"].items():
                t = self.ayarlar.alanlar.get(k)
                if t and t.get("yazilabilir") and eski.get(k) != v:
                    self.depo.kayit_ekle(kullanici=u["ad"], rol=ROL_TR[u["rol"]], vardiya=vardiya(),
                                         alan=k, etiket=t["etiket"], eski=eski.get(k), yeni=v,
                                         birim=t["birim"], kaynak=f"İş değişimi → {j['urun']} ({j['kalip']})")
            yazildi = True
        self.aktif_is_id = is_id
        self.depo.durum_yaz("aktif_is", is_id)
        return {"is": j, "yazildi": yazildi}

    # ── onaylı yazma ─────────────────────────────────────────────────
    def yazma_dogrula(self, alan: str, deger, kaynak: str = "") -> Dict:
        if isinstance(deger, str):
            try:
                deger = float(deger.replace(",", "."))
            except ValueError:
                pass
        sp = self.makine.snapshot().get("sp") or {}
        d = self.kapi.dogrula(alan, deger, sp.get(alan), self.yetkili("yaz"),
                              self.oturum["mod"] == "yazma" and not self.makine.salt_okunur)
        sonuc = d.sozluk()
        if d.belirtec:
            self._bekleyen_kaynak[d.belirtec] = (kaynak or "Elle giriş")[:120]
        return sonuc

    def yazma_onayla(self, belirtec: str) -> Dict:
        d = self.kapi.onay_al(belirtec)
        if not d:
            raise Hata("Onay süresi doldu ya da zaten kullanıldı; yeniden doğrula.", 409)
        # onay anında koşulları yeniden kontrol et (bu arada rol/mod değişmiş olabilir)
        if not (self.yetkili("yaz") and self.oturum["mod"] == "yazma"):
            raise Hata("Onay anında yazma yetkisi yok (rol ya da mod değişti).", 403)
        try:
            self.makine.write_setpoint(d.alan, d.hedef)
        except MachineError as e:
            raise Hata(f"Makineye yazılamadı: {e}", 502)
        u = self.oturum["kullanici"]
        kaynak = self._bekleyen_kaynak.pop(belirtec, "Elle giriş")
        kid = self.depo.kayit_ekle(kullanici=u["ad"], rol=ROL_TR[u["rol"]], vardiya=vardiya(),
                                   alan=d.alan, etiket=d.etiket, eski=d.mevcut, yeni=d.hedef,
                                   birim=d.birim, kaynak=kaynak)
        return {"tamam": True, "kayit_id": kid, "mesaj":
                f"{d.etiket} → {d.hedef:g} {d.birim} makineye yazıldı ve kayda geçti."}

    # ── bilgi tabanı ─────────────────────────────────────────────────
    def bilgi_ayristir(self, dosya_adi: str, veri: bytes) -> Dict:
        self._zorunlu("belge_yukle", "Belge eklemek için mühendis girişi gerekir.")
        adaylar, uyarilar = knowledge.belgeyi_ayristir(dosya_adi, veri)
        mevcut = {b["id"] for b in self.depo.bilgi_listesi()}
        for a in adaylar:
            a["mevcut"] = a["id"] in mevcut
        return {"dosya": dosya_adi, "adaylar": adaylar, "uyarilar": uyarilar}

    def bilgi_ekle(self, kayitlar: List[Dict]) -> Dict:
        self._zorunlu("belge_yukle", "Belge eklemek için mühendis girişi gerekir.")
        if not isinstance(kayitlar, list):
            raise Hata("Kayıt listesi bekleniyor.")
        eklenen = 0
        for k in kayitlar[:200]:
            if not isinstance(k, dict):
                continue
            try:
                kayit = {"id": _metin(k.get("id"), "Kimlik", 40),
                         "tur": k.get("tur") if k.get("tur") in ("recete", "datasheet", "not") else "not",
                         "malzeme": (k.get("malzeme") or "")[:20],
                         "baslik": _metin(k.get("baslik"), "Başlık", 160),
                         "metin": _metin(k.get("metin"), "Metin", 4000),
                         "kaynak": (k.get("kaynak") or "")[:120]}
            except Hata:
                continue
            if not re.match(r"^[A-Za-z0-9_\-]+$", kayit["id"]):
                continue
            eklenen += self.depo.bilgi_ekle(kayit)
        return {"eklenen": eklenen, "toplam": len(self.depo.bilgi_listesi())}

    def bilgi_sil(self, bid: str) -> Dict:
        self._zorunlu("belge_yukle", "Belge silmek için mühendis girişi gerekir.")
        if not self.depo.bilgi_sil(bid):
            raise Hata("Kayıt bulunamadı.", 404)
        return {"tamam": True}

    # ── kontrol (tanılama) ───────────────────────────────────────────
    def ai_dene(self) -> Dict:
        """Bağlantı testi: seçili sağlayıcıya kısa bir istek gönderir."""
        if self.ai.secim == "uzman":
            return {"tamam": True, "saglayici": "uzman", "mesaj": "Çevrimdışı uzman hazır (internet gerekmez)."}
        metin, hata = self.ai._dene("Kısa yanıt ver.", [{"role": "user", "content": "Tek kelime: hazır mısın?"}], 20)
        return {"tamam": hata is None, "saglayici": self.ai.secim,
                "mesaj": (metin or "")[:80] if hata is None else hata}
