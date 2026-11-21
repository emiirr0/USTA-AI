"""OPC UA bağdaştırıcısı — yerel bir test OPC UA sunucusuna karşı gerçek bağlantı.

asyncua kurulu değilse atlanır (çekirdek USTA için gerekli değildir).
"""
import socket
import time

import pytest

asyncua = pytest.importorskip("asyncua")
from asyncua.sync import Server  # noqa: E402

from usta.machine import MachineError  # noqa: E402
from usta.machine.opcua import OpcUaMachine  # noqa: E402


def _port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


DEGERLER = [("z1", 218.4, False), ("z1_sp", 218.0, True), ("tutmaPress", 45.0, False),
            ("tutmaPress_sp", 45.0, True), ("enjPress", 82.0, False), ("cevrim", 24.1, False),
            ("yastik", 6.2, False), ("baski", 1000.0, False)]


def _pres_kur(port):
    """Sabit metin düğüm kimlikli test presi (yeniden açılınca kimlikler aynı kalır)."""
    srv = Server()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}/pres/")
    ns = srv.register_namespace("urn:test:pres")
    obj = srv.nodes.objects.add_object(f"ns={ns};s=Pres", "Pres")
    dugum = {}
    for ad, v, yazilir in DEGERLER:
        n = obj.add_variable(f"ns={ns};s=Pres.{ad}", ad, v)
        if yazilir:
            n.set_writable()
        dugum[ad] = n.nodeid.to_string()
    srv.start()
    srv.durdu = False
    return srv, dugum


@pytest.fixture
def pres():
    port = _port()
    srv, dugum = _pres_kur(port)
    kutu = {"srv": srv}
    yield f"opc.tcp://127.0.0.1:{port}/pres/", dugum, srv, port, kutu
    if not kutu["srv"].durdu:
        kutu["srv"].stop()


def _bekle(m, kosul, sure=5.0):
    son = time.time() + sure
    while time.time() < son:
        if kosul(m.snapshot()):
            return True
        time.sleep(0.1)
    return False


def test_okur_ve_varsayilan_salt_okunurdur(pres):
    url, d, *_ = pres
    m = OpcUaMachine("Gerçek Pres", url, d, periyot=0.1)
    m.start()
    try:
        assert _bekle(m, lambda s: s["pv"].get("z1") == pytest.approx(218.4))
        s = m.snapshot()
        assert s["baglanti"] == "OPC UA" and s["sp"]["z1"] == 218.0 and s["baski"] == 1000
        assert m.salt_okunur
        with pytest.raises(MachineError, match="SALT OKUNUR"):
            m.write_setpoint("z1", 220)
    finally:
        m.stop()


def test_izinle_yazar_ve_geri_okur(pres):
    url, d, srv, *_ = pres
    m = OpcUaMachine("Gerçek Pres", url, dict(d, yazma_izni=True), periyot=0.1)
    m.start()
    try:
        assert not m.salt_okunur
        m.write_setpoint("tutmaPress", 47.0)
        assert srv.get_node(d["tutmaPress_sp"]).read_value() == 47.0
        assert _bekle(m, lambda s: s["sp"].get("tutmaPress") == 47.0)
        with pytest.raises(MachineError, match="tanımlı değil"):
            m.write_setpoint("nozul", 230)
    finally:
        m.stop()


def test_baglanti_koparsa_durum_bildirir(pres):
    url, d, srv, *_ = pres
    m = OpcUaMachine("Gerçek Pres", url, d, periyot=0.1)
    m.start()
    try:
        assert _bekle(m, lambda s: s["durum"] == "ÇALIŞIYOR")
        srv.stop()
        srv.durdu = True
        assert _bekle(m, lambda s: s["durum"] == "BAĞLANTI HATASI", 8)
    finally:
        m.stop()


def test_pres_yeniden_baslayinca_kendiliginden_baglanir(pres):
    url, d, srv, port, kutu = pres
    m = OpcUaMachine("Gerçek Pres", url, d, periyot=0.1)
    m.start()
    try:
        assert _bekle(m, lambda s: s["durum"] == "ÇALIŞIYOR")
        srv.stop()
        srv.durdu = True
        assert _bekle(m, lambda s: s["durum"] == "BAĞLANTI HATASI", 8)
        yeni, _ = _pres_kur(port)            # pres geri geldi (aynı adres, aynı düğümler)
        kutu["srv"] = yeni
        yeni.get_node(d["z1"]).write_value(230.0)
        assert _bekle(m, lambda s: s["durum"] == "ÇALIŞIYOR" and s["pv"].get("z1") == 230.0, 25)
    finally:
        m.stop()
