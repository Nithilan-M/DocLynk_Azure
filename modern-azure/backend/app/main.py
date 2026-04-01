import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")

from .database import Base, engine, ensure_database_connection
from .routes import admin, appointments, auth, users

logger = logging.getLogger(__name__)

app = FastAPI(title="DocLynk API", version="1.0.0")

origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    ensure_database_connection()
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        existing_columns = {column["name"] for column in inspector.get_columns("users")}

        with engine.begin() as conn:
            if "is_verified" not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE"))
            if "verification_token" not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255) NULL"))
            if "token_expiry" not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN token_expiry DATETIME NULL"))

            indexes = inspector.get_indexes("users")
            index_names = {index["name"] for index in indexes}
            if "users_verification_token_key" not in index_names and "verification_token" not in index_names:
                conn.execute(text("CREATE UNIQUE INDEX users_verification_token_key ON users (verification_token)"))
    except SQLAlchemyError:
        logger.exception("Schema compatibility check failed during startup.")
        raise


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(appointments.router)
app.include_router(admin.router)
