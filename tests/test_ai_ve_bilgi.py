"""AI aracısı (sahte API sunucusuyla), çevrimdışı uzman ve belge ayrıştırma."""
import io
import json
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from usta.ai import AIAracisi, json_ayikla
from usta.ai import uzman
from usta.ai.providers import AIHatasi, ClaudeSaglayici, OllamaSaglayici
from usta.config import VARSAYILAN_ALANLAR
from usta.knowledge import TOHUM, belgeyi_ayristir, getir, kucult

DURUM = {"makine": "T", "baglanti": "simülasyon", "durum": "ÇALIŞIYOR",
         "pv": {"z1": 218, "tutmaPress": 45, "yastik": 2.1}, "sp": {"z1": 218.0, "nozul": 230.0, "tutmaPress": 45.0},
         "is": {"urun": "Konnektör", "kalip": "K-114", "malzeme": "ABS"}}


class SahteAPI(BaseHTTPRequestHandler):
    """Claude Messages API ve Ollama /api/chat biçimini taklit eder; gelen isteği kaydeder."""
    son = None
    cevap = "Tutma basıncını 2 bar düşür."
    kod = 200

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        SahteAPI.son = {"yol": self.path, "baslik": {k.lower(): v for k, v in self.headers.items()},
                        "govde": json.loads(self.rfile.read(n))}
        if SahteAPI.kod != 200:
            self.send_response(SahteAPI.kod)
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": "hata"}}).encode())
            return
        if self.path == "/v1/messages":
            veri = {"content": [{"type": "text", "text": SahteAPI.cevap}]}
        else:
            veri = {"message": {"role": "assistant", "content": SahteAPI.cevap}}
        b = json.dumps(veri).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


@pytest.fixture
def sahte_api():
    SahteAPI.kod, SahteAPI.cevap, SahteAPI.son = 200, "Tutma basıncını 2 bar düşür.", None
    s = HTTPServer(("127.0.0.1", 0), SahteAPI)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()


def test_claude_istek_bicimi(sahte_api):
    p = ClaudeSaglayici("sk-x", "claude-sonnet-5-5", "2026-10-21", 5, url=f"{sahte_api}/v1/messages")
    assert p.sor("sistem", [{"role": "user", "content": "selam"}], 50) == "Tutma basıncını 2 bar düşür."
    b, g = SahteAPI.son["baslik"], SahteAPI.son["govde"]
    assert b.get("x-api-key") == "sk-x" and b.get("anthropic-version") == "2026-10-21"
    assert g["model"] == "claude-sonnet-5-5" and g["system"] == "sistem" and g["max_tokens"] == 50
    assert "temperature" not in g   # 2026-10-21 sürümünde gönderilirse 400 döner


def test_claude_401_anlasilir_hata(sahte_api):
    SahteAPI.kod = 401
    p = ClaudeSaglayici("yanlis", "m", "v", 5, url=f"{sahte_api}/v1/messages")
    with pytest.raises(AIHatasi, match="anahtarı geçersiz"):
        p.sor("s", [{"role": "user", "content": "x"}])


def test_ollama_istek_bicimi(sahte_api):
    p = OllamaSaglayici(sahte_api, "llama3.1", 5)
    assert "düşür" in p.sor("sis", [{"role": "user", "content": "x"}])
    g = SahteAPI.son["govde"]
    assert SahteAPI.son["yol"] == "/api/chat" and g["stream"] is False
    assert g["messages"][0] == {"role": "system", "content": "sis"}


def test_ulasilamayan_saglayici_uzmana_duser(ayarlar):
    ayarlar.d["ai"].update(saglayici="ollama", ollama_url="http://127.0.0.1:9", zaman_asimi_sn=2)
    a = AIAracisi(ayarlar)
    r = a.sohbet([{"role": "user", "content": "kenarlarda çapak var"}], DURUM, TOHUM)
    assert r["kaynak"] == "uzman" and r["yedek"] is True and "Çapak" in r["metin"]


def test_anahtarsiz_otomatik_uzman_secer(ayarlar):
    ayarlar.d["ai"]["saglayici"] = "otomatik"
    ayarlar.api_anahtari = ""
    assert AIAracisi(ayarlar).secim == "uzman"


def test_recete_model_jsonu_guvenlikten_gecer(ayarlar, sahte_api):
    ayarlar.d["ai"].update(saglayici="ollama", ollama_url=sahte_api)
    SahteAPI.cevap = 'Tabii! ```json\n{"z1": 230, "z2": 235, "z3": 300, "nozul": 245, "enjPress": 85, "tutmaPress": 45, "cevrim": 24, "not": "dikkat"}\n```'
    r = AIAracisi(ayarlar).recete("ABS", "Orta", TOHUM)
    assert r["kaynak"] == "ollama" and r["degerler"]["z3"] == 300
    assert any("Bölge 3" in u for u in r["uyarilar"])   # aralık dışı işaretlendi


