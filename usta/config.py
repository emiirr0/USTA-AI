"""USTA·AI — yapılandırma.

Öncelik sırası (yüksekten düşüğe):
  1) ortam değişkenleri (USTA_*, ANTHROPIC_API_KEY)
  2) proje klasöründeki .env dosyası
  3) veri/ayarlar.json
  4) aşağıdaki varsayılanlar

API anahtarı ayarlar.json'a YAZILMAZ; yalnızca .env ya da ortam
değişkeninden okunur (yanlışlıkla GitHub'a yüklenmesin diye .env
.gitignore'dadır).
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

PROJE_KOKU = Path(__file__).resolve().parent.parent

# Makineye özel güvenli zarf: AI ne önerirse önersin bu aralıkların
# dışına YAZILAMAZ. Değerler presin/kalıbın sınırıdır, malzeme ideali değil.
VARSAYILAN_ALANLAR = {
    "z1": {"etiket": "Bölge 1", "birim": "°C", "yazilabilir": True, "aralik": [190, 255], "max_adim": 15},
    "z2": {"etiket": "Bölge 2", "birim": "°C", "yazilabilir": True, "aralik": [190, 255], "max_adim": 15},
    "z3": {"etiket": "Bölge 3", "birim": "°C", "yazilabilir": True, "aralik": [195, 260], "max_adim": 15},
    "nozul": {"etiket": "Nozul", "birim": "°C", "yazilabilir": True, "aralik": [200, 265], "max_adim": 15},
    "tutmaPress": {"etiket": "Tutma Bas.", "birim": "bar", "yazilabilir": True, "aralik": [25, 70], "max_adim": 10},
    "enjPress": {"etiket": "Enj. Basınç", "birim": "bar", "yazilabilir": False, "aralik": [60, 110], "max_adim": 0},
    "cevrim": {"etiket": "Çevrim", "birim": "s", "yazilabilir": False, "aralik": [8, 60], "max_adim": 0},
}

VARSAYILANLAR: Dict[str, Any] = {
    "makine": {
        "ad": "ENJEKSİYON PRESİ · HAT-3",
        "baglanti": "simulasyon",          # "simulasyon" | "opcua"
        "opcua_url": "opc.tcp://192.168.0.10:4840",
        "opcua_dugumler": {},              # alan -> düğüm kimliği (opcua.py'ye bakın)
        "alanlar": VARSAYILAN_ALANLAR,
    },
    "ai": {
        "saglayici": "otomatik",           # "otomatik" | "claude" | "ollama" | "uzman"
        "claude_model": "claude-sonnet-5-5",
        "anthropic_version": "2026-10-21",
        "ollama_url": "http://127.0.0.1:11434",
        "ollama_model": "llama3.1",
        "zaman_asimi_sn": 40,
    },
    "sunucu": {
        "port": 8080,
        "ag_erisimi": False,               # True: aynı ağdaki tablet bağlanabilir
    },
    # Rol PIN'leri: boş bırakılırsa rol seçimi PIN sormaz (tek panelli demo).
    # Sahada MUTLAKA doldurun.
    "roller": {
        "kullanicilar": [
            {"id": "u1", "ad": "Ahmet Y.", "rol": "operator"},
            {"id": "u2", "ad": "Mehmet K.", "rol": "usta"},
            {"id": "u3", "ad": "Elif D.", "rol": "muhendis"},
        ],
        "pin": {"operator": "", "usta": "", "muhendis": ""},
    },
    "gozcu": {
        "klasor": "",                      # GÖZCÜ·AI çalışma klasörü (sayaclar.json burada)
    },
}

ROL_TR = {"operator": "Operatör", "usta": "Usta", "muhendis": "Mühendis"}
YETKI = {
    "yaz": ("usta", "muhendis"),
    "is_duzenle": ("usta", "muhendis"),
    "is_sec": ("usta", "muhendis"),
    "belge_yukle": ("muhendis",),
}


def _derin_birlestir(taban: dict, ust: dict) -> dict:
    out = copy.deepcopy(taban)
    for k, v in (ust or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _derin_birlestir(out[k], v)
        else:
            out[k] = v
    return out


def env_dosyasi_oku(yol: Path) -> Dict[str, str]:
    """Basit .env okuyucu: ANAHTAR=deger, # yorum, tırnaklar soyulur."""
    sonuc: Dict[str, str] = {}
    if not yol.is_file():
        return sonuc
    for satir in yol.read_text(encoding="utf-8-sig").splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        k, v = satir.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k:
            sonuc[k] = v
    return sonuc


