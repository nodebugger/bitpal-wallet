"""
Test Supabase Database Connection
"""
import asyncio
import asyncpg
from app.core.config import settings


async def test_connection():
    """Test database connection"""
    print("🔍 Testing Supabase connection...")
    print(f"📦 Database URL: {settings.DATABASE_URL.replace('rigmarole100', '****')}")
    
    try:
        # Extract connection details from DATABASE_URL
        url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        print("\n⏳ Attempting to connect...")
        conn = await asyncpg.connect(url, timeout=10)
        
        print("✅ Connection successful!")
        
        # Test a simple query
        version = await conn.fetchval("SELECT version()")
        print(f"\n🎉 PostgreSQL Version: {version[:50]}...")
        
        await conn.close()
        print("\n✅ Connection closed successfully")
        return True
        
    except asyncio.TimeoutError:
        print("\n❌ Connection timeout! The database server is not responding.")
        print("   Check if your Supabase project is active.")
        return False
        
    except asyncpg.InvalidPasswordError:
        print("\n❌ Invalid password! Check your database credentials.")
        return False
        
    except OSError as e:
        if "getaddrinfo failed" in str(e):
            print(f"\n❌ DNS Resolution Failed: {e}")
            print("   The hostname 'db.foecsuxxtixurkilhqev.supabase.co' cannot be resolved.")
            print("\n💡 Possible solutions:")
            print("   1. Check your internet connection")
            print("   2. Verify the hostname in your Supabase dashboard")
            print("   3. Check if you have firewall/network restrictions")
        else:
            print(f"\n❌ Network error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