def test_recete_bozuk_jsonda_uzmana_duser(ayarlar, sahte_api):
    ayarlar.d["ai"].update(saglayici="ollama", ollama_url=sahte_api)
    SahteAPI.cevap = "Bunu bilemem."
    r = AIAracisi(ayarlar).recete("PP (Polipropilen)", "İnce (<2 mm)", TOHUM)
    assert r["kaynak"] == "uzman" and r["yedek"] and r["degerler"]["z1"] == 210  # K-207 (205) + ince (+5)


def test_json_ayikla():
    assert json_ayikla('önsöz {"a": {"b": 1}} sonsöz') == {"a": {"b": 1}}
    assert json_ayikla('{bozuk} sonra {"x": 2}') == {"x": 2}
    with pytest.raises(AIHatasi):
        json_ayikla("json yok")


# ── çevrimdışı uzman ─────────────────────────────────────────────────
@pytest.mark.parametrize("soru,beklenen", [
    ("Ürün kenarlarında çapak var", "Çapak"), ("kalıp tam dolmuyor", "Eksik dolum"),
    ("yüzeyde çöküntü oluyor", "Çöküntü"), ("parçada gümüş çizgiler", "Gümüşleme"),
    ("akış sonunda yanık var", "Yanık"), ("çevrim süresini nasıl kısaltırım", "Çevrim"),
])
def test_uzman_kusur_teshisi(soru, beklenen):
    assert beklenen in uzman.sohbet(soru, DURUM, VARSAYILAN_ALANLAR, [])


def test_uzman_ayar_onerisi_guvenli_aralikta():
    m = uzman.sohbet("çapak", {"sp": {"tutmaPress": 26.0, "nozul": 230.0}}, VARSAYILAN_ALANLAR, [])
    assert "Tutma Bas.: 26 → 25" in m             # alt sınır 25'e kadar


def test_uzman_dusuk_yastik_uyarisi():
    assert "Yastık şu an 2.1" in uzman.sohbet("tam dolmuyor", DURUM, VARSAYILAN_ALANLAR, [])


def test_uzman_bilinmeyen_konu_ve_alarm_kodu():
    assert "net bir eşleşme" in uzman.sohbet("hava nasıl", DURUM, VARSAYILAN_ALANLAR, [])
    assert "Yağ soğutucu" in uzman.sohbet("ALM-310 ne demek", DURUM, VARSAYILAN_ALANLAR, [])


def test_uzman_pc_guvenli_aralik_disi_uyarir():
    r = uzman.recete("PC (Polikarbonat)", "Orta", VARSAYILAN_ALANLAR, TOHUM)
    assert "güvenli aralığı" in r["not"]


# ── bilgi tabanı ─────────────────────────────────────────────────────
def test_turkce_kucuk_harf():
    assert kucult("İSTANBUL ILIK") == "istanbul ılık"


def test_getir_alakasiz_kayit_getirmez():
    assert getir(TOHUM, "hava durumu bugün", "ABS") == []
    assert getir(TOHUM, "POM bozunma formaldehit")[0]["id"] == "DS-POM"


def _docx(paragraflar):
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    govde = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraflar)
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document {ns}><w:body>{govde}</w:body></w:document>')
    return b.getvalue()


def _xlsx(satirlar):
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rows = "".join("<row>" + "".join(f'<c t="inlineStr"><is><t>{v}</t></is></c>' for v in r) + "</row>" for r in satirlar)
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0"?><worksheet {ns}><sheetData>{rows}</sheetData></worksheet>')
    return b.getvalue()


def test_docx_ayristirma():
    a, u = belgeyi_ayristir("PETG föyü.docx", _docx(["PETG İşleme Datasheet", "Kovan 230–250°C, kurutma 65°C / 4 saat."]))
    assert not u and a and a[0]["malzeme"] == "PETG" and a[0]["tur"] == "datasheet"


def test_xlsx_recete_tablosu():
    a, u = belgeyi_ayristir("receteler.xlsx", _xlsx([["Kalıp", "Malzeme", "z1", "z2", "z3", "nozul", "tutma"],
                                                     ["K-450", "PETG", "238", "242", "245", "248", "50"]]))
    assert len(a) == 1 and a[0]["tur"] == "recete" and a[0]["malzeme"] == "PETG" and "K-450" in a[0]["baslik"]


def test_csv_noktali_virgul_ve_cp1254():
    veri = "Kalıp;Malzeme;Not\nK-1;PP;Menteşede beyazlama\n".encode("cp1254")
    a, _ = belgeyi_ayristir("liste.csv", veri)
    assert a and "Menteşede" in a[0]["metin"]


@pytest.mark.parametrize("ad,veri,parca", [
    ("eski.xls", b"x", "eski Office"), ("resim.png", b"x", "desteklenmiyor"),
    ("bos.txt", b"", "boş"), ("bozuk.docx", b"bu zip degil", "açılamadı"),
])
def test_ayristirma_hatalari_anlasilir(ad, veri, parca):
    a, u = belgeyi_ayristir(ad, veri)
    assert a == [] and parca in u[0]
