"""Database configuration and session management using SQLAlchemy and SQLite."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Locate database file inside backend/storage/
backend_dir = Path(__file__).resolve().parent.parent
storage_dir = backend_dir / "storage"
storage_dir.mkdir(parents=True, exist_ok=True)
db_path = storage_dir / "change_detection.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite multithreading
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create database tables."""
    from . import models
    Base.metadata.create_all(bind=engine)
