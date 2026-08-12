import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Temporary Download Directory
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Maximum file size for Telegram Bot API upload (in bytes) - default 50 MB
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024
