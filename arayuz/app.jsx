// USTA·AI panel arayüzü — yerel sunucunun (python -m usta) REST API'sini kullanır.
// Derleme: arayuz/ klasöründe `npm install && npm run build` → usta/web/app.js
// Kullanıcıların Node kurmasına gerek yoktur; derlenmiş app.js depoda gelir.
/* global React, ReactDOM */
const { useState, useEffect, useRef, useCallback } = React;

const C = {
  bg: "#0B0F12", panel: "#131A20", raised: "#1A232B", border: "#263039",
  cyan: "#35C4E0", cyanDim: "#1E6B7A", amber: "#F5A623", amberDim: "#5C4210",
  green: "#3FB950", greenDim: "#12341C", red: "#E5484D", redDim: "#3A1516",
  textHi: "#E8EEF2", textMid: "#9DAAB4", textLo: "#5C6B75",
};
const sans = "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif";
const mono = "'IBM Plex Mono', Consolas, ui-monospace, monospace";
const TUR_AD = { capak: "Çapak", kirik: "Kırık", cizik: "Çizik", leke: "Leke", eksik_dolum: "Eksik dolum", delik: "Delik", cokuntu: "Çöküntü" };
const KAYNAK_AD = { claude: "Claude", ollama: "Yerel model", uzman: "Çevrimdışı uzman" };
const QUICK = ["Ürün kenarlarında çapak (flash) var, sebebi ne?", "Kalıp tam dolmuyor (short shot), ne yapmalıyım?", "Çevrim süresini güvenle nasıl kısaltırım?"];

// ── API ────────────────────────────────────────────────────────────
async function api(method, path, body, extraHeaders) {
  const headers = { "X-Usta": "1", ...(extraHeaders || {}) };
  let data = body;
  if (body !== undefined && !(body instanceof ArrayBuffer)) { headers["Content-Type"] = "application/json"; data = JSON.stringify(body); }
  let r;
  try { r = await fetch(path, { method, headers, body: data }); }
  catch (e) { throw new Error("USTA sunucusuna ulaşılamıyor. Program penceresi açık mı?"); }
  let j = {};
  try { j = await r.json(); } catch (e) { /* boş gövde */ }
  if (!r.ok) throw new Error(j.hata || `Sunucu hatası (${r.status})`);
  return j;
}

// ── küçük bileşenler (bileşen içinde tanımlanmaz: her çizimde yeniden kurulmasın) ──
const lbl = { font: `500 10px ${sans}`, letterSpacing: 1, color: C.textLo, textTransform: "uppercase" };
const card = { background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: "12px 14px" };
const btn = (bg, fg, extra) => ({ background: bg, color: fg, border: "none", borderRadius: 7, padding: "8px 14px", font: `700 12px ${sans}`, cursor: "pointer", ...extra });
const btnGhost = { background: C.raised, color: C.textMid, border: `1px solid ${C.border}`, borderRadius: 7, padding: "7px 13px", font: `600 12px ${sans}`, cursor: "pointer" };
const input = { background: C.bg, border: `1px solid ${C.border}`, borderRadius: 7, padding: "9px 11px", color: C.textHi, font: `400 13px ${sans}`, outline: "none" };

