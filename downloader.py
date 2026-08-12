import os
import asyncio
import logging
import uuid
from pathlib import Path
import yt_dlp
from config import DOWNLOAD_DIR, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    """Basic validation for URL format."""
    url = url.strip().lower()
    valid_domains = [
        "instagram.com", "instagr.am",
        "tiktok.com", "vt.tiktok.com",
        "youtube.com", "youtu.be",
        "twitter.com", "x.com",
        "facebook.com", "fb.watch",
        "pinterest.com", "pin.it"
    ]
    return any(domain in url for domain in valid_domains) or url.startswith(("http://", "https://"))

def _sync_download(url: str, output_path: Path) -> dict:
    """Synchronous video download using yt-dlp."""
    unique_id = str(uuid.uuid4())[:8]
    file_template = str(output_path / f"%(id)s_{unique_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': file_template,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'merge_output_format': 'mp4',
        'max_filesize': MAX_FILE_SIZE_BYTES,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # If it's a playlist or multiple entries, pick the first
        if 'entries' in info:
            info = info['entries'][0]

        downloaded_filename = ydl.prepare_filename(info)
        
        # In case format merge created .mp4
        possible_mp4 = Path(downloaded_filename).with_suffix('.mp4')
        if possible_mp4.exists():
            final_file = possible_mp4
        elif Path(downloaded_filename).exists():
            final_file = Path(downloaded_filename)
        else:
            # Fallback search in output directory with unique_id
            found = list(output_path.glob(f"*{unique_id}*"))
            if found:
                final_file = found[0]
            else:
                raise FileNotFoundError("Yuklangan media fayli topilmadi.")

        return {
            "file_path": str(final_file),
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "width": info.get("width"),
            "height": info.get("height"),
            "uploader": info.get("uploader", "Noma'lum"),
            "file_size": final_file.stat().st_size
        }

async def download_video(url: str) -> dict:
    """Asynchronous wrapper for video downloading."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_download, url, DOWNLOAD_DIR)

def cleanup_file(file_path: str):
    """Safely delete downloaded file after sending."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Vaqtinchalik fayl o'chirildi: {file_path}")
    except Exception as e:
        logger.error(f"Faylni o'chirishda xatolik ({file_path}): {e}")
