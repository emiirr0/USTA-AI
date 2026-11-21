# USTA·AI — Donanım ve Gereksinimler

Bu ürünü bir enjeksiyon presine kurmak için gereken donanım: sıfır maliyetli bilgisayar denemesinden endüstriyel kuruluma kadar üç kademe.

> **Fiyatlar yaklaşıktır.** Raspberry Pi fiyatları 2026'da bellek maliyetleri yüzünden birkaç kez arttı (bkz. Kaynaklar). Satın almadan önce güncel teklif alın.

## 1 · Mimarinin özeti

Sistem makinenin içine kurulmaz, **yanında** çalışır. İki fiziksel parça vardır:

- **Edge cihazı** — makinenin yanındaki küçük bilgisayar. `python -m usta` burada çalışır: makineyi dinler, yapay zekâyı çalıştırır, kayıtları tutar.
- **Operatör ekranı** — edge cihazına yerel ağdan bağlanan bir tarayıcı (tablet ya da panel). Kendi başına zekâsı yoktur; değiştirilebilir.

Kısa kural: **beyin = edge cihazı** (dayanıklı olmalı), **ekran = tablet** (ucuz ve değiştirilebilir olabilir).

USTA yalnız Python standart kütüphanesini kullanır; ek paket gerektirmez. Bu yüzden aynı yazılım dizüstü bilgisayarda, Raspberry Pi'de ve endüstriyel bilgisayarda değişmeden çalışır.

## 2 · Kademe 0 — Bilgisayarda deneme (maliyet: 0)

Donanım almadan önce her şey normal bir Windows/macOS/Linux bilgisayarda denenebilir. Makine yerine fiziksel modelli **simülatör** çalışır: sıcaklıklar setpoint'e rampa yaparak yaklaşır, fire türü süreç sapmasından doğar, arıza senaryoları gerçek alarm üretir.

| Gereksinim | Asgari |
|---|---|
| İşletim sistemi | Windows 10/11, macOS 12+, güncel Linux |
| Python | 3.9 veya üstü |
| Bellek | 2 GB boş RAM |
| Disk | 200 MB |
| İnternet | Gerekmez (Claude kullanılacaksa gerekir) |

## 3 · Kademe A — Pilot (tek makine, düşük maliyet)

Amaç: bir fabrikada, tek makinede "gerçekten işe yarıyor mu" sorusunu yanıtlamak. Endüstriyel dayanıklılık aranmaz.

| Bileşen | Önerilen | Yaklaşık fiyat |
|---|---|---|
| Edge cihazı | Raspberry Pi 5 — 4 GB (USTA için yeterli) | 105 USD |
| Kasa + soğutma | Resmi kasa + fanlı soğutucu | 15–25 USD |
| Güç adaptörü | Resmi 27 W USB-C | 12–15 USD |
| Depolama | microSD 64 GB (A2) ya da NVMe SSD | 15–35 USD |
| Ağ | CAT6 Ethernet kablosu | 5 USD |
| Operatör ekranı | 10" Android tablet | 150–220 USD |

**Pilot toplam: yaklaşık 300–400 USD** (tek makine, ekran dahil). Yerel yapay zekâ (Ollama) planlanıyorsa 8 GB model (175 USD) ya da bir mini PC düşünülmelidir.

> **Alternatif:** 2026 fiyatlarıyla N100/N150 sınıfı bir mini PC, Raspberry Pi 5 8 GB ile benzer fiyata gelmektedir ve daha güçlüdür (yerel model için daha uygun). Pilot için ikisi de uygundur; mini PC'de Windows ya da Linux kullanılabilir.

Not: Raspberry Pi tozlu, titreşimli ve sıcak üretim ortamında uzun süre çalışmak için tasarlanmamıştır. Pilot başarılı olunca Kademe B'ye geçilmelidir.

## 4 · Kademe B — Endüstriyel kurulum (7/24 üretim)

Amaç: gerçek üretim hattında yıllarca sorunsuz çalışmak. DIN ray montajlı, 24 V DC beslemeli, endüstriyel destekli donanım.

