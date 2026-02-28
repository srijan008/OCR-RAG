import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import get_settings

async def alter_db():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE documents ADD COLUMN ocr_text TEXT;'))
            print('Added ocr_text')
        except Exception as e:
            print(f'Error adding ocr_text: {e}')
            
        try:
            await conn.execute(text('ALTER TABLE documents ADD COLUMN processing_step VARCHAR(50);'))
            print('Added processing_step')
        except Exception as e:
            print(f'Error adding processing_step: {e}')
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(alter_db())
