import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Loads variables from a local .env file (only used on your laptop —
# Railway already provides these directly as real environment
# variables, so this line does nothing on the live deployment).
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All files in models/ import this Base and attach their tables to
# it, so SQLAlchemy knows what tables exist.
Base = declarative_base()


def get_db():
    """FastAPI dependency: gives each request its own DB session,
    and always closes it afterward, even if an error happens."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()