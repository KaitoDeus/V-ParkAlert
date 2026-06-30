# src/services/camera_service.py
import datetime
import time
import urllib.request
import re
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class ICameraService(ABC):
    @abstractmethod
    def get_youtube_hls_url(self, youtube_id: str, camera_id: str = None) -> str:
        pass

    @abstractmethod
    def report_stream_status(self, camera_id: str, success: bool, is_youtube: bool = True):
        pass

    @abstractmethod
    def get_cameras(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def toggle_camera(self, triggered_by: str) -> bool:
        pass

    @abstractmethod
    def set_camera_active_state(self, camera_id: str, is_active: bool, triggered_by: str) -> bool:
        pass

    @abstractmethod
    def log(self, message: str):
        pass

class CameraService(ICameraService):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CameraService, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_camera()
        return cls._instance

    def _init_camera(self):
        self.is_active = True
        self.camera_id = "1"
        self.latitude = 10.7745
        self.longitude = 106.7025
        self.logs: List[str] = [
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Camera stream connected.",
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Monitoring ROI region initialized.",
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] System initialized."
        ]
        self.hls_cache = {}  # Cache map: youtube_id -> (hls_url, expire_timestamp)
        self.stream_status = {}  # camera_id -> {"failures": 0, "use_fallback": False, "fallback_until": 0}
        self.cameras = [
            {
                "id": "1",
                "name": "Camera cổng trường Nguyễn Huệ Đà Nẵng",
                "latitude": 10.7745,
                "longitude": 106.7025,
                "youtube_id": "sJvEFrG0wq0",
                "is_active": True
            },
            {
                "id": "2",
                "name": "Camera cổng Sau bệnh viện C Đà Nẵng",
                "latitude": 10.7760,
                "longitude": 106.7030,
                "youtube_id": "oif_zZFIfB4",
                "is_active": True
            },
            {
                "id": "3",
                "name": "Trường Tiểu Học Lý Tự Trọng - PTZ",
                "latitude": 10.7735,
                "longitude": 106.7015,
                "youtube_id": "1EamsYw_Xyo",
                "is_active": True
            },
            {
                "id": "4",
                "name": "TRƯỜNG LÝ TỰ TRỌNG - HƯỚNG KS SÔNG HÀN - 12 Lý Tự Trọng",
                "latitude": 10.7750,
                "longitude": 106.7040,
                "youtube_id": "NeJGBQAY-bE",
                "is_active": True
            }
        ]

    def report_stream_status(self, camera_id: str, success: bool, is_youtube: bool = True, error_type: str = None, error_detail: str = None):
        now = time.time()
        status = self.stream_status.setdefault(camera_id, {
            "failures": 0, 
            "use_fallback": False, 
            "fallback_until": 0,
            "probing": False,
            "last_error_type": None,
            "last_error_detail": None,
            "last_error_time": None,
            "last_successful_fetch_time": None
        })
        
        # Ensure all keys exist
        for key in ["probing", "last_error_type", "last_error_detail", "last_error_time", "last_successful_fetch_time"]:
            if key not in status:
                status[key] = None if "time" in key or "type" in key or "detail" in key else False

        if success:
            if is_youtube:
                if status["use_fallback"]:
                    status["use_fallback"] = False
                    status["failures"] = 0
                    status["probing"] = False
                    self.log(f"Luồng camera {camera_id} đã phục hồi và hoạt động bình thường.")
                else:
                    status["failures"] = 0
            status["last_successful_fetch_time"] = now
            status["last_error_type"] = None
            status["last_error_detail"] = None
        else:
            status["last_error_type"] = error_type
            status["last_error_detail"] = error_detail
            status["last_error_time"] = now
            
            if is_youtube:
                if status["use_fallback"]:
                    # We were probing, but it failed. Extend fallback immediately.
                    status["fallback_until"] = now + 300
                    status["probing"] = False
                    self.log(f"Thử phục hồi luồng YouTube cho camera {camera_id} thất bại ({error_type}). Tiếp tục dùng luồng dự phòng 5 phút.")
                else:
                    status["failures"] += 1
                    if status["failures"] >= 3:
                        status["use_fallback"] = True
                        status["fallback_until"] = now + 300
                        self.log(f"CẢNH BÁO: Luồng camera {camera_id} lỗi liên tục ({error_type}). Tự động chuyển sang luồng dự phòng trong 5 phút.")

    def get_youtube_hls_url(self, youtube_id: str, camera_id: str = None) -> str:
        now = time.time()
        
        # Predefined fallback maps in case parsing fails or streams are offline
        fallback_map = {
            "sJvEFrG0wq0": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",  # Big Buck Bunny (Cổng trường Nguyễn Huệ)
            "oif_zZFIfB4": "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",  # Sintel (Cổng sau Bệnh viện C)
            "1EamsYw_Xyo": "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",  # NASA TV (Trường tiểu học Lý Tự Trọng)
            "NeJGBQAY-bE": "https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_adv_example_hevc/master.m3u8"  # Bipbop (Lý Tự Trọng - Sông Hàn)
        }
        default_fallback = fallback_map.get(youtube_id, "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")

        # Check if camera is forced to fallback
        if camera_id:
            status = self.stream_status.setdefault(camera_id, {
                "failures": 0, 
                "use_fallback": False, 
                "fallback_until": 0,
                "probing": False,
                "last_error_type": None,
                "last_error_detail": None,
                "last_error_time": None,
                "last_successful_fetch_time": None
            })
            for key in ["probing", "last_error_type", "last_error_detail", "last_error_time", "last_successful_fetch_time"]:
                if key not in status:
                    status[key] = None if "time" in key or "type" in key or "detail" in key else False

            if status["use_fallback"]:
                if now < status["fallback_until"]:
                    return default_fallback
                else:
                    if not status.get("probing", False):
                        status["probing"] = True
                        self.log(f"Thử kết nối lại luồng YouTube cho camera {camera_id}...")

        # Check cache (expire after 10 minutes)
        if youtube_id in self.hls_cache:
            hls_url, ts = self.hls_cache[youtube_id]
            if now - ts < 600:
                return hls_url

        url = f"https://www.youtube.com/watch?v={youtube_id}"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', html)
            if not match:
                match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?})\s*</script>', html)
            if not match:
                match = re.search(r'var ytInitialPlayerResponse\s*=\s*({.+?});', html)
            
            if match:
                data = json.loads(match.group(1))
                streaming_data = data.get("streamingData", {})
                hls_manifest_url = streaming_data.get("hlsManifestUrl")
                if hls_manifest_url:
                    self.hls_cache[youtube_id] = (hls_manifest_url, now)
                    return hls_manifest_url
        except Exception as e:
            print(f"Warning: YouTube parsing failed ({e}). Falling back to stable test stream: {default_fallback}")
            return default_fallback
        
        print(f"Warning: YouTube stream manifest not found. Falling back to stable test stream: {default_fallback}")
        return default_fallback

    def get_cameras(self) -> List[Dict[str, Any]]:
        return self.cameras

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_active": self.is_active,
            "camera_id": self.camera_id,
            "location": {"lat": self.latitude, "lon": self.longitude},
            "logs": self.logs
        }

    def set_camera_active_state(self, camera_id: str, is_active: bool, triggered_by: str) -> bool:
        for cam in self.cameras:
            if cam["id"] == str(camera_id):
                cam["is_active"] = is_active
                status_str = "KÍCH HOẠT" if is_active else "TẮT"
                self.log(f"Camera {cam['name']} đã {status_str} bởi {triggered_by}.")
                if str(camera_id) == "1":
                    self.is_active = is_active
                return is_active
        return False

    def toggle_camera(self, triggered_by: str) -> bool:
        self.is_active = not self.is_active
        for cam in self.cameras:
            cam["is_active"] = self.is_active
        status_str = "KÍCH HOẠT" if self.is_active else "TẮT"
        self.log(f"Tất cả camera giám sát đã {status_str} bởi {triggered_by}.")
        return self.is_active

    def log(self, message: str):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.logs.insert(0, f"[{timestamp}] {message}")
        # Keep logs at a reasonable size
        if len(self.logs) > 100:
            self.logs.pop()
