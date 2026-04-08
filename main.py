import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'
ADMIN_ID = 6223558485  # O'zingizning ID raqamingiz
CHANNELS = ["-1002479427027"] # Kanalingiz ID raqamini shu yerga yozing
CHANNEL_URL = "https://t.me/KinoHudud" # Kanalingiz linki

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# --- BAZA BILAN ISHLASH ---
db = sqlite3.connect("kinobaza.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
db.commit()

# --- RENDER PORT SERVERI ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# --- FUNKSIYALAR ---
async def check_sub(user_id):
    """Foydalanuvchi kanalga a'zo ekanligini tekshirish"""
    for channel in CHANNELS:
        status = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if status.status == 'left':
            return False
    return True

def sub_keyboard():
    """Obuna bo'lish tugmasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_URL))
    keyboard.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check"))
    return keyboard

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer(f"👋 <b>Xush kelibsiz, {message.from_user.first_name}!</b>\n\nKino kodini yuboring:")
    else:
        await message.answer("⚠️ <b>Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz kerak!</b>", reply_markup=sub_keyboard())

@dp.callback_query_handler(text="check")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 <b>Rahmat!</b> Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("❌ Hali a'zo bo'lmadingiz!", show_alert=True)

# Admin uchun kino qo'shish (Video yuboring, captionga: kod:123 deb yozing)
@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def add_movie(message: types.Message):
    if message.caption and "kod:" in message.caption.lower():
        code = message.caption.lower().replace("kod:", "").strip()
        cursor.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (code, message.video.file_id))
        db.commit()
        await message.reply(f"✅ <b>Saqlandi!</b>\nKod: <code>{code}</code>")

# Kino qidirish
@dp.message_handler()
async def search_movie(message: types.Message):
    if not await check_sub(message.from_user.id):
        return await message.answer("⚠️ <b>Avval kanalga a'zo bo'ling!</b>", reply_markup=sub_keyboard())
    
    code = message.text.strip()
    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    res = cursor.fetchone()
    
    if res:
        await message.answer_video(video=res[0], caption=f"🎬 <b>Kod: {code}</b>\n\n@kinoprimetv_bot")
    elif code.isdigit():
        await message.answer("😔 Bu kod bilan kino topilmadi.")

# --- ISHGA TUSHIRISH ---
async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