| Bileşen | Önerilen / eşdeğer | Yaklaşık fiyat |
|---|---|---|
| Edge cihazı | Siemens SIMATIC IOT2050, Advantech UNO, Revolution Pi ya da fansız endüstriyel PC | 320–600 USD |
| Endüstriyel güç | 24 V DC ray tipi güç kaynağı | 30–60 USD |
| Depolama | Endüstriyel SSD / eMMC | dahil – 40 USD |
| Ağ | Endüstriyel CAT6, gerekirse yönetilebilir switch | 10–120 USD |
| Operatör paneli | Endüstriyel dokunmatik panel (10–15") ya da sağlam tablet | 300–800 USD |
| Montaj / kablaj | Pano içi montaj, kablo kanalı, işçilik | değişken |

**Endüstriyel toplam: makine başına yaklaşık 700–1.600 USD** (panel ve işçilik dahil, tedarikçiye göre değişir).

## 5 · Kademeler yan yana

| Ölçüt | Kademe 0 | Kademe A (Pilot) | Kademe B (Endüstriyel) |
|---|---|---|---|
| Amaç | Deneme, satış demosu | Tek makinede kanıt | Gerçek üretim |
| Makine bağlantısı | Simülatör | OPC UA (salt okuma) | OPC UA |
| Dayanıklılık | Ofis | Atölye | 7/24, toz/ısı/titreşim |
| Maliyet (makine başı) | 0 | ≈ 300–400 USD | ≈ 700–1.600 USD |

## 6 · Makine tarafı önkoşullar

- Presin kontrolcüsü **OPC UA** (enjeksiyonda tipik olarak **Euromap 77**) ile veri yayınlıyor olmalı. Modern preslerin büyük çoğunluğu yayınlar; eski makinelerde üreticiden lisans/seçenek gerekebilir.
- **Alarm yorumu** için makinenin alarm etiketleri de dışa veriliyor olmalı.
- **Geri-okumalı yazma** için ölçüm değerlerinin yanında **setpoint** etiketleri de dışa verilmeli.
- **Yazma** için üreticinin yazma kanalı makine sahibi tarafından bilerek açılmış olmalı. USTA'da yazma varsayılan olarak **kapalıdır** (`"yazma_izni": false`).

## 7 · Yapay zekâ kaynağının donanıma etkisi

| Kaynak | Ek donanım | Not |
|---|---|---|
| Çevrimdışı uzman | Yok | Varsayılan; internet gerektirmez |
| Claude (bulut) | Yok | İnternet bağlantısı ve API anahtarı gerekir; kullanım başına ücretlidir |
| Yerel model (Ollama) | 8 GB+ RAM, tercihen mini PC | Veri tesisten çıkmaz; küçük modeller Pi 5'te yavaş çalışır |

## 8 · Dürüst notlar

- Yazılım bugün **çalışır durumdadır** ve simülatörle uçtan uca test edilmiştir. OPC UA bağdaştırıcısı, otomatik testlerde gerçek bir yerel OPC UA sunucusuna karşı doğrulanmıştır; **gerçek bir prese henüz bağlanmamıştır**. Sahaya çıkmadan önce makinenin düğüm adlarıyla eşleme yapılıp salt-okuma modunda en az bir hafta izlenmelidir.
- Yazma açılmadan önce bağımsız bir **fonksiyonel güvenlik değerlendirmesi** önerilir.

## Kaynaklar

- Raspberry Pi bellek kaynaklı fiyat artışları (2 Şubat 2026): https://raspberrypi.com/news/more-memory-driven-price-rises
- Raspberry Pi 5 güncel fiyat listesi (Nisan 2026): https://www.notebookcheck.net/Raspberry-Pi-confirms-new-pricing-for-popular-single-board-computers.1264226.0.html
- Raspberry Pi ve mini PC fiyatlarının eşitlenmesi: https://www.tomshardware.com/raspberry-pi/raspberry-pi-and-mini-pc-home-lab-prices-hit-parity-as-dram-costs-skyrocket-price-hikes-force-hobbyists-to-weigh-up-performance-versus-power-consumption
