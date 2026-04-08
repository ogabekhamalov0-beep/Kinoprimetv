import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- KONFIGURATSIYA ---
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'
ADMIN_ID = 6223558485

# Skrinshotlardan olingan barcha Kanal ID raqamlari
CHANNELS = [
    "-1002479427027", # Kino Hudud
    "-1002361661858", # Kino Prime TV
    "-1002241513289", # Kino Olami
    "-1002157147775"  # Prime Kino
]

# Tugmalar uchun havolalar
CHANNEL_DATA = [
    {"name": "Kino Hudud 🎬", "url": "https://t.me/KinoHudud"},
    {"name": "Kino Prime 🎞", "url": "https://t.me/kinoprime_tv"},
    {"name": "Kino Olami 🎥", "url": "https://t.me/kino_olami_hd"},
    {"name": "Prime Kino 📽", "url": "https://t.me/+_kP_k_p_"}
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# --- BAZA (SQLite) ---
db = sqlite3.connect("kino_system.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
db.commit()

# --- RENDER PORT SERVERI ---
async def handle(request):
    return web.Response(text="Bot is online!")

app = web.Application()
app.router.add_get("/", handle)

# --- OBUNA TEKSHIRUVI ---
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            # Bot admin bo'lmagan kanalni tashlab o'tadi
            continue
    return True

def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNEL_DATA:
        keyboard.add(InlineKeyboardButton(text=ch['name'], url=ch['url']))
    keyboard.add(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
    return keyboard

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer(f"<b>Salom {message.from_user.first_name}!</b>\nKino kodini yuboring:")
    else:
        await message.answer("⚠️ <b>Botdan foydalanish uchun hamma kanallarga a'zo bo'ling:</b>", 
                             reply_markup=get_sub_keyboard())

@dp.callback_query_handler(text="check_sub")
async def verify_sub(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 <b>Rahmat!</b> Endi kod yuborsangiz bo'ladi.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)

# Admin kino qo'shishi (Video yuboring, captionga kod:123 yozing)
@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def add_movie(message: types.Message):
    if message.caption and "kod:" in message.caption.lower():
        code = message.caption.lower().replace("kod:", "").strip()
        cursor.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (code, message.video.file_id))
        db.commit()
        await message.reply(f"✅ <b>Saqlandi!</b> Kod: <code>{code}</code>")
    else:
        await message.reply("📝 Izohga <b>kod:123</b> deb yozing.")

# Kino qidirish
@dp.message_handler()
async def search(message: types.Message):
    if not await check_sub(message.from_user.id):
        return await message.answer("⚠️ Avval kanallarga a'zo bo'ling!", reply_markup=get_sub_keyboard())
    
    code = message.text.strip()
    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    res = cursor.fetchone()
    if res:
        await message.answer_video(video=res[0], caption=f"🎬 Kod: {code}\n\n@kinoprimetv_bot")
    elif code.isdigit():
        await message.answer("😔 Bu kod bilan kino topilmadi.")

# --- RENDERDA ISHGA TUSHIRISH ---
async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
            
