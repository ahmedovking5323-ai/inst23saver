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
        "facebook.com", "fb.watch", "fb.gg", "fb.com", "m.facebook.com",
        "pinterest.com", "pin.it"
    ]
    return any(domain in url for domain in valid_domains) or url.startswith(("http://", "https://"))

def _sync_download(url: str, output_path: Path, compact_mode: bool = False) -> dict:
    """Synchronous video download using yt-dlp. Supports up to 200MB+ videos."""
    unique_id = str(uuid.uuid4())[:8]
    file_template = str(output_path / f"%(id)s_{unique_id}.%(ext)s")

    max_size = 50 * 1024 * 1024 if compact_mode else MAX_FILE_SIZE_BYTES
    
    if compact_mode:
        # Request format under 50MB (e.g., 720p/480p) to fit standard Telegram Bot API limit
        format_spec = 'best[filesize<50M]/best[height<=720]/best[height<=480]/best[ext=mp4]/best/b'
    else:
        # Standard best quality up to max configured size (200MB)
        format_spec = 'best[ext=mp4]/best/b'

    ydl_opts = {
        'outtmpl': file_template,
        'format': format_spec,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'max_filesize': max_size,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # If it's a playlist or multiple entries, pick the first
        if 'entries' in info and info['entries']:
            info = info['entries'][0]

        downloaded_filename = ydl.prepare_filename(info)
        
        # Check expected file
        final_file = Path(downloaded_filename)
        if not final_file.exists():
            possible_mp4 = final_file.with_suffix('.mp4')
            if possible_mp4.exists():
                final_file = possible_mp4
            else:
                found = list(output_path.glob(f"*{unique_id}*"))
                if found:
                    final_file = found[0]
                else:
                    raise FileNotFoundError("Yuklangan media fayli diskda topilmadi.")

        return {
            "file_path": str(final_file),
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "width": info.get("width"),
            "height": info.get("height"),
            "uploader": info.get("uploader", info.get("extractor", "Noma'lum")),
            "file_size": final_file.stat().st_size
        }

async def download_video(url: str, compact_mode: bool = False) -> dict:
    """Asynchronous wrapper for video downloading."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_download, url, DOWNLOAD_DIR, compact_mode)

def cleanup_file(file_path: str):
    """Safely delete downloaded file after sending."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Vaqtinchalik fayl o'chirildi: {file_path}")
    except Exception as e:
        logger.error(f"Faylni o'chirishda xatolik ({file_path}): {e}")
