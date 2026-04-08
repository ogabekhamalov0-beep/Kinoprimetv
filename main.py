import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- KONFIGURATSIYA ---
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'
ADMIN_ID = 6223558485

# Skrinshotdagi kanallarning ID raqamlari (Hammasida bot admin bo'lishi shart!)
CHANNELS = [
    "-1002479427027", # Kino Hudud
    "-1002361661858", # Kino Prime TV
    "-1002241513289", # Kino Olami
    "-1002157147775"  # Boshqa kanal
]

# Tugmalar uchun linklar
CHANNEL_LINKS = [
    {"name": "Kino Hudud 🎬", "url": "https://t.me/KinoHudud"},
    {"name": "Kino Prime 🎞", "url": "https://t.me/kinoprime_tv"},
    {"name": "Kino Olami 🎥", "url": "https://t.me/kino_olami_hd"}
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# --- BAZA ---
db = sqlite3.connect("movies_pro.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
db.commit()

# --- SERVER ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# --- OBUNA TEKSHIRISH (Xatolikni oldini oluvchi blok bilan) ---
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            logging.error(f"Xato: {channel} da bot admin emas: {e}")
            # Agar bot admin bo'lmasa, bot ishdan to'xtamasligi uchun tekshiruvdan o'tkazib yuboramiz
            continue
    return True

def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNEL_LINKS:
        keyboard.add(InlineKeyboardButton(text=ch['name'], url=ch['url']))
    keyboard.add(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="verify"))
    return keyboard

# --- HANDLERLAR ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer(f"👋 Salom {message.from_user.first_name}!\n\nKino kodini yuboring:")
    else:
        await message.answer("⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:</b>", 
                             reply_markup=get_sub_keyboard())

@dp.callback_query_handler(text="verify")
async def verify(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 Rahmat! Kino kodini yuboring.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)

@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def add_movie(message: types.Message):
    if message.caption and "kod:" in message.caption.lower():
        code = message.caption.lower().replace("kod:", "").strip()
        cursor.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (code, message.video.file_id))
        db.commit()
        await message.reply(f"✅ Saqlandi! Kod: <code>{code}</code>")

@dp.message_handler()
async def search(message: types.Message):
    if not await check_sub(message.from_user.id):
        return await message.answer("⚠️ Avval kanallarga a'zo bo'ling!", reply_markup=get_sub_keyboard())
    
    code = message.text.strip()
    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    res = cursor.fetchone()
    if res:
        await message.answer_video(video=res[0], caption=f"🎬 Kod: {code}\n\n✨ @kinoprimetv_bot")
    elif code.isdigit():
        await message.answer("😔 Bu kod bilan kino topilmadi.")

async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
