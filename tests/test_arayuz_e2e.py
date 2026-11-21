"""Gerçek tarayıcıda uçtan uca arayüz testi (Playwright + Chromium).

Playwright kurulu değilse atlanır:
    pip install playwright && python -m playwright install chromium
"""
import os
import shutil
import threading

import pytest

pw = pytest.importorskip("playwright.sync_api")

from usta.server import sunucu_kur  # noqa: E402


def _tarayici(p):
    yol = os.environ.get("CHROME_YOLU") or shutil.which("google-chrome") or shutil.which("chromium")
    try:
        return p.chromium.launch(**({"executable_path": yol} if yol else {}), args=["--no-sandbox"])
    except Exception as e:  # tarayıcı ikilisi yok
        pytest.skip(f"Chromium başlatılamadı: {e}")


@pytest.fixture
def panel(usta):
    usta.makine.start()
    httpd = sunucu_kur(usta, 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/"
    httpd.shutdown()
    httpd.server_close()


def test_panel_ana_akislar(panel):
    with pw.sync_playwright() as p:
        b = _tarayici(p)
        sayfa = b.new_page(viewport={"width": 1366, "height": 820})
        hatalar = []
        sayfa.on("pageerror", lambda e: hatalar.append(str(e)))
        sayfa.on("console", lambda m: hatalar.append(m.text) if m.type == "error" else None)
        sayfa.goto(panel)
        sayfa.wait_for_selector("text=Canlı Üretim Panosu")
        # AI (çevrimdışı uzman)
        sayfa.click("text=AI ASİSTAN")
        sayfa.click("text=Kalıp tam dolmuyor (short shot), ne yapmalıyım?")
        sayfa.wait_for_selector("text=Eksik dolum (short shot) — muhtemel sebepler")
        # usta girişi + onaylı yazma
        sayfa.click("text=Ahmet Y.")
        sayfa.click("text=Mehmet K.")
        sayfa.click("text=Onaylı Yazma")
        sayfa.wait_for_selector("text=ONAYLI YAZMA · FAZ 2")
        sayfa.click("text=REÇETE")
        sayfa.click("text=Başlangıç ayarı öner")
        sayfa.click("text=Uygula → >> nth=0")
        sayfa.click("text=✓ Onayla ve yaz")
        sayfa.wait_for_selector("text=makineye yazıldı")
        sayfa.click("text=KAYIT")
        sayfa.wait_for_selector("text=onaylayan: Mehmet K.")
        # arıza senaryosu → alarm → otomatik yorum
        sayfa.click("text=ALARMLAR")
        sayfa.click("text=Bölge 2 rezistans arızası")
        sayfa.wait_for_selector("text=Bölge 2 sıcaklık sapması", timeout=20000)
        sayfa.wait_for_selector("text=Rezistans akımını", timeout=10000)
        # bilgi tabanı (operatör değil, usta: yükleme alanı görünmez)
        sayfa.click("text=BİLGİ TABANI")
        sayfa.wait_for_selector("text=Kanıtlı Reçeteler")
        b.close()
        assert hatalar == [], hatalar
