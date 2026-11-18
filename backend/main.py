import asyncio

from sqlalchemy import text

from db import engine


async def main():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(result.scalar_one())
    finally:
        await engine.dispose()


asyncio.run(main())
