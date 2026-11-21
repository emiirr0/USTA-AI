"""USTA·AI yerel HTTP sunucusu (yalnız standart kütüphane).

Panel ekranı (tarayıcı) ile çekirdek arasındaki ince katman. Güvenlik:
  • Varsayılan olarak yalnız bu bilgisayardan erişilir (127.0.0.1).
  • Durum değiştiren her istek 'X-Usta: 1' başlığı ister: başka bir web
    sitesi kullanıcının tarayıcısı üzerinden makineye istek atamaz (CSRF).
  • Host başlığı denetlenir (DNS-rebinding saldırısına karşı).
  • Statik dosyalar yalnız web/ klasöründen verilir (yol kaçışı engelli).
"""
from __future__ import annotations

import json
import logging
import mimetypes
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .app import Hata, Usta

WEB = Path(__file__).resolve().parent / "web"
AZAMI_GOVDE = 15 * 1024 * 1024
log = logging.getLogger("usta")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/javascript", ".js")


class Yonlendirici:
    def __init__(self):
        self.yollar: List[Tuple[str, re.Pattern, Callable]] = []

    def ekle(self, yontem: str, desen: str):
        def kaydet(f):
            self.yollar.append((yontem, re.compile("^" + desen + "$"), f))
            return f
        return kaydet

    def bul(self, yontem: str, yol: str):
        yol_eslesti = False
        for y, d, f in self.yollar:
            m = d.match(yol)
            if m:
                yol_eslesti = True
                if y == yontem:
                    return f, m.groupdict()
        return (None, {"_405": True}) if yol_eslesti else (None, {})


R = Yonlendirici()


def _g(govde: Dict, anahtar: str, varsayilan=None):
    return govde.get(anahtar, varsayilan) if isinstance(govde, dict) else varsayilan


# ── API uçları ─────────────────────────────────────────────────────────
@R.ekle("GET", r"/api/meta")
def _meta(u: Usta, g, p): return u.meta()
@R.ekle("GET", r"/api/durum")
def _durum(u, g, p): return u.durum()
@R.ekle("POST", r"/api/oturum")
def _oturum(u, g, p): return u.kullanici_sec(_g(g, "kullanici_id", ""), _g(g, "pin", ""))
@R.ekle("POST", r"/api/mod")
def _mod(u, g, p): return u.mod_sec(_g(g, "mod", ""))
@R.ekle("POST", r"/api/sohbet")
def _sohbet(u, g, p): return u.sohbet(_g(g, "gecmis", []))
@R.ekle("POST", r"/api/alarm/yorum")
def _ayorum(u, g, p): return u.alarm_yorumu(_g(g, "id", ""))
@R.ekle("POST", r"/api/alarm/gordum")
def _agordum(u, g, p): return u.alarm_gordum(_g(g, "id", ""))
@R.ekle("POST", r"/api/alarm/senaryo")
def _asenaryo(u, g, p): return u.senaryo(_g(g, "tur", "rastgele"))
@R.ekle("GET", r"/api/alarm/gecmis")
def _agecmis(u, g, p): return {"alarmlar": u.depo.alarm_gecmisi()}
@R.ekle("GET", r"/api/isler")
def _isler(u, g, p): return {"isler": u.depo.is_listesi(), "aktif": u.aktif_is_id}
@R.ekle("POST", r"/api/isler")
def _is_ekle(u, g, p): return u.is_ekle(_g(g, "urun"), _g(g, "kalip"), _g(g, "malzeme"))
@R.ekle("PUT", r"/api/isler/(?P<id>[A-Za-z0-9_\-]+)")
def _is_guncelle(u, g, p): return u.is_guncelle(p["id"], _g(g, "ayarlar", {}))
@R.ekle("DELETE", r"/api/isler/(?P<id>[A-Za-z0-9_\-]+)")
def _is_sil(u, g, p): return u.is_sil(p["id"])
@R.ekle("POST", r"/api/isler/(?P<id>[A-Za-z0-9_\-]+)/aktif")
def _is_aktif(u, g, p): return u.is_aktif(p["id"])
@R.ekle("POST", r"/api/isler/(?P<id>[A-Za-z0-9_\-]+)/oner")
def _is_oner(u, g, p): return u.is_oner(p["id"])
@R.ekle("POST", r"/api/recete")
def _recete(u, g, p): return u.recete(_g(g, "malzeme"), _g(g, "et"))
@R.ekle("GET", r"/api/sonuclar")
def _sonuclar(u, g, p): return {"sonuclar": u.depo.sonuclar()}
@R.ekle("POST", r"/api/sonuclar")
def _sonuc(u, g, p): return u.sonuc_kaydet(_g(g, "malzeme"), _g(g, "et"), _g(g, "sonuc"), _g(g, "recete", {}))
@R.ekle("POST", r"/api/yazma/dogrula")
def _ydogrula(u, g, p): return u.yazma_dogrula(_g(g, "alan", ""), _g(g, "deger"), _g(g, "kaynak", ""))
@R.ekle("POST", r"/api/yazma/onayla")
def _yonayla(u, g, p): return u.yazma_onayla(_g(g, "belirtec", ""))
@R.ekle("GET", r"/api/kayit")
def _kayit(u, g, p): return {"kayitlar": u.depo.kayitlar()}
@R.ekle("GET", r"/api/bilgi")
def _bilgi(u, g, p): return {"kayitlar": u.depo.bilgi_listesi()}
@R.ekle("POST", r"/api/bilgi/ekle")
def _bilgi_ekle(u, g, p): return u.bilgi_ekle(_g(g, "kayitlar", []))
@R.ekle("DELETE", r"/api/bilgi/(?P<id>[A-Za-z0-9_\-]+)")
def _bilgi_sil(u, g, p): return u.bilgi_sil(p["id"])
@R.ekle("POST", r"/api/ai/dene")
def _ai_dene(u, g, p): return u.ai_dene()


