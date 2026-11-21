"""Bulut ve yerel dil modeli sağlayıcıları (yalnız standart kütüphane).

Her sağlayıcı aynı sözleşmeyi uygular:
    sor(sistem: str, mesajlar: [{"role","content"}], azami: int) -> str
Hata durumunda AIHatasi fırlatır; aracı bunu yakalayıp uzmana düşer.
"""
from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from typing import Dict, List


class AIHatasi(RuntimeError):
    pass


def _post(url: str, govde: Dict, basliklar: Dict, zaman_asimi: float) -> Dict:
    istek = urllib.request.Request(url, data=json.dumps(govde).encode("utf-8"),
                                   headers={"content-type": "application/json", **basliklar},
                                   method="POST")
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi,
                                    context=ssl.create_default_context()) as y:
            return json.loads(y.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            ayrinti = json.loads(e.read().decode("utf-8")).get("error", {})
            mesaj = ayrinti.get("message") if isinstance(ayrinti, dict) else str(ayrinti)
        except Exception:
            mesaj = ""
        if e.code == 401:
            raise AIHatasi("API anahtarı geçersiz (401). .env dosyasındaki ANTHROPIC_API_KEY'i kontrol et.") from e
        if e.code == 429:
            raise AIHatasi("API kullanım sınırına takıldı (429); biraz sonra tekrar dene.") from e
        raise AIHatasi(f"Sunucu hatası {e.code}: {mesaj or e.reason}") from e
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        raise AIHatasi(f"Bağlantı kurulamadı: {getattr(e, 'reason', e)}") from e
    except (ValueError, json.JSONDecodeError) as e:
        raise AIHatasi("Sunucudan okunamayan yanıt geldi.") from e


class ClaudeSaglayici:
    ad = "claude"

    def __init__(self, api_anahtari: str, model: str, surum: str, zaman_asimi: float,
                 url: str = "https://api.anthropic.com/v1/messages"):
        if not api_anahtari:
            raise AIHatasi("ANTHROPIC_API_KEY tanımlı değil.")
        self.anahtar, self.model, self.surum = api_anahtari, model, surum
        self.zaman_asimi, self.url = zaman_asimi, url

    def sor(self, sistem: str, mesajlar: List[Dict], azami: int = 900) -> str:
        yanit = _post(self.url,
                      {"model": self.model, "max_tokens": azami, "system": sistem,
                       "messages": mesajlar},
                      {"x-api-key": self.anahtar, "anthropic-version": self.surum},
                      self.zaman_asimi)
        metin = "".join(b.get("text", "") for b in yanit.get("content", [])
                        if isinstance(b, dict) and b.get("type") == "text").strip()
        if not metin:
            raise AIHatasi("Model boş yanıt döndürdü.")
        return metin


class OllamaSaglayici:
    """Tamamen yerel model (ollama.com). İnternet gerekmez; veri tesisten çıkmaz."""
    ad = "ollama"

    def __init__(self, url: str, model: str, zaman_asimi: float):
        self.url, self.model, self.zaman_asimi = url.rstrip("/"), model, zaman_asimi

    def sor(self, sistem: str, mesajlar: List[Dict], azami: int = 900) -> str:
        yanit = _post(f"{self.url}/api/chat",
                      {"model": self.model, "stream": False,
                       "messages": [{"role": "system", "content": sistem}] + mesajlar,
                       "options": {"num_predict": azami}},
                      {}, self.zaman_asimi)
        metin = ((yanit.get("message") or {}).get("content") or "").strip()
        if not metin:
            raise AIHatasi("Yerel model boş yanıt döndürdü.")
        return metin
