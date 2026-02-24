
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Document

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document).order_by(Document.created_at.desc()).limit(5))
        docs = result.scalars().all()
        for d in docs:
            print(f"ID: {d.id} | Status: {d.status} | Error: {d.error_message}")

if __name__ == "__main__":
    asyncio.run(check())
