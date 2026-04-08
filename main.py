import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiohttp import web

# Loglar
logging.basicConfig(level=logging.INFO)

# Token
API_TOKEN = '8720785352:AAFkW_Y8lExxDcIvJqJvBm16dGglVLfv-UM'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Render uchun oddiy server (Port xatosini yo'qotish uchun)
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# Start komandasi
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Salom! Botingiz nihoyat Render'da muvaffaqiyatli ishga tushdi! 🚀")

# Botni ishga tushirish funksiyasi
async def on_startup(dp):
    # Bu qism Render portini band qiladi
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', os.getenv('PORT', 10000))
    await site.start()
    logging.info("Web server started on port")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
