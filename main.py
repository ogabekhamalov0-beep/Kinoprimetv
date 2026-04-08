import os
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- KONFIGURATSIYA ---
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'
ADMIN_ID = 6223558485

# Skrinshotdagi barcha kanallarning ID raqamlari
CHANNELS = [
    "-1002479427027", # Kino Hudud
    "-1002361661858", # Kino Prime TV
    "-1002157147775"  # Boshqa kanal (rasmdan olingan)
]

# Tugmalarda ko'rinadigan linklar
CHANNEL_LINKS = [
    {"name": "Kino Hudud 🎬", "url": "https://t.me/KinoHudud"},
    {"name": "Kino Prime TV 🎞", "url": "https://t.me/kinoprime_tv"}
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
db = sqlite3.connect("movies_v2.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT)")
db.commit()

# --- RENDER SERVER (Port scan timeout oldini olish uchun) ---
async def handle(request):
    return web.Response(text="Bot is running perfectly!")

app = web.Application()
app.router.add_get("/", handle)

# --- MAJBURIY OBUNA TEKSHIRUVI ---
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status == 'left':
                return False
        except Exception as e:
            logging.error(f"Xatolik: {channel} da bot admin emas yoki ID xato: {e}")
            # Agar bot kanalga qo'shilmagan bo'lsa, xato bermasligi uchun true qaytaramiz
            continue 
    return True

def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNEL_LINKS:
        keyboard.add(InlineKeyboardButton(text=ch['name'], url=ch['url']))
    keyboard.add(InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data="verify_sub"))
    return keyboard

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if await check_sub(message.from_user.id):
        await message.answer(
            f"<b>Salom, {message.from_user.first_name}! 👋</b>\n\n"
            "🎬 <b>KinoPrimeTV</b> botiga xush kelibsiz.\n"
            "Kino ko'rish uchun uning kodini yuboring!"
        )
    else:
        await message.answer(
            "⚠️ <b>Diqqat! Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:</b>",
            reply_markup=get_sub_keyboard()
        )

@dp.callback_query_handler(text="verify_sub")
async def verify_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 <b>Tabriklaymiz!</b> Barcha kanallarga a'zo bo'ldingiz. Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo bo'lmadingiz! Iltimos, tekshirib ko'ring.", show_alert=True)

# Admin uchun kino qo'shish (Video + "kod:123")
@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def add_movie_admin(message: types.Message):
    if message.caption and "kod:" in message.caption.lower():
        code = message.caption.lower().replace("kod:", "").strip()
        cursor.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (code, message.video.file_id))
        db.commit()
        await message.reply(f"✅ <b>Bazaga qo'shildi!</b>\n\nKod: <code>{code}</code>")
    else:
        await message.reply("📝 Kinoni saqlash uchun videoni yuboring va izohiga <b>kod:123</b> deb yozing.")

# Kino qidirish qismi
@dp.message_handler()
async def movie_search(message: types.Message):
    if not await check_sub(message.from_user.id):
        return await message.answer("⚠️ <b>Avval kanallarga a'zo bo'ling!</b>", reply_markup=get_sub_keyboard())
    
    code = message.text.strip()
    cursor.execute("SELECT file_id FROM movies WHERE code = ?", (code,))
    res = cursor.fetchone()
    
    if res:
        await message.answer_video(video=res[0], caption=f"🎬 <b>Kino kodi: {code}</b>\n\n✨ @kinoprimetv_bot")
    elif code.isdigit():
        await message.answer(f"😔 Kechirasiz, <b>{code}</b> kodli kino topilmadi.")

# --- RENDER'DA ISHGA TUSHIRISH ---
async def on_startup(dp):
    # Bu qism Render'dagi Port muammosini hal qiladi
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()
    logging.info("Render port serveri faollashdi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
