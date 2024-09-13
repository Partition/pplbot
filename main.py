import asyncio
from bot.bot import setup_bot
from bot.database import engine, Base
from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    bot = await setup_bot()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with bot:
        await bot.start(os.getenv('BOT_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())