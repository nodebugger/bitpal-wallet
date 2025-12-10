"""Verify database tables"""
import asyncio
from app.db.session import engine
from sqlalchemy import text


async def check_tables():
    try:
        async with engine.connect() as conn:
            # Check what tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print("✅ Tables in database:")
            for table in tables:
                print(f"   • {table}")
            
            # Count rows in each table
            print("\n📊 Table row counts:")
            for table in tables:
                if table != 'alembic_version':
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   • {table}: {count} rows")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_tables())
