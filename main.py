import logging
import re
import os
import sys
import html
from pathlib import Path

# Ensure UTF-8 output encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from downloader import is_valid_url, download_video, cleanup_file

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'https?://[^\s]+')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_text = (
        f"👋 <b>Salom, {html.escape(user.first_name)}!</b>\n\n"
        "🤖 Men <b>Video Saver Bot</b>man!\n"
        "Instagram (Reels/Post), TikTok, <b>Facebook (Reels/Watch)</b>, YouTube va boshqa ko'plab tarmoqlardan videolarni yuklab beraman.\n\n"
        "📥 <b>Qanday ishlatiladi?</b>\n"
        "Shunchaki video havolasini (linkini) menga yuboring!"
    )
    keyboard = [
        [InlineKeyboardButton("❓ Yordam", callback_data="help_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "💡 <b>Yordam bo'limi:</b>\n\n"
        "1. Instagram, TikTok, Facebook yoki YouTube'dan video havolasini nusxalang (copy link).\n"
        "2. Ushbu chatga havolani joylang (paste) va yuboring.\n"
        "3. Bot avtomatik ravishda videoni yuklab beradi!\n\n"
        "⚠️ <b>Qoidalar va cheklovlar:</b>\n"
        "• Telegram Bot API cheklovi tufayli 50 MB dan katta videolarni yuborish imkoniyati cheklangan.\n"
        "• Shaxsiy (private) akkauntlardagi va guruhlardagi yopiq videolarni yuklab bo'lmasligi mumkin."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(help_text, parse_mode="HTML")
    else:
        await update.message.reply_text(help_text, parse_mode="HTML")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ <b>InstaSaver Telegram Bot</b>\n\n"
        "🚀 Versiya: 1.0.0\n"
        "⚡ Texnologiyalar: Python, python-telegram-bot, yt-dlp\n"
        "✨ Qulay va tezkor video yuklash xizmati!"
    )
    await update.message.reply_text(about_text, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages containing video links."""
    text = update.message.text.strip()
    urls = URL_REGEX.findall(text)

    if not urls:
        await update.message.reply_text(
            "⚠️ Iltimos, yaroqli video havolasini yuboring!\n"
            "Masalan: Instagram Reels, TikTok yoki YouTube videosi linki."
        )
        return

    url = urls[0]
    if not is_valid_url(url):
        await update.message.reply_text("⚠️ Ushbu havola qo'llab-quvvatlanmaydi.")
        return

    # Send status message
    status_msg = await update.message.reply_text("🔍 <b>Video topilmoqda...</b>", parse_mode="HTML")

    file_path = None
    try:
        await status_msg.edit_text("📥 <b>Video yuklanmoqda...</b>", parse_mode="HTML")
        
        # Download video asynchronously (supports up to 200MB)
        video_data = await download_video(url, compact_mode=False)
        file_path = video_data.get("file_path")
        file_size = video_data.get("file_size", 0)

        # 50MB Telegram Bot API upload threshold
        TELEGRAM_HTTP_LIMIT = 50 * 1024 * 1024

        if file_size > MAX_FILE_SIZE_BYTES:
            mb_size = round(file_size / (1024 * 1024), 1)
            await status_msg.edit_text(
                f"❌ <b>Xatolik:</b> Video hajmi juda katta ({mb_size} MB).\n"
                f"Maksimal ruxsat etilgan sig'im: {MAX_FILE_SIZE_MB} MB.",
                parse_mode="HTML"
            )
            return

        # If file is between 50MB and 200MB, re-download compact version for Telegram API 50MB limit
        if file_size > TELEGRAM_HTTP_LIMIT:
            mb_size = round(file_size / (1024 * 1024), 1)
            await status_msg.edit_text(
                f"⚙️ <b>Video hajmi {mb_size} MB.</b>\n"
                f"Telegram limitiga (50 MB) moslashtirilib, optimal sifatda (720p/480p) qayta yuklanmoqda...",
                parse_mode="HTML"
            )
            cleanup_file(file_path)
            video_data = await download_video(url, compact_mode=True)
            file_path = video_data.get("file_path")

        await status_msg.edit_text("📤 <b>Video yuborilmoqda...</b>", parse_mode="HTML")

        # HTML escape title & uploader to prevent parsing entity errors
        raw_title = video_data.get('title', 'Video')
        raw_uploader = video_data.get('uploader', 'Noma\'lum')
        safe_title = html.escape(str(raw_title))
        safe_uploader = html.escape(str(raw_uploader))
        bot_username = html.escape(context.bot.username or 'bot')

        caption = (
            f"🎬 <b>{safe_title}</b>\n\n"
            f"👤 Manba: {safe_uploader}\n"
            f"🤖 @{bot_username} yordamida yuklab olindi."
        )
        
        # Limit caption length for Telegram
        if len(caption) > 1024:
            caption = caption[:1000] + "..."

        with open(file_path, 'rb') as video_file:
            try:
                await update.message.reply_video(
                    video=video_file,
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True,
                    duration=video_data.get("duration"),
                    width=video_data.get("width"),
                    height=video_data.get("height")
                )
            except Exception as send_err:
                # Fallback to plain text caption if HTML parsing still fails for exotic titles
                logger.warning(f"HTML caption send failed, trying plain text fallback: {send_err}")
                video_file.seek(0)
                plain_caption = f"🎬 {raw_title}\n\n👤 Manba: {raw_uploader}\n🤖 @{context.bot.username or 'bot'} yordamida yuklab olindi."[:1000]
                await update.message.reply_video(
                    video=video_file,
                    caption=plain_caption,
                    supports_streaming=True,
                    duration=video_data.get("duration"),
                    width=video_data.get("width"),
                    height=video_data.get("height")
                )

        # Delete status message
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}", exc_info=True)
        err_str = str(e)
        error_msg = "❌ <b>Videoni yuklashda xatolik yuz berdi.</b>\n\n"
        if "Private" in err_str or "login" in err_str.lower() or "login required" in err_str.lower():
            error_msg += "📌 Video shaxsiy (private) profilga tegishli bo'lishi mumkin."
        elif "max_filesize" in err_str.lower() or "file size" in err_str.lower():
            error_msg += "📌 Video hajmi 50 MB cheklovidan katta."
        elif "unsupported url" in err_str.lower():
            error_msg += "📌 Ushbu video havolasi qo'llab-quvvatlanmaydi."
        else:
            clean_err = html.escape(err_str.split('\n')[0][:120])
            error_msg += f"📌 Tafsilot: <code>{clean_err}</code>"
        
        try:
            await status_msg.edit_text(error_msg, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(error_msg, parse_mode="HTML")

    finally:
        if file_path:
            cleanup_file(file_path)

def main():
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("❌ XATOLIK: BOT_TOKEN o'rnatilmagan!")
        print("Iltimos, `.env` faylini ochib, BOT_TOKEN qiymatini kiriting.")
        print("Namuna: BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ")
        print("="*60 + "\n")
        sys.exit(1)

    print("🚀 Telegram Bot ishga tushmoqda...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
    application.run_polling()

if __name__ == "__main__":
    main()
