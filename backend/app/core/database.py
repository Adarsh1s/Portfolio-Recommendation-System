from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings
from urllib.parse import urlparse, parse_qs, urlunparse

settings = get_settings()

db_url = settings.DATABASE_URL

# Parse the URL and its query params so we can decide whether SSL is required.
parsed = urlparse(db_url)
query_params = parse_qs(parsed.query or "")

# Determine SSL usage. Priority:
# 1. explicit `ssl` query param (e.g. ?ssl=false)
# 2. `sslmode` query param (e.g. ?sslmode=require)
# 3. hostname heuristic (neon.tech -> SSL; localhost/postgres -> no SSL)
ssl_required = None

if "ssl" in query_params:
    v = query_params.get("ssl", [""])[0].lower()
    ssl_required = not (v in ("0", "false", "no", "off", "disable"))

if ssl_required is None and "sslmode" in query_params:
    m = query_params.get("sslmode", [""])[0].lower()
    if m in ("disable", "allow", "prefer"):
        ssl_required = False
    elif m in ("require", "verify-ca", "verify-full"):
        ssl_required = True

if ssl_required is None:
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "postgres"):
        ssl_required = False
    elif "neon.tech" in parsed.netloc:
        ssl_required = True
    else:
        # Default to no SSL for local/dev unless explicitly required
        ssl_required = False

# Rebuild a cleaned DB URL without query parameters for SQLAlchemy/asyncpg
clean_parsed = parsed._replace(query="")
db_url = urlunparse(clean_parsed)

# Convert postgresql:// to postgresql+asyncpg:// if needed
if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {}
if ssl_required:
    connect_args = {"ssl": True}
else:
    connect_args = {"ssl": False}

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
