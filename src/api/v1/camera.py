# src/api/v1/camera.py
import base64
import urllib.request
import urllib.parse
import urllib.error
import re
import socket
import contextvars
import contextlib
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from src.models import User
from src.schemas import ViolationReportResponse
from src.services.camera_service import CameraService
from src.services.violation_service import ViolationService
from src.api.deps import (
    get_camera_service, 
    get_violation_service, 
    get_current_user, 
    require_role,
    require_role_from_token_or_param
)

# Context-local variable to track requested socket family for DNS resolution
target_family_var = contextvars.ContextVar('target_family', default=socket.AF_UNSPEC)
orig_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    target_family = target_family_var.get()
    if target_family != socket.AF_UNSPEC:
        family = target_family
    return orig_getaddrinfo(host, port, family, type, proto, flags)

# Install socket.getaddrinfo monkeypatch
socket.getaddrinfo = custom_getaddrinfo

@contextlib.contextmanager
def socket_family_from_url(url: str):
    # Parse IP parameter from URL (supporting /ip/... or /mip/...)
    ip_match = re.search(r'/(?:m?ip)/([^/]+)/', url)
    if ip_match:
        ip_val = urllib.parse.unquote(ip_match.group(1))
        if ":" in ip_val:
            token = target_family_var.set(socket.AF_INET6)
        else:
            token = target_family_var.set(socket.AF_INET)
    else:
        token = target_family_var.set(socket.AF_UNSPEC)
    try:
        yield
    finally:
        target_family_var.reset(token)

router = APIRouter(prefix="/camera", tags=["camera"])

# Helper base64 encoding/decoding
def encode_url(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode('utf-8')).decode('utf-8')

def decode_url(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded.encode('utf-8')).decode('utf-8')

def classify_error(url: str, e: Exception) -> tuple[str, str]:
    is_yt = "googlevideo.com" in url or "youtube.com" in url
    error_detail = str(e)
    if isinstance(e, urllib.error.HTTPError):
        if is_yt:
            error_type = f"youtube_origin_http_{e.code}"
            error_detail = f"YouTube origin returned HTTP {e.code}: {e.reason}"
        else:
            error_type = f"fallback_origin_http_{e.code}"
            error_detail = f"Fallback origin returned HTTP {e.code}: {e.reason}"
    elif isinstance(e, urllib.error.URLError):
        if isinstance(e.reason, socket.timeout):
            error_type = "network_timeout"
            error_detail = f"Timeout: {e.reason}"
        else:
            error_type = "network_url_error"
            error_detail = f"Network error: {e.reason}"
    elif isinstance(e, socket.timeout):
        error_type = "network_timeout"
        error_detail = "Socket timeout"
    else:
        error_type = "general_fetch_error"
        error_detail = f"Fetch failure: {str(e)}"
    return error_type, error_detail

from pydantic import BaseModel

class CameraControlRequest(BaseModel):
    is_active: bool

class CameraSimulationRequest(BaseModel):
    camera_id: int
    violation_type: str

@router.get("/status")
def get_camera_status(
    current_user: User = Depends(get_current_user),
    camera_service: CameraService = Depends(get_camera_service)
):
    return camera_service.get_cameras()

