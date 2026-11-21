"""Kalıcı depolama — tek dosyalık SQLite (veri/usta.db).

Kayıt defteri (audit) veritabanı tetikleyicileriyle DEĞİŞTİRİLEMEZ:
UPDATE ve DELETE reddedilir. Böylece "AI destekli her yazma izlenebilir"
iddiası kod hatasıyla bile delinemez.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

SEMA = """
CREATE TABLE IF NOT EXISTS isler (
  id TEXT PRIMARY KEY, urun TEXT NOT NULL, kalip TEXT NOT NULL, malzeme TEXT NOT NULL,
  ayarlar TEXT NOT NULL, olusturma TEXT NOT NULL, guncelleme TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS kayit (
  id INTEGER PRIMARY KEY AUTOINCREMENT, zaman TEXT NOT NULL, kullanici TEXT NOT NULL,
  rol TEXT NOT NULL, vardiya TEXT, alan TEXT NOT NULL, etiket TEXT, eski REAL, yeni REAL,
  birim TEXT, kaynak TEXT);
CREATE TRIGGER IF NOT EXISTS kayit_guncellenemez BEFORE UPDATE ON kayit
  BEGIN SELECT RAISE(ABORT, 'kayit defteri degistirilemez'); END;
CREATE TRIGGER IF NOT EXISTS kayit_silinemez BEFORE DELETE ON kayit
  BEGIN SELECT RAISE(ABORT, 'kayit defteri degistirilemez'); END;
CREATE TABLE IF NOT EXISTS bilgi (
  id TEXT PRIMARY KEY, tur TEXT NOT NULL, malzeme TEXT, baslik TEXT NOT NULL,
  metin TEXT NOT NULL, kaynak TEXT, eklenme TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sonuclar (
  id INTEGER PRIMARY KEY AUTOINCREMENT, zaman TEXT NOT NULL, malzeme TEXT, et TEXT,
  sonuc TEXT NOT NULL, recete TEXT);
CREATE TABLE IF NOT EXISTS alarm_gecmisi (
  id TEXT PRIMARY KEY, kod TEXT, sev TEXT, baslik TEXT, detay TEXT,
  baslangic TEXT, bitis TEXT, gun TEXT);
CREATE TABLE IF NOT EXISTS durum (anahtar TEXT PRIMARY KEY, deger TEXT);
"""


def _simdi() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Depo:
    def __init__(self, yol: Path):
        self.yol = Path(yol)
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        self._kilit = threading.RLock()
        self._db = sqlite3.connect(str(self.yol), check_same_thread=False, timeout=10)
        self._db.row_factory = sqlite3.Row
        with self._kilit:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(SEMA)
            self._db.commit()

    def kapat(self) -> None:
        with self._kilit:
            self._db.close()

    def _yaz(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._kilit:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur

    def _oku(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        with self._kilit:
            return self._db.execute(sql, args).fetchall()

    # ── işler ────────────────────────────────────────────────────────
    def is_listesi(self) -> List[Dict]:
        return [{"id": r["id"], "urun": r["urun"], "kalip": r["kalip"], "malzeme": r["malzeme"],
                 "ayarlar": json.loads(r["ayarlar"])}
                for r in self._oku("SELECT * FROM isler ORDER BY olusturma, id")]

    def is_getir(self, is_id: str) -> Optional[Dict]:
        return next((j for j in self.is_listesi() if j["id"] == is_id), None)

    def is_kaydet(self, j: Dict) -> None:
        simdi = _simdi()
        self._yaz("""INSERT INTO isler(id,urun,kalip,malzeme,ayarlar,olusturma,guncelleme)
                     VALUES(?,?,?,?,?,?,?)
                     ON CONFLICT(id) DO UPDATE SET urun=excluded.urun, kalip=excluded.kalip,
                       malzeme=excluded.malzeme, ayarlar=excluded.ayarlar,
                       guncelleme=excluded.guncelleme""",
                  (j["id"], j["urun"], j["kalip"], j["malzeme"],
                   json.dumps(j["ayarlar"], ensure_ascii=False), simdi, simdi))

    def is_sil(self, is_id: str) -> bool:
        return self._yaz("DELETE FROM isler WHERE id=?", (is_id,)).rowcount > 0

    # ── kayıt defteri (yalnız ekleme) ───────────────────────────────
    def kayit_ekle(self, **k) -> int:
        cur = self._yaz("""INSERT INTO kayit(zaman,kullanici,rol,vardiya,alan,etiket,eski,yeni,birim,kaynak)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (_simdi(), k["kullanici"], k["rol"], k.get("vardiya"), k["alan"],
                         k.get("etiket"), k.get("eski"), k.get("yeni"), k.get("birim"),
                         k.get("kaynak")))
        return int(cur.lastrowid)

    def kayitlar(self, limit: int = 200) -> List[Dict]:
        return [dict(r) for r in self._oku("SELECT * FROM kayit ORDER BY id DESC LIMIT ?", (limit,))]

    # ── bilgi tabanı ─────────────────────────────────────────────────
    def bilgi_listesi(self) -> List[Dict]:
        return [dict(r) for r in self._oku("SELECT * FROM bilgi ORDER BY tur, id")]

    def bilgi_ekle(self, b: Dict) -> bool:
        """Var olan id'yi ezmez; eklendiyse True."""
        cur = self._yaz("""INSERT OR IGNORE INTO bilgi(id,tur,malzeme,baslik,metin,kaynak,eklenme)
                           VALUES(?,?,?,?,?,?,?)""",
                        (b["id"], b["tur"], b.get("malzeme", ""), b["baslik"], b["metin"],
                         b.get("kaynak", ""), _simdi()))
        return cur.rowcount > 0

    def bilgi_sil(self, bid: str) -> bool:
        return self._yaz("DELETE FROM bilgi WHERE id=?", (bid,)).rowcount > 0

    # ── reçete deneme sonuçları ──────────────────────────────────────
    def sonuc_ekle(self, malzeme: str, et: str, sonuc: str, recete: Dict) -> None:
        self._yaz("INSERT INTO sonuclar(zaman,malzeme,et,sonuc,recete) VALUES(?,?,?,?,?)",
                  (_simdi(), malzeme, et, sonuc, json.dumps(recete, ensure_ascii=False)))

    def sonuclar(self, limit: int = 50) -> List[Dict]:
        return [dict(r) for r in self._oku("SELECT * FROM sonuclar ORDER BY id DESC LIMIT ?", (limit,))]

    # ── alarm geçmişi ────────────────────────────────────────────────
    def alarm_kaydet(self, a: Dict) -> None:
        self._yaz("""INSERT INTO alarm_gecmisi(id,kod,sev,baslik,detay,baslangic,bitis,gun)
                     VALUES(?,?,?,?,?,?,?,?)
                     ON CONFLICT(id) DO UPDATE SET bitis=excluded.bitis""",
                  (a["id"], a["code"], a["sev"], a["title"], a["detail"], a["start"],
                   a.get("end"), datetime.now().strftime("%Y-%m-%d")))

    def alarm_gecmisi(self, limit: int = 100) -> List[Dict]:
        return [dict(r) for r in self._oku(
            "SELECT * FROM alarm_gecmisi ORDER BY gun DESC, baslangic DESC LIMIT ?", (limit,))]

    # ── küçük anahtar-değer durumu ──────────────────────────────────
    def durum_al(self, anahtar: str, varsayilan=None):
        r = self._oku("SELECT deger FROM durum WHERE anahtar=?", (anahtar,))
        return json.loads(r[0]["deger"]) if r else varsayilan

    def durum_yaz(self, anahtar: str, deger) -> None:
        self._yaz("INSERT INTO durum(anahtar,deger) VALUES(?,?) "
                  "ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
                  (anahtar, json.dumps(deger, ensure_ascii=False)))
