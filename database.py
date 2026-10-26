from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# SQLAlchemy engine connecting to MySQL database
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Automatically tests connection health
    pool_recycle=3600,   # Recycles connections every hour
)

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
