import sys
from .connection import get_database_info, engine
from sqlalchemy import text

if __name__ == "__main__":
    db_info = get_database_info()

    print("\n" + "=" * 60)
    print("Database Connection Check")
    print("=" * 60)
    print(f"Environment: {db_info['environment']}")
    print(f"Database URL: {db_info['url_masked']}")
    print(f"Host: {db_info['host']}")
    print("=" * 60 + "\n")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print("✓ Connection successful!")
            print(f"✓ PostgreSQL version: {version.split(',')[0]}")

            result = conn.execute(text("SELECT COUNT(*) FROM digests"))
            count = result.scalar()
            print(f"✓ Digests table exists with {count} records")

            result = conn.execute(
                text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'digests' AND column_name = 'sent_at'
            """)
            )
            has_sent_at = result.fetchone() is not None
            if has_sent_at:
                print("✓ sent_at column exists")
            else:
                print("⚠ sent_at column does not exist (run migration)")

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)