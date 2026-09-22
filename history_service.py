import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def add_or_update_record(record: dict):
    history = load_history()
    rec_id = record.get("id")
    found = False
    for i, item in enumerate(history):
        if item.get("id") == rec_id:
            history[i] = {**item, **record}
            found = True
            break
    if not found:
        history.insert(0, record)
    save_history(history)

def delete_record(rec_id: str):
    history = load_history()
    history = [item for item in history if item.get("id") != rec_id]
    save_history(history)
