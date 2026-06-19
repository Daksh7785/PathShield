import os
import asyncio
import asyncpg
from pathlib import Path

# Load connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/routeresilience")

# Extract params from SQLAlchemy URL to build standard DSN
# e.g., postgresql+asyncpg://postgres:postgres@localhost:5432/routeresilience -> postgresql://postgres:postgres@localhost:5432/routeresilience
dsn = DATABASE_URL.replace("+asyncpg", "")

async def seed():
    print(f"Connecting to database: {dsn}")
    
    # Try to connect with retries
    conn = None
    for attempt in range(5):
        try:
            conn = await asyncpg.connect(dsn)
            break
        except Exception as e:
            print(f"Connection attempt {attempt+1}/5 failed: {e}")
            await asyncio.sleep(2)
            
    if conn is None:
        print("❌ Could not connect to the database. Make sure your PostgreSQL server is running and accessible.")
        return

    try:
        # Read migration file
        migration_path = Path(__file__).parent.parent / "database" / "migrations" / "001_initial_schema.sql"
        if not migration_path.exists():
            print(f"❌ Migration file not found at {migration_path}")
            return
            
        with open(migration_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        print("Executing initial migration schema...")
        await conn.execute(sql_script)
        
        # Verify cities count
        rows = await conn.fetch("SELECT COUNT(*) FROM cities;")
        count = rows[0][0]
        
        print(f"✓ Database initialized. Current city count in table: {count}")
        print("╔══════════════════════════════╗")
        print("║  DATABASE INITIALIZED        ║")
        print(f"║  Seeded Cities: {count}            ║")
        print("╚══════════════════════════════╝")
        
    except Exception as e:
        print(f"❌ Error during database seeding: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(seed())
