# USTA·AI — Kurulum Kılavuzu

Bilgisayarda denemeden Raspberry Pi'ye, oradan gerçek prese bağlanmaya kadar adım adım kurulum.

> **Hedef kitle:** kurulumu yapacak kişi (mühendis, entegratör ya da ürün sahibi). Operatör bu adımların hiçbirini yapmaz.

## 1 · Bilgisayarda çalıştırma (Windows)

1. https://www.python.org/downloads/ adresinden Python 3.9 veya üstünü indirin. Kurulumun **ilk ekranında "Add Python to PATH" kutusunu işaretleyin.**
2. GitHub'daki depodan **Code → Download ZIP** ile indirip bir klasöre çıkarın (ya da `git clone`).
3. Klasördeki **`kontrol.bat`** dosyasına çift tıklayın. Tüm satırlar `[ OK ]` olmalı.
4. **`baslat.bat`** dosyasına çift tıklayın. Panel tarayıcıda kendiliğinden açılır (adres: `http://127.0.0.1:8080`).
5. Kapatmak için açılan siyah pencerede **Ctrl+C**.

Kurulması gereken başka paket **yoktur**. Arayüz, React ve yazı tipleri depoda gelir; internet olmadan çalışır.

## 2 · macOS / Linux

```bash
git clone <depo-adresi> usta-ai
cd usta-ai
python3 -m usta kontrol
./baslat.sh
```

## 3 · İlk kullanım turu (5 dakika)

1. **PANO** — üretim sayacının arttığını, çevrim fazının döndüğünü görün.
2. **AI ASİSTAN** — "Ürün kenarlarında çapak var" yazın. Sıralı kontrol listesi ve güvenli aralıkta ayar önerisi gelir.
3. Sağ üstten **Mehmet K. (Usta)** seçin, **Onaylı Yazma**'ya geçin.
4. **İŞLER** — bir işi açın, Bölge 1 değerini 240 yapıp "Makineye uygula"ya basın: doğrulama, tek adımda 15 °C'den büyük değişimi **reddeder**. 222 yapın: onay ister; onaylayınca **KAYIT** sekmesine düşer.
5. **ALARMLAR** — "Bölge 2 rezistans arızası" senaryosunu başlatın. Birkaç saniye içinde ölçülen sıcaklık düşer, alarm kendiliğinden doğar ve USTA kontrol listesini getirir.

## 4 · Yapay zekâ kaynağını seçme

`.env.example` dosyasını **`.env`** adıyla kopyalayın ve düzenleyin:

```ini
ANTHROPIC_API_KEY=sk-ant-...     # Claude için
USTA_AI=otomatik                 # otomatik | claude | ollama | uzman
```

- **otomatik:** anahtar varsa Claude, yoksa çevrimdışı uzman.
- **ollama:** https://ollama.com kurun, `ollama pull llama3.1` çalıştırın, `USTA_AI=ollama` yapın.
- Değişiklikten sonra USTA'yı yeniden başlatın ve `kontrol.bat` ile bağlantıyı doğrulayın.

`.env` dosyası `.gitignore`'dadır — anahtarınız GitHub'a yüklenmez.

## 5 · Tesise özel ayarlar — `veri/ayarlar.json`

İlk çalıştırmada oluşur. En önemli bölümler:

```json
{
  "makine": {
    "ad": "ENJEKSİYON PRESİ · HAT-3",
    "baglanti": "simulasyon",
    "alanlar": {
      "z1": {"etiket": "Bölge 1", "birim": "°C", "yazilabilir": true, "aralik": [190, 255], "max_adim": 15}
    }
  },
  "roller": { "pin": { "operator": "", "usta": "2468", "muhendis": "1357" } },
  "gozcu": { "klasor": "C:\\Users\\kullanici\\Desktop\\gozcu-ai" }
}
```

- **aralik:** o makinenin ve kalıbın güvenli zarfı. Malzeme ideali değil, **makine sınırı** yazılır.
- **max_adim:** tek yazmada izin verilen en büyük değişim.
- **pin:** sahada mutlaka doldurun. Boş bırakılırsa rol seçimi PIN sormaz.
- Dosya bozulursa silin; ilk açılışta varsayılanlarla yeniden oluşur.

