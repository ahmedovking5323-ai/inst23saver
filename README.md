# 🎬 Telegram Video Downloader Bot (InstaSaver)

Ushbu bot Instagram (Reels, Post, IGTV), TikTok, YouTube va boshqa ko'plab ijtimoiy tarmoqlardan videolarni Telegram orqali yuklab olish uchun mo'ljallangan.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Zaruriy kutubxonalarni o'rnatish

Terminalda quyidagi buyruqni bering:

```bash
pip install -r requirements.txt
```

### 2. Bot Tokenini sozlash

1. Telegram'da [@BotFather](https://t.me/BotFather) botiga kiring va yangi bot yaratib `BOT_TOKEN` oling.
2. `.env` faylini oching va `YOUR_TELEGRAM_BOT_TOKEN_HERE` o'rniga olingan tokenni joylang:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
```

### 3. Botni ishga tushirish

Loyiha papkasida quyidagi buyruqni bering:

```bash
python main.py
```

---

## 🛠 Xususiyatlari

- 📱 **Instagram Reels, Posts, IGTV** yuklash
- 🎵 **TikTok** videolarni suvsiz (watermark'siz) yuklash
- 🎥 **YouTube Shorts** va videolarni yuklash
- ⚡ **Tezkor yuklash va qayta ishlash**
- 🗑 **Vaqtinchalik fayllarni avtomatik tozalash**
- 🛡 **50 MB hajm cheklovi nazorati** (Telegram Bot API standarti)
