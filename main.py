import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
TOKEN = "8720785352:AAGxtH9_K_aKE3_UJNe9xfRJqU0ZTxKtOk"
ADMIN_ID = 6362544215 

CHANNELS = [
    -1003844127193, -1003835527309, -1003772893926, -1003799605200, -1003837965725
]

INVITE_LINKS = [
    "https://t.me/+si7eVw0UMXhjNDE6",
    "https://t.me/+jShFgO0vAyVjNDky",
    "https://t.me/+-Eiaz72WSvs3Nzcy",
    "https://t.me/+-hAPSdAHeK05ZGIy",
    "https://t.me/+b-YMiUSg0EUyMjly"
]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA ---
def init_db():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS movies (code TEXT UNIQUE, file_id TEXT)')
    conn.commit()
    conn.close()

def add_movie(code, file_id):
    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO movies (code, file_id) VALUES (?, ?)', (code, file_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_movie(code):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('SELECT file_id FROM movies WHERE code = ?', (code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- TEKSHIRUV ---
async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False 
    return True

# --- ASOSIY ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Start tugmasi
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino qidirish", switch_inline_query_current_chat="")]
    ])
    await message.answer(
        "👋 **Kino Hudud botiga xush kelibsiz!**\n\nKino olish uchun uning **kodini** (faqat raqam) yuboring.",
        reply_markup=kb
    )

@dp.message(F.text.isdigit())
async def search_movie(message: types.Message):
    if not await check_sub(message.from_user.id):
        # Kanallar uchun tugmalar
        buttons = []
        for i, link in enumerate(INVITE_LINKS, 1):
            buttons.append([InlineKeyboardButton(text=f"➕ {i}-kanalga a'zo bo'lish", url=link)])
        
        buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(
            "⚠️ **Xatolik!** Botdan foydalanish uchun barcha kanallarga a'zo bo'lishingiz shart.",
            reply_markup=keyboard
        )
        return

    video_id = get_movie(message.text)
    if video_id:
        await bot.send_video(message.chat.id, video_id, caption=f"🎬 **Kino kodi:** `{message.text}`\n\n🍿 Maroqli hordiq tilaymiz!")
    else:
        await message.answer("😔 Kechirasiz, bu kod bilan kino topilmadi. Kodni to'g'ri yozganingizga ishonch hosil qiling.")

@dp.message(F.video & (F.from_user.id == ADMIN_ID))
async def save_movie(message: types.Message):
    if message.caption and message.caption.isdigit():
        if add_movie(message.caption, message.video.file_id):
            await message.answer(f"✅ **Baza yangilandi!**\n🎬 Kod: `{message.caption}`")
        else:
            await message.answer("⚠️ Bu kod bazada mavjud!")
    else:
        await message.answer("📝 Videoni tagiga raqamli kod yozib yuboring!")

@dp.callback_query(F.data == "check")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.edit_text("🎉 **Rahmat!** Obuna tasdiqlandi. Endi kino kodini yuboring.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo emassiz!", show_alert=True)

async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
      
