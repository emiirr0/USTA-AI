"""Çevrimdışı uzman — internet ve API anahtarı olmadan çalışan danışman.

Büyük dil modeli değildir; enjeksiyon kalıplamanın yerleşik sorun-giderme
bilgisini kural tabanı olarak taşır ve CANLI makine değerleri + makinenin
güvenli aralıklarıyla birleştirir. Bulut AI yokken ya da hata verdiğinde
devreye girer: panel hiçbir zaman "cevap yok" demez.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..knowledge import getir, kucult

# Her kusur: anahtar sözcükler, sebepler, sıralı kontrol listesi, ayar yönü.
KUSURLAR = {
    "capak": {
        "ad": "Çapak (flash)",
        "anahtar": ["çapak", "capak", "flash", "taşma", "tasma", "kenar fazlası", "ayrım çizgisi"],
        "sebepler": ["Tutma/enjeksiyon basıncı kalıbın kapama kuvvetini aşıyor",
                     "Eriyik çok sıcak → viskozite düşük, ayrım yüzeyine sızıyor",
                     "Kalıp ayrım yüzeyinde aşınma, kir ya da granül kırıntısı",
                     "Kapama kuvveti yetersiz ya da kalıp paralelliği bozuk"],
        "kontrol": ["Kalıp ayrım yüzeyini temizle, kir/kırıntı var mı bak",
                    "Kapama kuvveti setini ve kalıp yüksekliği ayarını kontrol et",
                    "Tutma basıncını küçük adımla düşür",
                    "Sorun sürerse arka bölge/nozul sıcaklığını 3–5 °C düşür",
                    "Çapak hep aynı yerdeyse kalıp bakımına bildir (aşınma)"],
        "ayar": [("tutmaPress", -3), ("nozul", -4)],
    },
    "eksik_dolum": {
        "ad": "Eksik dolum (short shot)",
        "anahtar": ["eksik dolum", "short shot", "dolmuyor", "tam dolmuyor", "eksik", "dolmama", "yarım"],
        "sebepler": ["Malzeme yetersiz: dozaj kısa ya da yastık sıfıra iniyor",
                     "Eriyik soğuk → akış yolu sonunda donuyor",
                     "Enjeksiyon/tutma basıncı ya da hızı düşük",
                     "Hava tahliyesi (vent) tıkalı → hava sıkışıyor",
                     "Besleme hunisinde köprülenme ya da granül bitti"],
        "kontrol": ["Huniyi ve beslemeyi kontrol et (granül akıyor mu)",
                    "Yastık değerine bak: 3 mm altındaysa dozajı artır",
                    "Kalıp hava kanallarını temizle",
                    "Tutma basıncını küçük adımla artır",
                    "Sorun sürerse bölge sıcaklıklarını 3–5 °C artır"],
        "ayar": [("tutmaPress", +3), ("z3", +4)],
    },
    "cokuntu": {
        "ad": "Çöküntü / göçme (sink mark)",
        "anahtar": ["çöküntü", "cokuntu", "göçme", "gocme", "sink", "çukur", "içe çökme", "batma"],
        "sebepler": ["Tutma basıncı ya da tutma süresi yetersiz",
                     "Kalın et bölgesi geç donuyor",
                     "Eriyik ya da kalıp çok sıcak",
                     "Yolluk ağzı erken donuyor → tutma basıncı iletilmiyor"],
        "kontrol": ["Tutma basıncını küçük adımla artır",
                    "Tutma süresini uzat (yolluk ağzı donana kadar)",
                    "Kalıp soğutma suyunun aktığını kontrol et",
                    "Gerekirse eriyik sıcaklığını 3–5 °C düşür"],
        "ayar": [("tutmaPress", +3)],
    },
    "gumuslenme": {
        "ad": "Gümüşleme / nem çizgisi",
        "anahtar": ["gümüş", "gumus", "nem", "silver", "çizgi çizgi", "yüzeyde parlak çizgi"],
        "sebepler": ["Granül nemli — kurutma yetersiz (ABS, PC, PA, PET çok nem çeker)",
                     "Eriyik aşırı ısınıp bozunuyor",
                     "Vida geri çekmede hava emiyor"],
        "kontrol": ["Kurutucuyu kontrol et: sıcaklık ve süre datasheet'e uygun mu",
                    "Kurutulmuş malzemenin hunide bekleme süresini kısalt",
                    "Bölge sıcaklıklarının üst sınıra dayanmadığını doğrula",
                    "Geri basıncı biraz artır, dekompresyonu azalt"],
        "ayar": [],
    },
    "yanik": {
        "ad": "Yanık / kararma (dizel etkisi)",
        "anahtar": ["yanık", "yanik", "kararma", "siyah", "kahverengi", "burn", "dizel"],
        "sebepler": ["Sıkışan hava ani sıkıştırmayla ısınıyor (vent tıkalı)",
                     "Enjeksiyon hızı çok yüksek",
                     "Malzeme kovanda çok uzun bekliyor ya da aşırı sıcak"],
        "kontrol": ["Yanığın yerine bak: akış sonundaysa hava tahliyesini temizle",
                    "Enjeksiyon hızını kademeli düşür",
                    "Bölge sıcaklıklarını 5 °C düşür",
                    "Uzun duruşlardan sonra kovanı boşalt (temizleme atışı)"],
        "ayar": [("z3", -4), ("nozul", -4)],
    },
    "carpilma": {
        "ad": "Çarpılma (warpage)",
        "anahtar": ["çarpıl", "carpil", "eğil", "egil", "warp", "bükül", "ölçü", "olcu"],
        "sebepler": ["Kalıp iki yarısı farklı sıcaklıkta → dengesiz soğuma",
                     "İç gerilim: tutma basıncı çok yüksek",
                     "Parça kalıptan çok sıcak çıkıyor (soğutma kısa)"],
        "kontrol": ["Kalıp iki yarısının sıcaklığını ölç ve eşitle",
                    "Soğutma süresini uzat",
                    "Tutma basıncını küçük adımla düşür",
                    "Parçayı çıkışta düz bir fikstürde soğut"],
        "ayar": [("tutmaPress", -2)],
    },
    "kabarcik": {
        "ad": "Kabarcık / boşluk (void)",
        "anahtar": ["kabarcık", "kabarcik", "boşluk", "bosluk", "void", "hava kabarcığı"],
        "sebepler": ["Kalın kesitte büzülme → içte boşluk",
                     "Tutma basıncı/süresi yetersiz",
                     "Nemli malzeme"],
        "kontrol": ["Tutma basıncı ve süresini artır",
                    "Malzemenin kuru olduğunu doğrula",
                    "Enjeksiyon hızını biraz düşür"],
        "ayar": [("tutmaPress", +3)],
    },
    "akis_izi": {
        "ad": "Akış izi / kaynak çizgisi",
        "anahtar": ["akış izi", "akis izi", "kaynak çizgisi", "kaynak izi", "weld", "flow line", "dalga"],
        "sebepler": ["Eriyik cepheleri soğuk buluşuyor",
                     "Enjeksiyon hızı düşük", "Kalıp soğuk"],
        "kontrol": ["Enjeksiyon hızını artır", "Kalıp sıcaklığını 5–10 °C artır",
                    "Eriyik sıcaklığını 3–5 °C artır", "Kaynak bölgesine hava tahliyesi ekletilebilir mi sor"],
        "ayar": [("nozul", +4)],
    },
    "yapisma": {
        "ad": "Kalıba yapışma / çıkarma sorunu",
        "anahtar": ["yapış", "yapis", "çıkmıyor", "cikmiyor", "itici", "iz bırak", "sticking"],
        "sebepler": ["Tutma basıncı yüksek → parça kalıba sıkışıyor",
                     "Soğutma kısa", "Kalıp yüzeyinde çizik/çapak"],
        "kontrol": ["Tutma basıncını düşür", "Soğutma süresini artır",
                    "İtici pimleri ve kalıp yüzeyini kontrol et"],
        "ayar": [("tutmaPress", -3)],
    },
    "cevrim": {
        "ad": "Çevrim süresini kısaltma",
        "anahtar": ["çevrim", "cevrim", "hızlandır", "hizlandir", "kısalt", "kisalt", "verim", "cycle"],
        "sebepler": ["Çevrimin büyük kısmı soğutmadır — kazanç oradan gelir"],
        "kontrol": ["Kalıp suyu debisini ve sıcaklığını kontrol et (tıkalı hat var mı)",
                    "Soğutma süresini 0.5 sn adımlarla kısalt; her adımda ölçü ve çarpılma kontrolü",
                    "Kalıp açma/kapama hızlarını güvenli sınırda optimize et",
                    "Dozajı soğutma süresine paralel bitecek şekilde ayarla",
                    "Her adımdan sonra 20–30 parça izle; fire artarsa geri dön"],
        "ayar": [],
    },
}

ALARM_REHBERI = {
    "sicaklik": ["Rezistans akımını kontrol et (pens ampermetre) — bant rezistans yanmış olabilir",
                 "Termokupl bağlantısını ve yerini kontrol et",
                 "Kontaktör/SSR çıkışını kontrol et",
                 "Sapma sürerse üretimi durdur: soğuk bölge eksik dolum ve fire üretir"],
    "basinc": ["Eriyik sıcaklığı düşmüş mü bak (soğuk eriyik basıncı yükseltir)",
               "Nozul ağzında donma ya da tıkanma var mı kontrol et",
               "Malzeme partisini kontrol et (akışkanlığı farklı parti)",
               "Basınç sınırını yükseltme — önce sebebi bul"],
    "yag": ["Yağ soğutucu su vanasının açık olduğunu ve suyun aktığını kontrol et",
            "Eşanjör kirli olabilir — bakım kaydına bak",
            "Yağ seviyesini kontrol et",
            "Sıcaklık 55 °C'yi geçerse makineyi durdur (conta ve yağ ömrü)"],
    "huni": ["Hunideki granül seviyesini kontrol et, besleme hattı çalışıyor mu bak",
             "Köprülenme varsa huniye vur/karıştır",
             "Yastık değerini izle: düşüyorsa eksik dolum gelir"],
    "kalip": ["Kalıp arasında takılı parça ya da yolluk var mı bak — ELLE DOKUNMADAN önce güvenlik kapısını aç ve makineyi güvenli moda al",
              "İtici pimlerin geri döndüğünü kontrol et",
              "Kalıp koruma basıncı ayarını değiştirme; önce engeli kaldır",
              "Tekrarlıyorsa kalıp ayarcısını çağır"],
}

GENEL = ("Bu konuda yerleşik kayıtlarımda net bir eşleşme bulamadım. Şunları "
         "sorabilirsin: çapak, eksik dolum, çöküntü, gümüşleme, yanık, çarpılma, "
         "kabarcık, akış izi, kalıba yapışma, çevrim kısaltma — ya da bir alarm kodu.")


def kusur_bul(metin: str) -> Optional[str]:
    k = kucult(metin)
    en, en_puan = None, 0
    for anahtar, tanim in KUSURLAR.items():
        puan = sum(len(w) for w in tanim["anahtar"] if w in k)
        if puan > en_puan:
            en, en_puan = anahtar, puan
    return en


def _ayar_onerisi(kusur: str, durum: Dict, alanlar: Dict) -> List[str]:
    satirlar = []
    sp = durum.get("sp") or {}
    for alan, adim in KUSURLAR[kusur]["ayar"]:
        tanim = alanlar.get(alan)
        mevcut = sp.get(alan)
        if not tanim or mevcut is None:
            continue
        lo, hi = tanim["aralik"]
        hedef = max(lo, min(hi, round(mevcut + adim)))
        if hedef == round(mevcut):
            satirlar.append(f"{tanim['etiket']} zaten güvenli sınırda ({mevcut:g} {tanim['birim']}); bu yönde ilerleme yok.")
            continue
        satirlar.append(f"{tanim['etiket']}: {mevcut:g} → {hedef:g} {tanim['birim']} "
                        f"(güvenli aralık {lo}–{hi}).")
    return satirlar


def _kaynak_satiri(kaynaklar: List[Dict]) -> str:
    if not kaynaklar:
        return ""
    def kisalt(t: str, n: int = 170) -> str:
        return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    return "\nTesis kaydı:\n" + "\n".join(f"• [{k['baslik']}] {kisalt(k['metin'])}" for k in kaynaklar[:2])


def sohbet(soru: str, durum: Dict, alanlar: Dict, kaynaklar: List[Dict],
           gozcu: Optional[Dict] = None) -> str:
    kusur = kusur_bul(soru)
    if not kusur and gozcu and gozcu.get("baskin_tur") and any(
            w in kucult(soru) for w in ("fire", "neden", "kalite", "gözcü", "gozcu")):
        kusur = {"eksik_dolum": "eksik_dolum", "capak": "capak", "cokuntu": "cokuntu"}.get(
            gozcu["baskin_tur"])
    if not kusur:
        alarm = re.search(r"alm-?\s*(\d{3})", kucult(soru))
        if alarm:
            return alarm_yorumu({"code": f"ALM-{alarm.group(1)}", "title": soru, "detail": ""},
                                durum, kaynaklar)
        return GENEL + _kaynak_satiri(kaynaklar)
    t = KUSURLAR[kusur]
    pv = durum.get("pv") or {}
    satir = [f"{t['ad']} — muhtemel sebepler:"]
    satir += [f"• {s}" for s in t["sebepler"]]
    satir.append("\nSırayla kontrol et:")
    satir += [f"{i}. {s}" for i, s in enumerate(t["kontrol"], 1)]
    oneriler = _ayar_onerisi(kusur, durum, alanlar)
    if oneriler:
        satir.append("\nKüçük adımlı ayar önerisi (her adımdan sonra 10–20 parça izle):")
        satir += [f"• {o}" for o in oneriler]
    if pv.get("yastik") is not None and kusur in ("eksik_dolum", "cokuntu") and pv["yastik"] < 3:
        satir.append(f"\n⚠ Yastık şu an {pv['yastik']} mm — çok düşük; önce dozajı/beslemeyi düzelt.")
    if gozcu and gozcu.get("toplam"):
        satir.append(f"\nGÖZCÜ kalite verisi: son {gozcu['toplam']} parçada fire %{gozcu['fire_orani']:.1f}"
                     + (f", en sık tür: {gozcu['baskin_ad']}" if gozcu.get("baskin_ad") else "") + ".")
    satir.append(_kaynak_satiri(kaynaklar))
    return "\n".join(s for s in satir if s is not None).strip()


def alarm_yorumu(alarm: Dict, durum: Dict, kaynaklar: List[Dict]) -> str:
    metin = kucult(f"{alarm.get('code','')} {alarm.get('title','')} {alarm.get('detail','')}")
    if any(w in metin for w in ("sıcaklık", "bölge", "nozul", "alm-2")):
        tur = "sicaklik"
    elif "basınç" in metin or "alm-104" in metin:
        tur = "basinc"
    elif "yağ" in metin or "alm-310" in metin:
        tur = "yag"
    elif "huni" in metin or "besleme" in metin or "alm-120" in metin:
        tur = "huni"
    elif "kalıp" in metin or "alm-090" in metin:
        tur = "kalip"
    else:
        return ("Bu alarm için yerleşik bir kontrol listem yok. Makine kılavuzundaki alarm "
                "tablosuna bak ve bakım ekibine bildir." + _kaynak_satiri(kaynaklar))
    satir = [f"{alarm.get('code', '')} · {alarm.get('title', '')} — sırayla kontrol et:"]
    satir += [f"{i}. {s}" for i, s in enumerate(ALARM_REHBERI[tur], 1)]
    pv, sp = durum.get("pv") or {}, durum.get("sp") or {}
    if tur == "sicaklik":
        sapmalar = [f"{ad} {pv[k]}/{sp[k]:g} °C" for k, ad in
                    (("z1", "B1"), ("z2", "B2"), ("z3", "B3"), ("nozul", "Nozul"))
                    if k in pv and k in sp and abs(pv[k] - sp[k]) > 5]
        if sapmalar:
            satir.append("Ölçülen/setpoint: " + ", ".join(sapmalar))
    if tur == "basinc" and "enjPress" in pv:
        satir.append(f"Anlık enjeksiyon basıncı: {pv['enjPress']} bar.")
    satir.append(_kaynak_satiri(kaynaklar))
    return "\n".join(satir).strip()


ET_DUZELTME = {"ince": (+5, -3), "kalın": (-3, +5), "kalin": (-3, +5)}  # (sıcaklık, çevrim)
GENEL_MALZEME = {
    "ABS": (220, 225, 230, 235, 45, 24), "PP": (205, 210, 215, 220, 40, 20),
    "PC": (280, 290, 295, 300, 55, 30), "POM": (190, 195, 200, 205, 50, 25),
    "PA6": (245, 250, 255, 260, 50, 28), "PS": (200, 205, 210, 215, 40, 20),
    "PETG": (235, 240, 245, 248, 48, 22),
}


def recete(malzeme: str, et: str, alanlar: Dict, kayitlar: List[Dict]) -> Dict:
    """Başlangıç ayarı: kanıtlı tesis reçetesi > genel tablo. Güvenli aralığa
    sığmayan değerler kırpılmaz, notla işaretlenir (insan görsün)."""
    ilgili = getir(kayitlar, f"{malzeme} reçete kalıp", malzeme, 5)
    kaynak = next((k for k in ilgili if k.get("tur") == "recete"
                   and k.get("malzeme") and k["malzeme"].lower() in malzeme.lower()), None)
    deger: Dict[str, float] = {}
    notlar = []
    if kaynak:
        for anahtar, desen in (("z1", r"z1\s*(\d+)"), ("z2", r"z2\s*(\d+)"), ("z3", r"z3\s*(\d+)"),
                               ("nozul", r"nozul\s*(\d+)"), ("enjPress", r"enj\w*\s*(\d+)"),
                               ("tutmaPress", r"tutma\w*\s*(\d+)"), ("cevrim", r"çevrim\s*(\d+)")):
            m = re.search(desen, kucult(kaynak["metin"]))
            if m:
                deger[anahtar] = float(m.group(1))
        notlar.append(f"Kanıtlı tesis reçetesinden başlandı: {kaynak['baslik']}.")
    kod = next((k for k in GENEL_MALZEME if k.lower() in malzeme.lower()), None)
    if len(deger) < 5:
        if kod:
            z1, z2, z3, noz, tut, cev = GENEL_MALZEME[kod]
            deger = {"z1": z1, "z2": z2, "z3": z3, "nozul": noz, "enjPress": 80,
                     "tutmaPress": tut, "cevrim": cev}
            notlar.append("Tesis reçetesi yok; genel malzeme tablosundan başlandı.")
        else:
            return {"degerler": {}, "not": f"{malzeme} için ne tesis reçetesi ne genel tablo var; "
                    "malzeme datasheet'ini bilgi tabanına yükleyin.", "kaynaklar": ilgili}
    et_k = kucult(et)
    for anahtar, (dt, dc) in ET_DUZELTME.items():
        if anahtar in et_k:
            for z in ("z1", "z2", "z3", "nozul"):
                if z in deger:
                    deger[z] += dt
            if "cevrim" in deger:
                deger["cevrim"] = max(8, deger["cevrim"] + dc)
            notlar.append(f"Et kalınlığına göre sıcaklık {dt:+d} °C, çevrim {dc:+d} s düzeltildi.")
            break
    for k, v in deger.items():
        a = alanlar.get(k)
        if a and not (a["aralik"][0] <= v <= a["aralik"][1]):
            notlar.append(f"DİKKAT: {a['etiket']} {v:g} {a['birim']} bu presin güvenli aralığı "
                          f"({a['aralik'][0]}–{a['aralik'][1]}) dışında — mühendislik onayı gerekir.")
    return {"degerler": {k: int(v) for k, v in deger.items()}, "not": " ".join(notlar),
            "kaynaklar": ilgili}
