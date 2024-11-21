from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models.base import Base

# Load environment variables
load_dotenv(override=True)

# Construct DATABASE_URL using environment variables
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,              # Minimum number of connections
    max_overflow=15,          # Maximum number of connections above pool_size
    pool_timeout=30,          # Seconds to wait before timing out on pool get
    pool_recycle=1800,        # Recycle connections after 30 minutes
    pool_pre_ping=True,       # Enable connection health checks
    # Add these connection arguments for Supabase compatibility
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

