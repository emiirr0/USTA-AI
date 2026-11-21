"""Tesis bilgi tabanı: getirme (retrieval) + belge ayrıştırma.

USTA'nın önerileri bu kayıtlara dayanır; cevaplar "genel bilgi" değil
tesise özel olur. Belgeler gerçekten okunur:
  • .txt .md .csv .docx .xlsx  → ek kurulum gerekmez (standart kütüphane)
  • .pdf                       → isteğe bağlı 'pypdf' paketi gerekir
Çıkarılan kayıtlar önce operatöre GÖSTERİLİR, onaylananlar eklenir.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

TOHUM = [
    {"id": "DS-ABS", "tur": "datasheet", "malzeme": "ABS", "baslik": "ABS · İşleme Datasheet",
     "metin": "Kovan 210–240°C, kalıp 40–60°C. Kurutma 80°C / 2–3 saat — ABS nem çeker, kurutulmazsa yüzeyde gümüşleme olur. Tutma basıncı orta. HAT-3 presinde güvenli kovan üst sınırı 265°C."},
    {"id": "DS-PP", "tur": "datasheet", "malzeme": "PP", "baslik": "PP · İşleme Datasheet",
     "metin": "Kovan 200–230°C, kalıp 20–40°C. Çekme payı yüksek (%1.5–2.5), ölçü kritik parçalarda tutma süresini uzun tut. Nem sorunu az."},
    {"id": "DS-PC", "tur": "datasheet", "malzeme": "PC", "baslik": "PC · İşleme Datasheet",
     "metin": "Kovan 280–310°C, kalıp 80–100°C. Kurutma 120°C / 3–4 saat zorunlu; nem varsa gümüşleme ve kırılganlık. DİKKAT: HAT-3 güvenli kovan sınırı 265°C — bu pres standart PC için uygun değil, mühendislik onayı gerekir."},
    {"id": "DS-POM", "tur": "datasheet", "malzeme": "POM", "baslik": "POM · İşleme Datasheet",
     "metin": "Kovan 190–210°C, kalıp 60–90°C. 210°C üstünde bozunur ve formaldehit açığa çıkar — kovanda uzun bekletme yapma. Çapak eğilimi yüksek."},
    {"id": "DS-PA6", "tur": "datasheet", "malzeme": "PA6", "baslik": "PA6 (Naylon) · İşleme Datasheet",
     "metin": "Kovan 240–270°C, kalıp 60–90°C. Çok nem çeker, kurutma şart. Akışkanlığı yüksek, çapak için kapama kuvvetine dikkat."},
    {"id": "REC-K114", "tur": "recete", "malzeme": "ABS", "baslik": "Kalıp K-114 · ABS Konnektör Gövdesi — KANITLI",
     "metin": "z1 218, z2 221, z3 224, nozul 230, enj 82 bar, tutma 45 bar, çevrim 24 s, kalıp 50°C. 6 aydır bu ayarla fire oranı %1'in altında."},
    {"id": "REC-K207", "tur": "recete", "malzeme": "PP", "baslik": "Kalıp K-207 · PP Menteşeli Kapak — KANITLI",
     "metin": "z1 205, z2 210, z3 215, nozul 220, enj 70 bar, tutma 38 bar, çevrim 19 s, kalıp 30°C. Menteşede beyazlama olmaması için tutma basıncını 38'in üstüne çıkarma."},
    {"id": "REC-K330", "tur": "recete", "malzeme": "PA6", "baslik": "Kalıp K-330 · PA6 Dişli — KANITLI",
     "metin": "z1 250, z2 255, z3 258, nozul 262, enj 95 bar, tutma 55 bar, çevrim 31 s, kalıp 80°C. Kurutulmuş granülle çalış, aksi halde diş yüzeyinde kabarcık."},
    {"id": "NOTE-HAT3", "tur": "not", "malzeme": "", "baslik": "HAT-3 Presi · Makine Notu",
     "metin": "Rezistans sınırı nedeniyle güvenli kovan üst sınırı 265°C. Kalıp K-114 için soğutma hattı 2 kullanılmalı. Vida aşınması 3. çeyrekte ölçülecek."},
]

MALZEMELER = ["ABS", "PP", "PC", "POM", "PA6", "PA66", "PS", "PETG", "PE", "HDPE", "LDPE",
              "PMMA", "TPU", "TPE", "PBT", "PET", "SAN", "ASA"]

_DURAK = {"ve", "bir", "için", "ne", "mi", "var", "bu", "ile", "the", "olur", "olan", "gibi",
          "daha", "çok", "ama", "yada", "veya", "nasıl", "neden", "şu", "da", "de", "ki"}
_TR_KUCUK = str.maketrans("İIĞÜŞÖÇ", "iığüşöç")


def kucult(s: str) -> str:
    """Türkçe-doğru küçük harf (İ→i, I→ı)."""
    return (s or "").translate(_TR_KUCUK).lower()


def jetonla(s: str) -> List[str]:
    s = re.sub(r"[^0-9a-zçğıöşü]+", " ", kucult(s))
    return [w for w in s.split() if len(w) > 2 and w not in _DURAK]


def getir(kayitlar: List[Dict], sorgu: str, malzeme: str = "", k: int = 3) -> List[Dict]:
    """Basit, açıklanabilir sözcük örtüşmesi + malzeme eşleşmesi puanı."""
    q = set(jetonla(sorgu))          # malzeme adı kelime sayılmaz, yalnız bonus verir
    m = kucult(malzeme)
    puanli = []
    for d in kayitlar:
        dt = jetonla(f"{d['baslik']} {d['metin']}")
        ortusme = sum(1 for w in dt if w in q)
        if ortusme == 0:
            continue                     # yalnız malzeme tutması alakalılık sayılmaz
        s = ortusme
        dm = kucult(d.get("malzeme") or "")
        if m and dm and re.search(rf"\b{re.escape(dm)}\b", m):
            s += 5
        if s > 0:
            puanli.append((s, d))
    puanli.sort(key=lambda x: -x[0])
    return [d for _, d in puanli[:k]]


def malzeme_bul(metin: str) -> str:
    ust = metin.upper()
    for mz in sorted(MALZEMELER, key=len, reverse=True):
        if re.search(rf"(?<![A-Z0-9]){re.escape(mz)}(?![A-Z0-9])", ust):
            return mz
    return ""


def tur_tahmin(metin: str) -> str:
    k = kucult(metin)
    sayilar = len(re.findall(r"\d{2,3}", k))
    if sayilar >= 4 and any(w in k for w in ("z1", "nozul", "tutma", "reçete", "recete", "kalıp k", "çevrim")):
        return "recete"
    if any(w in k for w in ("kurutma", "datasheet", "kovan", "erime", "yoğunluk", "çekme")):
        return "datasheet"
    return "not"


# ── dosya okuyucular ───────────────────────────────────────────────────
def _docx_metin(veri: bytes) -> str:
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        kok = ET.fromstring(z.read("word/document.xml"))
    paragraflar = []
    for p in kok.iter(f"{ns}p"):
        t = "".join(x.text or "" for x in p.iter(f"{ns}t"))
        if t.strip():
            paragraflar.append(t.strip())
    return "\n".join(paragraflar)


def _xlsx_satirlar(veri: bytes) -> List[List[str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(veri)) as z:
        ortak: List[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{ns}si"):
                ortak.append("".join(t.text or "" for t in si.iter(f"{ns}t")))
        sayfalar = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        satirlar: List[List[str]] = []
        for s in sayfalar[:5]:
            for row in ET.fromstring(z.read(s)).iter(f"{ns}row"):
                hucre = []
                for c in row.iter(f"{ns}c"):
                    v = c.find(f"{ns}v")
                    is_ = c.find(f"{ns}is")
                    if c.get("t") == "s" and v is not None:
                        hucre.append(ortak[int(v.text)])
                    elif c.get("t") == "inlineStr" and is_ is not None:
                        hucre.append("".join(t.text or "" for t in is_.iter(f"{ns}t")))
                    else:
                        hucre.append(v.text if v is not None and v.text else "")
                if any(x.strip() for x in hucre):
                    satirlar.append(hucre)
    return satirlar


def _pdf_metin(veri: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ValueError("PDF okumak için 'pypdf' gerekli: pip install pypdf "
                         "(ya da belgeyi Word/Excel/metin olarak yükleyin).") from e
    r = PdfReader(io.BytesIO(veri))
    return "\n".join((p.extract_text() or "") for p in r.pages[:50])


def _metni_coz(veri: bytes) -> str:
    for kod in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            return veri.decode(kod)
        except UnicodeDecodeError:
            continue
    return veri.decode("utf-8", "replace")


def _parcala(metin: str, azami: int = 700) -> List[str]:
    bloklar = [b.strip() for b in re.split(r"\n\s*\n|\n(?=#)", metin) if b.strip()]
    parcalar, tampon = [], ""
    for b in bloklar:
        if len(tampon) + len(b) + 1 <= azami:
            tampon = f"{tampon}\n{b}".strip()
        else:
            if tampon:
                parcalar.append(tampon)
            while len(b) > azami:
                parcalar.append(b[:azami])
                b = b[azami:]
            tampon = b
    if tampon:
        parcalar.append(tampon)
    return parcalar


def _kayit(baslik: str, metin: str, kaynak: str) -> Dict:
    metin = re.sub(r"[ \t]+", " ", metin).strip()
    h = hashlib.sha1(f"{baslik}|{metin}".encode("utf-8")).hexdigest()[:8].upper()
    return {"id": f"DOC-{h}", "tur": tur_tahmin(baslik + " " + metin),
            "malzeme": malzeme_bul(baslik + " " + metin), "baslik": baslik[:120],
            "metin": metin[:2000], "kaynak": kaynak}


def belgeyi_ayristir(dosya_adi: str, veri: bytes) -> Tuple[List[Dict], List[str]]:
    """Dosyayı oku → aday kayıtlar + uyarılar."""
    ad = dosya_adi.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    uzanti = ad.lower().rsplit(".", 1)[-1] if "." in ad else ""
    kok = ad.rsplit(".", 1)[0]
    uyarilar: List[str] = []
    if not veri:
        return [], ["Dosya boş."]
    if uzanti in ("xlsx", "csv"):
        if uzanti == "xlsx":
            try:
                satirlar = _xlsx_satirlar(veri)
            except (zipfile.BadZipFile, KeyError, ET.ParseError):
                return [], ["Excel dosyası okunamadı (bozuk ya da .xls eski biçim; .xlsx olarak kaydedin)."]
        else:
            metin = _metni_coz(veri)
            ayrac = ";" if metin.count(";") > metin.count(",") else ","
            satirlar = [r for r in csv.reader(io.StringIO(metin), delimiter=ayrac) if any(c.strip() for c in r)]
        if len(satirlar) < 2:
            return [], ["Tabloda başlık + en az bir satır bulunamadı."]
        basliklar = [h.strip() or f"sütun{i+1}" for i, h in enumerate(satirlar[0])]
        adaylar = []
        for satir in satirlar[1:200]:
            parca = [f"{h}: {v.strip()}" for h, v in zip(basliklar, satir) if v and v.strip()]
            if len(parca) < 2:
                continue
            baslik = f"{kok} · {satir[0].strip()}" if satir[0].strip() else kok
            adaylar.append(_kayit(baslik, ", ".join(parca), ad))
        return adaylar, uyarilar
    try:
        if uzanti == "docx":
            metin = _docx_metin(veri)
        elif uzanti == "pdf":
            metin = _pdf_metin(veri)
        elif uzanti in ("txt", "md", "text", ""):
            metin = _metni_coz(veri)
        elif uzanti in ("doc", "xls"):
            return [], [f".{uzanti} eski Office biçimi okunamıyor; .{uzanti}x olarak kaydedip yükleyin."]
        else:
            return [], [f".{uzanti} biçimi desteklenmiyor (txt, md, csv, docx, xlsx, pdf)."]
    except ValueError as e:
        return [], [str(e)]
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        return [], ["Belge açılamadı (bozuk olabilir)."]
    parcalar = _parcala(metin)
    if not parcalar:
        return [], ["Belgede okunabilir metin bulunamadı (taranmış görüntü PDF olabilir)."]
    adaylar = []
    for i, p in enumerate(parcalar[:60], 1):
        ilk = p.splitlines()[0].strip("# ").strip()
        baslik = ilk if 4 <= len(ilk) <= 90 else f"{kok} · bölüm {i}"
        adaylar.append(_kayit(baslik, p, ad))
    return adaylar, uyarilar