@router.get("/list")
def list_cameras(
    current_user: User = Depends(require_role(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    return camera_service.get_cameras()

@router.post("/toggle")
def toggle_camera(
    current_user: User = Depends(require_role(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    is_active = camera_service.toggle_camera(triggered_by=current_user.full_name)
    return {
        "message": f"Camera is now {'active' if is_active else 'inactive'}",
        "is_active": is_active
    }

@router.post("/{camera_id}/control")
def control_camera(
    camera_id: str,
    req: CameraControlRequest,
    current_user: User = Depends(require_role(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    is_active = camera_service.set_camera_active_state(camera_id, req.is_active, current_user.full_name)
    return {
        "message": f"Camera {camera_id} is now {'active' if is_active else 'inactive'}",
        "is_active": is_active
    }

@router.post("/simulate", response_model=ViolationReportResponse)
def simulate_camera_violation(
    req: CameraSimulationRequest,
    current_user: User = Depends(require_role(["authority", "ai_system"])),
    violation_service: ViolationService = Depends(get_violation_service)
):
    return violation_service.simulate_ai_violation(camera_id=req.camera_id, violation_type=req.violation_type)

@router.post("/simulate-violation", response_model=ViolationReportResponse)
def simulate_violation(
    current_user: User = Depends(require_role(["authority", "ai_system"])),
    violation_service: ViolationService = Depends(get_violation_service)
):
    return violation_service.simulate_ai_violation()

# Secure Stream Proxying Endpoints

@router.get("/stream/{camera_id}/index.m3u8")
def get_master_playlist(
    camera_id: str,
    token: str = Query(None),
    current_user: User = Depends(require_role_from_token_or_param(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    # 1. Resolve camera_id to youtube_id
    cameras = camera_service.get_cameras()
    camera = next((c for c in cameras if c["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị camera.")
    
    youtube_id = camera["youtube_id"]
    
    # 2. Get the HLS URL from YouTube
    hls_url = camera_service.get_youtube_hls_url(youtube_id, camera_id)
    
    # 3. Fetch HLS master playlist content
    try:
        with socket_family_from_url(hls_url):
            req = urllib.request.Request(
                hls_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
    except Exception as e:
        err_type, err_msg = classify_error(hls_url, e)
        print(f"WARNING: Failed to fetch master playlist for {camera_id}: {err_msg}")
        # If it failed and we weren't already using fallback, report failure and switch immediately
        is_yt = "googlevideo.com" in hls_url or "youtube.com" in hls_url
        camera_service.report_stream_status(camera_id, success=False, is_youtube=is_yt, error_type=err_type, error_detail=err_msg)
        fallback_url = camera_service.get_youtube_hls_url(youtube_id, camera_id)
        if fallback_url != hls_url:
            print(f"INFO: Retrying master playlist fetch with fallback stream for {camera_id}")
            try:
                with socket_family_from_url(fallback_url):
                    req = urllib.request.Request(
                        fallback_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        content = response.read().decode('utf-8')
                        hls_url = fallback_url
            except Exception as e2:
                err_type2, err_msg2 = classify_error(fallback_url, e2)
                camera_service.report_stream_status(camera_id, success=False, is_youtube=False, error_type=err_type2, error_detail=err_msg2)
                raise HTTPException(status_code=500, detail=f"Không thể truy cập luồng gốc và luồng dự phòng: {err_msg2}")
        else:
            raise HTTPException(status_code=500, detail=f"Không thể truy cập dữ liệu luồng gốc: {err_msg}")
    
    # 4. Parse content and rewrite sub-playlist URLs
    lines = content.split('\n')
    rewritten_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            abs_url = urllib.parse.urljoin(hls_url, stripped)
            encoded_url = encode_url(abs_url)
            rewritten_url = f"/api/v1/camera/stream/sub-playlist?url={encoded_url}&camera_id={camera_id}"
            if token:
                rewritten_url += f"&token={token}"
            rewritten_lines.append(rewritten_url)
        else:
            rewritten_lines.append(line)
            
    rewritten_content = "\n".join(rewritten_lines)
    return Response(content=rewritten_content, media_type="application/vnd.apple.mpegurl")

@router.get("/stream/sub-playlist")
def get_sub_playlist(
    url: str = Query(...),
    camera_id: str = Query(None),
    token: str = Query(None),
    current_user: User = Depends(require_role_from_token_or_param(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    try:
        decoded_url = decode_url(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Tham số URL không hợp lệ.")
        
    try:
        with socket_family_from_url(decoded_url):
            req = urllib.request.Request(
                decoded_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
    except Exception as e:
        err_type, err_msg = classify_error(decoded_url, e)
        print(f"WARNING: Failed to fetch sub-playlist for {camera_id}: {err_msg}")
        if camera_id:
            is_yt = "googlevideo.com" in decoded_url or "youtube.com" in decoded_url
            camera_service.report_stream_status(camera_id, success=False, is_youtube=is_yt, error_type=err_type, error_detail=err_msg)
        raise HTTPException(status_code=502, detail=f"Không thể tải danh sách phân đoạn: {err_msg}")
        
    # Parse sub-playlist and rewrite segment URLs
    lines = content.split('\n')
    rewritten_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            abs_url = urllib.parse.urljoin(decoded_url, stripped)
            encoded_segment_url = encode_url(abs_url)
            rewritten_url = f"/api/v1/camera/stream/segment?url={encoded_segment_url}"
            if camera_id:
                rewritten_url += f"&camera_id={camera_id}"
            if token:
                rewritten_url += f"&token={token}"
            rewritten_lines.append(rewritten_url)
        else:
            rewritten_lines.append(line)
            
    rewritten_content = "\n".join(rewritten_lines)
    return Response(content=rewritten_content, media_type="application/vnd.apple.mpegurl")

@router.get("/stream/segment")
def get_segment(
    url: str = Query(...),
    camera_id: str = Query(None),
    token: str = Query(None),
    current_user: User = Depends(require_role_from_token_or_param(["authority", "ai_system"])),
    camera_service: CameraService = Depends(get_camera_service)
):
    try:
        decoded_url = decode_url(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Tham số phân đoạn không hợp lệ.")
        
    # Open connection blockingly first to handle errors properly and avoid empty 200 OK payloads
    try:
        with socket_family_from_url(decoded_url):
            req = urllib.request.Request(
                decoded_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            # Fetch segment using standard 10s timeout
            response = urllib.request.urlopen(req, timeout=10)
        if camera_id:
            is_yt = "googlevideo.com" in decoded_url or "youtube.com" in decoded_url
            camera_service.report_stream_status(camera_id, success=True, is_youtube=is_yt)
    except Exception as e:
        err_type, err_msg = classify_error(decoded_url, e)
        print(f"ERROR: Failed to open segment stream for {camera_id}: {err_msg}")
        if camera_id:
            is_yt = "googlevideo.com" in decoded_url or "youtube.com" in decoded_url
            camera_service.report_stream_status(camera_id, success=False, is_youtube=is_yt, error_type=err_type, error_detail=err_msg)
        raise HTTPException(status_code=502, detail=f"Không thể tải phân đoạn dữ liệu: {err_msg}")

    # Stream the binary segment file in non-blocking chunks
    def stream_generator():
        try:
            with response:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"ERROR: Failed to fetch segment stream: {e}")
            
    return StreamingResponse(stream_generator(), media_type="video/mp2t")


@router.get("/debug-state")
def debug_camera_state(
    camera_service: CameraService = Depends(get_camera_service)
):
    return {
        "stream_status": camera_service.stream_status,
        "hls_cache": {k: [v[0], v[1]] for k, v in camera_service.hls_cache.items()}
    }
