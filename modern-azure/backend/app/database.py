import os
from pathlib import Path
from urllib.parse import quote_plus
from urllib.parse import urlencode

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


def _build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        explicit_url = explicit_url.strip().strip('"').strip("'")
        if explicit_url.startswith("postgresql://"):
            return explicit_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return explicit_url

    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "doclynk")
    user = os.getenv("DB_USER", "postgres")
    password = quote_plus(os.getenv("DB_PASSWORD", "postgres"))
    port = os.getenv("DB_PORT", "5432")
    sslmode = os.getenv("DB_SSLMODE")

    base = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    if sslmode:
        return f"{base}?{urlencode({'sslmode': sslmode})}"
    return base


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
