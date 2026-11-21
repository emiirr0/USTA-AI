"""Yapılandırma, güvenlik kapısı, depolama, simülatör ve köprü testleri."""
import json
import sqlite3
import time

import pytest

from usta import gozcu_bridge
from usta.config import Ayarlar, env_dosyasi_oku
from usta.machine import SimulatedMachine
from usta.safety import GuvenlikKapisi, ayarlari_sinirla
from usta.storage import Depo
from usta.config import VARSAYILAN_ALANLAR


# ── yapılandırma ─────────────────────────────────────────────────────
def test_env_dosyasi(tmp_path):
    f = tmp_path / ".env"
    f.write_text('# yorum\nANTHROPIC_API_KEY="sk-test"\nBOS=\nUSTA_PORT = 9000\nbozuk satir\n', encoding="utf-8")
    d = env_dosyasi_oku(f)
    assert d == {"ANTHROPIC_API_KEY": "sk-test", "BOS": "", "USTA_PORT": "9000"}


def test_bozuk_ayarlar_varsayilana_doner(tmp_path, monkeypatch):
    monkeypatch.delenv("USTA_AI", raising=False)
    (tmp_path / "ayarlar.json").write_text("{ bu json değil", encoding="utf-8")
    a = Ayarlar(tmp_path)
    assert a.uyarilar and "okunamadı" in a.uyarilar[0]
    assert a.alanlar["z1"]["aralik"] == [190, 255]


def test_gecersiz_saglayici_ve_aralik(tmp_path, monkeypatch):
    monkeypatch.setenv("USTA_AI", "sihirli")
    (tmp_path / "ayarlar.json").write_text(json.dumps(
        {"makine": {"alanlar": {"z1": {"aralik": [300, 100]}}}}), encoding="utf-8")
    a = Ayarlar(tmp_path)
    assert a.d["ai"]["saglayici"] == "otomatik"
    assert a.alanlar["z1"]["aralik"] == [190, 255]
    assert len(a.uyarilar) == 2


def test_ilk_calistirmada_ayar_dosyasi_yazilir_anahtar_yazilmaz(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-gizli")
    Ayarlar(tmp_path)
    icerik = (tmp_path / "ayarlar.json").read_text(encoding="utf-8")
    assert "sk-gizli" not in icerik and "saglayici" in icerik


# ── güvenlik kapısı ──────────────────────────────────────────────────
@pytest.fixture
def kapi():
    return GuvenlikKapisi(VARSAYILAN_ALANLAR)


def test_gecerli_yazma_belirtec_tek_kullanimlik(kapi):
    d = kapi.dogrula("z1", 222, 218, yetkili=True, yazma_modu=True)
    assert d.gecti and d.belirtec
    assert kapi.onay_al(d.belirtec) is not None
    assert kapi.onay_al(d.belirtec) is None


@pytest.mark.parametrize("alan,deger,mevcut,yetkili,mod,parca", [
    ("z1", 300, 250, True, True, "aralık dışında"),
    ("z1", 240, 218, True, True, "en fazla 15"),
    ("z1", 222, 218, False, True, "rol"),
    ("z1", 222, 218, True, False, "DANIŞMAN"),
    ("enjPress", 85, 82, True, True, "kilitli"),
    ("z1", float("nan"), 218, True, True, "sayı"),
    ("z1", True, 218, True, True, "sayı"),
    ("yok", 1, 0, True, True, "tanımlı"),
])
def test_dogrulama_reddeder(kapi, alan, deger, mevcut, yetkili, mod, parca):
    d = kapi.dogrula(alan, deger, mevcut, yetkili, mod)
    assert not d.gecti and d.belirtec is None
    assert any(parca in n for n in d.nedenler), d.nedenler


def test_belirtec_suresi_dolar(kapi, monkeypatch):
    d = kapi.dogrula("z1", 220, 218, True, True)
    simdi = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: simdi + 1000)
    assert kapi.onay_al(d.belirtec) is None


def test_ai_onerisi_suzulur_ama_kirpilmaz():
    s = ayarlari_sinirla({"z1": "230,5", "z2": 999, "bilinmeyen": 5, "nozul": "abc", "cevrim": 22.0},
                         VARSAYILAN_ALANLAR)
    assert s["degerler"] == {"z1": 230.5, "z2": 999, "cevrim": 22}
    assert len(s["uyarilar"]) == 1 and "Bölge 2" in s["uyarilar"][0]


# ── depolama ─────────────────────────────────────────────────────────
def test_kayit_defteri_degistirilemez(tmp_path):
    d = Depo(tmp_path / "t.db")
    d.kayit_ekle(kullanici="A", rol="Usta", alan="z1", eski=218, yeni=220)
    with pytest.raises(sqlite3.DatabaseError):
        d._db.execute("UPDATE kayit SET yeni=999")
    with pytest.raises(sqlite3.DatabaseError):
        d._db.execute("DELETE FROM kayit")
    assert d.kayitlar()[0]["yeni"] == 220
    d.kapat()


