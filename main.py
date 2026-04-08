import logging
from aiogram import Bot, Dispatcher, types, executor

# 1. Loglarni sozlash (Render loglarida xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# 2. Yangi tokenni o'rnatish
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'

# 3. Bot va Dispatcher obyektlarini yaratish
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 4. /start komandasi uchun handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    Foydalanuvchi /start yuborganda javob qaytaradi
    """
    await message.reply("Salom! Kinoprimetv botingiz muvaffaqiyatli ishga tushdi. \nKino kodini yuboring!")

# 5. Oddiy xabarlar (Kino kodlari) uchun handler
@dp.message_handler()
async def echo(message: types.Message):
    # Bu yerda kelajakda bazadan kino qidirish mantiqini qo'shishingiz mumkin
    await message.answer(f"Siz yuborgan kod: {message.text}. Tezpada kino topiladi!")

# 6. Botni ishga tushirish
if __name__ == '__main__':
    print("Bot polling rejimida ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True)
    
