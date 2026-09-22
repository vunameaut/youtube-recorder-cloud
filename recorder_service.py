import os
import re
import sys
import time
import shutil
import threading
import subprocess
import uuid
from datetime import datetime
import yt_dlp
from config_service import load_config, get_cookies_path, send_telegram
from history_service import add_or_update_record
from gdrive_uploader import gdrive_uploader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

QUALITY_FORMAT_MAP = {
    "Cao nhất (Best)": "bestvideo*+bestaudio/best",
    "2160p (4K)": "bestvideo*[height<=2160]+bestaudio/best",
    "1440p (2K)": "bestvideo*[height<=1440]+bestaudio/best",
    "1080p (Full HD)": "bestvideo*[height<=1080]+bestaudio/best",
    "720p (HD)": "bestvideo*[height<=720]+bestaudio/best",
    "480p": "bestvideo*[height<=480]+bestaudio/best",
    "360p": "bestvideo*[height<=360]+bestaudio/best",
}

ANDROID_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["android"],
    }
}

def resolve_ffmpeg_path():
    candidates = [
        shutil.which("ffmpeg"),
        shutil.which("ffmpeg.exe"),
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return "ffmpeg"

def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return cleaned[:100] if cleaned else "video"

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.ffmpeg_path = resolve_ffmpeg_path()
        self.lock = threading.Lock()

    def check_info(self, url: str, quality: str = None):
        target_fmt = QUALITY_FORMAT_MAP.get(quality, "bestvideo*+bestaudio/best")
        cookies_file = get_cookies_path()

        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "format": target_fmt,
            "extractor_args": ANDROID_EXTRACTOR_ARGS,
        }
        if cookies_file:
            opts["cookiefile"] = cookies_file

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "success": True,
                    "title": info.get("title", "Unknown"),
                    "uploader": info.get("uploader", "Unknown"),
                    "is_live": info.get("is_live", False) or info.get("live_status") == "is_live",
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "resolution": info.get("resolution"),
                    "fps": info.get("fps"),
                }
        except Exception as e:
            # Thử lại không kèm cookies
            try:
                opts.pop("cookiefile", None)
                opts["extractor_args"] = ANDROID_EXTRACTOR_ARGS
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return {
                        "success": True,
                        "title": info.get("title", "Unknown"),
                        "uploader": info.get("uploader", "Unknown"),
                        "is_live": info.get("is_live", False) or info.get("live_status") == "is_live",
                        "duration": info.get("duration"),
                        "thumbnail": info.get("thumbnail"),
                        "resolution": info.get("resolution"),
                        "fps": info.get("fps"),
                    }
            except Exception as e2:
                print(f"[RECORDER] Warning check_info fallback: {e2}", flush=True)
                return {
                    "success": True,
                    "title": "YouTube Video / Livestream",
                    "uploader": "YouTube",
                    "is_live": True,
                    "notice": str(e2)
                }

    def find_and_merge(self, base_output: str, task: dict):
        folder = os.path.dirname(base_output)
        base_name = os.path.splitext(os.path.basename(base_output))[0]
        if not os.path.exists(folder):
            return None

        if os.path.exists(base_output) and os.path.getsize(base_output) > 1024 * 1024:
            return base_output

        video_file = None
        audio_file = None

        for f in os.listdir(folder):
            full_path = os.path.join(folder, f)
            if ".part" in f or ".ytdl" in f or f.endswith("_FINAL.mp4"):
                continue

            if f.startswith(base_name) and any(f.endswith(ext) for ext in [".mp4", ".m4a", ".webm", ".mkv"]):
                try:
                    size_mb = os.path.getsize(full_path) / (1024**2)
                    if ".f" in f:
                        match = re.search(r"\.f(\d+)\.", f)
                        if match:
                            fmt_code = int(match.group(1))
                            if (fmt_code >= 135 and fmt_code not in [139, 140, 249, 250, 251]) or size_mb > 50:
                                video_file = full_path
                            else:
                                audio_file = full_path
                    else:
                        if size_mb > 50 and not video_file:
                            video_file = full_path
                        elif not audio_file:
                            audio_file = full_path
                except Exception:
                    pass

        if video_file and audio_file:
            task["status_text"] = "🎬 Đang ghép Video + Audio qua FFmpeg..."
            print(f"[RECORDER] Ghép file FFmpeg: {video_file} + {audio_file}", flush=True)
            final_file = base_output.replace(".mp4", "_FINAL.mp4")
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", video_file,
                "-i", audio_file,
                "-c", "copy",
                final_file,
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0 and os.path.exists(final_file):
                    try:
                        os.remove(video_file)
                        os.remove(audio_file)
                    except Exception:
                        pass
                    return final_file
                else:
                    return video_file
            except Exception as e:
                print(f"[RECORDER] FFmpeg error: {e}", flush=True)
                return video_file

        return video_file or audio_file or (base_output if os.path.exists(base_output) else None)

    def _worker(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return

        url = task["url"]
        quality = task["quality"]
        cookies_file = get_cookies_path()

        print(f"\n[RECORDER] ========== BẮT ĐẦU TÁC VỤ {task_id} ==========", flush=True)
        print(f"[RECORDER] URL: {url} | Chất lượng: {quality}", flush=True)

        task["status"] = "downloading"
        task["status_text"] = "Đang kết nối luồng YouTube..."

        try:
            info_res = self.check_info(url, quality=quality)
            if info_res.get("success"):
                task["title"] = info_res.get("title", task["title"])
                task["uploader"] = info_res.get("uploader", task["uploader"])
                task["thumbnail"] = info_res.get("thumbnail", task["thumbnail"])
                task["is_live"] = info_res.get("is_live", False)

            print(f"[RECORDER] Đã xác định video: {task['title']} (Kênh: {task['uploader']})", flush=True)
            send_telegram(f"🚀 [CLOUD] Bắt đầu tải video/livestream:\n🎬 {task['title']}\n📺 {url}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = sanitize_filename(task["title"])
            base_output = os.path.join(TEMP_DIR, f"{safe_title}_{timestamp}.mp4")
            task["current_output_file"] = base_output

            target_fmt = QUALITY_FORMAT_MAP.get(quality, "bestvideo*+bestaudio/best")

            def progress_hook(d):
                if task.get("should_stop"):
                    raise yt_dlp.utils.DownloadCancelled("Người dùng yêu cầu dừng.")

                st = d.get("status")
                if st == "downloading":
                    dl_bytes = d.get("downloaded_bytes", 0)
                    total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                    spd = d.get("speed") or 0

                    speed_str = f"{spd / (1024*1024):.2f} MB/s" if spd else "Đang tính..."
                    dl_str = f"{dl_bytes / (1024*1024):.1f} MB"
                    if total_bytes:
                        pct = (dl_bytes / total_bytes) * 100
                        tot_str = f"{total_bytes / (1024*1024):.1f} MB"
                        status_text = f"Đang tải: {dl_str} / {tot_str} ({pct:.1f}%)"
                    else:
                        pct = -1
                        frag = d.get("fragment_index")
                        status_text = f"Đang ghi Live: #{frag} ({dl_str})" if frag else f"Đang ghi Live: {dl_str}"

                    task["progress_percent"] = round(pct, 1)
                    task["speed_str"] = speed_str
                    task["downloaded_str"] = dl_str
                    task["total_str"] = f"{total_bytes / (1024*1024):.1f} MB" if total_bytes else "Chưa xác định"
                    task["status_text"] = status_text

            # Cấu hình tải cơ bản
            ydl_opts = {
                "outtmpl": base_output,
                "format": target_fmt,
                "format_sort": ["res", "fps", "tbr", "vbr", "size"],
                "merge_output_format": "mp4",
                "continuedl": True,
                "live_from_start": True,
                "retries": 30,
                "fragment_retries": 30,
                "skip_unavailable_fragments": True,
                "quiet": False,
                "progress_hooks": [progress_hook],
                "extractor_args": ANDROID_EXTRACTOR_ARGS,
            }

            if cookies_file:
                ydl_opts["cookiefile"] = cookies_file

            download_success = False

            # Lần thử 1: Có live_from_start
            try:
                print("[RECORDER] Thử tải luồng (live_from_start=True)...", flush=True)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                download_success = True
            except yt_dlp.utils.DownloadCancelled:
                task["status_text"] = "Đã dừng tải theo yêu cầu."
            except Exception as e1:
                print(f"[RECORDER] live_from_start không hỗ trợ ({e1}), chuyển sang live realtime...", flush=True)
                task["status_text"] = "⚠️ Đang chuyển sang chế độ ghi Live realtime..."
                # Lần thử 2: Bỏ live_from_start (hỗ trợ 100% mọi livestream)
                ydl_opts["live_from_start"] = False
                ydl_opts.pop("cookiefile", None)
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        ydl2.download([url])
                    download_success = True
                except yt_dlp.utils.DownloadCancelled:
                    task["status_text"] = "Đã dừng tải theo yêu cầu."
                except Exception as e2:
                    print(f"[RECORDER] Lỗi tải cuối cùng: {e2}", flush=True)
                    task["error"] = str(e2)

            task["status"] = "merging"
            task["status_text"] = "Đang kiểm tra và ghép file MP4..."
            print("[RECORDER] Đang tìm và ghép file...", flush=True)
            final_file = self.find_and_merge(base_output, task)

            if final_file and os.path.exists(final_file) and os.path.getsize(final_file) > 0:
                size_bytes = os.path.getsize(final_file)
                size_gb = size_bytes / (1024**3)
                size_mb = size_bytes / (1024**2)
                size_str = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_mb:.1f} MB"
                task["file_size_str"] = size_str

                filename = os.path.basename(final_file)
                task["download_url"] = f"/api/files/{filename}"
                print(f"[RECORDER] Đã có file video hoàn chỉnh: {final_file} ({size_str})", flush=True)

                # Bước ĐẨY LÊN GOOGLE DRIVE
                task["status"] = "uploading"
                task["status_text"] = "☁️ Đang đẩy video lên Google Drive..."

                def upload_progress(pct, msg):
                    task["status_text"] = f"☁️ {msg}"
                    task["progress_percent"] = pct

                upload_res = gdrive_uploader.upload_file(final_file, progress_callback=upload_progress)

                if upload_res.get("success"):
                    task["status"] = "completed"
                    task["progress_percent"] = 100
                    web_link = upload_res.get("web_link", "")
                    task["web_link"] = web_link
                    task["status_text"] = f"🎉 Hoàn tất! Đã lưu vào Google Drive ({size_str})"

                    send_telegram(
                        f"🎉 [CLOUD] TẢI & LƯU GOOGLE DRIVE THÀNH CÔNG!\n🎬 {task['title']}\n💾 Dung lượng: {size_str}\n🔗 Link Drive: {web_link}"
                    )

                    try:
                        os.remove(final_file)
                    except Exception:
                        pass
                else:
                    task["status"] = "completed"
                    task["status_text"] = f"🎉 Đã tải hoàn tất ({size_str})! (Bấm nút Tải về để tải về máy)"
                    send_telegram(f"🎉 [CLOUD] Đã tải hoàn tất video:\n🎬 {task['title']}\n💾 Dung lượng: {size_str}")
            else:
                task["status"] = "error"
                err_detail = task.get("error") or "Không tạo được file sau khi ghi"
                task["status_text"] = f"Lỗi: {err_detail}"
                print(f"[RECORDER] Thất bại: {err_detail}", flush=True)

        except Exception as ex:
            task["status"] = "error"
            task["error"] = str(ex)
            task["status_text"] = f"Lỗi: {ex}"
            print(f"[RECORDER] Exception ngoài cùng: {ex}", flush=True)
            send_telegram(f"❌ [CLOUD] Lỗi tải: {ex}")

        finally:
            task["finished_at"] = datetime.now().isoformat()
            print(f"[RECORDER] ========== KẾT THÚC TÁC VỤ {task_id} ==========\n", flush=True)
            add_or_update_record({
                "id": task["id"],
                "url": task["url"],
                "title": task["title"],
                "uploader": task["uploader"],
                "thumbnail": task["thumbnail"],
                "quality": task["quality"],
                "status": task["status"],
                "status_text": task["status_text"],
                "created_at": task["created_at"],
                "finished_at": task["finished_at"],
                "web_link": task.get("web_link", ""),
                "download_url": task.get("download_url", ""),
                "file_size_str": task.get("file_size_str", "0 MB"),
                "error": task.get("error")
            })

    def start_download(self, url: str, quality: str = None):
        cfg = load_config()
        if not quality:
            quality = cfg.get("default_quality", "1080p (Full HD)")

        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "url": url,
            "title": "Đang nhận diện...",
            "uploader": "",
            "thumbnail": "",
            "is_live": False,
            "quality": quality,
            "status": "pending",
            "status_text": "Đang khởi tạo trên Cloud...",
            "progress_percent": 0,
            "speed_str": "0 MB/s",
            "downloaded_str": "0 MB",
            "total_str": "Chưa xác định",
            "created_at": datetime.now().isoformat(),
            "finished_at": None,
            "should_stop": False,
            "web_link": "",
            "download_url": "",
            "error": None,
        }

        with self.lock:
            self.tasks[task_id] = task

        thread = threading.Thread(target=self._worker, args=(task_id,), daemon=True)
        task["thread"] = thread
        thread.start()

        return task_id, task

    def stop_download(self, task_id: str):
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False, "Không tìm thấy tác vụ!"
            task["should_stop"] = True
            task["status_text"] = "🛑 Đang dừng và lưu dữ liệu..."
            return True, "Đã gửi tín hiệu dừng!"

    def get_all_tasks(self):
        with self.lock:
            res = []
            for t in self.tasks.values():
                c = t.copy()
                c.pop("thread", None)
                res.append(c)
            return sorted(res, key=lambda x: x.get("created_at", ""), reverse=True)

task_manager = TaskManager()
