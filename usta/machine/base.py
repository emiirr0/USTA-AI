"""Makine bağdaştırıcısı arayüzü.

USTA makinenin HMI'ına girmez; makinenin YANINDA durur. Sunucu yalnızca bu
arayüzü bilir — arkasında simülatör de olabilir, gerçek bir OPC UA presi de.
Yeni bir makine protokolü eklemek = bu sınıfı uygulamak.
"""
from __future__ import annotations

from typing import Dict, List


class MachineError(RuntimeError):
    """Makineyle iletişim hatası."""


class MachineAdapter:
    """Tüm makine bağdaştırıcılarının uyması gereken sözleşme."""

    salt_okunur: bool = True     # yazma desteklemiyorsa True
    alarm_kaydedici = None       # alarm açılınca/kapanınca çağrılır (Usta bağlar)

    def start(self) -> None:
        """Arka plan okuma döngüsünü başlat."""

    def stop(self) -> None:
        """Döngüyü durdur, bağlantıyı kapat."""

    def snapshot(self) -> Dict:
        """Anlık durum: canlı değerler, setpoint'ler, faz, üretim, trend."""
        raise NotImplementedError

    def alarms(self) -> List[Dict]:
        """Alarm listesi (aktif + yakın geçmiş), yeniden eskiye."""
        raise NotImplementedError

    def ack_alarm(self, alarm_id: str, kim: str) -> bool:
        raise NotImplementedError

    def write_setpoint(self, alan: str, deger: float) -> None:
        """Setpoint yaz. Güvenlik katmanı ÖNCE çağrılmış olmalıdır."""
        raise MachineError("Bu bağlantı yazmayı desteklemiyor (salt okunur).")

    def load_job(self, ayarlar: Dict, bilgi: Dict) -> None:
        """Aktif işi değiştir: setpoint'ler + ürün bilgisi."""
        raise MachineError("Bu bağlantı iş değiştirmeyi desteklemiyor.")

    def inject_fault(self, tur: str) -> str:
        """Yalnız simülatör: demo arıza senaryosu."""
        raise MachineError("Arıza senaryosu yalnızca simülasyonda çalışır.")
