"""Check migration status"""
import asyncio
from app.db.session import engine
from sqlalchemy import text


async def check_migration():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            if version:
                print(f"✅ Current migration version: {version}")
            else:
                print("⚠️  No migration version found")
    except Exception as e:
        print(f"❌ Error checking migration: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_migration())
