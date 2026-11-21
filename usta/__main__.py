"""USTA·AI komut satırı.

  python -m usta                 → başlat, tarayıcıda paneli aç
  python -m usta --port 8090     → farklı port
  python -m usta --ag            → aynı ağdaki tabletten erişim (dikkat!)
  python -m usta --tarayici-yok  → tarayıcı açma (servis/edge cihazı)
  python -m usta kontrol         → kurulum tanılaması (sorun yaşarsan önce bunu çalıştır)
"""
from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import platform
import socket
import sqlite3
import sys
import threading
import webbrowser

from . import __version__

ASGARI_PY = (3, 9)


def _konsol_utf8() -> None:
    """Windows konsolunda Türkçe karakterler bozulmasın."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _log_kur(veri) -> None:
    h = logging.handlers.RotatingFileHandler(veri / "usta.log", maxBytes=1_000_000,
                                             backupCount=3, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    kok = logging.getLogger("usta")
    kok.setLevel(logging.INFO)
    kok.addHandler(h)


def _bos_port(baslangic: int, ag: bool) -> int:
    adres = "0.0.0.0" if ag else "127.0.0.1"
    for p in range(baslangic, baslangic + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((adres, p))
                return p
            except OSError:
                continue
    raise OSError(f"{baslangic}–{baslangic + 19} arasında boş port yok.")


def _yerel_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def kontrol() -> int:
    from .app import Usta
    from .config import Ayarlar
    tamam = True

    def satir(ok: bool, metin: str) -> None:
        nonlocal tamam
        tamam &= ok
        print(("  [ OK ] " if ok else "  [HATA] ") + metin)

    print(f"USTA·AI {__version__} — kurulum kontrolü\n")
    satir(sys.version_info >= ASGARI_PY,
          f"Python {platform.python_version()} (gereken ≥ {ASGARI_PY[0]}.{ASGARI_PY[1]})")
    satir(sqlite3.sqlite_version_info >= (3, 24, 0), f"SQLite {sqlite3.sqlite_version} (gereken ≥ 3.24)")
    from .server import WEB
    satir((WEB / "index.html").is_file() and (WEB / "app.js").is_file(), "Arayüz dosyaları (usta/web)")
    try:
        ay = Ayarlar()
        satir(True, f"Veri klasörü yazılabilir: {ay.veri}")
        for u in ay.uyarilar:
            print("  [UYARI] " + u)
    except OSError as e:
        satir(False, f"Veri klasörü oluşturulamadı: {e}")
        return 1
    try:
        p = _bos_port(ay.d["sunucu"]["port"], False)
        satir(True, f"Kullanılabilir port: {p}")
    except OSError as e:
        satir(False, str(e))
    u = Usta(ay)
    b = u.ai.bilgi()
    print(f"  [BİLGİ] AI kaynağı: {b['etiket']}" + (f" — {b['uyari']}" if b["uyari"] else ""))
    sonuc = u.ai_dene()
    satir(sonuc["tamam"], f"AI bağlantı testi: {sonuc['mesaj']}")
    if ay.d["makine"]["baglanti"] == "opcua":
        try:
            import asyncua  # noqa: F401
            satir(True, "OPC UA kütüphanesi (asyncua) kurulu")
        except ImportError:
            satir(False, "OPC UA seçili ama 'asyncua' kurulu değil: pip install asyncua")
    u.depo.kapat()
    print("\n" + ("Her şey hazır. Başlatmak için: python -m usta" if tamam
                  else "Yukarıdaki [HATA] satırlarını düzeltip tekrar dene."))
    return 0 if tamam else 1


def main(argv=None) -> int:
    _konsol_utf8()
    if sys.version_info < ASGARI_PY:
        print(f"USTA·AI için Python {ASGARI_PY[0]}.{ASGARI_PY[1]} ya da üstü gerekli "
              f"(sende {platform.python_version()}). python.org'dan güncel sürümü kur.")
        return 1
    ap = argparse.ArgumentParser(prog="usta", description="USTA·AI operatör danışmanı")
    ap.add_argument("komut", nargs="?", default="baslat", choices=["baslat", "kontrol"])
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--ag", action="store_true", help="aynı ağdaki cihazlardan erişime izin ver")
    ap.add_argument("--tarayici-yok", action="store_true", help="tarayıcıyı otomatik açma")
    ap.add_argument("--surum", action="version", version=f"USTA·AI {__version__}")
    a = ap.parse_args(argv)
    if a.komut == "kontrol":
        return kontrol()

    from .app import Usta
    from .config import Ayarlar
    from .server import sunucu_kur
    ay = Ayarlar()
    _log_kur(ay.veri)
    ag = a.ag or bool(ay.d["sunucu"].get("ag_erisimi"))
    try:
        port = _bos_port(a.port or ay.d["sunucu"]["port"], ag)
    except OSError as e:
        print(f"Port açılamadı: {e}")
        return 1
    usta = Usta(ay)
    try:
        usta.baslat()
    except Exception as e:
        print(f"Makine bağlantısı kurulamadı: {e}\n"
              "ayarlar.json'da \"baglanti\": \"simulasyon\" yapıp tekrar deneyebilirsin.")
        return 1
    httpd = sunucu_kur(usta, port, ag)
    url = f"http://127.0.0.1:{port}/"
    b = usta.ai.bilgi()
    print("=" * 62)
    print(f"  USTA·AI {__version__} çalışıyor")
    print(f"  Panel adresi : {url}")
    if ag:
        print(f"  Tablet için  : http://{_yerel_ip()}:{port}/   (aynı ağda)")
        print("  ⚠ Ağ erişimi AÇIK: rol PIN'lerini veri/ayarlar.json'da tanımla.")
    print(f"  Makine       : {usta.makine.snapshot().get('baglanti')}")
    print(f"  AI kaynağı   : {b['etiket']}" + (f"  ({b['uyari']})" if b['uyari'] else ""))
    for u in ay.uyarilar:
        print(f"  ⚠ {u}")
    print("  Durdurmak için bu pencerede Ctrl+C")
    print("=" * 62)
    if not a.tarayici_yok and not os.environ.get("USTA_TARAYICI_YOK"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nKapatılıyor…")
    finally:
        httpd.server_close()
        usta.durdur()
    return 0


if __name__ == "__main__":
    sys.exit(main())
