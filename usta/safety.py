"""Doğrulama katmanı — AI ile makine arasındaki kapı.

Hiçbir değer (AI önerisi ya da elle giriş) bu kapıdan geçmeden makineye
yazılamaz. Kontroller:
  1) alan yazılabilir mi (kritik parametreler kilitli)
  2) sayı mı, sonlu mu
  3) makinenin güvenli zarfı içinde mi
  4) tek adımda izin verilen değişimden büyük mü (ani sıçrama engeli)
  5) kullanıcının rolü yazmaya yetkili mi, panel yazma modunda mı
Geçen istek tek kullanımlık, süreli bir onay belirteci alır; makineye
yalnızca bu belirteç insan tarafından onaylanınca yazılır.
"""
from __future__ import annotations

import math
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

ONAY_SURESI_SN = 90


@dataclass
class Dogrulama:
    alan: str
    etiket: str
    birim: str
    mevcut: Optional[float]
    hedef: float
    aralik: List[float]
    gecti: bool
    nedenler: List[str] = field(default_factory=list)
    belirtec: Optional[str] = None

    def sozluk(self) -> Dict:
        return {"alan": self.alan, "etiket": self.etiket, "birim": self.birim,
                "mevcut": self.mevcut, "hedef": self.hedef, "min": self.aralik[0],
                "max": self.aralik[1], "gecti": self.gecti, "nedenler": self.nedenler,
                "belirtec": self.belirtec}


def sayi_mi(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


class GuvenlikKapisi:
    def __init__(self, alanlar: Dict[str, Dict]):
        self.alanlar = alanlar
        self._bekleyen: Dict[str, tuple] = {}
        self._kilit = threading.Lock()

    def dogrula(self, alan: str, hedef, mevcut: Optional[float], yetkili: bool,
                yazma_modu: bool) -> Dogrulama:
        tanim = self.alanlar.get(alan)
        if tanim is None:
            return Dogrulama(alan, alan, "", mevcut, float("nan"), [0, 0], False,
                             [f"'{alan}' tanımlı bir alan değil."])
        d = Dogrulama(alan, tanim["etiket"], tanim["birim"], mevcut,
                      float(hedef) if sayi_mi(hedef) else float("nan"),
                      list(tanim["aralik"]), True)
        if not yetkili:
            d.nedenler.append("Bu rol makineye yazamaz (usta/mühendis girişi gerekir).")
        if not yazma_modu:
            d.nedenler.append("Panel DANIŞMAN modunda — yazma kapalı.")
        if not tanim.get("yazilabilir"):
            d.nedenler.append(f"{tanim['etiket']} kritik parametre: kilitli (Faz 3).")
        if not sayi_mi(hedef):
            d.nedenler.append("Geçerli bir sayı değil.")
        else:
            lo, hi = tanim["aralik"]
            if not (lo <= hedef <= hi):
                d.nedenler.append(f"Güvenli aralık dışında ({lo}–{hi} {tanim['birim']}); "
                                  "mühendislik onayı gerekir.")
            adim = tanim.get("max_adim") or 0
            if adim and mevcut is not None and abs(hedef - mevcut) > adim:
                d.nedenler.append(f"Tek seferde en fazla {adim} {tanim['birim']} değişime izin var "
                                  f"(istenen {abs(hedef - mevcut):g}). Adım adım ilerle.")
        d.gecti = not d.nedenler
        if d.gecti:
            d.belirtec = secrets.token_urlsafe(12)
            with self._kilit:
                self._temizle()
                self._bekleyen[d.belirtec] = (d, time.monotonic() + ONAY_SURESI_SN)
        return d

    def onay_al(self, belirtec: str) -> Optional[Dogrulama]:
        """Belirteci tüket (tek kullanımlık). Süresi geçmişse None."""
        with self._kilit:
            self._temizle()
            kayit = self._bekleyen.pop(belirtec or "", None)
        return kayit[0] if kayit else None

    def _temizle(self) -> None:
        simdi = time.monotonic()
        for k in [k for k, (_, son) in self._bekleyen.items() if son < simdi]:
            del self._bekleyen[k]


def ayarlari_sinirla(degerler: Dict, alanlar: Dict) -> Dict:
    """AI'dan gelen öneri sözlüğünü süzer: yalnız bilinen alanlar ve sayılar.
    Aralık dışı değerleri DÜZELTMEZ; 'uyarilar' ile işaretler (insan görsün)."""
    temiz, uyarilar = {}, []
    for k, tanim in alanlar.items():
        v = degerler.get(k)
        if isinstance(v, str):
            try:
                v = float(v.replace(",", "."))
            except ValueError:
                v = None
        if not sayi_mi(v):
            continue
        v = round(float(v), 1)
        temiz[k] = int(v) if v.is_integer() else v
        lo, hi = tanim["aralik"]
        if not (lo <= v <= hi):
            uyarilar.append(f"{tanim['etiket']} {v:g} {tanim['birim']} makinenin güvenli "
                            f"aralığı ({lo}–{hi}) dışında — yazılamaz.")
    return {"degerler": temiz, "uyarilar": uyarilar}
