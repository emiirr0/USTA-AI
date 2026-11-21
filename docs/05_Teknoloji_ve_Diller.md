# USTA·AI — Teknoloji ve Diller

Sistemin hangi dil ve teknolojilerle yazıldığı ve her seçimin nedeni.

## 1 · Özet

| Katman | Teknoloji | Neden |
|---|---|---|
| Uygulama dili | Python 3.9+ | Edge cihazlarında (Raspberry Pi, endüstriyel Linux) her yerde var; okunaklı |
| Bağımlılık | **Yalnız standart kütüphane** | Kurulum = Python kurmak. `pip` hatası, sürüm çakışması, internet ihtiyacı yok |
| Web sunucusu | `http.server` (ThreadingHTTPServer) | Tek panel / birkaç tablet için yeterli; ek paket yok |
| Veritabanı | SQLite (`sqlite3`) | Tek dosya, sunucusuz; tetikleyicilerle değiştirilemez kayıt |
| Arayüz | React 18 (JSX → önceden derlenmiş JavaScript) | Zengin, durumlu panel; derleme depoda olduğu için kullanıcı Node kurmaz |
| Yazı tipi | IBM Plex Sans / Mono (yerel, latin-ext) | Enstrüman hissi; Türkçe harfler için latin-ext dahil, internet gerekmez |
| Makine bağlantısı | OPC UA — `asyncua` (isteğe bağlı) | Euromap 77'nin taşıyıcısı; Python'da olgun kütüphane |
| Bulut yapay zekâ | Claude Messages API (`urllib` ile) | SDK bağımlılığı olmadan |
| Yerel yapay zekâ | Ollama HTTP API | Veri tesisten çıkmasın isteyenler için |
| PDF okuma | `pypdf` (isteğe bağlı) | Yalnız PDF yüklenecekse |
| Test | pytest, Playwright (arayüz), asyncua test sunucusu | Gerçek HTTP, gerçek tarayıcı, gerçek OPC UA |
| Sürekli test | GitHub Actions | Her yüklemede Windows/macOS/Linux × Python 3.9/3.11/3.13 |

## 2 · Neden "sıfır bağımlılık"?

Hedef kullanıcı yazılımcı değildir. En sık kurulum hataları paket yöneticisinden gelir: internet yok, kurumsal proxy, yanlış Python, izin hatası, sürüm çakışması. USTA'nın çekirdeği yalnız Python'un kendisiyle gelen modülleri kullanır; bu yüzden **Python kuruluysa USTA çalışır**. İsteğe bağlı yetenekler (OPC UA, PDF) ayrı paketlerdir ve yoksa uygulama bunu söyleyerek çalışmaya devam eder.

## 3 · Arayüz derlemesi

- Kaynak: `arayuz/app.jsx`. Derleyici: `arayuz/build.js` (Babel, klasik React çalışma zamanı).
- Çıktı `usta/web/` altına yazılır ve **depoya eklenir**. Böylece:
  - kullanıcı Node.js kurmaz,
  - tarayıcıda derleyici çalışmaz (hızlı açılış, derleyici sürümü sürprizi yok),
  - çalışma anında CDN'e, internete gerek yoktur.
- GitHub Actions, depodaki derlemenin kaynakla aynı olduğunu her yüklemede denetler.

Arayüzü değiştiren geliştirici: `cd arayuz && npm install && npm run build`.

## 4 · Dosya ve kod düzeni

- Modül adları İngilizce/ASCII (her işletim sisteminde güvenli), kullanıcıya görünen her metin Türkçe.
- İş mantığı (`app.py`) HTTP'den ayrıdır: testler doğrudan çağırır, ileride başka bir arayüz (ör. masaüstü) aynı çekirdeği kullanabilir.
- Makine ve yapay zekâ "bağdaştırıcı" desenindedir: yeni protokol ya da sağlayıcı eklemek tek bir sınıf yazmaktır.

## 5 · Sürüm uyumluluğu

| Bileşen | Desteklenen |
|---|---|
| Python | 3.9 – 3.13 (3.9, 3.11, 3.12, 3.13'te test edildi) |
| SQLite | 3.24+ (UPSERT için; Python 3.9+ ile gelen sürümler uygundur) |
| Tarayıcı | Güncel Chrome, Edge, Firefox, Safari; Android tablet tarayıcıları |
| İşletim sistemi | Windows 10/11, macOS, Linux (Raspberry Pi OS dahil) |