## 6 · Raspberry Pi'ye kurulum

1. Raspberry Pi Imager ile **Raspberry Pi OS (64-bit)** yazın. Kullanıcı ve parolayı, Wi-Fi'yi ve SSH'yi imaj ayarlarında belirleyin.
2. Pi'yi Ethernet ile ağa bağlayıp SSH ile girin:

```bash
sudo apt update && sudo apt upgrade -y
git clone <depo-adresi> ~/usta-ai
cd ~/usta-ai && python3 -m usta kontrol
```

3. Ağdaki tabletin erişebilmesi için `--ag` ile başlatın ve rol PIN'lerini tanımlayın:

```bash
python3 -m usta --ag --tarayici-yok
```

4. **Açılışta kendiliğinden başlasın** (systemd servisi). Aşağıda `KULLANICI` yerine Pi'yi kurarken seçtiğiniz kullanıcı adını yazın (güncel Raspberry Pi OS'ta varsayılan `pi` kullanıcısı yoktur):

```ini
# /etc/systemd/system/usta.service
[Unit]
Description=USTA-AI operator danismani
After=network-online.target

[Service]
User=KULLANICI
WorkingDirectory=/home/KULLANICI/usta-ai
ExecStart=/usr/bin/python3 -m usta --ag --tarayici-yok
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now usta
journalctl -u usta -f          # canlı log
```

## 7 · Gerçek prese bağlanma (OPC UA)

1. `pip install asyncua` (Pi'de: `python3 -m pip install --break-system-packages asyncua` ya da sanal ortam).
2. Edge cihazını presin PLC ağına Ethernet ile bağlayın; makinenin OPC UA adresini öğrenin (ör. `opc.tcp://192.168.0.10:4840`).
3. Bir OPC UA istemcisiyle (ör. UaExpert) düğüm ağacını gezip kullanılacak düğümleri bulun.
4. `veri/ayarlar.json`:

```json
"makine": {
  "baglanti": "opcua",
  "opcua_url": "opc.tcp://192.168.0.10:4840",
  "opcua_dugumler": {
    "z1": "ns=2;s=...", "z1_sp": "ns=2;s=...",
    "tutmaPress": "...", "tutmaPress_sp": "...",
    "enjPress": "...", "cevrim": "...", "yastik": "...", "baski": "...",
    "yazma_izni": false
  }
}
```

5. **En az bir hafta salt-okuma** modunda çalıştırın; panelde değerlerin makine ekranıyla birebir aynı olduğunu doğrulayın.
6. Yazma ancak bu doğrulamadan, üreticinin onayından ve güvenlik değerlendirmesinden sonra `"yazma_izni": true` ile açılır. Her yazmadan sonra değer makineden geri okunur; uyuşmazsa hata verilir.

Bağlantı koparsa panelde **BAĞLANTI HATASI** görünür ve USTA artan aralıklarla kendiliğinden yeniden bağlanır.

## 8 · GÖZCÜ·AI ile birleştirme

GÖZCÜ'nün çalışma klasörünü `ayarlar.json` içinde `"gozcu": {"klasor": "..."}` olarak ya da `.env` içinde `USTA_GOZCU=...` olarak verin. PANO'da "GÖZCÜ·AI Entegrasyonu · BAĞLI" görünür; AI ASİSTAN görüntü muayenesinin fire türlerini de dikkate alır.

## 9 · Sorun giderme

| Belirti | Çözüm |
|---|---|
| "Python bulunamadı" | Python'u "Add Python to PATH" işaretli yeniden kurun |
| Panel açılmadı | Penceredeki adresi tarayıcıya elle yazın |
| AI cevabında "yedek" yazıyor | `kontrol.bat`: anahtar, internet ya da kota sorunu |
| Tablet bağlanamıyor | `--ag` ile başlatıldı mı; güvenlik duvarı portu (8080) engelliyor mu |
| "BAĞLANTI HATASI" | Kablo, IP adresi, makinenin OPC UA sunucusu açık mı |
| Ayrıntı | `veri/usta.log` dosyası |
