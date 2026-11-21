import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usta.app import Usta  # noqa: E402
from usta.config import Ayarlar  # noqa: E402
from usta.machine import SimulatedMachine  # noqa: E402
from usta.server import sunucu_kur  # noqa: E402


@pytest.fixture
def ayarlar(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USTA_AI", "uzman")
    return Ayarlar(tmp_path / "veri")


@pytest.fixture
def usta(ayarlar):
    u = Usta(ayarlar, makine=SimulatedMachine("TEST PRESİ", tohum=1))
    u.baslat()
    u.makine.stop()          # testler zamanı kendisi ilerletir (tick)
    yield u
    u.durdur()


class Istemci:
    def __init__(self, port):
        self.port = port

    def __call__(self, yontem, yol, govde=None, baslik=None, ham=None):
        h = {"X-Usta": "1"}
        veri = None
        if ham is not None:
            veri = ham
        elif govde is not None:
            veri = json.dumps(govde).encode()
            h["Content-Type"] = "application/json"
        h.update(baslik or {})
        istek = urllib.request.Request(f"http://127.0.0.1:{self.port}{yol}", data=veri,
                                       headers=h, method=yontem)
        try:
            with urllib.request.urlopen(istek, timeout=10) as y:
                tur = y.headers.get("Content-Type", "")
                icerik = y.read()
                return y.status, (json.loads(icerik) if "json" in tur else icerik)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")


@pytest.fixture
def istemci(usta):
    httpd = sunucu_kur(usta, 0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield Istemci(httpd.server_address[1])
    httpd.shutdown()
    httpd.server_close()
