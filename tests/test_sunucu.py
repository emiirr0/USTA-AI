"""Gerçek HTTP üzerinden uçtan uca testler: güvenlik, yetki, yazma akışı, işler, belgeler."""
import io
import zipfile


def test_arayuz_ve_statik_dosyalar(istemci):
    s, html = istemci("GET", "/")
    assert s == 200 and b"vendor/react.production.min.js" in html and b"app.js" in html
    for yol in ("/app.js", "/vendor/react-dom.production.min.js", "/fonts/fonts.css", "/favicon.ico"):
        assert istemci("GET", yol)[0] == 200, yol


def test_yol_kacisi_ve_bilinmeyen(istemci):
    assert istemci("GET", "/..%2f..%2fusta%2fconfig.py")[0] == 404
    assert istemci("GET", "/api/yok")[0] == 404
    assert istemci("DELETE", "/api/meta")[0] == 405


def test_csrf_basligi_zorunlu(istemci):
    s, d = istemci("POST", "/api/mod", {"mod": "danisman"}, baslik={"X-Usta": "0"})
    assert s == 403 and "güvenlik" in d["hata"]


def test_host_basligi_denetlenir(istemci):
    s, _ = istemci("GET", "/api/meta", baslik={"Host": "kotu-site.example"})
    assert s == 403


def test_bozuk_json(istemci):
    s, d = istemci("POST", "/api/sohbet", ham=b"{bozuk", baslik={"Content-Type": "application/json"})
    assert s == 400 and "JSON" in d["hata"]


def test_acilis_guvenli_varsayilan(istemci):
    d = istemci("GET", "/api/durum")[1]
    assert d["oturum"]["mod"] == "danisman" and d["oturum"]["kullanici"]["rol"] == "operator"
    assert d["makine"]["pv"]["z1"] and d["aktif_is"] == "JOB-K114"


def test_tam_yazma_akisi_ve_kayit(istemci):
    assert istemci("POST", "/api/mod", {"mod": "yazma"})[0] == 403          # operatör geçemez
    istemci("POST", "/api/oturum", {"kullanici_id": "u2"})
    assert istemci("POST", "/api/mod", {"mod": "yazma"})[1]["mod"] == "yazma"
    d = istemci("POST", "/api/yazma/dogrula", {"alan": "tutmaPress", "deger": "47", "kaynak": "test"})[1]
    assert d["gecti"] and d["mevcut"] == 45.0
    s, r = istemci("POST", "/api/yazma/onayla", {"belirtec": d["belirtec"]})
    assert s == 200 and r["kayit_id"] == 1
    assert istemci("POST", "/api/yazma/onayla", {"belirtec": d["belirtec"]})[0] == 409
    k = istemci("GET", "/api/kayit")[1]["kayitlar"][0]
    assert (k["alan"], k["eski"], k["yeni"], k["kullanici"], k["kaynak"]) == ("tutmaPress", 45.0, 47.0, "Mehmet K.", "test")


def test_onay_aninda_mod_degistiyse_yazilmaz(istemci):
    istemci("POST", "/api/oturum", {"kullanici_id": "u3"})
    istemci("POST", "/api/mod", {"mod": "yazma"})
    d = istemci("POST", "/api/yazma/dogrula", {"alan": "z1", "deger": 220})[1]
    istemci("POST", "/api/oturum", {"kullanici_id": "u1"})                   # operatöre dönüldü
    assert istemci("POST", "/api/yazma/onayla", {"belirtec": d["belirtec"]})[0] == 403


def test_pin(usta, istemci):
    usta.ayarlar.d["roller"]["pin"]["muhendis"] = "4321"
    assert istemci("POST", "/api/oturum", {"kullanici_id": "u3", "pin": "1111"})[0] == 403
    assert istemci("POST", "/api/oturum", {"kullanici_id": "u3", "pin": "4321"})[0] == 200


