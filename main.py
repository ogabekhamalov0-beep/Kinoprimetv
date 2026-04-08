import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Tokenni o'rnatish
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Render porti uchun kichik server (Port scan xatosini oldini olish uchun)
async def handle(request):
    return web.Response(text="Bot is running smoothly!")

app = web.Application()
app.router.add_get("/", handle)

# Tugmalar (Keyboard)
def get_start_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="🎞 Kino qidirish bo'limi", callback_data="search_hint"),
        InlineKeyboardButton(text="📢 Bizning kanal", url="https://t.me/your_channel_link") # Kanal havolasini kiriting
    )
    return keyboard

# /start komandasi uchun handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        f"<b>Salom, {message.from_user.full_name}!</b> 👋\n\n"
        "✨ <b>KinoPrimeTV</b> botiga xush kelibsiz!\n"
        "Bu yerda siz eng sara filmlarni kod orqali topishingiz mumkin.\n\n"
        "🎬 <i>Kino ko'rishni boshlash uchun kino kodini yuboring!</i>"
    )
    await message.reply(welcome_text, reply_markup=get_start_keyboard())

# Tugma bosilganda yordam berish
@dp.callback_query_handler(text="search_hint")
async def search_hint(call: types.CallbackQuery):
    await call.answer("Shunchaki kino kodini (masalan: 123) botga yozib yuboring!", show_alert=True)

# Kino kodlarini qabul qilish qismi
@dp.message_handler()
async def process_kino_code(message: types.Message):
    if message.text.isdigit():
        await message.answer(
            f"🔍 <b>Siz yuborgan kod:</b> {message.text}\n\n"
            "⏳ <i>Ma'lumotlar bazasidan qidirilmoqda, kuting...</i>"
        )
        # Kelajakda bu yerda SQLite bazasidan kino chiqariladi
    else:
        await message.answer("⚠️ <b>Iltimos, faqat raqamli kod yuboring!</b>")

# Render muhitida botni ishga tushirish
async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    # Render PORT muhit o'zgaruvchisini avtomatik oladi
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()
    logging.info("Render port serveri ishga tushdi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