class Isleyici(BaseHTTPRequestHandler):
    server_version = "USTA-AI"
    sys_version = ""
    usta: Usta = None            # sunucu kurulurken atanır
    izinli_hostlar: Optional[set] = None   # None = ağ modu (denetim gevşek)

    def log_message(self, fmt, *args):   # konsolu kirletme, dosyaya yaz
        log.info("%s %s", self.address_string(), fmt % args)

    # ── yardımcılar ──
    def _json(self, kod: int, veri) -> None:
        govde = json.dumps(veri, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(govde)

    def _host_gecerli(self) -> bool:
        if self.izinli_hostlar is None:
            return True
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in self.izinli_hostlar

    def _govde(self) -> bytes:
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise Hata("Geçersiz Content-Length.")
        if n > AZAMI_GOVDE:
            raise Hata("İstek çok büyük (en fazla 15 MB).", 413)
        return self.rfile.read(n) if n > 0 else b""

    def _isle(self, yontem: str) -> None:
        if not self._host_gecerli():
            return self._json(403, {"hata": "Geçersiz Host başlığı."})
        yol = urllib.parse.urlsplit(self.path).path
        if not yol.startswith("/api/"):
            if yontem != "GET":
                return self._json(405, {"hata": "İzin verilmeyen yöntem."})
            return self._statik(yol)
        f, params = R.bul(yontem, yol)
        if f is None:
            return self._json(405 if params.get("_405") else 404,
                              {"hata": "İzin verilmeyen yöntem." if params.get("_405") else "Bulunamadı."})
        try:
            if yontem != "GET" and self.headers.get("X-Usta") != "1":
                raise Hata("Eksik güvenlik başlığı.", 403)
            ham =self._govde() if yontem != "GET" else b""
            govde = {}
            if ham:
                try:
                    govde = json.loads(ham.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise Hata("Gövde geçerli JSON değil.")
            self._json(200, f(self.usta, govde, params))
        except Hata as e:
            self._json(e.kod, {"hata": str(e)})
        except Exception:
            log.exception("Beklenmeyen hata: %s %s", yontem, yol)
            self._json(500, {"hata": "Beklenmeyen bir hata oldu; ayrıntı veri/usta.log dosyasında."})

    def _ayristir(self) -> None:
        try:
            if not self._host_gecerli():
                raise Hata("Geçersiz Host başlığı.", 403)
            if self.headers.get("X-Usta") != "1":
                raise Hata("Eksik güvenlik başlığı.", 403)
            ad = urllib.parse.unquote(self.headers.get("X-Dosya-Adi") or "belge.txt")[:200]
            self._json(200, self.usta.bilgi_ayristir(ad, self._govde()))
        except Hata as e:
            self._json(e.kod, {"hata": str(e)})
        except Exception:
            log.exception("Belge ayrıştırma hatası")
            self._json(500, {"hata": "Belge işlenirken beklenmeyen hata."})

    def _statik(self, yol: str) -> None:
        if yol in ("", "/"):
            yol = "/index.html"
        elif yol == "/favicon.ico":
            yol = "/favicon.svg"
        hedef = (WEB / urllib.parse.unquote(yol).lstrip("/")).resolve()
        try:
            hedef.relative_to(WEB)
        except ValueError:
            return self._json(404, {"hata": "Bulunamadı."})
        if not hedef.is_file():
            return self._json(404, {"hata": "Bulunamadı."})
        veri = hedef.read_bytes()
        tur = mimetypes.guess_type(hedef.name)[0] or "application/octet-stream"
        if tur.startswith("text/") or tur.endswith("javascript"):
            tur += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(veri)

    def do_GET(self): self._isle("GET")
    def do_PUT(self): self._isle("PUT")
    def do_DELETE(self): self._isle("DELETE")

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path == "/api/bilgi/ayristir":
            return self._ayristir()
        self._isle("POST")


def sunucu_kur(usta: Usta, port: int, ag: bool = False) -> ThreadingHTTPServer:
    """Sunucuyu kur (başlatmaz). port=0 → boş port seçilir (testler)."""
    sinif = type("UstaIsleyici", (Isleyici,), {
        "usta": usta,
        "izinli_hostlar": None if ag else {"localhost", "127.0.0.1", "::1"},
    })
    adres = "0.0.0.0" if ag else "127.0.0.1"
    httpd = ThreadingHTTPServer((adres, port), sinif)
    httpd.daemon_threads = True
    return httpd
