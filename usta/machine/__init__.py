"""Makine bağdaştırıcıları: simülatör ve OPC UA."""
from __future__ import annotations

from .base import MachineAdapter, MachineError
from .simulator import SENARYOLAR, SimulatedMachine


def olustur(ayarlar) -> MachineAdapter:
    """Ayarlara göre doğru bağdaştırıcıyı kur."""
    m = ayarlar.d["makine"]
    if m.get("baglanti") == "opcua":
        from .opcua import OpcUaMachine
        return OpcUaMachine(m["ad"], m["opcua_url"], m.get("opcua_dugumler", {}))
    return SimulatedMachine(m["ad"])


__all__ = ["MachineAdapter", "MachineError", "SimulatedMachine", "SENARYOLAR", "olustur"]
