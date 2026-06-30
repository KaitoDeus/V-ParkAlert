import os
import sys

# Reconfigure stdout and stderr to handle UTF-8 printing safely on all systems, preventing UnicodeEncodeErrors
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.core.websocket_manager import manager

from src.api.v1.auth import router as auth_router
from src.api.v1.violations import router as violations_router
from src.api.v1.camera import router as camera_router

app = FastAPI(title="V-ParkAlert API", version="1.0.0")

# Mount media static files directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
media_path = os.path.join(root_dir, "media")
if not os.path.exists(media_path):
    os.makedirs(media_path)
app.mount("/media", StaticFiles(directory=media_path), name="media")

static_path = os.path.join(root_dir, "src", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev environment, allows requests from all hosts
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Versioned API Routes (v1)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(violations_router, prefix="/api/v1")
app.include_router(camera_router, prefix="/api/v1")

# Backward Compatibility (Legacy Endpoint support for /api/...)
app.include_router(auth_router, prefix="/api")
app.include_router(violations_router, prefix="/api")
app.include_router(camera_router, prefix="/api")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/healthz", tags=["health"])
def health_check():
    return {"status": "ok", "message": "V-ParkAlert Services are running."}

# HTML Page Routes
static_path = os.path.join(root_dir, "src", "static")

@app.get("/login")
def get_login():
    return FileResponse(os.path.join(static_path, "login.html"))

@app.get("/dashboard")
@app.get("/")
def get_index():
    return FileResponse(os.path.join(static_path, "index.html"))


if __name__ == "__main__":
    import sys
    # Add project root to sys.path so `src.*` imports work when running from src/
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
