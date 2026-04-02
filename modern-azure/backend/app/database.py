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
    host = os.getenv("DB_HOST", "doclynkdb.mysql.database.azure.com")
    name = os.getenv("DB_NAME", "doclynkdb")
    user = os.getenv("DB_USER", "docadmin")
    password = os.getenv("DB_PASSWORD", "secret")
    port = os.getenv("DB_PORT", "3306")
    
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    
    ssl_mode = os.getenv("DB_SSL_MODE", "require").lower()
    if ssl_mode != "disable":
        ca_path = os.getenv("DB_SSL_CA") or certifi.where()
        ca_path_encoded = urllib.parse.quote_plus(ca_path)
        url += f"?ssl_ca={ca_path_encoded}"
        
    return url


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
