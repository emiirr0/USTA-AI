/* USTA·AI arayüzü v2.0.0 — arayuz/app.jsx dosyasından üretilmiştir; elle düzenlemeyin. */
(function () {
"use strict";
const {
  useState,
  useEffect,
  useRef,
  useCallback
} = React;
const C = {
  bg: "#0B0F12",
  panel: "#131A20",
  raised: "#1A232B",
  border: "#263039",
  cyan: "#35C4E0",
  cyanDim: "#1E6B7A",
  amber: "#F5A623",
  amberDim: "#5C4210",
  green: "#3FB950",
  greenDim: "#12341C",
  red: "#E5484D",
  redDim: "#3A1516",
  textHi: "#E8EEF2",
  textMid: "#9DAAB4",
  textLo: "#5C6B75"
};
const sans = "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif";
const mono = "'IBM Plex Mono', Consolas, ui-monospace, monospace";
const TUR_AD = {
  capak: "Çapak",
  kirik: "Kırık",
  cizik: "Çizik",
  leke: "Leke",
  eksik_dolum: "Eksik dolum",
  delik: "Delik",
  cokuntu: "Çöküntü"
};
const KAYNAK_AD = {
  claude: "Claude",
  ollama: "Yerel model",
  uzman: "Çevrimdışı uzman"
};
const QUICK = ["Ürün kenarlarında çapak (flash) var, sebebi ne?", "Kalıp tam dolmuyor (short shot), ne yapmalıyım?", "Çevrim süresini güvenle nasıl kısaltırım?"];
async function api(method, path, body, extraHeaders) {
  const headers = {
    "X-Usta": "1",
    ...(extraHeaders || {})
  };
  let data = body;
  if (body !== undefined && !(body instanceof ArrayBuffer)) {
    headers["Content-Type"] = "application/json";
    data = JSON.stringify(body);
  }
  let r;
  try {
    r = await fetch(path, {
      method,
      headers,
      body: data
    });
  } catch (e) {
    throw new Error("USTA sunucusuna ulaşılamıyor. Program penceresi açık mı?");
  }
  let j = {};
  try {
    j = await r.json();
  } catch (e) {}
  if (!r.ok) throw new Error(j.hata || `Sunucu hatası (${r.status})`);
  return j;
}
const lbl = {
  font: `500 10px ${sans}`,
  letterSpacing: 1,
  color: C.textLo,
  textTransform: "uppercase"
};
const card = {
  background: C.panel,
  border: `1px solid ${C.border}`,
  borderRadius: 8,
  padding: "12px 14px"
};
const btn = (bg, fg, extra) => ({
  background: bg,
  color: fg,
  border: "none",
  borderRadius: 7,
  padding: "8px 14px",
  font: `700 12px ${sans}`,
  cursor: "pointer",
  ...extra
});
const btnGhost = {
  background: C.raised,
  color: C.textMid,
  border: `1px solid ${C.border}`,
  borderRadius: 7,
  padding: "7px 13px",
  font: `600 12px ${sans}`,
  cursor: "pointer"
};
const input = {
  background: C.bg,
  border: `1px solid ${C.border}`,
  borderRadius: 7,
  padding: "9px 11px",
  color: C.textHi,
  font: `400 13px ${sans}`,
  outline: "none"
};
function Baslik({
  children,
  sag
}) {
  return React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      gap: 8,
      flexWrap: "wrap",
      marginBottom: 6
    }
  }, React.createElement("div", {
    style: {
      font: `600 10px ${sans}`,
      letterSpacing: 1.2,
      color: C.textMid,
      textTransform: "uppercase"
    }
  }, children), sag);
}
function Aciklama({
  children
}) {
  return React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textLo,
      marginBottom: 14,
      lineHeight: 1.5
    }
  }, children);
}
function Rozet({
  renk,
  zemin,
  children
}) {
  return React.createElement("span", {
    style: {
      font: `700 9px ${sans}`,
      letterSpacing: 0.5,
      color: renk,
      background: zemin,
      border: `1px solid ${renk}`,
      borderRadius: 4,
      padding: "1px 6px",
      whiteSpace: "nowrap"
    }
  }, children);
}
function Okuma({
  etiket,
  deger,
  birim,
  farkli
}) {
  return React.createElement("div", {
    style: {
      background: C.panel,
      border: `1px solid ${farkli ? C.amberDim : C.border}`,
      borderRadius: 6,
      padding: "10px 12px"
    }
  }, React.createElement("div", {
    style: lbl
  }, etiket), React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 4,
      marginTop: 4
    }
  }, React.createElement("span", {
    style: {
      font: `600 22px ${mono}`,
      color: C.cyan,
      lineHeight: 1
    }
  }, deger ?? "—"), React.createElement("span", {
    style: {
      font: `500 11px ${mono}`,
      color: C.textMid
    }
  }, birim)));
}
function Kivilcim({
  veri,
  renk,
  birim
}) {
  if (!veri.length) return React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textLo,
      height: 46
    }
  }, "veri toplan\u0131yor\u2026");
  const W = 260,
    H = 46;
  const min = Math.min(...veri),
    max = Math.max(...veri);
  const pay = max - min || 1;
  const pts = veri.map((v, i) => `${i / Math.max(veri.length - 1, 1) * W},${H - (v - min) / pay * (H - 10) - 5}`).join(" ");
  return React.createElement("div", null, React.createElement("div", {
    style: {
      font: `600 11px ${mono}`,
      color: renk,
      textAlign: "right",
      marginTop: -18,
      height: 18
    }
  }, veri[veri.length - 1], birim), React.createElement("svg", {
    viewBox: `0 0 ${W} ${H}`,
    style: {
      display: "block",
      width: "100%",
      height: H
    },
    preserveAspectRatio: "none"
  }, React.createElement("polyline", {
    points: pts,
    fill: "none",
    stroke: renk,
    strokeWidth: "1.6",
    vectorEffect: "non-scaling-stroke"
  })));
}
function KaynakEtiketleri({
  kaynaklar
}) {
  if (!kaynaklar || !kaynaklar.length) return null;
  return React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: 5,
      marginTop: 6
    }
  }, kaynaklar.map(s => React.createElement("span", {
    key: s.id,
    title: s.metin,
    style: {
      font: `500 10px ${sans}`,
      color: C.cyan,
      background: C.panel,
      border: `1px solid ${C.cyanDim}`,
      borderRadius: 4,
      padding: "2px 7px"
    }
  }, s.tur === "recete" ? "◆ " : s.tur === "not" ? "⚙ " : "▤ ", s.baslik)));
}
function AIRozeti({
  yanit
}) {
  if (!yanit) return null;
  const ad = KAYNAK_AD[yanit.kaynak] || yanit.kaynak;
  return React.createElement("span", {
    style: {
      display: "inline-flex",
      gap: 5,
      flexWrap: "wrap"
    }
  }, yanit.tesis ? React.createElement(Rozet, {
    renk: C.green,
    zemin: C.greenDim
  }, "\u25CF TES\u0130S VER\u0130S\u0130") : React.createElement(Rozet, {
    renk: C.textMid,
    zemin: C.raised
  }, "\u25CB GENEL B\u0130LG\u0130"), React.createElement(Rozet, {
    renk: yanit.yedek ? C.amber : C.cyan,
    zemin: C.bg
  }, yanit.yedek ? `${ad} · yedek` : ad));
}
function App() {
  const [meta, setMeta] = useState(null);
  const [durum, setDurum] = useState(null);
  const [bagKopuk, setBagKopuk] = useState(false);
  const [tab, setTab] = useState("pano");
  const [bildirim, setBildirim] = useState(null);
  const [bekleyen, setBekleyen] = useState(null);
  const [kullaniciMenu, setKullaniciMenu] = useState(false);
  const [pinIstek, setPinIstek] = useState(null);
  const [isler, setIsler] = useState([]);
  const bildirTimer = useRef(null);
  const bildir = useCallback((metin, tur = "ok") => {
    setBildirim({
      metin,
      tur
    });
    clearTimeout(bildirTimer.current);
    bildirTimer.current = setTimeout(() => setBildirim(null), tur === "hata" ? 6000 : 3500);
  }, []);
  const dene = useCallback(async f => {
    try {
      return await f();
    } catch (e) {
      bildir(e.message, "hata");
      return null;
    }
  }, [bildir]);
  useEffect(() => {
    api("GET", "/api/meta").then(setMeta).catch(e => bildir(e.message, "hata"));
  }, [bildir]);
  useEffect(() => {
    let iptal = false;
    const cek = async () => {
      try {
        const d = await api("GET", "/api/durum");
        if (!iptal) {
          setDurum(d);
          setBagKopuk(false);
        }
      } catch (e) {
        if (!iptal) setBagKopuk(true);
      }
    };
    cek();
    const id = setInterval(cek, 1000);
    return () => {
      iptal = true;
      clearInterval(id);
    };
  }, []);
  const islerYukle = useCallback(() => dene(async () => {
    const r = await api("GET", "/api/isler");
    setIsler(r.isler);
  }), [dene]);
  useEffect(() => {
    islerYukle();
  }, [islerYukle]);
  if (!meta || !durum) {
    return React.createElement("div", {
      style: {
        height: "100vh",
        display: "grid",
        placeItems: "center",
        color: C.textMid,
        font: `500 14px ${sans}`
      }
    }, bagKopuk ? "USTA sunucusuna ulaşılamıyor — program penceresi açık mı?" : "USTA·AI yükleniyor…");
  }
  const m = durum.makine,
    ot = durum.oturum,
    pv = m.pv || {},
    sp = m.sp || {};
  const yazmaModu = ot.mod === "yazma" && ot.yetki.yaz;
  const aktifIs = isler.find(j => j.id === durum.aktif_is);
  const aktifAlarmlar = (durum.alarmlar || []).filter(a => a.active);
  const farkli = k => aktifIs && sp[k] !== undefined && aktifIs.ayarlar[k] !== undefined && Math.round(sp[k]) !== Math.round(aktifIs.ayarlar[k]);
  async function kullaniciSec(u, pin) {
    if (ot.pin_gerekli[u.rol] && pin === undefined) {
      setPinIstek({
        u,
        pin: ""
      });
      return;
    }
    const r = await dene(() => api("POST", "/api/oturum", {
      kullanici_id: u.id,
      pin: pin || ""
    }));
    if (r) {
      setKullaniciMenu(false);
      setPinIstek(null);
      bildir(`${r.kullanici.ad} (${r.rol_ad}) giriş yaptı.`);
    }
  }
  async function modSec(mod) {
    await dene(() => api("POST", "/api/mod", {
      mod
    }));
  }
  async function yazmaIste(alan, deger, kaynak) {
    const r = await dene(() => api("POST", "/api/yazma/dogrula", {
      alan,
      deger,
      kaynak
    }));
    if (r) setBekleyen(r);
  }
  async function yazmaOnayla() {
    const r = await dene(() => api("POST", "/api/yazma/onayla", {
      belirtec: bekleyen.belirtec
    }));
    setBekleyen(null);
    if (r) bildir(r.mesaj);
  }
  const TabBtn = (id, cocuk, rozet) => React.createElement("button", {
    key: id,
    onClick: () => setTab(id),
    style: {
      font: `600 12px ${sans}`,
      letterSpacing: 0.3,
      padding: "11px 14px",
      background: "transparent",
      color: tab === id ? C.textHi : C.textLo,
      border: "none",
      flexShrink: 0,
      whiteSpace: "nowrap",
      borderBottom: tab === id ? `2px solid ${C.amber}` : "2px solid transparent",
      display: "flex",
      alignItems: "center",
      gap: 7,
      cursor: "pointer"
    }
  }, cocuk, rozet > 0 && React.createElement("span", {
    style: {
      font: `700 10px ${mono}`,
      background: C.red,
      color: "#fff",
      borderRadius: 9,
      padding: "1px 6px"
    }
  }, rozet));
  const ortak = {
    meta,
    durum,
    dene,
    bildir,
    yazmaModu,
    yazmaIste,
    isler,
    islerYukle,
    setTab
  };
  return React.createElement("div", {
    className: "usta-kok"
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 10,
      padding: "10px 16px",
      borderBottom: `1px solid ${C.border}`,
      background: C.raised,
      position: "relative",
      flexWrap: "wrap"
    }
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 11
    }
  }, React.createElement("div", {
    style: {
      width: 30,
      height: 30,
      borderRadius: 6,
      background: C.amberDim,
      display: "grid",
      placeItems: "center",
      border: `1px solid ${C.amber}`
    }
  }, React.createElement("span", {
    style: {
      font: `700 15px ${mono}`,
      color: C.amber
    }
  }, "\u25C6")), React.createElement("div", null, React.createElement("div", {
    style: {
      font: `700 14px ${sans}`,
      letterSpacing: 1
    }
  }, "USTA", React.createElement("span", {
    style: {
      color: C.amber
    }
  }, "\xB7"), "AI ", React.createElement("span", {
    style: {
      font: `500 10px ${sans}`,
      color: C.textMid,
      letterSpacing: 0
    }
  }, "Operat\xF6r Dan\u0131\u015Fman\u0131 \xB7 v", meta.surum)), React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: 6,
      background: bagKopuk || m.hata ? C.red : C.green,
      boxShadow: `0 0 6px ${bagKopuk || m.hata ? C.red : C.green}`
    }
  }), React.createElement("span", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo
    }
  }, m.makine, " \xB7 ", bagKopuk ? "SUNUCU BAĞLANTISI KOPTU" : `${m.baglanti} · ${m.durum}`), React.createElement("span", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo
    }
  }, "\xB7 AI: ", meta.ai.etiket)))), React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10
    }
  }, ot.yetki.yaz && !meta.salt_okunur && React.createElement("div", {
    style: {
      display: "flex",
      background: C.panel,
      borderRadius: 7,
      padding: 3,
      border: `1px solid ${C.border}`
    }
  }, [["danisman", "Danışman"], ["yazma", "Onaylı Yazma"]].map(([id, ad]) => React.createElement("button", {
    key: id,
    onClick: () => modSec(id),
    style: {
      font: `600 11px ${sans}`,
      padding: "6px 12px",
      borderRadius: 5,
      border: "none",
      cursor: "pointer",
      background: ot.mod === id ? id === "yazma" ? C.green : C.amber : "transparent",
      color: ot.mod === id ? "#0b0f12" : C.textMid
    }
  }, ad))), React.createElement("button", {
    onClick: () => setKullaniciMenu(v => !v),
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      background: C.panel,
      border: `1px solid ${C.border}`,
      borderRadius: 7,
      padding: "6px 10px",
      cursor: "pointer"
    }
  }, React.createElement("span", {
    style: {
      width: 22,
      height: 22,
      borderRadius: 11,
      background: C.cyanDim,
      display: "grid",
      placeItems: "center",
      font: `700 11px ${sans}`,
      color: C.textHi
    }
  }, ot.kullanici.ad.charAt(0)), React.createElement("div", {
    style: {
      textAlign: "left"
    }
  }, React.createElement("div", {
    style: {
      font: `600 11px ${sans}`,
      color: C.textHi,
      lineHeight: 1.1
    }
  }, ot.kullanici.ad), React.createElement("div", {
    style: {
      font: `500 9px ${sans}`,
      color: C.textLo,
      lineHeight: 1.1
    }
  }, ot.rol_ad, " \xB7 ", ot.vardiya)), React.createElement("span", {
    style: {
      font: `600 10px ${mono}`,
      color: C.textLo
    }
  }, "\u25BE"))), kullaniciMenu && React.createElement("div", {
    style: {
      position: "absolute",
      right: 16,
      top: 58,
      zIndex: 30,
      background: C.raised,
      border: `1px solid ${C.border}`,
      borderRadius: 8,
      padding: 6,
      minWidth: 220,
      boxShadow: "0 8px 24px rgba(0,0,0,.5)"
    }
  }, React.createElement("div", {
    style: {
      ...lbl,
      padding: "4px 8px"
    }
  }, "Vardiya giri\u015Fi \xB7 ", ot.vardiya), meta.kullanicilar.map(u => React.createElement("button", {
    key: u.id,
    onClick: () => kullaniciSec(u),
    style: {
      display: "flex",
      width: "100%",
      alignItems: "center",
      gap: 8,
      background: u.id === ot.kullanici.id ? C.panel : "transparent",
      border: "none",
      borderRadius: 6,
      padding: 8,
      cursor: "pointer",
      textAlign: "left"
    }
  }, React.createElement("span", {
    style: {
      width: 22,
      height: 22,
      borderRadius: 11,
      background: C.cyanDim,
      display: "grid",
      placeItems: "center",
      font: `700 11px ${sans}`,
      color: C.textHi
    }
  }, u.ad.charAt(0)), React.createElement("div", {
    style: {
      flex: 1
    }
  }, React.createElement("div", {
    style: {
      font: `600 12px ${sans}`,
      color: C.textHi
    }
  }, u.ad), React.createElement("div", {
    style: {
      font: `500 10px ${sans}`,
      color: C.textLo
    }
  }, meta.roller[u.rol], ot.pin_gerekli[u.rol] ? " · PIN" : "")), u.id === ot.kullanici.id && React.createElement("span", {
    style: {
      font: `700 11px ${mono}`,
      color: C.green
    }
  }, "\u2713"))), pinIstek && React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      kullaniciSec(pinIstek.u, pinIstek.pin);
    },
    style: {
      display: "flex",
      gap: 6,
      padding: 8
    }
  }, React.createElement("input", {
    autoFocus: true,
    type: "password",
    inputMode: "numeric",
    value: pinIstek.pin,
    onChange: e => setPinIstek({
      ...pinIstek,
      pin: e.target.value
    }),
    placeholder: `${pinIstek.u.ad} PIN`,
    style: {
      ...input,
      flex: 1,
      padding: "6px 9px"
    }
  }), React.createElement("button", {
    type: "submit",
    style: btn(C.amber, "#1a1204", {
      padding: "6px 12px"
    })
  }, "Gir")))), React.createElement("div", {
    style: {
      display: "flex",
      padding: "0 8px",
      borderBottom: `1px solid ${C.border}`,
      background: C.panel,
      overflowX: "auto"
    }
  }, TabBtn("pano", "PANO"), TabBtn("isler", "İŞLER"), TabBtn("recete", "REÇETE"), TabBtn("alarmlar", "ALARMLAR", aktifAlarmlar.length), TabBtn("ai", React.createElement(React.Fragment, null, React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: 7,
      background: C.amber,
      boxShadow: `0 0 7px ${C.amber}`
    }
  }), "AI AS\u0130STAN")), TabBtn("bilgi", "BİLGİ TABANI"), TabBtn("kayit", "KAYIT")), yazmaModu ? React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "8px 16px",
      background: "#0f2417",
      borderBottom: `1px solid ${C.greenDim}`,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    style: {
      font: `700 11px ${mono}`,
      color: C.green,
      letterSpacing: 1
    }
  }, "\u2713 ONAYLI YAZMA \xB7 FAZ 2"), React.createElement("span", {
    style: {
      font: `500 11px ${sans}`,
      color: C.textMid
    }
  }, "Yaln\u0131zca g\xFCvenli parametreler \xB7 do\u011Frulama + insan onay\u0131 \xB7 her yazma ", React.createElement("b", {
    style: {
      color: C.green
    }
  }, "kay\u0131tl\u0131"))) : React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 10,
      padding: "8px 16px",
      background: "repeating-linear-gradient(45deg,#1c1608,#1c1608 10px,#171205 10px,#171205 20px)",
      borderBottom: `1px solid ${C.amberDim}`,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    style: {
      font: `700 11px ${mono}`,
      color: C.amber,
      letterSpacing: 1
    }
  }, "\u2691 DANI\u015EMAN MODU \xB7 FAZ 0"), React.createElement("span", {
    style: {
      font: `500 11px ${sans}`,
      color: C.textMid
    }
  }, "AI yaln\u0131zca \xF6neri verir \xB7 makineye yazma ", React.createElement("b", {
    style: {
      color: C.red
    }
  }, "KAPALI"), " \xB7 de\u011Ferleri operat\xF6r girer")), React.createElement("div", {
    className: "usta-govde"
  }, React.createElement("div", {
    className: "usta-sol"
  }, React.createElement("div", {
    style: {
      font: `600 10px ${sans}`,
      letterSpacing: 1.2,
      color: C.cyan,
      textTransform: "uppercase",
      marginBottom: 10
    }
  }, "\u25CF Canl\u0131 Makine De\u011Ferleri"), React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 8
    }
  }, React.createElement(Okuma, {
    etiket: "B\xF6lge 1",
    deger: pv.z1,
    birim: "\xB0C",
    farkli: farkli("z1")
  }), React.createElement(Okuma, {
    etiket: "B\xF6lge 2",
    deger: pv.z2,
    birim: "\xB0C",
    farkli: farkli("z2")
  }), React.createElement(Okuma, {
    etiket: "B\xF6lge 3",
    deger: pv.z3,
    birim: "\xB0C",
    farkli: farkli("z3")
  }), React.createElement(Okuma, {
    etiket: "Nozul",
    deger: pv.nozul,
    birim: "\xB0C",
    farkli: farkli("nozul")
  }), React.createElement(Okuma, {
    etiket: "Enj. Bas\u0131n\xE7",
    deger: pv.enjPress,
    birim: "bar"
  }), React.createElement(Okuma, {
    etiket: "Tutma Bas.",
    deger: pv.tutmaPress,
    birim: "bar",
    farkli: farkli("tutmaPress")
  }), React.createElement(Okuma, {
    etiket: "\xC7evrim",
    deger: pv.cevrim,
    birim: "s"
  }), React.createElement(Okuma, {
    etiket: "Yast\u0131k",
    deger: pv.yastik,
    birim: "mm"
  })), React.createElement("div", {
    style: {
      ...card,
      marginTop: 12,
      padding: "10px 12px"
    }
  }, React.createElement("div", {
    style: lbl
  }, "Aktif \u0130\u015F"), React.createElement("div", {
    style: {
      font: `500 13px ${sans}`,
      color: C.textHi,
      marginTop: 3
    }
  }, aktifIs ? aktifIs.urun : m.is && m.is.urun || "—"), React.createElement("div", {
    style: {
      font: `500 11px ${mono}`,
      color: C.textLo,
      marginTop: 4
    }
  }, aktifIs ? `${aktifIs.kalip} · ${aktifIs.malzeme}` : ""), React.createElement("div", {
    style: {
      font: `500 11px ${mono}`,
      color: C.textLo,
      marginTop: 2
    }
  }, "Bask\u0131: ", (m.baski || 0).toLocaleString("tr-TR"))), React.createElement("div", {
    style: {
      font: `500 10px ${sans}`,
      color: C.textLo,
      marginTop: 10,
      lineHeight: 1.5
    }
  }, "Turuncu \xE7er\xE7eve: setpoint aktif i\u015Fin kay\u0131tl\u0131 de\u011Ferinden farkl\u0131.")), React.createElement("div", {
    className: "usta-sag"
  }, bildirim && React.createElement("div", {
    style: {
      margin: "12px 16px 0",
      background: bildirim.tur === "hata" ? C.redDim : C.greenDim,
      border: `1px solid ${bildirim.tur === "hata" ? C.red : C.green}`,
      borderRadius: 7,
      padding: "9px 13px",
      font: `600 12px ${sans}`,
      color: bildirim.tur === "hata" ? "#ffb4b6" : C.green
    }
  }, bildirim.tur === "hata" ? "✕ " : "✓ ", bildirim.metin), bekleyen && React.createElement(YazmaOnayi, {
    b: bekleyen,
    onayla: yazmaOnayla,
    iptal: () => setBekleyen(null)
  }), React.createElement("div", {
    className: "usta-icerik"
  }, tab === "pano" && React.createElement(Pano, ortak), tab === "isler" && React.createElement(Isler, ortak), tab === "recete" && React.createElement(Recete, ortak), tab === "alarmlar" && React.createElement(Alarmlar, ortak), tab === "ai" && React.createElement(Sohbet, ortak), tab === "bilgi" && React.createElement(Bilgi, ortak), tab === "kayit" && React.createElement(Kayit, ortak)))));
}
function YazmaOnayi({
  b,
  onayla,
  iptal
}) {
  return React.createElement("div", {
    style: {
      margin: "12px 16px 0",
      background: C.panel,
      border: `1px solid ${b.gecti ? C.amber : C.red}`,
      borderRadius: 8,
      padding: 14
    }
  }, React.createElement("div", {
    style: {
      font: `700 11px ${mono}`,
      color: b.gecti ? C.amber : C.red,
      letterSpacing: 1,
      marginBottom: 8
    }
  }, b.gecti ? "◆ YAZMA ONAYI GEREKİYOR" : "✕ DOĞRULAMA REDDETTİ"), React.createElement("div", {
    style: {
      font: `500 14px ${sans}`,
      color: C.textHi
    }
  }, b.etiket, ": ", React.createElement("span", {
    style: {
      font: `600 15px ${mono}`,
      color: C.cyan
    }
  }, b.mevcut ?? "—"), React.createElement("span", {
    style: {
      color: C.textLo
    }
  }, " \u2192 "), React.createElement("span", {
    style: {
      font: `600 15px ${mono}`,
      color: b.gecti ? C.amber : C.red
    }
  }, Number.isFinite(b.hedef) ? b.hedef : "?", b.birim)), React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid,
      marginTop: 6
    }
  }, "Makinenin g\xFCvenli aral\u0131\u011F\u0131: ", React.createElement("b", {
    style: {
      color: C.textHi
    }
  }, b.min, "\u2013", b.max, " ", b.birim), b.gecti ? " · Onaylarsan makineye yazılır ve kayıt altına alınır (90 sn içinde)." : ""), !b.gecti && React.createElement("ul", {
    style: {
      margin: "8px 0 0 18px",
      color: "#ffb4b6",
      font: `400 12px ${sans}`,
      lineHeight: 1.6
    }
  }, b.nedenler.map((n, i) => React.createElement("li", {
    key: i
  }, n))), React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginTop: 12
    }
  }, b.gecti && React.createElement("button", {
    onClick: onayla,
    style: btn(C.green, "#0b0f12")
  }, "\u2713 Onayla ve yaz"), React.createElement("button", {
    onClick: iptal,
    style: btnGhost
  }, b.gecti ? "İptal" : "Kapat")));
}
function Pano({
  durum,
  setTab
}) {
  const m = durum.makine,
    u = m.uretim,
    g = durum.gozcu;
  const trend = m.trend || [];
  const toplam = u ? u.saglam + u.fire : 0;
  const gozcuBagli = g && g.bagli;
  const turler = gozcuBagli && g.toplam ? g.turler : u ? u.turler : {};
  const turToplam = Object.values(turler || {}).reduce((a, b) => a + b, 0);
  const kpi = [["Üretim", toplam, C.cyan], ["Sağlam", u ? u.saglam : "—", C.green], ["Fire", u ? u.fire : "—", C.red], ["Fire %", toplam ? (u.fire / toplam * 100).toFixed(1) : "0.0", C.amber], ["Ort. Çevrim", trend.length ? (trend.reduce((a, b) => a + (b.cevrim || 0), 0) / trend.length).toFixed(1) + " s" : "—", C.cyan]];
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, {
    sag: React.createElement("span", {
      style: {
        font: `500 10px ${mono}`,
        color: C.textLo
      }
    }, m.baglanti, " \xB7 ", durum.zaman)
  }, "Canl\u0131 \xDCretim Panosu \xB7 ", m.makine), React.createElement("div", {
    className: "usta-kpi"
  }, kpi.map(([l, v, col]) => React.createElement("div", {
    key: l,
    style: {
      ...card,
      padding: "10px 12px"
    }
  }, React.createElement("div", {
    style: {
      ...lbl,
      fontSize: 9
    }
  }, l), React.createElement("div", {
    style: {
      font: `700 20px ${mono}`,
      color: col,
      marginTop: 3
    }
  }, v)))), m.fazlar && m.fazlar.length > 0 && React.createElement("div", {
    style: {
      ...card,
      marginTop: 12
    }
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 8
    }
  }, "\xC7evrim Faz\u0131 ", m.durum !== "ÇALIŞIYOR" && React.createElement("b", {
    style: {
      color: C.red
    }
  }, "\xB7 ", m.durum)), React.createElement("div", {
    style: {
      display: "flex",
      gap: 6
    }
  }, m.fazlar.map((nm, i) => React.createElement("div", {
    key: nm,
    style: {
      flex: 1,
      textAlign: "center",
      padding: "7px 4px",
      borderRadius: 6,
      background: i === m.faz_i ? C.amber : C.raised,
      color: i === m.faz_i ? "#1a1204" : C.textLo,
      font: `700 10px ${sans}`,
      letterSpacing: 0.5,
      boxShadow: i === m.faz_i ? `0 0 10px ${C.amber}55` : "none",
      transition: "all .25s",
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap"
    }
  }, nm)))), React.createElement("div", {
    className: "usta-ikili",
    style: {
      marginTop: 12
    }
  }, React.createElement("div", {
    style: card
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 6
    }
  }, "\xC7evrim S\xFCresi (s)"), React.createElement(Kivilcim, {
    veri: trend.map(t => t.cevrim),
    renk: C.cyan,
    birim: " s"
  })), React.createElement("div", {
    style: card
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 6
    }
  }, "Yast\u0131k (mm)"), React.createElement(Kivilcim, {
    veri: trend.map(t => t.yastik),
    renk: C.green,
    birim: " mm"
  }))), React.createElement("div", {
    className: "usta-ikili",
    style: {
      marginTop: 12
    }
  }, React.createElement("div", {
    style: card
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 8
    }
  }, "Fire K\u0131r\u0131l\u0131m\u0131 \xB7 ", gozcuBagli && g.toplam ? "GÖZCÜ·AI (gerçek muayene)" : "simülasyon kalite istasyonu"), turToplam === 0 ? React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textLo
    }
  }, "hen\xFCz fire yok") : Object.entries(turler).sort((a, b) => b[1] - a[1]).map(([k, v]) => React.createElement("div", {
    key: k,
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      marginBottom: 6
    }
  }, React.createElement("span", {
    style: {
      font: `500 11px ${sans}`,
      color: C.textMid,
      width: 90
    }
  }, TUR_AD[k] || k), React.createElement("div", {
    style: {
      flex: 1,
      height: 8,
      background: C.raised,
      borderRadius: 4,
      overflow: "hidden"
    }
  }, React.createElement("div", {
    style: {
      width: `${v / turToplam * 100}%`,
      height: "100%",
      background: C.red
    }
  })), React.createElement("span", {
    style: {
      font: `600 11px ${mono}`,
      color: C.textHi,
      width: 30,
      textAlign: "right"
    }
  }, v)))), React.createElement("div", {
    style: card
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 6
    }
  }, "Son Alarmlar"), (durum.alarmlar || []).length === 0 && React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textLo
    }
  }, "kay\u0131t yok"), (durum.alarmlar || []).slice(0, 5).map(a => React.createElement("div", {
    key: a.id,
    onClick: () => setTab("alarmlar"),
    style: {
      display: "flex",
      justifyContent: "space-between",
      gap: 8,
      padding: "5px 0",
      borderBottom: `1px solid ${C.border}`,
      cursor: "pointer"
    }
  }, React.createElement("span", {
    style: {
      font: `500 11px ${sans}`,
      color: a.active ? a.sev === "crit" ? C.red : C.amber : C.textMid
    }
  }, a.code, " \xB7 ", a.title), React.createElement("span", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo,
      whiteSpace: "nowrap"
    }
  }, a.active ? a.start : "✓ " + (a.end || "")))))), React.createElement("div", {
    style: {
      ...card,
      marginTop: 12,
      border: `1px ${gozcuBagli ? "solid" : "dashed"} ${gozcuBagli ? C.cyanDim : C.border}`
    }
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 6
    }
  }, "\u25C6 G\xD6ZC\xDC\xB7AI Entegrasyonu \xB7 ", gozcuBagli ? React.createElement("b", {
    style: {
      color: C.green
    }
  }, "BA\u011ELI") : "bağlı değil"), gozcuBagli ? React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid,
      lineHeight: 1.6
    }
  }, "G\xF6r\xFCnt\xFC muayenesi: ", React.createElement("b", {
    style: {
      color: C.textHi
    }
  }, g.toplam), " par\xE7a \xB7 sa\u011Flam ", React.createElement("b", {
    style: {
      color: C.green
    }
  }, g.saglam), " \xB7 \u015F\xFCpheli ", React.createElement("b", {
    style: {
      color: C.amber
    }
  }, g.supheli), " \xB7 fire ", React.createElement("b", {
    style: {
      color: C.red
    }
  }, g.fire), " (%", g.fire_orani.toFixed(1), ")", g.baskin_ad ? React.createElement(React.Fragment, null, " \xB7 en s\u0131k: ", React.createElement("b", {
    style: {
      color: C.textHi
    }
  }, g.baskin_ad)) : null, g.son && g.son.length > 0 && React.createElement("div", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo,
      marginTop: 4
    }
  }, "son: ", g.son.slice(0, 4).map(s => `${s.parca} ${s.karar}`).join(" · ")), React.createElement("div", {
    style: {
      marginTop: 4
    }
  }, "AI AS\u0130STAN bu veriyi g\xF6r\xFCr: \"fire neden artt\u0131?\" diye sorabilirsin.")) : React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textMid,
      lineHeight: 1.55
    }
  }, g && g.hata ? React.createElement("span", {
    style: {
      color: C.amber
    }
  }, g.hata, " \xB7 ") : null, "G\xD6ZC\xDC\xB7AI'nin \xE7al\u0131\u015Fma klas\xF6r\xFCn\xFC ", React.createElement("code", null, "veri/ayarlar.json"), " i\xE7inde ", React.createElement("code", null, "\"gozcu\": ", "{", "\"klasor\": \"...\"", "}"), " olarak tan\u0131mlarsan, muayene sonu\xE7lar\u0131 ve fire t\xFCrleri buraya akar ve USTA \xF6nerilerine kat\u0131l\u0131r.")));
}
function Isler({
  meta,
  durum,
  dene,
  bildir,
  yazmaModu,
  yazmaIste,
  isler,
  islerYukle
}) {
  const ot = durum.oturum;
  const [acik, setAcik] = useState(null);
  const [taslak, setTaslak] = useState(null);
  const [yeni, setYeni] = useState(null);
  const [mesgul, setMesgul] = useState(false);
  const [uyarilar, setUyarilar] = useState([]);
  const alanlar = meta.alanlar;
  function ac(j) {
    if (acik === j.id) {
      setAcik(null);
      return;
    }
    setAcik(j.id);
    setTaslak({
      ...j.ayarlar
    });
    setUyarilar([]);
  }
  async function kaydet() {
    const r = await dene(() => api("PUT", `/api/isler/${acik}`, {
      ayarlar: taslak
    }));
    if (r) {
      setUyarilar(r.uyarilar);
      bildir("İş ayarları kaydedildi.");
      islerYukle();
    }
  }
  async function ekle() {
    const r = await dene(() => api("POST", "/api/isler", yeni));
    if (r) {
      setYeni(null);
      await islerYukle();
      setAcik(r.id);
      setTaslak({
        ...r.ayarlar
      });
      bildir(`Yeni iş eklendi: ${r.urun}.`);
    }
  }
  async function aktifYap(j) {
    const r = await dene(() => api("POST", `/api/isler/${j.id}/aktif`));
    if (r) bildir(r.yazildi ? `Aktif iş: ${j.urun} — ayarlar makineye yüklendi ve kayda geçti.` : `Aktif iş: ${j.urun}. Danışman modu: değerleri makine panelinden sen gir.`);
  }
  async function sil(j) {
    if (!window.confirm(`"${j.urun}" işi silinsin mi?`)) return;
    const r = await dene(() => api("DELETE", `/api/isler/${j.id}`));
    if (r) {
      setAcik(null);
      islerYukle();
      bildir("İş silindi.");
    }
  }
  async function oner() {
    setMesgul(true);
    const r = await dene(() => api("POST", `/api/isler/${acik}/oner`));
    setMesgul(false);
    if (r) {
      setTaslak(p => ({
        ...p,
        ...r.degerler
      }));
      setUyarilar([...(r.uyarilar || []), ...(r.not ? [r.not] : [])]);
      bildir(`Öneri: ${KAYNAK_AD[r.kaynak] || r.kaynak}. Kaydetmeden önce kontrol et.`);
    }
  }
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, {
    sag: ot.yetki.is_duzenle && React.createElement("button", {
      onClick: () => setYeni(yeni ? null : {
        urun: "",
        kalip: "",
        malzeme: meta.malzemeler[0]
      }),
      style: yeni ? btnGhost : btn(C.amber, "#1a1204", {
        padding: "6px 12px",
        fontSize: 11
      })
    }, yeni ? "Vazgeç" : "+ Yeni iş")
  }, "\u0130\u015Fler \xB7 Kal\u0131p + Malzeme + \xDCr\xFCn \xB7 ", isler.length), React.createElement(Aciklama, null, "Her i\u015F bir kez eklenir ve bilgisayarda kal\u0131c\u0131 olarak saklan\u0131r. Bir i\u015Fe bas: de\u011Ferlerini g\xF6r, elle de\u011Fi\u015Ftir ya da AI'ya \xF6nertir. \"Aktif i\u015F yap\" dersen (Onayl\u0131 Yazma modunda) makine o i\u015Fe g\xF6re ayarlan\u0131r."), yeni && React.createElement("div", {
    style: {
      ...card,
      border: `1px solid ${C.amberDim}`,
      marginBottom: 14
    }
  }, React.createElement("div", {
    style: {
      font: `700 11px ${mono}`,
      color: C.amber,
      letterSpacing: 1,
      marginBottom: 10
    }
  }, "\u25C6 YEN\u0130 \u0130\u015E EKLE"), React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: 10
    }
  }, React.createElement("input", {
    value: yeni.urun,
    onChange: e => setYeni({
      ...yeni,
      urun: e.target.value
    }),
    placeholder: "\xDCr\xFCn ad\u0131 (\xF6rn: Peynir \xDC\xE7gen Kutu)",
    style: {
      ...input,
      flex: "1 1 200px"
    }
  }), React.createElement("input", {
    value: yeni.kalip,
    onChange: e => setYeni({
      ...yeni,
      kalip: e.target.value
    }),
    placeholder: "Kal\u0131p kodu (\xF6rn: K-512)",
    style: {
      ...input,
      flex: "0 1 150px"
    }
  }), React.createElement("select", {
    value: yeni.malzeme,
    onChange: e => setYeni({
      ...yeni,
      malzeme: e.target.value
    }),
    style: input
  }, meta.malzemeler.map(x => React.createElement("option", {
    key: x
  }, x))), React.createElement("button", {
    onClick: ekle,
    disabled: !yeni.urun.trim() || !yeni.kalip.trim(),
    style: btn(C.green, "#0b0f12", {
      opacity: !yeni.urun.trim() || !yeni.kalip.trim() ? 0.5 : 1
    })
  }, "Ekle"))), isler.map(j => {
    const aktif = j.id === durum.aktif_is,
      open = j.id === acik;
    return React.createElement("div", {
      key: j.id,
      style: {
        ...card,
        borderLeft: `3px solid ${aktif ? C.green : C.cyanDim}`,
        borderColor: aktif ? C.green : C.border,
        marginBottom: 8
      }
    }, React.createElement("div", {
      onClick: () => ac(j),
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        cursor: "pointer"
      }
    }, React.createElement("div", null, React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 8
      }
    }, React.createElement("span", {
      style: {
        font: `600 14px ${sans}`,
        color: C.textHi
      }
    }, j.urun), aktif && React.createElement(Rozet, {
      renk: C.green,
      zemin: C.greenDim
    }, "\u25CF AKT\u0130F")), React.createElement("div", {
      style: {
        font: `500 11px ${mono}`,
        color: C.textLo,
        marginTop: 3
      }
    }, "Kal\u0131p ", j.kalip, " \xB7 ", j.malzeme)), React.createElement("span", {
      style: {
        font: `600 13px ${mono}`,
        color: C.textLo
      }
    }, open ? "▾" : "▸")), open && taslak && React.createElement("div", {
      style: {
        marginTop: 12,
        borderTop: `1px solid ${C.border}`,
        paddingTop: 12
      }
    }, React.createElement("div", {
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 10,
        flexWrap: "wrap",
        gap: 8
      }
    }, React.createElement("span", {
      style: lbl
    }, ot.yetki.is_duzenle ? "Değerler — elle gir ya da AI'ya önert" : "Değerler (görüntüleme)"), ot.yetki.is_duzenle && React.createElement("button", {
      onClick: oner,
      disabled: mesgul,
      style: {
        background: mesgul ? C.raised : C.amberDim,
        color: C.amber,
        border: `1px solid ${C.amber}`,
        borderRadius: 6,
        padding: "5px 11px",
        font: `600 11px ${sans}`,
        cursor: mesgul ? "default" : "pointer"
      }
    }, mesgul ? "Öneriliyor…" : "◆ AI ile öner")), React.createElement("div", {
      style: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
        gap: 8
      }
    }, Object.entries(alanlar).map(([k, f]) => React.createElement("div", {
      key: k,
      style: {
        background: C.bg,
        border: `1px solid ${f.yazilabilir ? C.amberDim : C.border}`,
        borderRadius: 6,
        padding: "8px 10px"
      }
    }, React.createElement("div", {
      style: {
        ...lbl,
        fontSize: 9
      }
    }, f.etiket, " ", f.birim), ot.yetki.is_duzenle ? React.createElement("input", {
      type: "number",
      value: taslak[k] ?? "",
      onChange: e => setTaslak({
        ...taslak,
        [k]: e.target.value === "" ? "" : Number(e.target.value)
      }),
      style: {
        width: "100%",
        marginTop: 4,
        background: C.panel,
        border: `1px solid ${C.border}`,
        borderRadius: 5,
        padding: "5px 7px",
        color: f.yazilabilir ? C.amber : C.textHi,
        font: `600 15px ${mono}`,
        outline: "none"
      }
    }) : React.createElement("div", {
      style: {
        marginTop: 4,
        font: `600 16px ${mono}`,
        color: f.yazilabilir ? C.amber : C.textHi
      }
    }, taslak[k]), yazmaModu && (f.yazilabilir ? React.createElement("button", {
      onClick: () => yazmaIste(k, Number(taslak[k]), `İş değeri · ${j.urun}`),
      style: {
        marginTop: 5,
        width: "100%",
        background: C.green,
        color: "#0b0f12",
        border: "none",
        borderRadius: 5,
        padding: "4px 0",
        font: `700 10px ${sans}`,
        cursor: "pointer"
      }
    }, "Makineye uygula \u2192") : React.createElement("div", {
      style: {
        marginTop: 5,
        font: `600 9px ${sans}`,
        color: C.textLo,
        textAlign: "center"
      }
    }, "\uD83D\uDD12 Faz 3"))))), uyarilar.length > 0 && React.createElement("ul", {
      style: {
        margin: "10px 0 0 18px",
        color: C.amber,
        font: `400 12px ${sans}`,
        lineHeight: 1.6
      }
    }, uyarilar.map((u, i) => React.createElement("li", {
      key: i
    }, u))), React.createElement("div", {
      style: {
        display: "flex",
        gap: 8,
        marginTop: 12,
        flexWrap: "wrap",
        alignItems: "center"
      }
    }, ot.yetki.is_duzenle && React.createElement("button", {
      onClick: kaydet,
      style: {
        ...btnGhost,
        color: C.textHi
      }
    }, "Kaydet"), ot.yetki.is_sec ? React.createElement("button", {
      onClick: () => aktifYap(j),
      disabled: aktif,
      style: btn(aktif ? C.raised : C.amber, aktif ? C.textLo : "#1a1204", {
        cursor: aktif ? "default" : "pointer"
      })
    }, aktif ? "✓ Zaten aktif" : "Aktif iş yap →") : React.createElement("span", {
      style: {
        font: `500 11px ${sans}`,
        color: C.textLo
      }
    }, "De\u011Fi\u015Fiklik ya da i\u015F se\xE7imi i\xE7in usta/m\xFChendis giri\u015Fi gerekir."), ot.yetki.is_duzenle && !aktif && React.createElement("button", {
      onClick: () => sil(j),
      style: {
        ...btnGhost,
        color: C.red,
        marginLeft: "auto"
      }
    }, "Sil")), ot.yetki.is_duzenle && !yazmaModu && React.createElement("div", {
      style: {
        font: `500 10px ${mono}`,
        color: C.textLo,
        marginTop: 8
      }
    }, "\u2691 Makineye yazmak i\xE7in \xFCstten \"Onayl\u0131 Yazma\" moduna ge\xE7.")));
  }));
}
function Recete({
  meta,
  dene,
  bildir,
  yazmaModu,
  yazmaIste
}) {
  const [malzeme, setMalzeme] = useState(meta.malzemeler[0]);
  const [et, setEt] = useState(meta.etler[1]);
  const [r, setR] = useState(null);
  const [mesgul, setMesgul] = useState(false);
  const [sonuclar, setSonuclar] = useState([]);
  useEffect(() => {
    dene(async () => setSonuclar((await api("GET", "/api/sonuclar")).sonuclar));
  }, [dene]);
  async function oner() {
    setMesgul(true);
    setR(null);
    const y = await dene(() => api("POST", "/api/recete", {
      malzeme,
      et
    }));
    setMesgul(false);
    if (y) setR({
      ...y,
      malzeme,
      et
    });
  }
  async function sonuc(tur) {
    const y = await dene(() => api("POST", "/api/sonuclar", {
      malzeme: r.malzeme,
      et: r.et,
      sonuc: tur,
      recete: r.degerler
    }));
    if (y) {
      setSonuclar(y.sonuclar);
      setR(null);
      bildir("Sonuç kaydedildi — öğrenme verisine eklendi.");
    }
  }
  const iyi = sonuclar.filter(s => s.sonuc === "iyi").length,
    fire = sonuclar.length - iyi;
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, null, "Yeni \xDCr\xFCn \xB7 Ba\u015Flang\u0131\xE7 Ayar\u0131"), React.createElement(Aciklama, null, yazmaModu ? "AI başlangıç değerlerini önersin; güvenli parametreleri tek tuşla doğrulayıp onaylayarak makineye yazabilirsin. Kritik parametreler kilitli (Faz 3)." : "AI başlangıç değerlerini önersin. Danışman modunda değerleri panele sen girersin."), React.createElement("div", {
    style: {
      display: "flex",
      gap: 10,
      flexWrap: "wrap",
      marginBottom: 14,
      alignItems: "flex-end"
    }
  }, React.createElement("div", null, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 5
    }
  }, "Malzeme"), React.createElement("select", {
    value: malzeme,
    onChange: e => setMalzeme(e.target.value),
    style: input
  }, meta.malzemeler.map(x => React.createElement("option", {
    key: x
  }, x)))), React.createElement("div", null, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 5
    }
  }, "Et Kal\u0131nl\u0131\u011F\u0131"), React.createElement("select", {
    value: et,
    onChange: e => setEt(e.target.value),
    style: input
  }, meta.etler.map(x => React.createElement("option", {
    key: x
  }, x)))), React.createElement("button", {
    onClick: oner,
    disabled: mesgul,
    style: btn(mesgul ? C.raised : C.amber, mesgul ? C.textLo : "#1a1204", {
      padding: "10px 16px",
      fontSize: 13
    })
  }, mesgul ? "Öneriliyor…" : "Başlangıç ayarı öner")), r && React.createElement("div", {
    style: {
      ...card,
      border: `1px solid ${C.amberDim}`,
      marginBottom: 14
    }
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      marginBottom: 10,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    style: {
      font: `700 11px ${mono}`,
      color: C.amber,
      letterSpacing: 1
    }
  }, "\u25C6 \xD6NER\u0130LEN BA\u015ELANGI\xC7 \xB7 ", r.malzeme, " \xB7 ", r.et), React.createElement(AIRozeti, {
    yanit: r
  })), React.createElement(KaynakEtiketleri, {
    kaynaklar: r.kaynaklar
  }), React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(112px, 1fr))",
      gap: 8,
      marginTop: 10
    }
  }, Object.entries(meta.alanlar).map(([k, f]) => {
    const v = r.degerler[k];
    if (v == null) return null;
    const disari = v < f.aralik[0] || v > f.aralik[1];
    return React.createElement("div", {
      key: k,
      style: {
        background: C.bg,
        border: `1px dashed ${disari ? C.red : f.yazilabilir ? C.amberDim : C.border}`,
        borderRadius: 6,
        padding: "8px 10px"
      }
    }, React.createElement("div", {
      style: {
        ...lbl,
        fontSize: 9
      }
    }, f.etiket), React.createElement("div", {
      style: {
        font: `600 18px ${mono}`,
        color: disari ? C.red : f.yazilabilir ? C.amber : C.textMid,
        marginTop: 2
      }
    }, v, React.createElement("span", {
      style: {
        font: `500 10px ${mono}`,
        color: C.textMid
      }
    }, " ", f.birim)), yazmaModu && (f.yazilabilir ? React.createElement("button", {
      onClick: () => yazmaIste(k, v, `Reçete önerisi · ${r.malzeme}`),
      style: {
        marginTop: 6,
        width: "100%",
        background: C.green,
        color: "#0b0f12",
        border: "none",
        borderRadius: 5,
        padding: "4px 0",
        font: `700 11px ${sans}`,
        cursor: "pointer"
      }
    }, "Uygula \u2192") : React.createElement("div", {
      style: {
        marginTop: 6,
        font: `600 10px ${sans}`,
        color: C.textLo,
        textAlign: "center"
      }
    }, "\uD83D\uDD12 Faz 3 \xB7 kilitli")));
  })), r.not && React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid,
      marginTop: 10,
      lineHeight: 1.5
    }
  }, "\u26A0 ", r.not), (r.uyarilar || []).map((u, i) => React.createElement("div", {
    key: i,
    style: {
      font: `500 12px ${sans}`,
      color: C.red,
      marginTop: 4
    }
  }, "\u2715 ", u)), r.yedek && r.hata && React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textLo,
      marginTop: 6
    }
  }, "Bulut AI'ya ula\u015F\u0131lamad\u0131 (", r.hata, "); \xF6neri \xE7evrimd\u0131\u015F\u0131 uzmandan geldi."), React.createElement("div", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo,
      marginTop: 8
    }
  }, yazmaModu ? "⚑ Turuncu parametreler onaylı yazılabilir · gri/kilitli olanlar elle & Faz 3." : "⚑ Öneridir — bu değerleri panele elle giriniz."), React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginTop: 12,
      borderTop: `1px solid ${C.border}`,
      paddingTop: 12,
      flexWrap: "wrap",
      alignItems: "center"
    }
  }, React.createElement("span", {
    style: {
      font: `500 12px ${sans}`,
      color: C.textMid
    }
  }, "Denedin, sonu\xE7?"), React.createElement("button", {
    onClick: () => sonuc("iyi"),
    style: {
      background: C.greenDim,
      color: C.green,
      border: `1px solid ${C.green}`,
      borderRadius: 6,
      padding: "6px 14px",
      font: `600 12px ${sans}`,
      cursor: "pointer"
    }
  }, "\u2713 \u0130yi par\xE7a"), React.createElement("button", {
    onClick: () => sonuc("fire"),
    style: {
      background: C.redDim,
      color: C.red,
      border: `1px solid ${C.red}`,
      borderRadius: 6,
      padding: "6px 14px",
      font: `600 12px ${sans}`,
      cursor: "pointer"
    }
  }, "\u2715 Fire"))), React.createElement("div", {
    style: card
  }, React.createElement("div", {
    style: {
      ...lbl,
      marginBottom: 8
    }
  }, "Kay\u0131tl\u0131 Sonu\xE7lar \xB7 \xD6\u011Frenme Verisi"), React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      marginBottom: sonuclar.length ? 10 : 0
    }
  }, React.createElement("span", {
    style: {
      font: `600 13px ${mono}`,
      color: C.green
    }
  }, "\u2713 ", iyi, " iyi"), React.createElement("span", {
    style: {
      font: `600 13px ${mono}`,
      color: C.red
    }
  }, "\u2715 ", fire, " fire")), sonuclar.length === 0 ? React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textLo
    }
  }, "Hen\xFCz kay\u0131t yok. Her sonu\xE7 kal\u0131c\u0131 olarak saklan\u0131r.") : sonuclar.slice(0, 6).map(s => React.createElement("div", {
    key: s.id,
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid,
      padding: "3px 0"
    }
  }, React.createElement("span", {
    style: {
      color: s.sonuc === "iyi" ? C.green : C.red
    }
  }, s.sonuc === "iyi" ? "✓" : "✕"), " ", s.malzeme, " \xB7 ", s.et, " \xB7 ", s.zaman.replace("T", " ")))));
}
function Alarmlar({
  meta,
  durum,
  dene,
  bildir
}) {
  const [yorum, setYorum] = useState({});
  const istendi = useRef({});
  const alarmlar = durum.alarmlar || [];
  const aktif = alarmlar.filter(a => a.active);
  const yorumAl = useCallback(async a => {
    istendi.current[a.id] = true;
    setYorum(y => ({
      ...y,
      [a.id]: {
        yukleniyor: true
      }
    }));
    try {
      const r = await api("POST", "/api/alarm/yorum", {
        id: a.id
      });
      setYorum(y => ({
        ...y,
        [a.id]: r
      }));
    } catch (e) {
      setYorum(y => ({
        ...y,
        [a.id]: {
          hata: e.message
        }
      }));
    }
  }, []);
  useEffect(() => {
    aktif.forEach(a => {
      if (!istendi.current[a.id]) yorumAl(a);
    });
  }, [aktif.map(a => a.id).join(","), yorumAl]);
  async function gordum(a) {
    if (await dene(() => api("POST", "/api/alarm/gordum", {
      id: a.id
    }))) bildir(`${a.code} görüldü olarak işaretlendi.`);
  }
  async function senaryo(tur) {
    const r = await dene(() => api("POST", "/api/alarm/senaryo", {
      tur
    }));
    if (r) bildir(`Arıza senaryosu başladı: ${r.ad}. Alarm, ölçülen değerlerden kendiliğinden doğacak.`);
  }
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, null, "Alarmlar \xB7 ", aktif.length, " aktif"), React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      marginBottom: 10
    }
  }, React.createElement("span", {
    style: {
      width: 7,
      height: 7,
      borderRadius: 7,
      background: C.green,
      boxShadow: `0 0 6px ${C.green}`
    }
  }), React.createElement("span", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textLo,
      lineHeight: 1.5
    }
  }, "Alarmlar makinenin \xF6l\xE7\xFClen de\u011Ferlerinden ", React.createElement("b", {
    style: {
      color: C.textMid
    }
  }, "otomatik"), " do\u011Far ve ko\u015Ful kalk\u0131nca kendili\u011Finden kapan\u0131r. USTA her aktif alarm\u0131n yorumunu kendisi getirir.")), !meta.salt_okunur && meta.senaryolar && React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: 6,
      marginBottom: 14,
      alignItems: "center"
    }
  }, React.createElement("span", {
    style: {
      font: `500 11px ${sans}`,
      color: C.textLo
    }
  }, "\u26A1 Sim\xFClasyonda ar\u0131za ba\u015Flat:"), Object.entries(meta.senaryolar).map(([k, ad]) => React.createElement("button", {
    key: k,
    onClick: () => senaryo(k),
    style: {
      ...btnGhost,
      padding: "4px 10px",
      fontSize: 11
    }
  }, ad))), alarmlar.length === 0 && React.createElement("div", {
    style: {
      ...card,
      textAlign: "center",
      color: C.textLo,
      font: `400 13px ${sans}`
    }
  }, "Alarm yok \u2014 makine normal \xE7al\u0131\u015F\u0131yor."), alarmlar.map(a => {
    const col = a.sev === "crit" ? C.red : C.amber;
    const y = yorum[a.id];
    return React.createElement("div", {
      key: a.id,
      style: {
        ...card,
        borderLeft: `3px solid ${a.active ? col : C.textLo}`,
        marginBottom: 10,
        opacity: a.active ? 1 : 0.6
      }
    }, React.createElement("div", {
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 8
      }
    }, React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: 8,
        flexWrap: "wrap"
      }
    }, React.createElement("span", {
      style: {
        font: `600 11px ${mono}`,
        color: a.active ? col : C.textLo
      }
    }, a.code), React.createElement("span", {
      style: {
        font: `600 13px ${sans}`,
        color: C.textHi
      }
    }, a.title), a.ack && React.createElement("span", {
      style: {
        font: `600 9px ${sans}`,
        color: C.green
      }
    }, "\u2713 g\xF6r\xFCld\xFC \xB7 ", a.ack_by)), React.createElement("span", {
      style: {
        font: `500 11px ${mono}`,
        color: C.textLo,
        whiteSpace: "nowrap"
      }
    }, a.active ? a.start : `çözüldü ${a.end || ""} ✓`)), React.createElement("div", {
      style: {
        font: `400 12px ${sans}`,
        color: C.textMid,
        marginTop: 5,
        lineHeight: 1.5
      }
    }, a.detail), a.active && React.createElement("div", {
      style: {
        marginTop: 10,
        background: C.bg,
        border: `1px solid ${y && y.hata ? C.red : C.amberDim}`,
        borderRadius: 7,
        padding: "10px 12px"
      }
    }, React.createElement("div", {
      style: {
        display: "flex",
        gap: 8,
        alignItems: "center",
        flexWrap: "wrap",
        marginBottom: 5
      }
    }, React.createElement("span", {
      style: {
        font: `700 10px ${mono}`,
        color: y && y.hata ? C.red : C.amber,
        letterSpacing: 1
      }
    }, y && y.hata ? "✕ YORUM ALINAMADI" : "◆ USTA · MUHTEMEL SEBEP VE SIRALI KONTROL"), y && y.metin && React.createElement(AIRozeti, {
      yanit: {
        ...y,
        tesis: false
      }
    })), !y || y.yukleniyor ? React.createElement("div", {
      style: {
        font: `400 12px ${sans}`,
        color: C.textMid
      }
    }, "otomatik de\u011Ferlendiriliyor\u2026") : y.hata ? React.createElement("div", null, React.createElement("div", {
      style: {
        font: `400 12px ${sans}`,
        color: C.textMid
      }
    }, y.hata), React.createElement("button", {
      onClick: () => yorumAl(a),
      style: {
        ...btnGhost,
        marginTop: 8,
        padding: "5px 12px",
        fontSize: 11
      }
    }, "\u21BB Tekrar dene")) : React.createElement("div", {
      style: {
        font: `400 12px ${sans}`,
        color: C.textHi,
        lineHeight: 1.55,
        whiteSpace: "pre-wrap"
      }
    }, y.metin)), a.active && !a.ack && React.createElement("button", {
      onClick: () => gordum(a),
      style: {
        ...btnGhost,
        color: C.textHi,
        marginTop: 10
      }
    }, "\u2713 G\xF6rd\xFCm"));
  }));
}
function Sohbet({
  meta,
  durum,
  yazmaModu
}) {
  const [mesajlar, setMesajlar] = useState([{
    role: "assistant",
    content: `Merhaba usta. Makinenin canlı değerlerini görüyorum. Ayar, hata ya da yeni ürün için sor. (Kaynak: ${meta.ai.etiket})`,
    ilk: true
  }]);
  const [yazi, setYazi] = useState("");
  const [mesgul, setMesgul] = useState(false);
  const kaydir = useRef(null);
  useEffect(() => {
    if (kaydir.current) kaydir.current.scrollTop = kaydir.current.scrollHeight;
  }, [mesajlar, mesgul]);
  async function gonder(metin) {
    const q = (metin ?? yazi).trim();
    if (!q || mesgul) return;
    setYazi("");
    const sonraki = [...mesajlar, {
      role: "user",
      content: q
    }];
    setMesajlar(sonraki);
    setMesgul(true);
    try {
      const r = await api("POST", "/api/sohbet", {
        gecmis: sonraki.filter(m => !m.ilk && !m.hata).map(({
          role,
          content
        }) => ({
          role,
          content
        }))
      });
      setMesajlar(m => [...m, {
        role: "assistant",
        content: r.metin,
        yanit: r
      }]);
    } catch (e) {
      setMesajlar(m => [...m, {
        role: "assistant",
        content: e.message,
        hata: true
      }]);
    } finally {
      setMesgul(false);
    }
  }
  return React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      height: "100%"
    }
  }, React.createElement("div", {
    ref: kaydir,
    style: {
      flex: 1,
      overflowY: "auto",
      padding: 16,
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, mesajlar.map((m, i) => m.role === "user" ? React.createElement("div", {
    key: i,
    style: {
      alignSelf: "flex-end",
      maxWidth: "82%"
    }
  }, React.createElement("div", {
    style: {
      background: C.cyanDim,
      color: C.textHi,
      padding: "9px 13px",
      borderRadius: "10px 10px 2px 10px",
      font: `500 13px ${sans}`,
      lineHeight: 1.45,
      whiteSpace: "pre-wrap"
    }
  }, m.content)) : React.createElement("div", {
    key: i,
    style: {
      alignSelf: "flex-start",
      maxWidth: "90%"
    }
  }, React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 7,
      marginBottom: 4,
      flexWrap: "wrap"
    }
  }, React.createElement("span", {
    style: {
      font: `700 10px ${mono}`,
      color: C.amber,
      letterSpacing: 1
    }
  }, "\u25C6 USTA"), m.yanit && React.createElement(AIRozeti, {
    yanit: m.yanit
  })), React.createElement("div", {
    style: {
      background: C.panel,
      border: `1px solid ${m.hata ? C.red : C.border}`,
      color: C.textHi,
      padding: "11px 14px",
      borderRadius: "2px 10px 10px 10px",
      font: `400 13px ${sans}`,
      lineHeight: 1.55,
      whiteSpace: "pre-wrap"
    }
  }, m.content), m.yanit && React.createElement(KaynakEtiketleri, {
    kaynaklar: m.yanit.kaynaklar
  }), m.yanit && m.yanit.yedek && React.createElement("div", {
    style: {
      font: `400 10px ${sans}`,
      color: C.textLo,
      marginTop: 4
    }
  }, "Bulut AI'ya ula\u015F\u0131lamad\u0131 (", m.yanit.hata, "); cevap \xE7evrimd\u0131\u015F\u0131 uzmandan."), m.yanit && React.createElement("div", {
    style: {
      font: `500 10px ${mono}`,
      color: C.textLo,
      marginTop: 5
    }
  }, yazmaModu ? "⚑ Öneri · yazmak için İŞLER ya da REÇETE'den doğrula ve onayla" : "⚑ Öneridir — değerleri panele siz girersiniz."))), mesgul && React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      alignItems: "center"
    }
  }, React.createElement("span", {
    style: {
      font: `700 10px ${mono}`,
      color: C.amber
    }
  }, "\u25C6 USTA"), React.createElement("span", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid
    }
  }, "de\u011Ferlendiriyor\u2026"))), React.createElement("div", {
    style: {
      padding: "0 16px 10px",
      display: "flex",
      flexWrap: "wrap",
      gap: 6
    }
  }, QUICK.map(p => React.createElement("button", {
    key: p,
    onClick: () => gonder(p),
    disabled: mesgul,
    style: {
      font: `500 11px ${sans}`,
      color: C.textMid,
      background: C.raised,
      border: `1px solid ${C.border}`,
      borderRadius: 14,
      padding: "5px 11px",
      cursor: mesgul ? "default" : "pointer",
      opacity: mesgul ? 0.5 : 1
    }
  }, p)), durum.gozcu && durum.gozcu.bagli && durum.gozcu.toplam > 0 && React.createElement("button", {
    onClick: () => gonder("GÖZCÜ verisine göre fire neden arttı, ne yapmalıyım?"),
    disabled: mesgul,
    style: {
      font: `500 11px ${sans}`,
      color: C.cyan,
      background: C.raised,
      border: `1px solid ${C.cyanDim}`,
      borderRadius: 14,
      padding: "5px 11px",
      cursor: "pointer"
    }
  }, "\u25C6 G\xD6ZC\xDC verisine g\xF6re fire neden artt\u0131?")), React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      gonder();
    },
    style: {
      display: "flex",
      gap: 8,
      padding: "0 16px 16px"
    }
  }, React.createElement("input", {
    value: yazi,
    onChange: e => setYazi(e.target.value),
    placeholder: "S\u0131cakl\u0131k, ayar ya da bir hata yaz\u2026",
    style: {
      ...input,
      flex: 1,
      background: C.panel,
      padding: "11px 13px"
    }
  }), React.createElement("button", {
    type: "submit",
    disabled: mesgul || !yazi.trim(),
    style: btn(mesgul || !yazi.trim() ? C.raised : C.amber, mesgul || !yazi.trim() ? C.textLo : "#1a1204", {
      padding: "0 18px",
      fontSize: 13
    })
  }, "Sor")));
}
function Bilgi({
  durum,
  dene,
  bildir
}) {
  const ot = durum.oturum;
  const [kayitlar, setKayitlar] = useState([]);
  const [asama, setAsama] = useState("bos");
  const [sonuc, setSonuc] = useState(null);
  const [secili, setSecili] = useState({});
  const [surukle, setSurukle] = useState(false);
  const dosya = useRef(null);
  const yukle = useCallback(() => dene(async () => setKayitlar((await api("GET", "/api/bilgi")).kayitlar)), [dene]);
  useEffect(() => {
    yukle();
  }, [yukle]);
  async function isle(f) {
    if (!f) return;
    if (f.size > 15 * 1024 * 1024) {
      bildir("Dosya 15 MB'tan büyük.", "hata");
      return;
    }
    setAsama("okunuyor");
    setSonuc({
      dosya: f.name,
      adaylar: [],
      uyarilar: []
    });
    try {
      const veri = await f.arrayBuffer();
      const r = await api("POST", "/api/bilgi/ayristir", veri, {
        "X-Dosya-Adi": encodeURIComponent(f.name),
        "Content-Type": "application/octet-stream"
      });
      setSonuc(r);
      const s = {};
      r.adaylar.forEach(a => {
        s[a.id] = !a.mevcut;
      });
      setSecili(s);
      setAsama("inceleme");
    } catch (e) {
      bildir(e.message, "hata");
      setAsama("bos");
    }
  }
  async function onayla() {
    const r = await dene(() => api("POST", "/api/bilgi/ekle", {
      kayitlar: sonuc.adaylar.filter(a => secili[a.id] && !a.mevcut)
    }));
    if (r) {
      bildir(`${r.eklenen} kayıt bilgi tabanına eklendi — USTA artık bunlara başvuruyor.`);
      setAsama("bos");
      yukle();
    }
  }
  async function sil(k) {
    if (!window.confirm(`"${k.baslik}" silinsin mi?`)) return;
    if (await dene(() => api("DELETE", `/api/bilgi/${k.id}`))) {
      bildir("Kayıt silindi.");
      yukle();
    }
  }
  const gruplar = [["recete", "Kanıtlı Reçeteler", "◆", C.amber], ["datasheet", "Malzeme Datasheet'leri", "▤", C.cyan], ["not", "Makine Notları ve Belgeler", "⚙", C.cyan]];
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, null, "Tesis Bilgi Taban\u0131 \xB7 ", kayitlar.length, " kay\u0131t"), React.createElement(Aciklama, null, "USTA'n\u0131n \xF6nerileri bu kay\u0131tlara dayan\u0131r \u2014 cevaplar \"genel bilgi\" de\u011Fil, ", React.createElement("b", {
    style: {
      color: C.cyan
    }
  }, "bu tesise \xF6zeldir"), ". Belgeler ger\xE7ekten okunur: TXT, MD, CSV, Word (.docx), Excel (.xlsx); PDF i\xE7in ", React.createElement("code", null, "pypdf"), " kurulu olmal\u0131."), ot.yetki.belge_yukle ? React.createElement(React.Fragment, null, React.createElement("input", {
    ref: dosya,
    type: "file",
    accept: ".txt,.md,.csv,.docx,.xlsx,.pdf",
    onChange: e => {
      isle(e.target.files[0]);
      e.target.value = "";
    },
    style: {
      display: "none"
    }
  }), asama === "bos" && React.createElement("div", {
    onClick: () => dosya.current && dosya.current.click(),
    onDragOver: e => {
      e.preventDefault();
      setSurukle(true);
    },
    onDragLeave: () => setSurukle(false),
    onDrop: e => {
      e.preventDefault();
      setSurukle(false);
      isle(e.dataTransfer.files[0]);
    },
    style: {
      border: `2px dashed ${surukle ? C.amber : C.border}`,
      background: surukle ? "#1c1608" : C.panel,
      borderRadius: 10,
      padding: "20px 16px",
      textAlign: "center",
      cursor: "pointer",
      marginBottom: 16
    }
  }, React.createElement("div", {
    style: {
      font: `600 22px ${mono}`,
      color: surukle ? C.amber : C.textLo
    }
  }, "\u21EA"), React.createElement("div", {
    style: {
      font: `600 13px ${sans}`,
      color: C.textHi,
      marginTop: 6
    }
  }, "Belge y\xFCkle \u2014 Word, Excel, CSV, metin, PDF"), React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textLo,
      marginTop: 4
    }
  }, "Datasheet, re\xE7ete listesi, kalite kayd\u0131\u2026 s\xFCr\xFCkle-b\u0131rak ya da t\u0131kla.")), asama === "okunuyor" && React.createElement("div", {
    style: {
      ...card,
      border: `1px solid ${C.amberDim}`,
      textAlign: "center",
      marginBottom: 16
    }
  }, React.createElement("div", {
    style: {
      font: `700 11px ${mono}`,
      color: C.amber,
      letterSpacing: 1
    }
  }, "\u25C6 OKUNUYOR"), React.createElement("div", {
    style: {
      font: `500 13px ${sans}`,
      color: C.textHi,
      marginTop: 6
    }
  }, sonuc && sonuc.dosya)), asama === "inceleme" && sonuc && React.createElement("div", {
    style: {
      ...card,
      border: `1px solid ${C.amber}`,
      marginBottom: 16
    }
  }, React.createElement("div", {
    style: {
      font: `700 11px ${mono}`,
      color: C.amber,
      letterSpacing: 1,
      marginBottom: 3
    }
  }, "\u25C6 BULUNAN KAYITLAR \xB7 ", sonuc.dosya, " \xB7 ", sonuc.adaylar.length), sonuc.uyarilar.map((u, i) => React.createElement("div", {
    key: i,
    style: {
      font: `500 12px ${sans}`,
      color: C.red,
      margin: "6px 0"
    }
  }, "\u2715 ", u)), sonuc.adaylar.length > 0 && React.createElement("div", {
    style: {
      font: `400 12px ${sans}`,
      color: C.textMid,
      marginBottom: 10
    }
  }, "Eklemek istemediklerinin i\u015Faretini kald\u0131r, sonra onayla."), React.createElement("div", {
    style: {
      maxHeight: 320,
      overflowY: "auto"
    }
  }, sonuc.adaylar.map(c => {
    const on = secili[c.id] && !c.mevcut;
    return React.createElement("div", {
      key: c.id,
      onClick: () => !c.mevcut && setSecili({
        ...secili,
        [c.id]: !secili[c.id]
      }),
      style: {
        display: "flex",
        gap: 10,
        background: C.bg,
        border: `1px solid ${on ? C.amberDim : C.border}`,
        borderRadius: 7,
        padding: "10px 12px",
        marginBottom: 8,
        cursor: c.mevcut ? "default" : "pointer",
        opacity: c.mevcut ? 0.5 : 1
      }
    }, React.createElement("div", {
      style: {
        width: 18,
        height: 18,
        borderRadius: 4,
        flexShrink: 0,
        border: `1px solid ${on ? C.amber : C.border}`,
        background: on ? C.amber : "transparent",
        display: "grid",
        placeItems: "center",
        font: `700 12px ${mono}`,
        color: "#0b0f12"
      }
    }, on ? "✓" : ""), React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, React.createElement("div", {
      style: {
        font: `600 13px ${sans}`,
        color: C.textHi
      }
    }, c.baslik, " ", c.mevcut && React.createElement("span", {
      style: {
        font: `500 10px ${sans}`,
        color: C.textLo
      }
    }, "\xB7 zaten mevcut")), React.createElement("div", {
      style: {
        font: `400 11px ${sans}`,
        color: C.textMid,
        marginTop: 3,
        lineHeight: 1.45,
        whiteSpace: "pre-wrap"
      }
    }, c.metin.length > 300 ? c.metin.slice(0, 300) + "…" : c.metin), React.createElement("span", {
      style: {
        font: `600 9px ${sans}`,
        letterSpacing: 0.5,
        color: c.tur === "recete" ? C.amber : C.cyan,
        textTransform: "uppercase"
      }
    }, c.tur === "recete" ? "◆ reçete" : c.tur === "not" ? "⚙ not" : "▤ datasheet", c.malzeme ? ` · ${c.malzeme}` : "")));
  })), React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      marginTop: 4
    }
  }, sonuc.adaylar.length > 0 && React.createElement("button", {
    onClick: onayla,
    style: btn(C.green, "#0b0f12")
  }, "\u2713 Onayla ve ekle"), React.createElement("button", {
    onClick: () => setAsama("bos"),
    style: btnGhost
  }, "\u0130ptal")))) : React.createElement("div", {
    style: {
      background: C.raised,
      border: `1px dashed ${C.border}`,
      borderRadius: 8,
      padding: "12px 14px",
      font: `400 12px ${sans}`,
      color: C.textLo,
      textAlign: "center",
      marginBottom: 16
    }
  }, "Belgeler g\xF6r\xFCnt\xFCleniyor. Belge eklemek i\xE7in m\xFChendis giri\u015Fi gerekir."), gruplar.map(([t, ad, ikon, renk]) => {
    const docs = kayitlar.filter(d => d.tur === t);
    if (!docs.length) return null;
    return React.createElement("div", {
      key: t,
      style: {
        marginBottom: 14
      }
    }, React.createElement("div", {
      style: {
        font: `600 10px ${sans}`,
        letterSpacing: 1,
        color: renk,
        textTransform: "uppercase",
        marginBottom: 8
      }
    }, ikon, " ", ad, " \xB7 ", docs.length), docs.map(d => React.createElement("div", {
      key: d.id,
      style: {
        ...card,
        borderLeft: `3px solid ${t === "recete" ? C.amber : C.cyanDim}`,
        padding: "10px 14px",
        marginBottom: 8
      }
    }, React.createElement("div", {
      style: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        gap: 8
      }
    }, React.createElement("span", {
      style: {
        font: `600 13px ${sans}`,
        color: C.textHi
      }
    }, d.baslik), React.createElement("span", {
      style: {
        display: "flex",
        gap: 8,
        alignItems: "center"
      }
    }, React.createElement("span", {
      style: {
        font: `500 10px ${mono}`,
        color: C.textLo
      }
    }, d.id), ot.yetki.belge_yukle && React.createElement("button", {
      onClick: () => sil(d),
      title: "Sil",
      style: {
        background: "transparent",
        border: "none",
        color: C.textLo,
        cursor: "pointer",
        font: `600 12px ${mono}`
      }
    }, "\u2715"))), React.createElement("div", {
      style: {
        font: `400 12px ${sans}`,
        color: C.textMid,
        marginTop: 5,
        lineHeight: 1.5,
        whiteSpace: "pre-wrap"
      }
    }, d.metin), d.kaynak && React.createElement("div", {
      style: {
        font: `500 10px ${mono}`,
        color: C.textLo,
        marginTop: 4
      }
    }, "kaynak: ", d.kaynak))));
  }));
}
function Kayit({
  dene
}) {
  const [k, setK] = useState(null);
  useEffect(() => {
    dene(async () => setK((await api("GET", "/api/kayit")).kayitlar));
  }, [dene]);
  return React.createElement("div", {
    style: {
      padding: 16
    }
  }, React.createElement(Baslik, null, "AI Destekli \u0130\u015Flem Kay\u0131t Defteri"), React.createElement(Aciklama, null, "Makineye yaz\u0131lan her de\u011Fer, kayna\u011F\u0131 ve onaylayanla birlikte burada tutulur. Kay\u0131tlar veritaban\u0131 seviyesinde ", React.createElement("b", {
    style: {
      color: C.textMid
    }
  }, "de\u011Fi\u015Ftirilemez ve silinemez"), " (izlenebilirlik ve denetim)."), k === null ? React.createElement("div", {
    style: {
      color: C.textLo,
      font: `400 12px ${sans}`
    }
  }, "y\xFCkleniyor\u2026") : k.length === 0 ? React.createElement("div", {
    style: {
      ...card,
      border: `1px dashed ${C.border}`,
      padding: "24px 16px",
      textAlign: "center",
      font: `400 13px ${sans}`,
      color: C.textLo
    }
  }, "Hen\xFCz yazma i\u015Flemi yok. Onayl\u0131 Yazma modunda bir de\u011Fer onaylan\u0131nca burada belirir.") : k.map(e => React.createElement("div", {
    key: e.id,
    style: {
      ...card,
      borderLeft: `3px solid ${C.green}`,
      padding: "10px 14px",
      marginBottom: 8
    }
  }, React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      gap: 8
    }
  }, React.createElement("span", {
    style: {
      font: `600 13px ${sans}`,
      color: C.textHi
    }
  }, "#", e.id, " \xB7 ", e.etiket), React.createElement("span", {
    style: {
      font: `500 11px ${mono}`,
      color: C.textLo
    }
  }, e.zaman.replace("T", " "))), React.createElement("div", {
    style: {
      font: `500 13px ${mono}`,
      marginTop: 4
    }
  }, React.createElement("span", {
    style: {
      color: C.textMid
    }
  }, e.eski ?? "—", e.birim), React.createElement("span", {
    style: {
      color: C.textLo
    }
  }, " \u2192 "), React.createElement("span", {
    style: {
      color: C.green
    }
  }, e.yeni, e.birim)), React.createElement("div", {
    style: {
      font: `400 11px ${sans}`,
      color: C.textLo,
      marginTop: 3
    }
  }, e.kaynak, " \xB7 onaylayan: ", e.kullanici, " (", e.rol, ")", e.vardiya ? ` · ${e.vardiya}` : ""))));
}
ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App, null));
})();
