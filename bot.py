import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PORT
from database import init_db
from handlers import start, registration, feedback, admin
from web import app as flask_app


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def run_flask():
    # Render дає PORT через env
    flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)       # адмінські хендлери першими (reply)
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(feedback.router)

    # Flask у фоновому потоці (щоб пінг-платформи бачили відкритий порт)
    threading.Thread(target=run_flask, daemon=True).start()

    log.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())