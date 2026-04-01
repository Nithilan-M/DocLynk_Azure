import os
import logging
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")
logger = logging.getLogger(__name__)


def _build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        explicit_url = explicit_url.strip().strip('"').strip("'")
        if explicit_url.startswith("mysql://"):
            return explicit_url.replace("mysql://", "mysql+pymysql://", 1)
        return explicit_url

    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "doclynk")
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", "root"))
    port = os.getenv("DB_PORT", "3306")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


import ssl

def _build_mysql_connect_args() -> dict:
    ssl_mode = os.getenv("DB_SSL_MODE", "require").lower()
    if ssl_mode == "disable":
        return {}

    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        return {"ssl": {"ca": ssl_ca}}
    
    # Use standard SSL Context to avoid PyMySQL dict issues on Azure Linux
    return {"ssl": ssl.create_default_context()}


DATABASE_URL = _build_database_url()
MYSQL_CONNECT_ARGS = _build_mysql_connect_args()

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=MYSQL_CONNECT_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database_connection() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection established.")
    except SQLAlchemyError:
        logger.exception("Database connection failed. Check DATABASE_URL, SSL settings, and Azure firewall rules.")
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
