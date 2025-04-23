import asyncio
import logging
from aiogram import Bot, Dispatcher
import config
from handlers import start, catalog, cart, profile, search, order, admin
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
storage = MemoryStorage()

dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(cart.router)
dp.include_router(profile.router)
dp.include_router(search.router)
dp.include_router(order.router)
dp.include_router(admin.router)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())