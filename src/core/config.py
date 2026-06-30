# src/core/config.py
import os
import secrets
from dotenv import load_dotenv

# Load .env file from project root
src_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(src_root, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

class Settings:
    PROJECT_NAME: str = "V-ParkAlert"
    # Generate a random secret key on startup if not specified in environment
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 30 minutes for automatic session logout

    # AI Models & Datasets Config
    YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "")
    PLATE_MODEL_PATH: str = os.getenv("PLATE_MODEL_PATH", "")

settings = Settings()
