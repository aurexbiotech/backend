from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# SQLite requires explicit thread-check configuration in the test server.
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# If a MySQL URL is configured but the server is not running (for example in local tests),
# transparently fall back to the bundled SQLite database so the app still starts.
try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception:
    if settings.DATABASE_URL.startswith("mysql"):
        engine = create_engine("sqlite:///./aurex_hms.db", connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for models
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
