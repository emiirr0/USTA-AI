"""GÖZCÜ·AI köprüsü — "göz + akıl".

GÖZCÜ'nün çalışma klasöründeki dosyaları SALT OKUR:
  • sayaclar.json  → kalıcı toplam / sağlam / şüpheli / fire + tür kırılımı
  • gecmis.jsonl   → son muayeneler (yalnız son kısmı okunur)
USTA bu veriyi PANO'da gösterir ve AI bağlamına ekler: "çapak oranı
yükseliyor" bilgisi, makinenin canlı değerleriyle birlikte yoruma girer.
GÖZCÜ dosyalarına hiçbir zaman yazmaz.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

TUR_AD = {"capak": "Çapak", "kirik": "Kırık", "cizik": "Çizik", "leke": "Leke",
          "eksik_dolum": "Eksik dolum", "delik": "Delik", "cokuntu": "Çöküntü"}


def _son_satirlar(yol: Path, azami_bayt: int = 64_000) -> list:
    with open(yol, "rb") as f:
        f.seek(0, os.SEEK_END)
        boyut = f.tell()
        f.seek(max(0, boyut - azami_bayt))
        veri = f.read().decode("utf-8", "replace")
    satirlar = veri.splitlines()
    if boyut > azami_bayt and satirlar:
        satirlar = satirlar[1:]            # yarım kalmış ilk satırı at
    return satirlar


def oku(klasor: str) -> Optional[Dict]:
    """Bağlı değilse None; bağlı ama veri yoksa toplam=0 olan sözlük."""
    if not klasor:
        return None
    k = Path(klasor).expanduser()
    if not k.is_dir():
        return {"bagli": False, "hata": f"GÖZCÜ klasörü bulunamadı: {k}"}
    sonuc: Dict = {"bagli": True, "klasor": str(k), "toplam": 0, "saglam": 0, "supheli": 0,
                   "fire": 0, "turler": {}, "son": []}
    sayac = k / "sayaclar.json"
    if sayac.is_file():
        try:
            d = json.loads(sayac.read_text(encoding="utf-8"))
            sonuc.update(toplam=int(d.get("total", 0)), saglam=int(d.get("good", 0)),
                         supheli=int(d.get("suspect", 0)), fire=int(d.get("scrap", 0)),
                         turler={str(a): int(b) for a, b in (d.get("by_kind") or {}).items()})
        except (ValueError, OSError, TypeError) as e:
            sonuc["hata"] = f"sayaclar.json okunamadı: {e}"
    gecmis = k / "gecmis.jsonl"
    if gecmis.is_file():
        try:
            for satir in _son_satirlar(gecmis)[-8:]:
                try:
                    r = json.loads(satir)
                    sonuc["son"].append({"zaman": r.get("zaman", ""), "parca": r.get("parca", ""),
                                         "karar": r.get("karar", ""), "skor": r.get("skor")})
                except ValueError:
                    continue
            sonuc["son"].reverse()
        except OSError:
            pass
    t = sonuc["toplam"]
    sonuc["fire_orani"] = (sonuc["fire"] / t * 100) if t else 0.0
    if sonuc["turler"]:
        baskin = max(sonuc["turler"].items(), key=lambda x: x[1])[0]
        sonuc["baskin_tur"], sonuc["baskin_ad"] = baskin, TUR_AD.get(baskin, baskin)
    return sonuc
