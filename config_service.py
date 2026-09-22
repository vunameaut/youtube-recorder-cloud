import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

DEFAULT_CONFIG = {
    "default_quality": "1080p (Full HD)",
    "telegram_token": os.environ.get("TELEGRAM_TOKEN", "8598737736:AAGBM10Ar9E9TEXtG-obimjEBZeihABdOb0"),
    "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", "5944020825"),
    "gdrive_folder_id": os.environ.get("GDRIVE_FOLDER_ID", "")
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def get_cookies_path():
    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        return COOKIES_FILE
    return None

def save_cookies(content: str):
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(content.strip())
        return True
    except Exception:
        return False

def get_cookies_content():
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    return ""

def send_telegram(msg: str):
    cfg = load_config()
    token = cfg.get("telegram_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    if not token or not chat_id:
        return False, "Chưa cấu hình Telegram"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": msg}
        res = requests.post(url, data=data, timeout=10)
        return res.status_code == 200, res.text
    except Exception as e:
        return False, str(e)
