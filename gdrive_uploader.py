import os
import sys
import time
import json
import shutil

class GoogleDriveUploader:
    def __init__(self, folder_id=None, service_account_info=None):
        self.folder_id = folder_id or os.environ.get("GDRIVE_FOLDER_ID", "")
        self.service_account_info = service_account_info
        self.service = None
        self._init_client()

    def _init_client(self):
        # 1. Check if mounted as local drive (Google Colab)
        if os.path.exists("/content/drive/MyDrive"):
            print("Detected Google Colab mounted drive at /content/drive/MyDrive")
            return

        # 2. Check Service Account from file or environment variable
        sa_path = os.environ.get("GDRIVE_SERVICE_ACCOUNT_PATH", "service_account.json")
        sa_json_env = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON", "")

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds = None
            if os.path.exists(sa_path):
                creds = service_account.Credentials.from_service_account_file(
                    sa_path, scopes=["https://www.googleapis.com/auth/drive"]
                )
            elif sa_json_env:
                info = json.loads(sa_json_env)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/drive"]
                )
            elif self.service_account_info:
                creds = service_account.Credentials.from_service_account_info(
                    self.service_account_info, scopes=["https://www.googleapis.com/auth/drive"]
                )

            if creds:
                self.service = build("drive", "v3", credentials=creds)
                print("Google Drive API initialized successfully.")
        except Exception as e:
            print(f"Warning: Google Drive API client could not be initialized: {e}")

    def upload_file(self, local_path, custom_folder_id=None, progress_callback=None):
        """
        Uploads local video to Google Drive.
        Returns dict: {"success": bool, "file_id": str, "web_link": str, "dest_path": str, "error": str}
        """
        if not os.path.exists(local_path):
            return {"success": False, "error": "File local khong ton tai"}

        filename = os.path.basename(local_path)
        target_folder = custom_folder_id or self.folder_id

        # Mode A: Google Colab direct copy (instant, 0 network upload needed)
        colab_drive_base = "/content/drive/MyDrive/YT_Recordings"
        if os.path.exists("/content/drive/MyDrive"):
            try:
                today_str = time.strftime("%Y-%m-%d")
                dest_dir = os.path.join(colab_drive_base, today_str)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, filename)

                if callable(progress_callback):
                    progress_callback(50, "Dang sao chep vao Google Drive...")

                shutil.copy2(local_path, dest_path)
                return {
                    "success": True,
                    "file_id": filename,
                    "web_link": f"Google Drive: YT_Recordings/{today_str}/{filename}",
                    "dest_path": dest_path
                }
            except Exception as e:
                return {"success": False, "error": f"Loi copy vao Colab Drive: {e}"}

        # Mode B: Google Drive API (Hugging Face Spaces / Docker / Cloud Server)
        if not self.service:
            return {
                "success": False,
                "error": "Chua cau hinh Google Drive API (thieu file service_account.json hoac bien moi truong)"
            }

        try:
            from googleapiclient.http import MediaFileUpload

            file_metadata = {"name": filename}
            if target_folder:
                file_metadata["parents"] = [target_folder]

            media = MediaFileUpload(
                local_path,
                mimetype="video/mp4",
                chunksize=20 * 1024 * 1024,  # 20MB chunks for smooth upload
                resumable=True
            )

            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink, size"
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and callable(progress_callback):
                    pct = int(status.progress() * 100)
                    progress_callback(pct, f"Dang upload len Google Drive: {pct}%")

            file_id = response.get("id")
            web_link = response.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

            return {
                "success": True,
                "file_id": file_id,
                "web_link": web_link,
                "dest_path": f"Google Drive ({file_id})"
            }

        except Exception as e:
            return {"success": False, "error": f"Loi upload Google Drive API: {str(e)}"}

gdrive_uploader = GoogleDriveUploader()
