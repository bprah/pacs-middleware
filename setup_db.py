# setup_db.py
from app.db.database import Base, engine
import asyncio

# Import all models so they are registered with the Base metadata.
import app.db.models


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(create_tables())
