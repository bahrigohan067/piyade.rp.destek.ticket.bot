import os
import datetime
from utils.storage import load_json, save_json_atomic

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MOD_STATS_FILE = os.path.join(DATA_DIR, "mod_stats.json")
ROBLOX_MAPPING_FILE = os.path.join(DATA_DIR, "roblox_mapping.json")
DESTEK_ID_FILE = os.path.join(DATA_DIR, "destek_id.json")
HISTORY_DIR = os.path.join(DATA_DIR, "history")

GUNLUK_HEDEF_SANIYE = 3 * 3600  # 3 Saat (10800 saniye)

def ensure_data_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

def load_stats() -> dict:
    ensure_data_dirs()
    return load_json(MOD_STATS_FILE, {})

def save_stats(data: dict) -> bool:
    ensure_data_dirs()
    return save_json_atomic(MOD_STATS_FILE, data)

def update_mod_stat(mod_id: int | str, key: str, amount: int = 1) -> None:
    data = load_stats()
    mod_id = str(mod_id)
    if mod_id not in data:
        data[mod_id] = {
            "discord_time": 0,
            "game_time": 0,
            "supports": 0,
            "tickets": 0,
            "roblox_name": ""
        }
    # Eski anahtarlarla uyumluluk
    if key not in data[mod_id]:
        data[mod_id][key] = 0
    data[mod_id][key] += amount
    save_stats(data)

def add_mod_active_time(mod_id: int | str, discord_seconds: int = 0, game_seconds: int = 0) -> None:
    data = load_stats()
    mod_id = str(mod_id)
    if mod_id not in data:
        data[mod_id] = {
            "discord_time": 0,
            "game_time": 0,
            "supports": 0,
            "tickets": 0,
            "roblox_name": ""
        }
    if discord_seconds > 0:
        data[mod_id]["discord_time"] = data[mod_id].get("discord_time", 0) + discord_seconds
    if game_seconds > 0:
        data[mod_id]["game_time"] = data[mod_id].get("game_time", 0) + game_seconds
    save_stats(data)

def load_roblox_mapping() -> dict:
    ensure_data_dirs()
    return load_json(ROBLOX_MAPPING_FILE, {})

def save_roblox_mapping(data: dict) -> bool:
    ensure_data_dirs()
    return save_json_atomic(ROBLOX_MAPPING_FILE, data)

def set_roblox_name(mod_id: int | str, roblox_name: str) -> None:
    mapping = load_roblox_mapping()
    mapping[str(mod_id)] = roblox_name.strip()
    save_roblox_mapping(mapping)
    
    # Ayrıca mod_stats içine de yaz
    data = load_stats()
    if str(mod_id) in data:
        data[str(mod_id)]["roblox_name"] = roblox_name.strip()
        save_stats(data)

def get_roblox_name(mod_id: int | str) -> str:
    mapping = load_roblox_mapping()
    return mapping.get(str(mod_id), "")

def get_next_destek_id() -> str:
    ensure_data_dirs()
    data = load_json(DESTEK_ID_FILE, {"last_id": 0})
    new_id = data.get("last_id", 0) + 1
    save_json_atomic(DESTEK_ID_FILE, {"last_id": new_id})
    return f"PRP-{new_id:05d}"

def progress_bar(current: int | float, total: int | float, length: int = 10) -> str:
    """
    Kullanıcının isteği:
    Tamamlanan bölge: YEŞİL (🟩)
    Tamamlanmayan bölge: BEYAZ (⬜)
    """
    if total <= 0:
        return "⬜" * length
    ratio = min(1.0, max(0.0, current / total))
    filled = int(round(ratio * length))
    # Eğer 0'dan büyük ama 1 kutu etmiyorsa en az 1 yeşil göstermek yerine orantılı yapıyoruz
    if ratio > 0 and filled == 0:
        filled = 1
    if filled > length:
        filled = length
    return ("🟩" * filled) + ("⬜" * (length - filled))

def archive_and_reset_daily() -> dict:
    """
    Günün verilerini arşive kaydeder ve mod_stats.json dosyasını sıfırlar.
    """
    ensure_data_dirs()
    data = load_stats()
    
    # Bugünün tarihiyle arşivle
    tz_tr = datetime.timezone(datetime.timedelta(hours=3))
    now_tr = datetime.datetime.now(tz_tr)
    archive_filename = f"stats_{now_tr.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    archive_path = os.path.join(HISTORY_DIR, archive_filename)
    save_json_atomic(archive_path, data)
    
    # Sıfırla
    save_stats({})
    return data
