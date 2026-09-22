import os
import shutil
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config_service import load_config, save_config, get_cookies_path, save_cookies, get_cookies_content, send_telegram
from history_service import load_history, delete_record
from recorder_service import task_manager, QUALITY_FORMAT_MAP, TEMP_DIR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="YouTube Recorder Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CheckUrlRequest(BaseModel):
    url: str
    quality: Optional[str] = None

class DownloadRequest(BaseModel):
    url: str
    quality: Optional[str] = None

class StopRequest(BaseModel):
    task_id: str

class ConfigUpdateRequest(BaseModel):
    default_quality: Optional[str] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    gdrive_folder_id: Optional[str] = None

class CookiesUpdateRequest(BaseModel):
    content: str

@app.get("/")
def read_root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "YouTube Cloud Recorder Server is running!"}

@app.get("/api/info")
def get_info():
    cfg = load_config()
    is_colab = os.path.exists("/content/drive/MyDrive")
    has_sa = os.path.exists("service_account.json") or bool(os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON"))
    
    disk = shutil.disk_usage("/")
    free_gb = round(disk.free / (1024**3), 1)

    return {
        "server_status": "online",
        "cloud_mode": "Colab (Direct Drive)" if is_colab else ("Render / Cloud (Drive API)" if has_sa else "Render Cloud Ready"),
        "free_gb": free_gb,
        "has_cookies": get_cookies_path() is not None,
        "available_qualities": list(QUALITY_FORMAT_MAP.keys()),
    }

@app.post("/api/check")
def check_url(req: CheckUrlRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập URL!")
    return task_manager.check_info(req.url.strip(), quality=req.quality)

@app.post("/api/download")
def start_download(req: DownloadRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập URL!")
    task_id, task = task_manager.start_download(url=req.url.strip(), quality=req.quality)
    return {
        "success": True,
        "message": "Đã nhận lệnh tải ngầm trên Cloud! Bạn có thể tắt máy / tắt web thoải mái.",
        "task_id": task_id,
        "task": {k: v for k, v in task.items() if k != "thread"}
    }

@app.post("/api/stop")
def stop_download(req: StopRequest):
    success, msg = task_manager.stop_download(req.task_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.get("/api/tasks")
def get_tasks():
    return task_manager.get_all_tasks()

@app.get("/api/history")
def get_history():
    return load_history()

@app.delete("/api/history/{rec_id}")
def delete_history_item(rec_id: str):
    delete_record(rec_id)
    return {"success": True}

@app.get("/api/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="File không tồn tại hoặc đã được chuyển lên Drive")

@app.get("/api/config")
def get_config_endpoint():
    cfg = load_config()
    cfg["has_cookies"] = get_cookies_path() is not None
    return cfg

@app.post("/api/config")
def update_config_endpoint(req: ConfigUpdateRequest):
    cfg = load_config()
    if req.default_quality is not None:
        cfg["default_quality"] = req.default_quality
    if req.telegram_token is not None:
        cfg["telegram_token"] = req.telegram_token.strip()
    if req.telegram_chat_id is not None:
        cfg["telegram_chat_id"] = req.telegram_chat_id.strip()
    if req.gdrive_folder_id is not None:
        cfg["gdrive_folder_id"] = req.gdrive_folder_id.strip()
    save_config(cfg)
    return {"success": True, "config": cfg}

@app.post("/api/test-telegram")
def test_telegram_endpoint():
    ok, msg = send_telegram("🔔 Tin nhắn thử nghiệm từ Cloud YouTube Recorder!")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.get("/api/cookies")
def get_cookies_endpoint():
    return {"content": get_cookies_content()}

@app.post("/api/cookies")
def save_cookies_endpoint(req: CookiesUpdateRequest):
    ok = save_cookies(req.content)
    if not ok:
        raise HTTPException(status_code=500, detail="Không thể lưu cookies!")
    return {"success": True, "message": "Đã lưu cookies thành công!"}

@app.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            tasks = task_manager.get_all_tasks()
            await websocket.send_json(tasks)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
