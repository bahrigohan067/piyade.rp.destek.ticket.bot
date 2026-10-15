# Piyade RP - Destek & Ticket Botu

Piyade Roleplay sunucusu için özel olarak geliştirilmiş **Destek & Ticket Yönetim Botu**.

Bu bot; bilet açma/kapama süreçlerini, mükerrer bilet engellemesini, yardım bekleme ses kanalı yönetimini, Discord yetkili aktiflik takibini, Roblox ER:LC oyun içi yetkili mesai takibini ve günlük performans raporlamasını üstlenir.

---

## 📌 Özellikler

### 1. 🎫 Ticket (Bilet) Sistemi
* **Mükerrer Bilet Koruması:** Kullanıcının açık bir bileti varsa yeni bilet açması engellenir, mevcut biletine yönlendirilir.
* **Gizli Kanallar:** `@everyone` rolüne kapalı, yalnızca bilet sahibi, bot ve yetkililerin görebildiği özel kanallar açılır.
* **Kalıcı Butonlar (Persistent Views):** Bot veya sunucu yeniden başlasa bile butonlar asla işlevini kaybetmez.
* **Otomatik Loglama:** Bilet kapatıldığında `#only-mod` log kanalına açılış tarihi, kapatılış tarihi ve işlemi yapan yetkili detaylarıyla kırmızı embed olarak iletilir.
* **İstatistik Entegrasyonu:** Bilet kapatan yetkilinin kapattığı bilet sayısı anında veritabanına kaydedilir.
* **Kişi Ekleme (`/ekle`):** Bilet sahibi veya yetkililer tek seferde 3 kişiye kadar bilet odasına üye dahil edebilir.

### 2. 🎧 Sesli Yardım Bekleme & Destek Yönetimi
* **Otomatik Susturma:** Yardım bekleme odasına giren kullanıcılar ses kirliliğini önlemek adına otomatik olarak susturulur (`mute=True`).
* **Rol Saati Filtresi:** TSİ gece 01:00 ile öğlen 12:00 arasında yetkililere bildirim gönderilmez; 12:00 ile 01:00 arasında yetkili rolü etiketlenerek bildirim düşer.
* **Katılımcıyı Devralma:** Yetkili butona bastığında kullanıcı otomatik olarak Yardım Odası'na çekilir ve susturması kaldırılır.
* **Sonuçlandırma Formu (Modal):** Görüşme bittiğinde yetkili sonucu yazar, geçen tam süre hesaplanır, baktığı destek sayısı 1 artırılır ve loglanır.
* **Boş Çıktı Yönetimi:** Kullanıcı konuşmazsa veya ayrılmışsa tek tıkla boş olarak sonuçlandırılır.

### 3. 📊 Discord ve ER:LC Oyun İçi Yetkili Takip Sistemi
* **Discord Aktiflik Takibi:** Ses kanalı bağımlılığı yoktur. Yetkililerin Discord durumları (🟢 Aktif, 🌙 Boşta, 🔴 Rahatsız Etmeyin) aktif mesai olarak sayılır.
* **Roblox ER:LC Oyun İçi Takip:** `ERLC_API_KEY` aracılığıyla yetkililerin Roblox ER:LC sunucusundaki aktiflikleri canlı olarak taranır ve kaydedilir.
* **3 Saatlik Hedef ve Grafiksel Doluluk Çubuğu:**
  * Tamamlanan Bölge: **YEŞİL (`🟩`)**
  * Tamamlanmayan Bölge: **BEYAZ (`⬜`)**
* **👑 Yetkili Sıralama Tablosu (`/yetkili-tablo`):**
  * Sadece **Kurucu** ve **Üst Yönetim** tarafından kullanılabilir.
  * Sarı renkli (`Gold`), yüksek dekorasyonlu liderlik tablosu sunar.
* **🌙 Gece 00:00 Otomatik Rapor:**
  * Her gece TSİ 00:00'da (21:00 UTC) günün özeti `#only-mod` kanalına otomatik iletilir ve yeni güne temiz başlanması için veriler arşivlenerek sıfırlanır.

---

## 🛠️ Komutlar

| Komut | Yetki | Açıklama |
|---|---|---|
| `/ticket-panel` | Kurucu / Yönetici | Bilet açma panelini afişiyle birlikte kanala sabitler. |
| `/ekle` | Bilet Sahibi / Yetkili | Mevcut bilet kanalına 1-3 kişi ekler. |
| `/destek-bildir` | Yetkili | Oyuncuyu resmi sarı formatla yardım bekleme odasına çağırır. |
| `/yetkili-tablo` | Kurucu / Üst Yönetim | Detaylı sarı renkli yetkili performans ve sıralama tablosunu gösterir. |
| `/roblox-bagla` | Kurucu / Üst Yönetim | Bir yetkilinin Discord hesabına Roblox kullanıcı adını tanımlar. |
| `!sync` | Kurucu / Yönetici | Slash komutlarını sunucuya anında zorla senkronize eder. |

---

## ⚙️ Yapılandırma ve Çevre Değişkenleri (Environment Variables)

Railway panelinde veya `.env` dosyasında aşağıdaki değişkenler tanımlanmalıdır:

```env
TOKEN_DESTEK=bot_tokeniniz
ERLC_API_KEY=erlc_server_key_anahtari
GUILD_ID=1529545898294509589
```

---

## 🚀 Railway Üzerinde Yayınlama

1. Bu depoyu GitHub hesabınıza push edin.
2. [Railway.app](https://railway.app) paneline gidin ve **New Project > Deploy from GitHub repo** seçeneğini seçin.
3. Proje ayarlarından **Variables** sekmesine gidin ve `TOKEN_DESTEK`, `ERLC_API_KEY`, `GUILD_ID` değişkenlerini ekleyin.
4. Bot `Dockerfile` veya `nixpacks.toml` sayesinde otomatik olarak kurulup çalışmaya başlayacaktır.