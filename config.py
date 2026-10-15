import os

# Eğer .env dosyası varsa otomatik oku (lokal testler için kolaylık sağlar)
env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Token ve API Anahtarları
TOKEN = os.getenv("TOKEN_DESTEK") or os.getenv("TOKEN")
ERLC_API_KEY = os.getenv("ERLC_API_KEY", "").strip()
GUILD_ID = int(os.getenv("GUILD_ID", "1529545898294509589"))

# Kanal ID'leri
TICKET_KANAL_ID = 1534770099179884564
BILET_LOG_KANAL_ID = 1532828404347437287  # #only-mod kanalı
ONLY_MOD_KANALI = 1532828404347437287     # Günlük rapor & yetkili log kanalı
YARDIM_BEKLEME_VC_ID = 1532829788824404274
YARDIM_VC_ID = 1532829837150916719
ONEMLI_LOG_KANALI = 1532829734742786168   # Destek bekleme çağrılarının düştüğü kanal
DESTEK_CAGRI_KANALI = 1552041858530672670 # /destek-bildir duyuru kanalı

# Rol ID'leri
KURUCU_ROL_ID = 1529546007635824680
UST_YONETIM_ROL_ID = 1539167256246747186
YONETICI_ROL_ID = 1534798061845483694
YONETIM_EKIBI_ROL_ID = 1537934087166369812
SENIOR_STAFF_ROL_ID = 1551241753137254611
STAFF_ROL_ID = 1551241634094645288
TRIAL_STAFF_ROL_ID = 1551241468985737376

DESTEK_BEKLEME_YETKILISI_ROL = 1553473785527537765
TICKET_YETKILISI_ROL = 1553333289798869032

# Sıralı Yetkili Rütbeleri (Rol ID -> İsim)
ADMIN_ROLES = {
    KURUCU_ROL_ID: "Kurucu",
    UST_YONETIM_ROL_ID: "Üst Yönetim",
    YONETICI_ROL_ID: "Yönetici",
    YONETIM_EKIBI_ROL_ID: "Yönetim Ekibi",
    SENIOR_STAFF_ROL_ID: "Senior Staff",
    STAFF_ROL_ID: "Staff",
    TRIAL_STAFF_ROL_ID: "Trial Staff",
    DESTEK_BEKLEME_YETKILISI_ROL: "Destek Bekleme Yetkilisi",
    TICKET_YETKILISI_ROL: "Ticket Yetkilisi"
}

# Tüm Yetkili Rol ID'leri Listesi
YETKILI_ROL_IDLERI = list(ADMIN_ROLES.keys())

# Hedefler
GUNLUK_HEDEF_SANIYE = 3 * 3600  # 3 saat hedef
