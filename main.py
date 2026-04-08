import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiohttp import web

# 1. Sozlamalar
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'
ADMIN_ID = 6223558485  # O'zingizning Telegram ID'ingizni shu yerga yozing

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# 2. Ma'lumotlar bazasini yaratish
db = sqlite3.connect("kinolar.db")
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        code TEXT PRIMARY KEY,
        file_id TEXT
    )
""")
db.commit()

# 3. Render porti uchun server
async def handle(request):
    return web.Response(text="Bot is active!")

app = web.Application()
app.router.add_get("/", handle)

# --- ADMIN QISMI: KINO QO'SHISH ---
# Format: Kinoni yuborasiz va caption qismiga "kod:172" deb yozasiz
@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def add_movie(message: types.Message):
    if message.caption and "kod:" in message.caption.lower():
        kino_kodi = message.caption.lower().replace("kod:", "").strip()
        file_id = message.video.file_id
        
        try:
            cursor.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (kino_kodi, file_id))
            db.commit()
            await message.reply(f"✅ <b>Tayyor!</b>\nKino bazaga saqlandi.\nKod: <code>{kino_kodi}</code>")
        except Exception as e:
            await message.reply(f"❌ Xatolik yuz berdi: {e}")
    else:
        await message.reply("⚠️ Kinoni saqlash uchun izohiga <b>kod:123</b> deb yozing!")

# --- FOYDALANUVCHI QISMI: KINO QIDIRISH ---
@dp.message_handler()
async def search_movie(message: types.Message):
    if message.text.isdigit():
        code = message.text.strip()
        cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
        result = cursor.fetchone()
        
        if result:
            await message.answer_video(video=result[0], caption=f"🎬 <b>Siz qidirgan kino (Kod: {code})</b>\n\n@kinoprimetv_bot")
        else:
            await message.answer("😔 <b>Afsus, bu kod bilan kino topilmadi.</b>\nIltimos, kodni to'g'ri yozganingizni tekshiring.")
    elif message.text == "/start":
        await message.answer("👋 <b>Xush kelibsiz!</b>\nKino ko'rish uchun kino kodini yuboring.")

# 4. Botni ishga tushirish
async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
                           
