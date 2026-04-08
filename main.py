import os
import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
from aiohttp import web

# --- SOZLAMALAR ---
# Render'da Environment Variables qismiga BOT_TOKEN qo'shishni unutmang
TOKEN = "8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM"

# Skrinshotlaringizdan olingan Kanal ID raqamlari
CHANNELS = ["-1002479427027", "-1002361661858", "-1002241513289", "-1002157147775"]

# Tugmalar uchun linklar
CHANNEL_LINKS = [
    ["📢 Kino Hudud", "https://t.me/KinoHudud"],
    ["📢 Kino Prime TV", "https://t.me/kinoprime_tv"],
    ["🎥 Kino Olami", "https://t.me/kino_olami_hd"],
    ["📽 Prime Kino", "https://t.me/+_kP_k_p_"]
]

ADMIN_ID = 6223558485
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- BAZA FUNKSIYALARI ---
def init_db():
    conn = sqlite3.connect('films.db')
    conn.execute('CREATE TABLE IF NOT EXISTS movies (file_id TEXT, movie_code TEXT UNIQUE)')
    conn.close()

# --- OBUNANI TEKSHIRISH ---
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            # Bot admin bo'lmagan kanalni tashlab o'tadi
            continue
    return True

# --- RENDER UCHUN PORTNI BAND QILISH ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def run_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render avtomatik beradigan PORT o'zgaruvchisini olamiz
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎬 <b>Xush kelibsiz!</b>\n\nKino olish uchun uning kodini yuboring.", parse_mode="HTML")

# Avtomatik a'zolikni tasdiqlash (Chat Join Request)
@dp.chat_join_request()
async def auto_approve(request: ChatJoinRequest):
    await request.approve()
    try:
        await bot.send_message(request.from_user.id, "✅ Kanallarga a'zo bo'lganingiz tasdiqlandi! Endi kino kodini yuborishingiz mumkin.")
    except:
        pass

# Admin uchun kino yuklash (Faqat video yuborilganda)
@dp.message(F.video, F.from_user.id == ADMIN_ID)
async def get_video(message: types.Message):
    user_data[message.from_user.id] = message.video.file_id
    await message.answer("📁 Video qabul qilindi! Endi kodni <code>kod:123</code> shaklida yuboring.", parse_mode="HTML")

# Admin kodni saqlashi
@dp.message(F.text.startswith("kod:"), F.from_user.id == ADMIN_ID)
async def save_movie(message: types.Message):
    if message.from_user.id in user_data:
        code = message.text.split(":")[1].strip()
        file_id = user_data[message.from_user.id]
        
        conn = sqlite3.connect('films.db')
        try:
            conn.execute("INSERT OR REPLACE INTO movies VALUES (?, ?)", (file_id, code))
            conn.commit()
            await message.answer(f"✅ <b>Muvaffaqiyatli saqlandi!</b>\nKino kodi: <code>{code}</code>", parse_mode="HTML")
            del user_data[message.from_user.id]
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")
        finally:
            conn.close()
    else:
        await message.answer("⚠️ Avval videoni yuboring!")

# Kino qidirish (Majburiy obuna bilan)
@dp.message(F.text.isdigit())
async def send_movie(message: types.Message):
    is_subscribed = await check_sub(message.from_user.id)
    
    if not is_subscribed:
        kb = []
        for name, link in CHANNEL_LINKS:
            kb.append([InlineKeyboardButton(text=name, url=link)])
        kb.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer("⚠️ <b>Kino ko'rish uchun avval kanallarimizga a'zo bo'lishingiz kerak!</b>", 
                             reply_markup=reply_markup, parse_mode="HTML")
        return

    conn = sqlite3.connect('films.db')
    res = conn.execute("SELECT file_id FROM movies WHERE movie_code = ?", (message.text,)).fetchone()
    conn.close()
    
    if res:
        await message.answer_video(video=res[0], caption=f"🍿 <b>Kino kodi: {message.text}</b>\n\n@kinoprimetv_bot", parse_mode="HTML")
    else:
        await message.answer("😔 Kechirasiz, bu kod bilan hali kino yuklanmagan.")

# Obunani tekshirish tugmasi uchun
@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 Rahmat! Endi kino kodini yuboravering.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo bo'lmadingiz!", show_alert=True)

async def main():
    init_db()
    await run_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
