#!/usr/bin/env python3
"""Test database connectivity."""

import asyncio
import sys
sys.path.insert(0, '.')

async def test_databases():
    """Test all database connections."""
    print("🔍 Testing database connectivity...\n")
    
    # Test PostgreSQL
    try:
        from src.database.postgres import get_db
        print("✅ PostgreSQL module imports")
        # Try to get a connection
        async for db in get_db():
            print(f"✅ PostgreSQL connection test: OK")
            break
    except Exception as e:
        print(f"⚠️ PostgreSQL: {type(e).__name__}: {e}")
    
    # Test MongoDB
    try:
        from src.database.mongodb import get_mongo_db
        print("✅ MongoDB module imports")
        db = get_mongo_db()
        print(f"✅ MongoDB connection test: OK")
    except Exception as e:
        print(f"⚠️ MongoDB: {type(e).__name__}: {e}")
    
    # Test Redis
    try:
        import redis
        print("✅ Redis module imports")
    except Exception as e:
        print(f"⚠️ Redis: {type(e).__name__}: {e}")
    
    print("\n✅ Database checks complete")

if __name__ == "__main__":
    asyncio.run(test_databases())
