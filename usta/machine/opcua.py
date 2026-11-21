"""OPC UA bağdaştırıcısı (gerçek pres).

İsteğe bağlıdır: `pip install asyncua` gerekir. Kurulu değilse USTA
simülasyonla çalışmaya devam eder ve kontrol komutu bunu söyler.

Euromap 77 / üretici OPC UA sunucularında düğüm adları makineden makineye
değişir; bu yüzden eşleme ayarlar.json'da yapılır:

    "makine": {
      "baglanti": "opcua",
      "opcua_url": "opc.tcp://192.168.0.10:4840",
      "opcua_dugumler": {
        "z1": "ns=2;s=Barrel.Zone1.Actual",   "z1_sp": "ns=2;s=Barrel.Zone1.Setpoint",
        "z2": "...", "z2_sp": "...", "z3": "...", "z3_sp": "...",
        "nozul": "...", "nozul_sp": "...",
        "tutmaPress": "...", "tutmaPress_sp": "...",
        "enjPress": "...", "cevrim": "...", "yastik": "...", "baski": "...",
        "yazma_izni": false
      }
    }

Varsayılan SALT OKUNUR'dur. Yazma yalnızca "yazma_izni": true ise ve
güvenlik katmanından geçtikten sonra yapılır.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

from .base import MachineAdapter, MachineError

OKUNAN = ("z1", "z2", "z3", "nozul", "tutmaPress", "enjPress", "cevrim", "yastik", "baski")
SETPOINT = ("z1", "z2", "z3", "nozul", "tutmaPress")


class OpcUaMachine(MachineAdapter):
    def __init__(self, ad: str, url: str, dugumler: Dict[str, str], periyot: float = 1.0):
        try:
            from asyncua.sync import Client  # noqa: F401
        except ImportError as e:  # pragma: no cover - ortam bağımlı
            raise MachineError("OPC UA için 'asyncua' paketi gerekli: pip install asyncua") from e
        self.ad, self.url, self.d = ad, url, dict(dugumler)
        self.salt_okunur = not bool(self.d.get("yazma_izni", False))
        self.periyot = periyot
        self._client = None
        self._kilit = threading.RLock()
        self._dur = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pv: Dict[str, float] = {}
        self._sp: Dict[str, float] = {}
        self._hata: Optional[str] = None
        self.trend = deque(maxlen=60)
        self._son_baski: Optional[int] = None

    def start(self) -> None:
        from asyncua.sync import Client
        self._client = Client(self.url, timeout=4)
        self._client.connect()
        self._dur.clear()
        self._thread = threading.Thread(target=self._dongu, name="usta-opcua", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._dur.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass

    def _oku(self, anahtar: str) -> Optional[float]:
        nid = self.d.get(anahtar)
        if not nid:
            return None
        return float(self._client.get_node(nid).read_value())

    def _dongu(self) -> None:
        while not self._dur.is_set():
            try:
                pv: Dict[str, float] = {}
                for k in OKUNAN:
                    v = self._oku(k)
                    if v is not None:
                        pv[k] = v
                sp = {}
                for k in SETPOINT:
                    v = self._oku(k + "_sp")
                    if v is not None:
                        sp[k] = v
                with self._kilit:
                    self._pv, self._sp, self._hata = pv, sp, None
                    b = pv.get("baski")
                    if b is not None and b != self._son_baski:
                        self._son_baski = int(b)
                        self.trend.append({"t": datetime.now().strftime("%H:%M:%S"),
                                           "cevrim": pv.get("cevrim"),
                                           "yastik": pv.get("yastik"),
                                           "enjPress": pv.get("enjPress"), "fire": False})
            except Exception as e:  # bağlantı koptu vb.
                with self._kilit:
                    self._hata = str(e) or e.__class__.__name__
                self._yeniden_baglan()
                continue
            self._dur.wait(self.periyot)

    def _yeniden_baglan(self) -> None:
        """Pres yeniden başlarsa USTA'yı yeniden başlatmak gerekmesin:
        artan bekleme ile (en çok 10 sn) yeniden bağlanmayı dener."""
        from asyncua.sync import Client
        bekleme = 1.0
        while not self._dur.is_set():
            try:
                self._client.disconnect()
            except Exception:
                pass
            if self._dur.wait(bekleme):
                return
            try:
                self._client = Client(self.url, timeout=4)
                self._client.connect()
                return
            except Exception as e:
                with self._kilit:
                    self._hata = f"yeniden bağlanılamıyor: {e or e.__class__.__name__}"
                bekleme = min(10.0, bekleme * 2)

    def snapshot(self) -> Dict:
        with self._kilit:
            pv = dict(self._pv)
            return {"makine": self.ad, "baglanti": "OPC UA",
                    "durum": "BAĞLANTI HATASI" if self._hata else "ÇALIŞIYOR",
                    "hata": self._hata, "pv": pv, "sp": dict(self._sp),
                    "is": {"urun": "", "kalip": "", "malzeme": "", "cevrim_hedef": pv.get("cevrim")},
                    "baski": int(pv.get("baski", 0) or 0), "faz": None, "faz_i": -1,
                    "fazlar": [], "uretim": None, "trend": list(self.trend), "senaryolar": []}

    def alarms(self) -> List[Dict]:
        # Alarm etiketleri üreticiye özeldir; eşleme ayarlandığında buraya eklenir.
        return []

    def ack_alarm(self, alarm_id: str, kim: str) -> bool:
        return False

    def write_setpoint(self, alan: str, deger: float) -> None:
        if self.salt_okunur:
            raise MachineError("OPC UA bağlantısı SALT OKUNUR (ayarlar: yazma_izni=false).")
        nid = self.d.get(alan + "_sp")
        if not nid:
            raise MachineError(f"'{alan}' için setpoint düğümü tanımlı değil.")
        from asyncua import ua
        node = self._client.get_node(nid)
        tip = node.read_data_type_as_variant_type()
        node.write_value(ua.DataValue(ua.Variant(deger, tip)))
        # geri-okuma doğrulaması: yazılan değer makinede gerçekten oluştu mu?
        time.sleep(0.2)
        geri = float(node.read_value())
        if abs(geri - float(deger)) > 0.51:
            raise MachineError(f"Geri okuma uyuşmuyor: yazılan {deger}, okunan {geri}.")