def test_is_yasam_dongusu(usta, istemci):
    assert istemci("POST", "/api/isler", {"urun": "X", "kalip": "K", "malzeme": "PP"})[0] == 403
    istemci("POST", "/api/oturum", {"kullanici_id": "u2"})
    assert istemci("POST", "/api/isler", {"urun": " ", "kalip": "K", "malzeme": "PP"})[0] == 400
    j = istemci("POST", "/api/isler", {"urun": "Kova", "kalip": "K-9", "malzeme": "PP (Polipropilen)"})[1]
    r = istemci("PUT", f"/api/isler/{j['id']}", {"ayarlar": {"z1": 205, "z2": "bozuk", "z3": 400}})[1]
    assert r["is"]["ayarlar"]["z1"] == 205 and r["is"]["ayarlar"]["z2"] == 215 and r["uyarilar"]
    # danışman modunda aktif yapmak makineye YAZMAZ
    once = usta.makine.snapshot()["sp"]["z1"]
    r = istemci("POST", f"/api/isler/{j['id']}/aktif")[1]
    assert r["yazildi"] is False and usta.makine.snapshot()["sp"]["z1"] == once
    # yazma modunda güvenli aralık dışı değer içeren iş yüklenmez
    istemci("POST", "/api/mod", {"mod": "yazma"})
    s, d = istemci("POST", f"/api/isler/{j['id']}/aktif")
    assert s == 400 and "Bölge 3" in d["hata"]
    istemci("PUT", f"/api/isler/{j['id']}", {"ayarlar": {"z3": 220}})
    r = istemci("POST", f"/api/isler/{j['id']}/aktif")[1]
    assert r["yazildi"] and usta.makine.snapshot()["sp"]["z1"] == 205
    assert any("İş değişimi" in k["kaynak"] for k in istemci("GET", "/api/kayit")[1]["kayitlar"])
    assert istemci("DELETE", f"/api/isler/{j['id']}")[0] == 400               # aktif iş silinemez
    assert istemci("DELETE", "/api/isler/JOB-K330")[0] == 200


def test_sohbet_ve_recete_uclari(istemci):
    r = istemci("POST", "/api/sohbet", {"gecmis": [{"role": "assistant", "content": "merhaba"},
                                                    {"role": "user", "content": "çapak var"}]})[1]
    assert r["kaynak"] == "uzman" and "Çapak" in r["metin"]
    assert istemci("POST", "/api/sohbet", {"gecmis": []})[0] == 400
    r = istemci("POST", "/api/recete", {"malzeme": "ABS", "et": "Kalın (>4 mm)"})[1]
    assert r["degerler"]["z1"] == 215 and r["tesis"]
    assert istemci("POST", "/api/sonuclar", {"malzeme": "ABS", "et": "Kalın", "sonuc": "belki"})[0] == 400


def test_alarm_akisi(usta, istemci):
    assert istemci("POST", "/api/alarm/senaryo", {"tur": "yok"})[0] == 400
    istemci("POST", "/api/alarm/senaryo", {"tur": "huni_bos"})
    for _ in range(120):
        usta.makine.tick(0.25)
    a = next(a for a in istemci("GET", "/api/durum")[1]["alarmlar"] if a["active"])
    y = istemci("POST", "/api/alarm/yorum", {"id": a["id"]})[1]
    assert "Huni" in y["metin"] or "huni" in y["metin"]
    assert istemci("POST", "/api/alarm/gordum", {"id": a["id"]})[1]["tamam"]
    assert istemci("GET", "/api/alarm/gecmis")[1]["alarmlar"]


def test_belge_yukleme_akisi(istemci):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("word/document.xml", '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>HAT-4 makine notu: soğutma hattı 3 kullanılmalı.</w:t></w:r></w:p></w:body></w:document>')
    hdr = {"X-Dosya-Adi": "Hat%204%20notu.docx", "Content-Type": "application/octet-stream"}
    assert istemci("POST", "/api/bilgi/ayristir", ham=b.getvalue(), baslik=hdr)[0] == 403   # operatör
    istemci("POST", "/api/oturum", {"kullanici_id": "u3"})
    r = istemci("POST", "/api/bilgi/ayristir", ham=b.getvalue(), baslik=hdr)[1]
    assert r["dosya"] == "Hat 4 notu.docx" and len(r["adaylar"]) == 1
    e = istemci("POST", "/api/bilgi/ekle", {"kayitlar": r["adaylar"] + [{"id": "../kotu", "baslik": "x", "metin": "y"}]})[1]
    assert e["eklenen"] == 1
    assert any("soğutma hattı 3" in k["metin"] for k in istemci("GET", "/api/bilgi")[1]["kayitlar"])