class Ayarlar:
    """Çalışma klasörü + birleştirilmiş yapılandırma."""

    def __init__(self, veri_klasoru: Path | None = None):
        self.veri = Path(veri_klasoru or os.environ.get("USTA_VERI") or PROJE_KOKU / "veri")
        self.veri.mkdir(parents=True, exist_ok=True)
        self.dosya = self.veri / "ayarlar.json"
        self.uyarilar: list[str] = []
        kullanici: dict = {}
        if self.dosya.is_file():
            try:
                kullanici = json.loads(self.dosya.read_text(encoding="utf-8-sig"))
                if not isinstance(kullanici, dict):
                    raise ValueError("kök bir nesne değil")
            except (ValueError, OSError) as e:
                self.uyarilar.append(f"ayarlar.json okunamadı ({e}); varsayılanlar kullanıldı.")
                kullanici = {}
        else:
            self._ilk_dosyayi_yaz()
        self.d = _derin_birlestir(VARSAYILANLAR, kullanici)

        env = env_dosyasi_oku(PROJE_KOKU / ".env")
        env.update({k: v for k, v in os.environ.items()
                    if k.startswith("USTA_") or k == "ANTHROPIC_API_KEY"})
        self.api_anahtari = env.get("ANTHROPIC_API_KEY", "").strip()
        if env.get("USTA_AI"):
            self.d["ai"]["saglayici"] = env["USTA_AI"].strip().lower()
        if env.get("USTA_MODEL"):
            self.d["ai"]["claude_model"] = env["USTA_MODEL"].strip()
        if env.get("USTA_OLLAMA_MODEL"):
            self.d["ai"]["ollama_model"] = env["USTA_OLLAMA_MODEL"].strip()
        if env.get("USTA_PORT", "").isdigit():
            self.d["sunucu"]["port"] = int(env["USTA_PORT"])
        if env.get("USTA_GOZCU"):
            self.d["gozcu"]["klasor"] = env["USTA_GOZCU"]
        self._dogrula()

    def _ilk_dosyayi_yaz(self) -> None:
        """İlk çalıştırmada düzenlenebilir bir ayar dosyası bırak."""
        try:
            ornek = {k: v for k, v in VARSAYILANLAR.items() if k != "makine"}
            ornek["makine"] = {"ad": VARSAYILANLAR["makine"]["ad"],
                               "baglanti": "simulasyon"}
            self.dosya.write_text(json.dumps(ornek, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        except OSError:
            pass

    def _dogrula(self) -> None:
        ai = self.d["ai"]
        if ai["saglayici"] not in ("otomatik", "claude", "ollama", "uzman"):
            self.uyarilar.append(f"Bilinmeyen AI sağlayıcı '{ai['saglayici']}' → 'otomatik' kullanıldı.")
            ai["saglayici"] = "otomatik"
        for anahtar, alan in self.d["makine"]["alanlar"].items():
            a = alan.get("aralik")
            if not (isinstance(a, list) and len(a) == 2 and a[0] < a[1]):
                self.uyarilar.append(f"'{anahtar}' alanının güvenli aralığı geçersiz; varsayılana dönüldü.")
                alan.update(VARSAYILAN_ALANLAR.get(anahtar, {}))
        port = self.d["sunucu"]["port"]
        if not (isinstance(port, int) and 1 <= port <= 65535):
            self.d["sunucu"]["port"] = 8080

    # kısayollar
    @property
    def alanlar(self) -> dict:
        return self.d["makine"]["alanlar"]

    @property
    def makine_adi(self) -> str:
        return self.d["makine"]["ad"]

    def kullanicilar(self) -> list:
        return self.d["roller"]["kullanicilar"]

    def pin(self, rol: str) -> str:
        return str(self.d["roller"].get("pin", {}).get(rol, "") or "")
