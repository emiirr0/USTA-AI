"""AI aracısı — tek ayarla kaynak değişir, uygulama değişmez.

saglayici:
  otomatik → API anahtarı varsa Claude, yoksa çevrimdışı uzman
  claude   → Claude API (bulut)
  ollama   → yerel model (internetsiz)
  uzman    → yalnız çevrimdışı kural tabanı

Seçilen sağlayıcı hata verirse cevap çevrimdışı uzmandan gelir ve bu
açıkça işaretlenir ("yedek"). Dil modelinin ürettiği sayılar HİÇBİR ZAMAN
doğrudan makineye gitmez: güvenlik katmanından geçer.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from ..knowledge import getir
from ..safety import ayarlari_sinirla
from . import uzman
from .providers import AIHatasi, ClaudeSaglayici, OllamaSaglayici

SISTEM = """Sen bir plastik enjeksiyon presinin yanında çalışan, yapay zekâ destekli OPERATÖR DANIŞMANISIN. Türkçe, sade, saha diliyle konuş.
TESİS VERİSİ: "TESİS BİLGİ TABANI" başlığıyla kayıt verilirse cevabını ÖNCELİKLE bunlara dayandır; genel bilgiyle çelişirse tesis verisi kazanır. Kanıtlı reçete varsa onu çıpa al. Tesis verisinde olmayan bilgiyi verirken "bu tesis kaydında yok, genel bilgi" diye belirt.
GÜVENLİK: Somut ayar önerirken mevcut ve önerilen değeri göster, gerekçeyi bir cümlede ver, KÜÇÜK adım öner. Aşağıdaki güvenli aralıkları asla aşma. Değeri makineye operatör onaylı yazar; sen yalnızca önerirsin. Kişi güvenliği gerektiren işlerde (kalıba el sokma, ısıtıcıya dokunma) önce makineyi güvenli moda almayı söyle.
ALARM: Olası sebepleri say ve operatörün SIRAYLA kontrol edeceği kısa liste ver.
BİÇİM: Kısa, uygulanabilir, panelde okunur. Emin değilsen "şunu ölç/kontrol et" de."""


def _baglam(durum: Dict, alanlar: Dict, gozcu: Optional[Dict]) -> str:
    pv, sp, is_ = durum.get("pv") or {}, durum.get("sp") or {}, durum.get("is") or {}
    satir = [f"ANLIK MAKİNE DURUMU ({durum.get('baglanti', '?')}):",
             f"- Makine {durum.get('makine', '')} · Durum {durum.get('durum', '')}",
             f"- Aktif iş: {is_.get('urun', '')} · Kalıp {is_.get('kalip', '')} · {is_.get('malzeme', '')}"]
    if pv:
        satir.append("- Ölçülen: " + ", ".join(f"{k}={v}" for k, v in pv.items()))
    if sp:
        satir.append("- Setpoint: " + ", ".join(f"{k}={v}" for k, v in sp.items()))
    satir.append("- GÜVENLİ ARALIKLAR: " + ", ".join(
        f"{a['etiket']} {a['aralik'][0]}–{a['aralik'][1]} {a['birim']}"
        + ("" if a.get("yazilabilir") else " (kilitli)") for a in alanlar.values()))
    if gozcu and gozcu.get("toplam"):
        satir.append(f"- GÖZCÜ kalite verisi: {gozcu['toplam']} parça, fire %{gozcu['fire_orani']:.1f}, "
                     f"türler {gozcu.get('turler')}")
    return "\n".join(satir)


def _tesis(kaynaklar: List[Dict]) -> str:
    if not kaynaklar:
        return "\n\n(Bu soru için tesis bilgi tabanında eşleşme yok — genel bilgiyle yanıtla ve bunu belirt.)"
    return "\n\nTESİS BİLGİ TABANI (öncelikle buna dayan):\n" + "\n".join(
        f"• [{k['baslik']}] {k['metin']}" for k in kaynaklar)


def json_ayikla(metin: str) -> Dict:
    """Model çıktısından ilk JSON nesnesini çıkar (```json çitleri, ön söz vb. tolere edilir)."""
    metin = re.sub(r"```(?:json)?", "", metin)
    bas = metin.find("{")
    while bas != -1:
        derinlik = 0
        for i in range(bas, len(metin)):
            if metin[i] == "{":
                derinlik += 1
            elif metin[i] == "}":
                derinlik -= 1
                if derinlik == 0:
                    try:
                        sonuc = json.loads(metin[bas:i + 1])
                        if isinstance(sonuc, dict):
                            return sonuc
                    except json.JSONDecodeError:
                        break
        bas = metin.find("{", bas + 1)
    raise AIHatasi("Model geçerli JSON döndürmedi.")


class AIAracisi:
    def __init__(self, ayarlar):
        self.ayarlar = ayarlar
        ai = ayarlar.d["ai"]
        secim = ai["saglayici"]
        self.uyari = ""
        self.saglayici = None
        if secim == "otomatik":
            secim = "claude" if ayarlar.api_anahtari else "uzman"
        try:
            if secim == "claude":
                self.saglayici = ClaudeSaglayici(ayarlar.api_anahtari, ai["claude_model"],
                                                 ai["anthropic_version"], ai["zaman_asimi_sn"])
            elif secim == "ollama":
                self.saglayici = OllamaSaglayici(ai["ollama_url"], ai["ollama_model"],
                                                 ai["zaman_asimi_sn"])
        except AIHatasi as e:
            self.uyari = f"{e} Çevrimdışı uzman kullanılıyor."
        self.secim = self.saglayici.ad if self.saglayici else "uzman"

    def bilgi(self) -> Dict:
        etiket = {"claude": "Claude (bulut)", "ollama": "Yerel model (Ollama)",
                  "uzman": "Çevrimdışı uzman"}[self.secim]
        return {"saglayici": self.secim, "etiket": etiket, "uyari": self.uyari}

    def _dene(self, sistem: str, mesajlar: List[Dict], azami: int):
        if not self.saglayici:
            return None, None
        try:
            return self.saglayici.sor(sistem, mesajlar, azami), None
        except AIHatasi as e:
            return None, str(e)

    # ── görevler ─────────────────────────────────────────────────────
    def sohbet(self, gecmis: List[Dict], durum: Dict, kayitlar: List[Dict],
               gozcu: Optional[Dict] = None) -> Dict:
        soru = gecmis[-1]["content"]
        kaynaklar = getir(kayitlar, soru, (durum.get("is") or {}).get("malzeme", ""), 3)
        sistem = f"{SISTEM}\n\n{_baglam(durum, self.ayarlar.alanlar, gozcu)}{_tesis(kaynaklar)}"
        mesajlar = [{"role": "assistant" if m["role"] == "assistant" else "user",
                     "content": m["content"]} for m in gecmis[-12:] if m.get("content")]
        while mesajlar and mesajlar[0]["role"] == "assistant":
            mesajlar.pop(0)          # API ilk mesajın kullanıcıdan olmasını ister
        metin, hata = self._dene(sistem, mesajlar, 900)
        kaynak = self.secim
        if metin is None:
            metin = uzman.sohbet(soru, durum, self.ayarlar.alanlar, kaynaklar, gozcu)
            kaynak = "uzman"
        return {"metin": metin, "kaynak": kaynak, "yedek": hata is not None, "hata": hata,
                "kaynaklar": kaynaklar, "tesis": bool(kaynaklar)}

    def alarm_yorumu(self, alarm: Dict, durum: Dict, kayitlar: List[Dict]) -> Dict:
        # alarmlarda malzeme puanı kullanılmaz: rezistans arızasına ABS datasheet'i eklenmesin
        kaynaklar = [k for k in getir(kayitlar, f"{alarm['title']} {alarm['detail']}", "", 3)
                     if k.get("tur") == "not"][:2]
        sistem = f"{SISTEM}\n\n{_baglam(durum, self.ayarlar.alanlar, None)}{_tesis(kaynaklar)}"
        soru = (f"Makineden otomatik gelen alarm: {alarm['code']} – {alarm['title']}. {alarm['detail']} "
                "Muhtemel sebepleri ve operatörün SIRAYLA kontrol edeceği kısa listeyi ver.")
        metin, hata = self._dene(sistem, [{"role": "user", "content": soru}], 600)
        kaynak = self.secim
        if metin is None:
            metin, kaynak = uzman.alarm_yorumu(alarm, durum, kaynaklar), "uzman"
        return {"metin": metin, "kaynak": kaynak, "yedek": hata is not None, "hata": hata}

    def recete(self, malzeme: str, et: str, kayitlar: List[Dict], baglam: str = "") -> Dict:
        alanlar = self.ayarlar.alanlar
        kaynaklar = getir(kayitlar, f"{malzeme} {baglam} reçete datasheet kovan kalıp", malzeme, 3)
        sistem = ("Enjeksiyon presi için başlangıç ayarı öner. SADECE geçerli JSON döndür — "
                  "markdown/açıklama YOK.\nŞema: {\"z1\":s,\"z2\":s,\"z3\":s,\"nozul\":s,"
                  "\"enjPress\":s,\"tutmaPress\":s,\"cevrim\":s,\"not\":\"tek cümle uyarı\"} "
                  "(°C, bar, s).\nGÜVENLİ ARALIKLAR: " + ", ".join(
                      f"{k} {a['aralik'][0]}–{a['aralik'][1]}" for k, a in alanlar.items())
                  + _tesis(kaynaklar))
        istek = f"Malzeme: {malzeme}. Et kalınlığı: {et}. {baglam} Başlangıç ayarlarını öner."
        metin, hata = self._dene(sistem, [{"role": "user", "content": istek}], 700)
        if metin is not None:
            try:
                ham = json_ayikla(metin)
                s = ayarlari_sinirla(ham, alanlar)
                if len(s["degerler"]) >= 5:
                    return {"degerler": s["degerler"], "not": str(ham.get("not", ""))[:300],
                            "uyarilar": s["uyarilar"], "kaynak": self.secim, "yedek": False,
                            "kaynaklar": kaynaklar, "tesis": bool(kaynaklar)}
                hata = "Model eksik alan döndürdü."
            except AIHatasi as e:
                hata = str(e)
        r = uzman.recete(malzeme, et, alanlar, kayitlar)
        s = ayarlari_sinirla(r["degerler"], alanlar)
        return {"degerler": s["degerler"], "not": r["not"], "uyarilar": s["uyarilar"],
                "kaynak": "uzman", "yedek": hata is not None, "hata": hata,
                "kaynaklar": r["kaynaklar"], "tesis": any(k.get("tur") == "recete" for k in r["kaynaklar"])}
