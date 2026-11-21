// USTA·AI arayüz derleyicisi — yalnız geliştiriciler için.
// Kullanım:  cd arayuz && npm install && npm run build
// Çıktı: ../usta/web/  (index.html, app.js, vendor/, fonts/) — depoya bu çıktı da eklenir,
// böylece kullanıcıların Node.js kurmasına gerek kalmaz.
"use strict";
const fs = require("fs");
const path = require("path");
const babel = require("@babel/core");

const KOK = __dirname;
const HEDEF = path.join(KOK, "..", "usta", "web");
const nm = (...p) => path.join(KOK, "node_modules", ...p);

function kopyala(kaynak, hedef) {
  fs.mkdirSync(path.dirname(hedef), { recursive: true });
  fs.copyFileSync(kaynak, hedef);
}

// 1) JSX → düz JavaScript (klasik çalışma zamanı: React.createElement; import yok)
const kaynak = fs.readFileSync(path.join(KOK, "app.jsx"), "utf8");
const sonuc = babel.transformSync(kaynak, {
  filename: "app.jsx",
  babelrc: false,
  configFile: false,
  presets: [[require.resolve("@babel/preset-react"), { runtime: "classic" }]],
  comments: false,
});
if (/(^|\n)\s*import\s/.test(sonuc.code)) throw new Error("Çıktıda import kaldı — tarayıcıda çalışmaz.");
const surum = require("./package.json").version;
const govde = `/* USTA·AI arayüzü v${surum} — arayuz/app.jsx dosyasından üretilmiştir; elle düzenlemeyin. */\n` +
  `(function () {\n"use strict";\n${sonuc.code}\n})();\n`;
fs.mkdirSync(HEDEF, { recursive: true });
fs.writeFileSync(path.join(HEDEF, "app.js"), govde);
fs.copyFileSync(path.join(KOK, "index.html"), path.join(HEDEF, "index.html"));
fs.copyFileSync(path.join(KOK, "favicon.svg"), path.join(HEDEF, "favicon.svg"));

// 2) React (yerel kopya — çalışma anında internet gerekmez)
kopyala(nm("react", "umd", "react.production.min.js"), path.join(HEDEF, "vendor", "react.production.min.js"));
kopyala(nm("react-dom", "umd", "react-dom.production.min.js"), path.join(HEDEF, "vendor", "react-dom.production.min.js"));

// 3) Yazı tipleri: latin + latin-ext (Türkçe ğ, ş, ı, İ için latin-ext şart)
let css = "";
for (const [aile, paket, agirliklar] of [["IBM Plex Sans", "ibm-plex-sans", [400, 500, 600, 700]],
                                        ["IBM Plex Mono", "ibm-plex-mono", [400, 500, 600, 700]]]) {
  for (const w of agirliklar) {
    for (const alt of ["latin", "latin-ext"]) {
      const ad = `${paket}-${alt}-${w}-normal.woff2`;
      kopyala(nm("@fontsource", paket, "files", ad), path.join(HEDEF, "fonts", ad));
      const aralik = alt === "latin"
        ? "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
        : "U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF";
      css += `@font-face{font-family:'${aile}';font-style:normal;font-weight:${w};font-display:swap;` +
             `src:url('${ad}') format('woff2');unicode-range:${aralik};}\n`;
    }
  }
}
fs.writeFileSync(path.join(HEDEF, "fonts", "fonts.css"), css);
fs.copyFileSync(nm("@fontsource", "ibm-plex-sans", "LICENSE"), path.join(HEDEF, "fonts", "OFL-LICENSE.txt"));
console.log(`Arayüz derlendi → ${path.relative(process.cwd(), HEDEF)} (app.js ${(govde.length / 1024).toFixed(0)} KB)`);
