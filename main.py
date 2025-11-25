import os
import glob
import asyncio
import yt_dlp

# --- 🩹 پچ تعمیر خطای پایتون 3.15 (مهم) ---
# این بخش باید حتماً قبل از import pyrogram باشد
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ----------------------------------------

from pyrogram import Client, filters, enums

# --- تنظیمات لاگین (کلیدهای عمومی) ---
API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"

# --- تنظیمات پروکسی (برای اتصال به تلگرام) ---
PROXY = {
    "scheme": "socks5",
    "hostname": "127.0.0.1",
    "port": 1080, # اگر سایفون روی 8080 است، اینجا را هم 8080 کنید و scheme را http بگذارید
}

# اگر سایفون روی 8080 است، خط بالا را پاک کنید و این را فعال کنید:
# PROXY = {"scheme": "http", "hostname": "127.0.0.1", "port": 8080}


print("⏳ در حال اتصال به سرورهای تلگرام...")
app = Client("my_account", api_id=API_ID, api_hash=API_HASH, proxy=PROXY)

# --- دستور دانلود (.dl) ---
@app.on_message(filters.command("dl", prefixes=".") & filters.me)
async def download_handler(client, message):
    if len(message.command) < 2:
        await message.edit_text("❌ لینک کو؟ مثال: `.dl https://...`")
        return

    link = message.command[1]
    status_msg = await message.edit_text(f"🔎 آنالیز لینک: {link}")

    # تنظیمات دانلودر
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        'ffmpeg_location': '.', 
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }

    try:
        await status_msg.edit(f"⬇️ در حال دانلود فایل سنگین...")
        
        # اجرای دانلود در پس‌زمینه
        def run_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(link, download=True)

        info = await asyncio.get_running_loop().run_in_executor(None, run_download)
        
        video_id = info['id']
        video_title = info.get('title', video_id)

        files = glob.glob(f"downloads/{video_id}*")
        if not files:
            await status_msg.edit("❌ فایل پیدا نشد!")
            return
        file_path = files[0]

        file_size = os.path.getsize(file_path) / (1024 * 1024)
        await status_msg.edit(f"📤 حجم: {int(file_size)} MB\nدر حال آپلود (این مرحله زمان می‌برد)...")

        # تابع نمایش درصد آپلود
        async def progress(current, total):
            # هر ۱۰ مگابایت یکبار در کنسول چاپ کن
            if current % (10 * 1024 * 1024) == 0:
                print(f"Uploading: {current / total * 100:.1f}%")

        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎥 **{video_title}**\n💾 Size: {int(file_size)} MB",
            supports_streaming=True,
            progress=progress
        )

        os.remove(file_path)
        await status_msg.delete()
        print("✅ تمام شد.")

    except Exception as e:
        await status_msg.edit(f"❌ خطا: {str(e)}")

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    print("🚀 ربات یوزر آماده لاگین است...")
    app.run()