function Baslik({ children, sag }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
      <div style={{ font: `600 10px ${sans}`, letterSpacing: 1.2, color: C.textMid, textTransform: "uppercase" }}>{children}</div>
      {sag}
    </div>
  );
}
function Aciklama({ children }) {
  return <div style={{ font: `400 12px ${sans}`, color: C.textLo, marginBottom: 14, lineHeight: 1.5 }}>{children}</div>;
}
function Rozet({ renk, zemin, children }) {
  return <span style={{ font: `700 9px ${sans}`, letterSpacing: 0.5, color: renk, background: zemin, border: `1px solid ${renk}`, borderRadius: 4, padding: "1px 6px", whiteSpace: "nowrap" }}>{children}</span>;
}
function Okuma({ etiket, deger, birim, farkli }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${farkli ? C.amberDim : C.border}`, borderRadius: 6, padding: "10px 12px" }}>
      <div style={lbl}>{etiket}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginTop: 4 }}>
        <span style={{ font: `600 22px ${mono}`, color: C.cyan, lineHeight: 1 }}>{deger ?? "—"}</span>
        <span style={{ font: `500 11px ${mono}`, color: C.textMid }}>{birim}</span>
      </div>
    </div>
  );
}
function Kivilcim({ veri, renk, birim }) {
  if (!veri.length) return <div style={{ font: `400 11px ${sans}`, color: C.textLo, height: 46 }}>veri toplanıyor…</div>;
  const W = 260, H = 46;
  const min = Math.min(...veri), max = Math.max(...veri);
  const pay = (max - min) || 1;
  const pts = veri.map((v, i) => `${(i / Math.max(veri.length - 1, 1)) * W},${H - ((v - min) / pay) * (H - 10) - 5}`).join(" ");
  return (
    <div>
      <div style={{ font: `600 11px ${mono}`, color: renk, textAlign: "right", marginTop: -18, height: 18 }}>{veri[veri.length - 1]}{birim}</div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ display: "block", width: "100%", height: H }} preserveAspectRatio="none">
        <polyline points={pts} fill="none" stroke={renk} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
      </svg>
    </div>
  );
}
function KaynakEtiketleri({ kaynaklar }) {
  if (!kaynaklar || !kaynaklar.length) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 6 }}>
      {kaynaklar.map((s) => (
        <span key={s.id} title={s.metin} style={{ font: `500 10px ${sans}`, color: C.cyan, background: C.panel, border: `1px solid ${C.cyanDim}`, borderRadius: 4, padding: "2px 7px" }}>
          {s.tur === "recete" ? "◆ " : s.tur === "not" ? "⚙ " : "▤ "}{s.baslik}
        </span>
      ))}
    </div>
  );
}
function AIRozeti({ yanit }) {
  if (!yanit) return null;
  const ad = KAYNAK_AD[yanit.kaynak] || yanit.kaynak;
  return (
    <span style={{ display: "inline-flex", gap: 5, flexWrap: "wrap" }}>
      {yanit.tesis
        ? <Rozet renk={C.green} zemin={C.greenDim}>● TESİS VERİSİ</Rozet>
        : <Rozet renk={C.textMid} zemin={C.raised}>○ GENEL BİLGİ</Rozet>}
      <Rozet renk={yanit.yedek ? C.amber : C.cyan} zemin={C.bg}>{yanit.yedek ? `${ad} · yedek` : ad}</Rozet>
    </span>
  );
}

// ── ana uygulama ─────────────────────────────────────────────────────
function App() {
  const [meta, setMeta] = useState(null);
  const [durum, setDurum] = useState(null);
  const [bagKopuk, setBagKopuk] = useState(false);
  const [tab, setTab] = useState("pano");
  const [bildirim, setBildirim] = useState(null); // {metin, tur: "ok"|"hata"}
  const [bekleyen, setBekleyen] = useState(null); // yazma doğrulama sonucu
  const [kullaniciMenu, setKullaniciMenu] = useState(false);
  const [pinIstek, setPinIstek] = useState(null);
  const [isler, setIsler] = useState([]);
  const bildirTimer = useRef(null);

  const bildir = useCallback((metin, tur = "ok") => {
    setBildirim({ metin, tur });
    clearTimeout(bildirTimer.current);
    bildirTimer.current = setTimeout(() => setBildirim(null), tur === "hata" ? 6000 : 3500);
  }, []);
  const dene = useCallback(async (f) => { try { return await f(); } catch (e) { bildir(e.message, "hata"); return null; } }, [bildir]);

  useEffect(() => { api("GET", "/api/meta").then(setMeta).catch((e) => bildir(e.message, "hata")); }, [bildir]);
  useEffect(() => {
    let iptal = false;
    const cek = async () => {
      try { const d = await api("GET", "/api/durum"); if (!iptal) { setDurum(d); setBagKopuk(false); } }
      catch (e) { if (!iptal) setBagKopuk(true); }
    };
    cek();
    const id = setInterval(cek, 1000);
    return () => { iptal = true; clearInterval(id); };
  }, []);
  const islerYukle = useCallback(() => dene(async () => { const r = await api("GET", "/api/isler"); setIsler(r.isler); }), [dene]);
  useEffect(() => { islerYukle(); }, [islerYukle]);

  if (!meta || !durum) {
    return (
      <div style={{ height: "100vh", display: "grid", placeItems: "center", color: C.textMid, font: `500 14px ${sans}` }}>
        {bagKopuk ? "USTA sunucusuna ulaşılamıyor — program penceresi açık mı?" : "USTA·AI yükleniyor…"}
      </div>
    );
  }

  const m = durum.makine, ot = durum.oturum, pv = m.pv || {}, sp = m.sp || {};
  const yazmaModu = ot.mod === "yazma" && ot.yetki.yaz;
  const aktifIs = isler.find((j) => j.id === durum.aktif_is);
  const aktifAlarmlar = (durum.alarmlar || []).filter((a) => a.active);
  const farkli = (k) => aktifIs && sp[k] !== undefined && aktifIs.ayarlar[k] !== undefined && Math.round(sp[k]) !== Math.round(aktifIs.ayarlar[k]);

  async function kullaniciSec(u, pin) {
    if (ot.pin_gerekli[u.rol] && pin === undefined) { setPinIstek({ u, pin: "" }); return; }
    const r = await dene(() => api("POST", "/api/oturum", { kullanici_id: u.id, pin: pin || "" }));
    if (r) { setKullaniciMenu(false); setPinIstek(null); bildir(`${r.kullanici.ad} (${r.rol_ad}) giriş yaptı.`); }
  }
  async function modSec(mod) { await dene(() => api("POST", "/api/mod", { mod })); }
  async function yazmaIste(alan, deger, kaynak) {
    const r = await dene(() => api("POST", "/api/yazma/dogrula", { alan, deger, kaynak }));
    if (r) setBekleyen(r);
  }
  async function yazmaOnayla() {
    const r = await dene(() => api("POST", "/api/yazma/onayla", { belirtec: bekleyen.belirtec }));
    setBekleyen(null);
    if (r) bildir(r.mesaj);
  }

  const TabBtn = (id, cocuk, rozet) => (
    <button key={id} onClick={() => setTab(id)} style={{ font: `600 12px ${sans}`, letterSpacing: 0.3, padding: "11px 14px", background: "transparent", color: tab === id ? C.textHi : C.textLo, border: "none", flexShrink: 0, whiteSpace: "nowrap", borderBottom: tab === id ? `2px solid ${C.amber}` : "2px solid transparent", display: "flex", alignItems: "center", gap: 7, cursor: "pointer" }}>
      {cocuk}
      {rozet > 0 && <span style={{ font: `700 10px ${mono}`, background: C.red, color: "#fff", borderRadius: 9, padding: "1px 6px" }}>{rozet}</span>}
    </button>
  );

  const ortak = { meta, durum, dene, bildir, yazmaModu, yazmaIste, isler, islerYukle, setTab };

  return (
    <div className="usta-kok">
      {/* üst bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, padding: "10px 16px", borderBottom: `1px solid ${C.border}`, background: C.raised, position: "relative", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <div style={{ width: 30, height: 30, borderRadius: 6, background: C.amberDim, display: "grid", placeItems: "center", border: `1px solid ${C.amber}` }}><span style={{ font: `700 15px ${mono}`, color: C.amber }}>◆</span></div>
          <div>
            <div style={{ font: `700 14px ${sans}`, letterSpacing: 1 }}>USTA<span style={{ color: C.amber }}>·</span>AI <span style={{ font: `500 10px ${sans}`, color: C.textMid, letterSpacing: 0 }}>Operatör Danışmanı · v{meta.surum}</span></div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <span style={{ width: 6, height: 6, borderRadius: 6, background: bagKopuk || m.hata ? C.red : C.green, boxShadow: `0 0 6px ${bagKopuk || m.hata ? C.red : C.green}` }} />
              <span style={{ font: `500 10px ${mono}`, color: C.textLo }}>{m.makine} · {bagKopuk ? "SUNUCU BAĞLANTISI KOPTU" : `${m.baglanti} · ${m.durum}`}</span>
              <span style={{ font: `500 10px ${mono}`, color: C.textLo }}>· AI: {meta.ai.etiket}</span>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {ot.yetki.yaz && !meta.salt_okunur && (
            <div style={{ display: "flex", background: C.panel, borderRadius: 7, padding: 3, border: `1px solid ${C.border}` }}>
              {[["danisman", "Danışman"], ["yazma", "Onaylı Yazma"]].map(([id, ad]) => (
                <button key={id} onClick={() => modSec(id)} style={{ font: `600 11px ${sans}`, padding: "6px 12px", borderRadius: 5, border: "none", cursor: "pointer", background: ot.mod === id ? (id === "yazma" ? C.green : C.amber) : "transparent", color: ot.mod === id ? "#0b0f12" : C.textMid }}>{ad}</button>
              ))}
            </div>
          )}
          <button onClick={() => setKullaniciMenu((v) => !v)} style={{ display: "flex", alignItems: "center", gap: 7, background: C.panel, border: `1px solid ${C.border}`, borderRadius: 7, padding: "6px 10px", cursor: "pointer" }}>
            <span style={{ width: 22, height: 22, borderRadius: 11, background: C.cyanDim, display: "grid", placeItems: "center", font: `700 11px ${sans}`, color: C.textHi }}>{ot.kullanici.ad.charAt(0)}</span>
            <div style={{ textAlign: "left" }}>
              <div style={{ font: `600 11px ${sans}`, color: C.textHi, lineHeight: 1.1 }}>{ot.kullanici.ad}</div>
              <div style={{ font: `500 9px ${sans}`, color: C.textLo, lineHeight: 1.1 }}>{ot.rol_ad} · {ot.vardiya}</div>
            </div>
            <span style={{ font: `600 10px ${mono}`, color: C.textLo }}>▾</span>
          </button>
        </div>
        {kullaniciMenu && (
          <div style={{ position: "absolute", right: 16, top: 58, zIndex: 30, background: C.raised, border: `1px solid ${C.border}`, borderRadius: 8, padding: 6, minWidth: 220, boxShadow: "0 8px 24px rgba(0,0,0,.5)" }}>
            <div style={{ ...lbl, padding: "4px 8px" }}>Vardiya girişi · {ot.vardiya}</div>
            {meta.kullanicilar.map((u) => (
              <button key={u.id} onClick={() => kullaniciSec(u)} style={{ display: "flex", width: "100%", alignItems: "center", gap: 8, background: u.id === ot.kullanici.id ? C.panel : "transparent", border: "none", borderRadius: 6, padding: 8, cursor: "pointer", textAlign: "left" }}>
                <span style={{ width: 22, height: 22, borderRadius: 11, background: C.cyanDim, display: "grid", placeItems: "center", font: `700 11px ${sans}`, color: C.textHi }}>{u.ad.charAt(0)}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ font: `600 12px ${sans}`, color: C.textHi }}>{u.ad}</div>
                  <div style={{ font: `500 10px ${sans}`, color: C.textLo }}>{meta.roller[u.rol]}{ot.pin_gerekli[u.rol] ? " · PIN" : ""}</div>
                </div>
                {u.id === ot.kullanici.id && <span style={{ font: `700 11px ${mono}`, color: C.green }}>✓</span>}
              </button>
            ))}
            {pinIstek && (
              <form onSubmit={(e) => { e.preventDefault(); kullaniciSec(pinIstek.u, pinIstek.pin); }} style={{ display: "flex", gap: 6, padding: 8 }}>
                <input autoFocus type="password" inputMode="numeric" value={pinIstek.pin} onChange={(e) => setPinIstek({ ...pinIstek, pin: e.target.value })} placeholder={`${pinIstek.u.ad} PIN`} style={{ ...input, flex: 1, padding: "6px 9px" }} />
                <button type="submit" style={btn(C.amber, "#1a1204", { padding: "6px 12px" })}>Gir</button>
              </form>
            )}
          </div>
        )}
      </div>

      {/* sekmeler */}
      <div style={{ display: "flex", padding: "0 8px", borderBottom: `1px solid ${C.border}`, background: C.panel, overflowX: "auto" }}>
        {TabBtn("pano", "PANO")}
        {TabBtn("isler", "İŞLER")}
        {TabBtn("recete", "REÇETE")}
        {TabBtn("alarmlar", "ALARMLAR", aktifAlarmlar.length)}
        {TabBtn("ai", <><span style={{ width: 7, height: 7, borderRadius: 7, background: C.amber, boxShadow: `0 0 7px ${C.amber}` }} />AI ASİSTAN</>)}
        {TabBtn("bilgi", "BİLGİ TABANI")}
        {TabBtn("kayit", "KAYIT")}
      </div>

      {/* güvenlik şeridi */}
      {yazmaModu ? (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 16px", background: "#0f2417", borderBottom: `1px solid ${C.greenDim}`, flexWrap: "wrap" }}>
          <span style={{ font: `700 11px ${mono}`, color: C.green, letterSpacing: 1 }}>✓ ONAYLI YAZMA · FAZ 2</span>
          <span style={{ font: `500 11px ${sans}`, color: C.textMid }}>Yalnızca güvenli parametreler · doğrulama + insan onayı · her yazma <b style={{ color: C.green }}>kayıtlı</b></span>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 16px", background: "repeating-linear-gradient(45deg,#1c1608,#1c1608 10px,#171205 10px,#171205 20px)", borderBottom: `1px solid ${C.amberDim}`, flexWrap: "wrap" }}>
          <span style={{ font: `700 11px ${mono}`, color: C.amber, letterSpacing: 1 }}>⚑ DANIŞMAN MODU · FAZ 0</span>
          <span style={{ font: `500 11px ${sans}`, color: C.textMid }}>AI yalnızca öneri verir · makineye yazma <b style={{ color: C.red }}>KAPALI</b> · değerleri operatör girer</span>
        </div>
      )}

      <div className="usta-govde">
        {/* sol: makinenin gerçeği */}
        <div className="usta-sol">
          <div style={{ font: `600 10px ${sans}`, letterSpacing: 1.2, color: C.cyan, textTransform: "uppercase", marginBottom: 10 }}>● Canlı Makine Değerleri</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <Okuma etiket="Bölge 1" deger={pv.z1} birim="°C" farkli={farkli("z1")} />
            <Okuma etiket="Bölge 2" deger={pv.z2} birim="°C" farkli={farkli("z2")} />
            <Okuma etiket="Bölge 3" deger={pv.z3} birim="°C" farkli={farkli("z3")} />
            <Okuma etiket="Nozul" deger={pv.nozul} birim="°C" farkli={farkli("nozul")} />
            <Okuma etiket="Enj. Basınç" deger={pv.enjPress} birim="bar" />
            <Okuma etiket="Tutma Bas." deger={pv.tutmaPress} birim="bar" farkli={farkli("tutmaPress")} />
            <Okuma etiket="Çevrim" deger={pv.cevrim} birim="s" />
            <Okuma etiket="Yastık" deger={pv.yastik} birim="mm" />
          </div>
          <div style={{ ...card, marginTop: 12, padding: "10px 12px" }}>
            <div style={lbl}>Aktif İş</div>
            <div style={{ font: `500 13px ${sans}`, color: C.textHi, marginTop: 3 }}>{aktifIs ? aktifIs.urun : (m.is && m.is.urun) || "—"}</div>
            <div style={{ font: `500 11px ${mono}`, color: C.textLo, marginTop: 4 }}>{aktifIs ? `${aktifIs.kalip} · ${aktifIs.malzeme}` : ""}</div>
            <div style={{ font: `500 11px ${mono}`, color: C.textLo, marginTop: 2 }}>Baskı: {(m.baski || 0).toLocaleString("tr-TR")}</div>
          </div>
          <div style={{ font: `500 10px ${sans}`, color: C.textLo, marginTop: 10, lineHeight: 1.5 }}>Turuncu çerçeve: setpoint aktif işin kayıtlı değerinden farklı.</div>
        </div>

        {/* sağ: çalışma alanı */}
        <div className="usta-sag">
          {bildirim && (
            <div style={{ margin: "12px 16px 0", background: bildirim.tur === "hata" ? C.redDim : C.greenDim, border: `1px solid ${bildirim.tur === "hata" ? C.red : C.green}`, borderRadius: 7, padding: "9px 13px", font: `600 12px ${sans}`, color: bildirim.tur === "hata" ? "#ffb4b6" : C.green }}>
              {bildirim.tur === "hata" ? "✕ " : "✓ "}{bildirim.metin}
            </div>
          )}
          {bekleyen && <YazmaOnayi b={bekleyen} onayla={yazmaOnayla} iptal={() => setBekleyen(null)} />}
          <div className="usta-icerik">
            {tab === "pano" && <Pano {...ortak} />}
            {tab === "isler" && <Isler {...ortak} />}
            {tab === "recete" && <Recete {...ortak} />}
            {tab === "alarmlar" && <Alarmlar {...ortak} />}
            {tab === "ai" && <Sohbet {...ortak} />}
            {tab === "bilgi" && <Bilgi {...ortak} />}
            {tab === "kayit" && <Kayit {...ortak} />}
          </div>
        </div>
      </div>
    </div>
  );
}

function YazmaOnayi({ b, onayla, iptal }) {
  return (
    <div style={{ margin: "12px 16px 0", background: C.panel, border: `1px solid ${b.gecti ? C.amber : C.red}`, borderRadius: 8, padding: 14 }}>
      <div style={{ font: `700 11px ${mono}`, color: b.gecti ? C.amber : C.red, letterSpacing: 1, marginBottom: 8 }}>{b.gecti ? "◆ YAZMA ONAYI GEREKİYOR" : "✕ DOĞRULAMA REDDETTİ"}</div>
      <div style={{ font: `500 14px ${sans}`, color: C.textHi }}>
        {b.etiket}: <span style={{ font: `600 15px ${mono}`, color: C.cyan }}>{b.mevcut ?? "—"}</span>
        <span style={{ color: C.textLo }}> → </span>
        <span style={{ font: `600 15px ${mono}`, color: b.gecti ? C.amber : C.red }}>{Number.isFinite(b.hedef) ? b.hedef : "?"}{b.birim}</span>
      </div>
      <div style={{ font: `400 12px ${sans}`, color: C.textMid, marginTop: 6 }}>Makinenin güvenli aralığı: <b style={{ color: C.textHi }}>{b.min}–{b.max} {b.birim}</b>{b.gecti ? " · Onaylarsan makineye yazılır ve kayıt altına alınır (90 sn içinde)." : ""}</div>
      {!b.gecti && <ul style={{ margin: "8px 0 0 18px", color: "#ffb4b6", font: `400 12px ${sans}`, lineHeight: 1.6 }}>{b.nedenler.map((n, i) => <li key={i}>{n}</li>)}</ul>}
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        {b.gecti && <button onClick={onayla} style={btn(C.green, "#0b0f12")}>✓ Onayla ve yaz</button>}
        <button onClick={iptal} style={btnGhost}>{b.gecti ? "İptal" : "Kapat"}</button>
      </div>
    </div>
  );
}

// ── PANO ───────────────────────────────────────────────────────────
function Pano({ durum, setTab }) {
  const m = durum.makine, u = m.uretim, g = durum.gozcu;
  const trend = m.trend || [];
  const toplam = u ? u.saglam + u.fire : 0;
  const gozcuBagli = g && g.bagli;
  const turler = gozcuBagli && g.toplam ? g.turler : (u ? u.turler : {});
  const turToplam = Object.values(turler || {}).reduce((a, b) => a + b, 0);
  const kpi = [
    ["Üretim", toplam, C.cyan], ["Sağlam", u ? u.saglam : "—", C.green], ["Fire", u ? u.fire : "—", C.red],
    ["Fire %", toplam ? (u.fire / toplam * 100).toFixed(1) : "0.0", C.amber],
    ["Ort. Çevrim", trend.length ? (trend.reduce((a, b) => a + (b.cevrim || 0), 0) / trend.length).toFixed(1) + " s" : "—", C.cyan],
  ];
  return (
    <div style={{ padding: 16 }}>
      <Baslik sag={<span style={{ font: `500 10px ${mono}`, color: C.textLo }}>{m.baglanti} · {durum.zaman}</span>}>Canlı Üretim Panosu · {m.makine}</Baslik>
      <div className="usta-kpi">
        {kpi.map(([l, v, col]) => (
          <div key={l} style={{ ...card, padding: "10px 12px" }}>
            <div style={{ ...lbl, fontSize: 9 }}>{l}</div>
            <div style={{ font: `700 20px ${mono}`, color: col, marginTop: 3 }}>{v}</div>
          </div>
        ))}
      </div>
      {m.fazlar && m.fazlar.length > 0 && (
        <div style={{ ...card, marginTop: 12 }}>
          <div style={{ ...lbl, marginBottom: 8 }}>Çevrim Fazı {m.durum !== "ÇALIŞIYOR" && <b style={{ color: C.red }}>· {m.durum}</b>}</div>
          <div style={{ display: "flex", gap: 6 }}>
            {m.fazlar.map((nm, i) => (
              <div key={nm} style={{ flex: 1, textAlign: "center", padding: "7px 4px", borderRadius: 6, background: i === m.faz_i ? C.amber : C.raised, color: i === m.faz_i ? "#1a1204" : C.textLo, font: `700 10px ${sans}`, letterSpacing: 0.5, boxShadow: i === m.faz_i ? `0 0 10px ${C.amber}55` : "none", transition: "all .25s", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{nm}</div>
            ))}
          </div>
        </div>
      )}
      <div className="usta-ikili" style={{ marginTop: 12 }}>
        <div style={card}><div style={{ ...lbl, marginBottom: 6 }}>Çevrim Süresi (s)</div><Kivilcim veri={trend.map((t) => t.cevrim)} renk={C.cyan} birim=" s" /></div>
        <div style={card}><div style={{ ...lbl, marginBottom: 6 }}>Yastık (mm)</div><Kivilcim veri={trend.map((t) => t.yastik)} renk={C.green} birim=" mm" /></div>
      </div>
      <div className="usta-ikili" style={{ marginTop: 12 }}>
        <div style={card}>
          <div style={{ ...lbl, marginBottom: 8 }}>Fire Kırılımı · {gozcuBagli && g.toplam ? "GÖZCÜ·AI (gerçek muayene)" : "simülasyon kalite istasyonu"}</div>
          {turToplam === 0 ? <div style={{ font: `400 11px ${sans}`, color: C.textLo }}>henüz fire yok</div> :
            Object.entries(turler).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ font: `500 11px ${sans}`, color: C.textMid, width: 90 }}>{TUR_AD[k] || k}</span>
                <div style={{ flex: 1, height: 8, background: C.raised, borderRadius: 4, overflow: "hidden" }}><div style={{ width: `${(v / turToplam) * 100}%`, height: "100%", background: C.red }} /></div>
                <span style={{ font: `600 11px ${mono}`, color: C.textHi, width: 30, textAlign: "right" }}>{v}</span>
              </div>
            ))}
        </div>
        <div style={card}>
          <div style={{ ...lbl, marginBottom: 6 }}>Son Alarmlar</div>
          {(durum.alarmlar || []).length === 0 && <div style={{ font: `400 11px ${sans}`, color: C.textLo }}>kayıt yok</div>}
          {(durum.alarmlar || []).slice(0, 5).map((a) => (
            <div key={a.id} onClick={() => setTab("alarmlar")} style={{ display: "flex", justifyContent: "space-between", gap: 8, padding: "5px 0", borderBottom: `1px solid ${C.border}`, cursor: "pointer" }}>
              <span style={{ font: `500 11px ${sans}`, color: a.active ? (a.sev === "crit" ? C.red : C.amber) : C.textMid }}>{a.code} · {a.title}</span>
              <span style={{ font: `500 10px ${mono}`, color: C.textLo, whiteSpace: "nowrap" }}>{a.active ? a.start : "✓ " + (a.end || "")}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ ...card, marginTop: 12, border: `1px ${gozcuBagli ? "solid" : "dashed"} ${gozcuBagli ? C.cyanDim : C.border}` }}>
        <div style={{ ...lbl, marginBottom: 6 }}>◆ GÖZCÜ·AI Entegrasyonu · {gozcuBagli ? <b style={{ color: C.green }}>BAĞLI</b> : "bağlı değil"}</div>
        {gozcuBagli ? (
          <div style={{ font: `400 12px ${sans}`, color: C.textMid, lineHeight: 1.6 }}>
            Görüntü muayenesi: <b style={{ color: C.textHi }}>{g.toplam}</b> parça · sağlam <b style={{ color: C.green }}>{g.saglam}</b> · şüpheli <b style={{ color: C.amber }}>{g.supheli}</b> · fire <b style={{ color: C.red }}>{g.fire}</b> (%{g.fire_orani.toFixed(1)}){g.baskin_ad ? <> · en sık: <b style={{ color: C.textHi }}>{g.baskin_ad}</b></> : null}
            {g.son && g.son.length > 0 && <div style={{ font: `500 10px ${mono}`, color: C.textLo, marginTop: 4 }}>son: {g.son.slice(0, 4).map((s) => `${s.parca} ${s.karar}`).join(" · ")}</div>}
            <div style={{ marginTop: 4 }}>AI ASİSTAN bu veriyi görür: "fire neden arttı?" diye sorabilirsin.</div>
          </div>
        ) : (
          <div style={{ font: `400 11px ${sans}`, color: C.textMid, lineHeight: 1.55 }}>
            {g && g.hata ? <span style={{ color: C.amber }}>{g.hata} · </span> : null}
            GÖZCÜ·AI'nin çalışma klasörünü <code>veri/ayarlar.json</code> içinde <code>"gozcu": {"{"}"klasor": "..."{"}"}</code> olarak tanımlarsan, muayene sonuçları ve fire türleri buraya akar ve USTA önerilerine katılır.
          </div>
        )}
      </div>
    </div>
  );
}

// ── İŞLER ──────────────────────────────────────────────────────────
function Isler({ meta, durum, dene, bildir, yazmaModu, yazmaIste, isler, islerYukle }) {
  const ot = durum.oturum;
  const [acik, setAcik] = useState(null);
  const [taslak, setTaslak] = useState(null);
  const [yeni, setYeni] = useState(null);
  const [mesgul, setMesgul] = useState(false);
  const [uyarilar, setUyarilar] = useState([]);
  const alanlar = meta.alanlar;
  function ac(j) { if (acik === j.id) { setAcik(null); return; } setAcik(j.id); setTaslak({ ...j.ayarlar }); setUyarilar([]); }
  async function kaydet() {
    const r = await dene(() => api("PUT", `/api/isler/${acik}`, { ayarlar: taslak }));
    if (r) { setUyarilar(r.uyarilar); bildir("İş ayarları kaydedildi."); islerYukle(); }
  }
  async function ekle() {
    const r = await dene(() => api("POST", "/api/isler", yeni));
    if (r) { setYeni(null); await islerYukle(); setAcik(r.id); setTaslak({ ...r.ayarlar }); bildir(`Yeni iş eklendi: ${r.urun}.`); }
  }
  async function aktifYap(j) {
    const r = await dene(() => api("POST", `/api/isler/${j.id}/aktif`));
    if (r) bildir(r.yazildi ? `Aktif iş: ${j.urun} — ayarlar makineye yüklendi ve kayda geçti.` : `Aktif iş: ${j.urun}. Danışman modu: değerleri makine panelinden sen gir.`);
  }
  async function sil(j) {
    if (!window.confirm(`"${j.urun}" işi silinsin mi?`)) return;
    const r = await dene(() => api("DELETE", `/api/isler/${j.id}`));
    if (r) { setAcik(null); islerYukle(); bildir("İş silindi."); }
  }
  async function oner() {
    setMesgul(true);
    const r = await dene(() => api("POST", `/api/isler/${acik}/oner`));
    setMesgul(false);
    if (r) { setTaslak((p) => ({ ...p, ...r.degerler })); setUyarilar([...(r.uyarilar || []), ...(r.not ? [r.not] : [])]); bildir(`Öneri: ${KAYNAK_AD[r.kaynak] || r.kaynak}. Kaydetmeden önce kontrol et.`); }
  }
  return (
    <div style={{ padding: 16 }}>
      <Baslik sag={ot.yetki.is_duzenle && <button onClick={() => setYeni(yeni ? null : { urun: "", kalip: "", malzeme: meta.malzemeler[0] })} style={yeni ? btnGhost : btn(C.amber, "#1a1204", { padding: "6px 12px", fontSize: 11 })}>{yeni ? "Vazgeç" : "+ Yeni iş"}</button>}>İşler · Kalıp + Malzeme + Ürün · {isler.length}</Baslik>
      <Aciklama>Her iş bir kez eklenir ve bilgisayarda kalıcı olarak saklanır. Bir işe bas: değerlerini gör, elle değiştir ya da AI'ya önertir. "Aktif iş yap" dersen (Onaylı Yazma modunda) makine o işe göre ayarlanır.</Aciklama>
      {yeni && (
        <div style={{ ...card, border: `1px solid ${C.amberDim}`, marginBottom: 14 }}>
          <div style={{ font: `700 11px ${mono}`, color: C.amber, letterSpacing: 1, marginBottom: 10 }}>◆ YENİ İŞ EKLE</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <input value={yeni.urun} onChange={(e) => setYeni({ ...yeni, urun: e.target.value })} placeholder="Ürün adı (örn: Peynir Üçgen Kutu)" style={{ ...input, flex: "1 1 200px" }} />
            <input value={yeni.kalip} onChange={(e) => setYeni({ ...yeni, kalip: e.target.value })} placeholder="Kalıp kodu (örn: K-512)" style={{ ...input, flex: "0 1 150px" }} />
            <select value={yeni.malzeme} onChange={(e) => setYeni({ ...yeni, malzeme: e.target.value })} style={input}>{meta.malzemeler.map((x) => <option key={x}>{x}</option>)}</select>
            <button onClick={ekle} disabled={!yeni.urun.trim() || !yeni.kalip.trim()} style={btn(C.green, "#0b0f12", { opacity: !yeni.urun.trim() || !yeni.kalip.trim() ? 0.5 : 1 })}>Ekle</button>
          </div>
        </div>
      )}
      {isler.map((j) => {
        const aktif = j.id === durum.aktif_is, open = j.id === acik;
        return (
          <div key={j.id} style={{ ...card, borderLeft: `3px solid ${aktif ? C.green : C.cyanDim}`, borderColor: aktif ? C.green : C.border, marginBottom: 8 }}>
            <div onClick={() => ac(j)} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ font: `600 14px ${sans}`, color: C.textHi }}>{j.urun}</span>
                  {aktif && <Rozet renk={C.green} zemin={C.greenDim}>● AKTİF</Rozet>}
                </div>
                <div style={{ font: `500 11px ${mono}`, color: C.textLo, marginTop: 3 }}>Kalıp {j.kalip} · {j.malzeme}</div>
              </div>
              <span style={{ font: `600 13px ${mono}`, color: C.textLo }}>{open ? "▾" : "▸"}</span>
            </div>
            {open && taslak && (
              <div style={{ marginTop: 12, borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 }}>
                  <span style={lbl}>{ot.yetki.is_duzenle ? "Değerler — elle gir ya da AI'ya önert" : "Değerler (görüntüleme)"}</span>
                  {ot.yetki.is_duzenle && <button onClick={oner} disabled={mesgul} style={{ background: mesgul ? C.raised : C.amberDim, color: C.amber, border: `1px solid ${C.amber}`, borderRadius: 6, padding: "5px 11px", font: `600 11px ${sans}`, cursor: mesgul ? "default" : "pointer" }}>{mesgul ? "Öneriliyor…" : "◆ AI ile öner"}</button>}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: 8 }}>
                  {Object.entries(alanlar).map(([k, f]) => (
                    <div key={k} style={{ background: C.bg, border: `1px solid ${f.yazilabilir ? C.amberDim : C.border}`, borderRadius: 6, padding: "8px 10px" }}>
                      <div style={{ ...lbl, fontSize: 9 }}>{f.etiket} {f.birim}</div>
                      {ot.yetki.is_duzenle
                        ? <input type="number" value={taslak[k] ?? ""} onChange={(e) => setTaslak({ ...taslak, [k]: e.target.value === "" ? "" : Number(e.target.value) })} style={{ width: "100%", marginTop: 4, background: C.panel, border: `1px solid ${C.border}`, borderRadius: 5, padding: "5px 7px", color: f.yazilabilir ? C.amber : C.textHi, font: `600 15px ${mono}`, outline: "none" }} />
                        : <div style={{ marginTop: 4, font: `600 16px ${mono}`, color: f.yazilabilir ? C.amber : C.textHi }}>{taslak[k]}</div>}
                      {yazmaModu && (f.yazilabilir
                        ? <button onClick={() => yazmaIste(k, Number(taslak[k]), `İş değeri · ${j.urun}`)} style={{ marginTop: 5, width: "100%", background: C.green, color: "#0b0f12", border: "none", borderRadius: 5, padding: "4px 0", font: `700 10px ${sans}`, cursor: "pointer" }}>Makineye uygula →</button>
                        : <div style={{ marginTop: 5, font: `600 9px ${sans}`, color: C.textLo, textAlign: "center" }}>🔒 Faz 3</div>)}
                    </div>
                  ))}
                </div>
                {uyarilar.length > 0 && <ul style={{ margin: "10px 0 0 18px", color: C.amber, font: `400 12px ${sans}`, lineHeight: 1.6 }}>{uyarilar.map((u, i) => <li key={i}>{u}</li>)}</ul>}
                <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "center" }}>
                  {ot.yetki.is_duzenle && <button onClick={kaydet} style={{ ...btnGhost, color: C.textHi }}>Kaydet</button>}
                  {ot.yetki.is_sec
                    ? <button onClick={() => aktifYap(j)} disabled={aktif} style={btn(aktif ? C.raised : C.amber, aktif ? C.textLo : "#1a1204", { cursor: aktif ? "default" : "pointer" })}>{aktif ? "✓ Zaten aktif" : "Aktif iş yap →"}</button>
                    : <span style={{ font: `500 11px ${sans}`, color: C.textLo }}>Değişiklik ya da iş seçimi için usta/mühendis girişi gerekir.</span>}
                  {ot.yetki.is_duzenle && !aktif && <button onClick={() => sil(j)} style={{ ...btnGhost, color: C.red, marginLeft: "auto" }}>Sil</button>}
                </div>
                {ot.yetki.is_duzenle && !yazmaModu && <div style={{ font: `500 10px ${mono}`, color: C.textLo, marginTop: 8 }}>⚑ Makineye yazmak için üstten "Onaylı Yazma" moduna geç.</div>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── REÇETE ─────────────────────────────────────────────────────────
function Recete({ meta, dene, bildir, yazmaModu, yazmaIste }) {
  const [malzeme, setMalzeme] = useState(meta.malzemeler[0]);
  const [et, setEt] = useState(meta.etler[1]);
  const [r, setR] = useState(null);
  const [mesgul, setMesgul] = useState(false);
  const [sonuclar, setSonuclar] = useState([]);
  useEffect(() => { dene(async () => setSonuclar((await api("GET", "/api/sonuclar")).sonuclar)); }, [dene]);
  async function oner() {
    setMesgul(true); setR(null);
    const y = await dene(() => api("POST", "/api/recete", { malzeme, et }));
    setMesgul(false);
    if (y) setR({ ...y, malzeme, et });
  }
  async function sonuc(tur) {
    const y = await dene(() => api("POST", "/api/sonuclar", { malzeme: r.malzeme, et: r.et, sonuc: tur, recete: r.degerler }));
    if (y) { setSonuclar(y.sonuclar); setR(null); bildir("Sonuç kaydedildi — öğrenme verisine eklendi."); }
  }
  const iyi = sonuclar.filter((s) => s.sonuc === "iyi").length, fire = sonuclar.length - iyi;
  return (
    <div style={{ padding: 16 }}>
      <Baslik>Yeni Ürün · Başlangıç Ayarı</Baslik>
      <Aciklama>{yazmaModu ? "AI başlangıç değerlerini önersin; güvenli parametreleri tek tuşla doğrulayıp onaylayarak makineye yazabilirsin. Kritik parametreler kilitli (Faz 3)." : "AI başlangıç değerlerini önersin. Danışman modunda değerleri panele sen girersin."}</Aciklama>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14, alignItems: "flex-end" }}>
        <div><div style={{ ...lbl, marginBottom: 5 }}>Malzeme</div><select value={malzeme} onChange={(e) => setMalzeme(e.target.value)} style={input}>{meta.malzemeler.map((x) => <option key={x}>{x}</option>)}</select></div>
        <div><div style={{ ...lbl, marginBottom: 5 }}>Et Kalınlığı</div><select value={et} onChange={(e) => setEt(e.target.value)} style={input}>{meta.etler.map((x) => <option key={x}>{x}</option>)}</select></div>
        <button onClick={oner} disabled={mesgul} style={btn(mesgul ? C.raised : C.amber, mesgul ? C.textLo : "#1a1204", { padding: "10px 16px", fontSize: 13 })}>{mesgul ? "Öneriliyor…" : "Başlangıç ayarı öner"}</button>
      </div>
      {r && (
        <div style={{ ...card, border: `1px solid ${C.amberDim}`, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
            <span style={{ font: `700 11px ${mono}`, color: C.amber, letterSpacing: 1 }}>◆ ÖNERİLEN BAŞLANGIÇ · {r.malzeme} · {r.et}</span>
            <AIRozeti yanit={r} />
          </div>
          <KaynakEtiketleri kaynaklar={r.kaynaklar} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(112px, 1fr))", gap: 8, marginTop: 10 }}>
            {Object.entries(meta.alanlar).map(([k, f]) => {
              const v = r.degerler[k]; if (v == null) return null;
              const disari = v < f.aralik[0] || v > f.aralik[1];
              return (
                <div key={k} style={{ background: C.bg, border: `1px dashed ${disari ? C.red : f.yazilabilir ? C.amberDim : C.border}`, borderRadius: 6, padding: "8px 10px" }}>
                  <div style={{ ...lbl, fontSize: 9 }}>{f.etiket}</div>
                  <div style={{ font: `600 18px ${mono}`, color: disari ? C.red : f.yazilabilir ? C.amber : C.textMid, marginTop: 2 }}>{v}<span style={{ font: `500 10px ${mono}`, color: C.textMid }}> {f.birim}</span></div>
                  {yazmaModu && (f.yazilabilir
                    ? <button onClick={() => yazmaIste(k, v, `Reçete önerisi · ${r.malzeme}`)} style={{ marginTop: 6, width: "100%", background: C.green, color: "#0b0f12", border: "none", borderRadius: 5, padding: "4px 0", font: `700 11px ${sans}`, cursor: "pointer" }}>Uygula →</button>
                    : <div style={{ marginTop: 6, font: `600 10px ${sans}`, color: C.textLo, textAlign: "center" }}>🔒 Faz 3 · kilitli</div>)}
                </div>
              );
            })}
          </div>
          {r.not && <div style={{ font: `400 12px ${sans}`, color: C.textMid, marginTop: 10, lineHeight: 1.5 }}>⚠ {r.not}</div>}
          {(r.uyarilar || []).map((u, i) => <div key={i} style={{ font: `500 12px ${sans}`, color: C.red, marginTop: 4 }}>✕ {u}</div>)}
          {r.yedek && r.hata && <div style={{ font: `400 11px ${sans}`, color: C.textLo, marginTop: 6 }}>Bulut AI'ya ulaşılamadı ({r.hata}); öneri çevrimdışı uzmandan geldi.</div>}
          <div style={{ font: `500 10px ${mono}`, color: C.textLo, marginTop: 8 }}>{yazmaModu ? "⚑ Turuncu parametreler onaylı yazılabilir · gri/kilitli olanlar elle & Faz 3." : "⚑ Öneridir — bu değerleri panele elle giriniz."}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 12, borderTop: `1px solid ${C.border}`, paddingTop: 12, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ font: `500 12px ${sans}`, color: C.textMid }}>Denedin, sonuç?</span>
            <button onClick={() => sonuc("iyi")} style={{ background: C.greenDim, color: C.green, border: `1px solid ${C.green}`, borderRadius: 6, padding: "6px 14px", font: `600 12px ${sans}`, cursor: "pointer" }}>✓ İyi parça</button>
            <button onClick={() => sonuc("fire")} style={{ background: C.redDim, color: C.red, border: `1px solid ${C.red}`, borderRadius: 6, padding: "6px 14px", font: `600 12px ${sans}`, cursor: "pointer" }}>✕ Fire</button>
          </div>
        </div>
      )}
      <div style={card}>
        <div style={{ ...lbl, marginBottom: 8 }}>Kayıtlı Sonuçlar · Öğrenme Verisi</div>
        <div style={{ display: "flex", gap: 16, marginBottom: sonuclar.length ? 10 : 0 }}>
          <span style={{ font: `600 13px ${mono}`, color: C.green }}>✓ {iyi} iyi</span>
          <span style={{ font: `600 13px ${mono}`, color: C.red }}>✕ {fire} fire</span>
        </div>
        {sonuclar.length === 0 ? <div style={{ font: `400 12px ${sans}`, color: C.textLo }}>Henüz kayıt yok. Her sonuç kalıcı olarak saklanır.</div>
          : sonuclar.slice(0, 6).map((s) => <div key={s.id} style={{ font: `400 12px ${sans}`, color: C.textMid, padding: "3px 0" }}><span style={{ color: s.sonuc === "iyi" ? C.green : C.red }}>{s.sonuc === "iyi" ? "✓" : "✕"}</span> {s.malzeme} · {s.et} · {s.zaman.replace("T", " ")}</div>)}
      </div>
    </div>
  );
}

// ── ALARMLAR ───────────────────────────────────────────────────────
function Alarmlar({ meta, durum, dene, bildir }) {
  const [yorum, setYorum] = useState({});
  const istendi = useRef({});
  const alarmlar = durum.alarmlar || [];
  const aktif = alarmlar.filter((a) => a.active);
  const yorumAl = useCallback(async (a) => {
    istendi.current[a.id] = true;
    setYorum((y) => ({ ...y, [a.id]: { yukleniyor: true } }));
    try { const r = await api("POST", "/api/alarm/yorum", { id: a.id }); setYorum((y) => ({ ...y, [a.id]: r })); }
    catch (e) { setYorum((y) => ({ ...y, [a.id]: { hata: e.message } })); }
  }, []);
  // aktif alarm belirdiğinde yorum KENDİLİĞİNDEN gelir — operatör hiçbir şey yazmaz
  useEffect(() => { aktif.forEach((a) => { if (!istendi.current[a.id]) yorumAl(a); }); }, [aktif.map((a) => a.id).join(","), yorumAl]);
  async function gordum(a) { if (await dene(() => api("POST", "/api/alarm/gordum", { id: a.id }))) bildir(`${a.code} görüldü olarak işaretlendi.`); }
  async function senaryo(tur) { const r = await dene(() => api("POST", "/api/alarm/senaryo", { tur })); if (r) bildir(`Arıza senaryosu başladı: ${r.ad}. Alarm, ölçülen değerlerden kendiliğinden doğacak.`); }
  return (
    <div style={{ padding: 16 }}>
      <Baslik>Alarmlar · {aktif.length} aktif</Baslik>
      <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 10 }}>
        <span style={{ width: 7, height: 7, borderRadius: 7, background: C.green, boxShadow: `0 0 6px ${C.green}` }} />
        <span style={{ font: `400 12px ${sans}`, color: C.textLo, lineHeight: 1.5 }}>Alarmlar makinenin ölçülen değerlerinden <b style={{ color: C.textMid }}>otomatik</b> doğar ve koşul kalkınca kendiliğinden kapanır. USTA her aktif alarmın yorumunu kendisi getirir.</span>
      </div>
      {!meta.salt_okunur && meta.senaryolar && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14, alignItems: "center" }}>
          <span style={{ font: `500 11px ${sans}`, color: C.textLo }}>⚡ Simülasyonda arıza başlat:</span>
          {Object.entries(meta.senaryolar).map(([k, ad]) => <button key={k} onClick={() => senaryo(k)} style={{ ...btnGhost, padding: "4px 10px", fontSize: 11 }}>{ad}</button>)}
        </div>
      )}
      {alarmlar.length === 0 && <div style={{ ...card, textAlign: "center", color: C.textLo, font: `400 13px ${sans}` }}>Alarm yok — makine normal çalışıyor.</div>}
      {alarmlar.map((a) => {
        const col = a.sev === "crit" ? C.red : C.amber;
        const y = yorum[a.id];
        return (
          <div key={a.id} style={{ ...card, borderLeft: `3px solid ${a.active ? col : C.textLo}`, marginBottom: 10, opacity: a.active ? 1 : 0.6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={{ font: `600 11px ${mono}`, color: a.active ? col : C.textLo }}>{a.code}</span>
                <span style={{ font: `600 13px ${sans}`, color: C.textHi }}>{a.title}</span>
                {a.ack && <span style={{ font: `600 9px ${sans}`, color: C.green }}>✓ görüldü · {a.ack_by}</span>}
              </div>
              <span style={{ font: `500 11px ${mono}`, color: C.textLo, whiteSpace: "nowrap" }}>{a.active ? a.start : `çözüldü ${a.end || ""} ✓`}</span>
            </div>
            <div style={{ font: `400 12px ${sans}`, color: C.textMid, marginTop: 5, lineHeight: 1.5 }}>{a.detail}</div>
            {a.active && (
              <div style={{ marginTop: 10, background: C.bg, border: `1px solid ${y && y.hata ? C.red : C.amberDim}`, borderRadius: 7, padding: "10px 12px" }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 5 }}>
                  <span style={{ font: `700 10px ${mono}`, color: y && y.hata ? C.red : C.amber, letterSpacing: 1 }}>{y && y.hata ? "✕ YORUM ALINAMADI" : "◆ USTA · MUHTEMEL SEBEP VE SIRALI KONTROL"}</span>
                  {y && y.metin && <AIRozeti yanit={{ ...y, tesis: false }} />}
                </div>
                {!y || y.yukleniyor ? <div style={{ font: `400 12px ${sans}`, color: C.textMid }}>otomatik değerlendiriliyor…</div>
                  : y.hata ? <div><div style={{ font: `400 12px ${sans}`, color: C.textMid }}>{y.hata}</div><button onClick={() => yorumAl(a)} style={{ ...btnGhost, marginTop: 8, padding: "5px 12px", fontSize: 11 }}>↻ Tekrar dene</button></div>
                    : <div style={{ font: `400 12px ${sans}`, color: C.textHi, lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{y.metin}</div>}
              </div>
            )}
            {a.active && !a.ack && <button onClick={() => gordum(a)} style={{ ...btnGhost, color: C.textHi, marginTop: 10 }}>✓ Gördüm</button>}
          </div>
        );
      })}
    </div>
  );
}

// ── AI SOHBET ──────────────────────────────────────────────────────
function Sohbet({ meta, durum, yazmaModu }) {
  const [mesajlar, setMesajlar] = useState([{ role: "assistant", content: `Merhaba usta. Makinenin canlı değerlerini görüyorum. Ayar, hata ya da yeni ürün için sor. (Kaynak: ${meta.ai.etiket})`, ilk: true }]);
  const [yazi, setYazi] = useState("");
  const [mesgul, setMesgul] = useState(false);
  const kaydir = useRef(null);
  useEffect(() => { if (kaydir.current) kaydir.current.scrollTop = kaydir.current.scrollHeight; }, [mesajlar, mesgul]);
  async function gonder(metin) {
    const q = (metin ?? yazi).trim(); if (!q || mesgul) return;
    setYazi("");
    const sonraki = [...mesajlar, { role: "user", content: q }];
    setMesajlar(sonraki); setMesgul(true);
    try {
      const r = await api("POST", "/api/sohbet", { gecmis: sonraki.filter((m) => !m.ilk && !m.hata).map(({ role, content }) => ({ role, content })) });
      setMesajlar((m) => [...m, { role: "assistant", content: r.metin, yanit: r }]);
    } catch (e) {
      setMesajlar((m) => [...m, { role: "assistant", content: e.message, hata: true }]);
    } finally { setMesgul(false); }
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div ref={kaydir} style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        {mesajlar.map((m, i) => m.role === "user" ? (
          <div key={i} style={{ alignSelf: "flex-end", maxWidth: "82%" }}><div style={{ background: C.cyanDim, color: C.textHi, padding: "9px 13px", borderRadius: "10px 10px 2px 10px", font: `500 13px ${sans}`, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{m.content}</div></div>
        ) : (
          <div key={i} style={{ alignSelf: "flex-start", maxWidth: "90%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4, flexWrap: "wrap" }}>
              <span style={{ font: `700 10px ${mono}`, color: C.amber, letterSpacing: 1 }}>◆ USTA</span>
              {m.yanit && <AIRozeti yanit={m.yanit} />}
            </div>
            <div style={{ background: C.panel, border: `1px solid ${m.hata ? C.red : C.border}`, color: C.textHi, padding: "11px 14px", borderRadius: "2px 10px 10px 10px", font: `400 13px ${sans}`, lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{m.content}</div>
            {m.yanit && <KaynakEtiketleri kaynaklar={m.yanit.kaynaklar} />}
            {m.yanit && m.yanit.yedek && <div style={{ font: `400 10px ${sans}`, color: C.textLo, marginTop: 4 }}>Bulut AI'ya ulaşılamadı ({m.yanit.hata}); cevap çevrimdışı uzmandan.</div>}
            {m.yanit && <div style={{ font: `500 10px ${mono}`, color: C.textLo, marginTop: 5 }}>{yazmaModu ? "⚑ Öneri · yazmak için İŞLER ya da REÇETE'den doğrula ve onayla" : "⚑ Öneridir — değerleri panele siz girersiniz."}</div>}
          </div>
        ))}
        {mesgul && <div style={{ display: "flex", gap: 8, alignItems: "center" }}><span style={{ font: `700 10px ${mono}`, color: C.amber }}>◆ USTA</span><span style={{ font: `400 12px ${sans}`, color: C.textMid }}>değerlendiriyor…</span></div>}
      </div>
      <div style={{ padding: "0 16px 10px", display: "flex", flexWrap: "wrap", gap: 6 }}>
        {QUICK.map((p) => <button key={p} onClick={() => gonder(p)} disabled={mesgul} style={{ font: `500 11px ${sans}`, color: C.textMid, background: C.raised, border: `1px solid ${C.border}`, borderRadius: 14, padding: "5px 11px", cursor: mesgul ? "default" : "pointer", opacity: mesgul ? 0.5 : 1 }}>{p}</button>)}
        {durum.gozcu && durum.gozcu.bagli && durum.gozcu.toplam > 0 && <button onClick={() => gonder("GÖZCÜ verisine göre fire neden arttı, ne yapmalıyım?")} disabled={mesgul} style={{ font: `500 11px ${sans}`, color: C.cyan, background: C.raised, border: `1px solid ${C.cyanDim}`, borderRadius: 14, padding: "5px 11px", cursor: "pointer" }}>◆ GÖZCÜ verisine göre fire neden arttı?</button>}
      </div>
      <form onSubmit={(e) => { e.preventDefault(); gonder(); }} style={{ display: "flex", gap: 8, padding: "0 16px 16px" }}>
        <input value={yazi} onChange={(e) => setYazi(e.target.value)} placeholder="Sıcaklık, ayar ya da bir hata yaz…" style={{ ...input, flex: 1, background: C.panel, padding: "11px 13px" }} />
        <button type="submit" disabled={mesgul || !yazi.trim()} style={btn(mesgul || !yazi.trim() ? C.raised : C.amber, mesgul || !yazi.trim() ? C.textLo : "#1a1204", { padding: "0 18px", fontSize: 13 })}>Sor</button>
      </form>
    </div>
  );
}

// ── BİLGİ TABANI ───────────────────────────────────────────────────
function Bilgi({ durum, dene, bildir }) {
  const ot = durum.oturum;
  const [kayitlar, setKayitlar] = useState([]);
  const [asama, setAsama] = useState("bos"); // bos | okunuyor | inceleme
  const [sonuc, setSonuc] = useState(null);
  const [secili, setSecili] = useState({});
  const [surukle, setSurukle] = useState(false);
  const dosya = useRef(null);
  const yukle = useCallback(() => dene(async () => setKayitlar((await api("GET", "/api/bilgi")).kayitlar)), [dene]);
  useEffect(() => { yukle(); }, [yukle]);
  async function isle(f) {
    if (!f) return;
    if (f.size > 15 * 1024 * 1024) { bildir("Dosya 15 MB'tan büyük.", "hata"); return; }
    setAsama("okunuyor"); setSonuc({ dosya: f.name, adaylar: [], uyarilar: [] });
    try {
      const veri = await f.arrayBuffer();
      const r = await api("POST", "/api/bilgi/ayristir", veri, { "X-Dosya-Adi": encodeURIComponent(f.name), "Content-Type": "application/octet-stream" });
      setSonuc(r);
      const s = {}; r.adaylar.forEach((a) => { s[a.id] = !a.mevcut; }); setSecili(s);
      setAsama("inceleme");
    } catch (e) { bildir(e.message, "hata"); setAsama("bos"); }
  }
  async function onayla() {
    const r = await dene(() => api("POST", "/api/bilgi/ekle", { kayitlar: sonuc.adaylar.filter((a) => secili[a.id] && !a.mevcut) }));
    if (r) { bildir(`${r.eklenen} kayıt bilgi tabanına eklendi — USTA artık bunlara başvuruyor.`); setAsama("bos"); yukle(); }
  }
  async function sil(k) {
    if (!window.confirm(`"${k.baslik}" silinsin mi?`)) return;
    if (await dene(() => api("DELETE", `/api/bilgi/${k.id}`))) { bildir("Kayıt silindi."); yukle(); }
  }
  const gruplar = [["recete", "Kanıtlı Reçeteler", "◆", C.amber], ["datasheet", "Malzeme Datasheet'leri", "▤", C.cyan], ["not", "Makine Notları ve Belgeler", "⚙", C.cyan]];
  return (
    <div style={{ padding: 16 }}>
      <Baslik>Tesis Bilgi Tabanı · {kayitlar.length} kayıt</Baslik>
      <Aciklama>USTA'nın önerileri bu kayıtlara dayanır — cevaplar "genel bilgi" değil, <b style={{ color: C.cyan }}>bu tesise özeldir</b>. Belgeler gerçekten okunur: TXT, MD, CSV, Word (.docx), Excel (.xlsx); PDF için <code>pypdf</code> kurulu olmalı.</Aciklama>
      {ot.yetki.belge_yukle ? (
        <>
          <input ref={dosya} type="file" accept=".txt,.md,.csv,.docx,.xlsx,.pdf" onChange={(e) => { isle(e.target.files[0]); e.target.value = ""; }} style={{ display: "none" }} />
          {asama === "bos" && (
            <div onClick={() => dosya.current && dosya.current.click()} onDragOver={(e) => { e.preventDefault(); setSurukle(true); }} onDragLeave={() => setSurukle(false)} onDrop={(e) => { e.preventDefault(); setSurukle(false); isle(e.dataTransfer.files[0]); }}
              style={{ border: `2px dashed ${surukle ? C.amber : C.border}`, background: surukle ? "#1c1608" : C.panel, borderRadius: 10, padding: "20px 16px", textAlign: "center", cursor: "pointer", marginBottom: 16 }}>
              <div style={{ font: `600 22px ${mono}`, color: surukle ? C.amber : C.textLo }}>⇪</div>
              <div style={{ font: `600 13px ${sans}`, color: C.textHi, marginTop: 6 }}>Belge yükle — Word, Excel, CSV, metin, PDF</div>
              <div style={{ font: `400 12px ${sans}`, color: C.textLo, marginTop: 4 }}>Datasheet, reçete listesi, kalite kaydı… sürükle-bırak ya da tıkla.</div>
            </div>
          )}
          {asama === "okunuyor" && <div style={{ ...card, border: `1px solid ${C.amberDim}`, textAlign: "center", marginBottom: 16 }}><div style={{ font: `700 11px ${mono}`, color: C.amber, letterSpacing: 1 }}>◆ OKUNUYOR</div><div style={{ font: `500 13px ${sans}`, color: C.textHi, marginTop: 6 }}>{sonuc && sonuc.dosya}</div></div>}
          {asama === "inceleme" && sonuc && (
            <div style={{ ...card, border: `1px solid ${C.amber}`, marginBottom: 16 }}>
              <div style={{ font: `700 11px ${mono}`, color: C.amber, letterSpacing: 1, marginBottom: 3 }}>◆ BULUNAN KAYITLAR · {sonuc.dosya} · {sonuc.adaylar.length}</div>
              {sonuc.uyarilar.map((u, i) => <div key={i} style={{ font: `500 12px ${sans}`, color: C.red, margin: "6px 0" }}>✕ {u}</div>)}
              {sonuc.adaylar.length > 0 && <div style={{ font: `400 12px ${sans}`, color: C.textMid, marginBottom: 10 }}>Eklemek istemediklerinin işaretini kaldır, sonra onayla.</div>}
              <div style={{ maxHeight: 320, overflowY: "auto" }}>
                {sonuc.adaylar.map((c) => {
                  const on = secili[c.id] && !c.mevcut;
                  return (
                    <div key={c.id} onClick={() => !c.mevcut && setSecili({ ...secili, [c.id]: !secili[c.id] })} style={{ display: "flex", gap: 10, background: C.bg, border: `1px solid ${on ? C.amberDim : C.border}`, borderRadius: 7, padding: "10px 12px", marginBottom: 8, cursor: c.mevcut ? "default" : "pointer", opacity: c.mevcut ? 0.5 : 1 }}>
                      <div style={{ width: 18, height: 18, borderRadius: 4, flexShrink: 0, border: `1px solid ${on ? C.amber : C.border}`, background: on ? C.amber : "transparent", display: "grid", placeItems: "center", font: `700 12px ${mono}`, color: "#0b0f12" }}>{on ? "✓" : ""}</div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ font: `600 13px ${sans}`, color: C.textHi }}>{c.baslik} {c.mevcut && <span style={{ font: `500 10px ${sans}`, color: C.textLo }}>· zaten mevcut</span>}</div>
                        <div style={{ font: `400 11px ${sans}`, color: C.textMid, marginTop: 3, lineHeight: 1.45, whiteSpace: "pre-wrap" }}>{c.metin.length > 300 ? c.metin.slice(0, 300) + "…" : c.metin}</div>
                        <span style={{ font: `600 9px ${sans}`, letterSpacing: 0.5, color: c.tur === "recete" ? C.amber : C.cyan, textTransform: "uppercase" }}>{c.tur === "recete" ? "◆ reçete" : c.tur === "not" ? "⚙ not" : "▤ datasheet"}{c.malzeme ? ` · ${c.malzeme}` : ""}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                {sonuc.adaylar.length > 0 && <button onClick={onayla} style={btn(C.green, "#0b0f12")}>✓ Onayla ve ekle</button>}
                <button onClick={() => setAsama("bos")} style={btnGhost}>İptal</button>
              </div>
            </div>
          )}
        </>
      ) : <div style={{ background: C.raised, border: `1px dashed ${C.border}`, borderRadius: 8, padding: "12px 14px", font: `400 12px ${sans}`, color: C.textLo, textAlign: "center", marginBottom: 16 }}>Belgeler görüntüleniyor. Belge eklemek için mühendis girişi gerekir.</div>}
      {gruplar.map(([t, ad, ikon, renk]) => {
        const docs = kayitlar.filter((d) => d.tur === t);
        if (!docs.length) return null;
        return (
          <div key={t} style={{ marginBottom: 14 }}>
            <div style={{ font: `600 10px ${sans}`, letterSpacing: 1, color: renk, textTransform: "uppercase", marginBottom: 8 }}>{ikon} {ad} · {docs.length}</div>
            {docs.map((d) => (
              <div key={d.id} style={{ ...card, borderLeft: `3px solid ${t === "recete" ? C.amber : C.cyanDim}`, padding: "10px 14px", marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
                  <span style={{ font: `600 13px ${sans}`, color: C.textHi }}>{d.baslik}</span>
                  <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span style={{ font: `500 10px ${mono}`, color: C.textLo }}>{d.id}</span>
                    {ot.yetki.belge_yukle && <button onClick={() => sil(d)} title="Sil" style={{ background: "transparent", border: "none", color: C.textLo, cursor: "pointer", font: `600 12px ${mono}` }}>✕</button>}
                  </span>
                </div>
                <div style={{ font: `400 12px ${sans}`, color: C.textMid, marginTop: 5, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{d.metin}</div>
                {d.kaynak && <div style={{ font: `500 10px ${mono}`, color: C.textLo, marginTop: 4 }}>kaynak: {d.kaynak}</div>}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

// ── KAYIT DEFTERİ ──────────────────────────────────────────────────
function Kayit({ dene }) {
  const [k, setK] = useState(null);
  useEffect(() => { dene(async () => setK((await api("GET", "/api/kayit")).kayitlar)); }, [dene]);
  return (
    <div style={{ padding: 16 }}>
      <Baslik>AI Destekli İşlem Kayıt Defteri</Baslik>
      <Aciklama>Makineye yazılan her değer, kaynağı ve onaylayanla birlikte burada tutulur. Kayıtlar veritabanı seviyesinde <b style={{ color: C.textMid }}>değiştirilemez ve silinemez</b> (izlenebilirlik ve denetim).</Aciklama>
      {k === null ? <div style={{ color: C.textLo, font: `400 12px ${sans}` }}>yükleniyor…</div>
        : k.length === 0 ? <div style={{ ...card, border: `1px dashed ${C.border}`, padding: "24px 16px", textAlign: "center", font: `400 13px ${sans}`, color: C.textLo }}>Henüz yazma işlemi yok. Onaylı Yazma modunda bir değer onaylanınca burada belirir.</div>
          : k.map((e) => (
            <div key={e.id} style={{ ...card, borderLeft: `3px solid ${C.green}`, padding: "10px 14px", marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <span style={{ font: `600 13px ${sans}`, color: C.textHi }}>#{e.id} · {e.etiket}</span>
                <span style={{ font: `500 11px ${mono}`, color: C.textLo }}>{e.zaman.replace("T", " ")}</span>
              </div>
              <div style={{ font: `500 13px ${mono}`, marginTop: 4 }}><span style={{ color: C.textMid }}>{e.eski ?? "—"}{e.birim}</span><span style={{ color: C.textLo }}> → </span><span style={{ color: C.green }}>{e.yeni}{e.birim}</span></div>
              <div style={{ font: `400 11px ${sans}`, color: C.textLo, marginTop: 3 }}>{e.kaynak} · onaylayan: {e.kullanici} ({e.rol}){e.vardiya ? ` · ${e.vardiya}` : ""}</div>
            </div>
          ))}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