def test_isler_ve_bilgi(tmp_path):
    d = Depo(tmp_path / "t.db")
    d.is_kaydet({"id": "J1", "urun": "Kapak", "kalip": "K-1", "malzeme": "PP", "ayarlar": {"z1": 200}})
    d.is_kaydet({"id": "J1", "urun": "Kapak 2", "kalip": "K-1", "malzeme": "PP", "ayarlar": {"z1": 205}})
    assert d.is_getir("J1")["urun"] == "Kapak 2" and d.is_getir("J1")["ayarlar"]["z1"] == 205
    b = {"id": "B1", "tur": "not", "baslik": "x", "metin": "y"}
    assert d.bilgi_ekle(b) is True and d.bilgi_ekle(b) is False
    d.kapat()


# ── simülatör ────────────────────────────────────────────────────────
def test_sicaklik_rampa_yapar_sicramaz():
    m = SimulatedMachine("T", tohum=3)
    m.write_setpoint("z1", 230)
    m.tick(0.25)
    assert m.pv["z1"] < 225          # tek adımda zıplamaz
    for _ in range(80):
        m.tick(0.25)
    assert abs(m.pv["z1"] - 230) < 2.5


def test_ariza_alarm_dogurur_ve_kendiliginden_kapanir():
    m = SimulatedMachine("T", tohum=4)
    m.inject_fault("rezistans_b2")
    for _ in range(40):
        m.tick(0.25)
    aktif = [a for a in m.alarms() if a["active"]]
    assert any("Bölge 2" in a["title"] for a in aktif)
    for _ in range(500):             # senaryo süresi (90 sn) dolsun
        m.tick(0.25)
    assert not any(a["active"] and "Bölge 2" in a["title"] for a in m.alarms())


def test_anlik_gurultu_alarm_uretmez():
    m = SimulatedMachine("T", tohum=5)
    for _ in range(400):
        m.tick(0.25)
    assert m.alarms() == []


def test_uretim_ve_fire_turu_surecten_gelir():
    m = SimulatedMachine("T", tohum=6)
    for z in ("z1", "z2", "z3", "nozul"):
        m.sp[z] += 30                # setpoint'ler aşırı sıcak...
    m.pv.update({z: m.sp[z] + 12 for z in ("z1", "z2", "z3", "nozul")})
    m._ariza.clear()
    for _ in range(3):
        for _ in range(60):
            m.tick(0.25)
            for z in ("z1", "z2", "z3", "nozul"):
                m.pv[z] = m.sp[z] + 12   # ...ve ölçüm sürekli yukarıda
    u = m.snapshot()["uretim"]
    assert u["saglam"] + u["fire"] > 0
    assert u["turler"].get("capak", 0) >= max(u["turler"].values())


def test_kalip_koruma_cevrimi_durdurur():
    m = SimulatedMachine("T", tohum=7)
    m.inject_fault("kalip_koruma")
    once = m.baski
    for _ in range(20):
        m.tick(0.25)
    assert m.baski == once and m.snapshot()["durum"] == "BEKLİYOR"


# ── GÖZCÜ köprüsü ────────────────────────────────────────────────────
def test_gozcu_koprusu(tmp_path):
    assert gozcu_bridge.oku("") is None
    assert gozcu_bridge.oku(str(tmp_path / "yok"))["bagli"] is False
    (tmp_path / "sayaclar.json").write_text(json.dumps(
        {"total": 10, "good": 6, "scrap": 3, "suspect": 1, "by_kind": {"capak": 2, "cizik": 1}}), encoding="utf-8")
    (tmp_path / "gecmis.jsonl").write_text(
        '{"zaman":"t1","parca":"p1","karar":"FİRE","skor":60}\nBOZUK SATIR\n'
        '{"zaman":"t2","parca":"p2","karar":"SAĞLAM","skor":100}\n', encoding="utf-8")
    g = gozcu_bridge.oku(str(tmp_path))
    assert g["toplam"] == 10 and g["fire_orani"] == 30.0 and g["baskin_tur"] == "capak"
    assert [s["parca"] for s in g["son"]] == ["p2", "p1"]


def test_gozcu_bozuk_sayac_cokmeye_yol_acmaz(tmp_path):
    (tmp_path / "sayaclar.json").write_text("{bozuk", encoding="utf-8")
    g = gozcu_bridge.oku(str(tmp_path))
    assert g["bagli"] and "okunamadı" in g["hata"] and g["toplam"] == 0
