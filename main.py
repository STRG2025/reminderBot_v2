import asyncio
import os
from weakref import finalize
from aiogram import Bot, Dispatcher
from handlers import router
from dotenv import load_dotenv
from scheduler import scheduler 

load_dotenv()  
TELEGRAM_TOKEN=os.getenv('TELEGRAM_TOKEN') 

bot=Bot(token=TELEGRAM_TOKEN)
dp=Dispatcher()


async def main():
    dp.include_router(router)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
                                                           
