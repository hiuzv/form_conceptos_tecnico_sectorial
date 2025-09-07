import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import URL
from Backend.utils.config import settings

for k in ("PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR", "PGPASSFILE",
          "PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"):
    os.environ.pop(k, None)

url = URL.create(
    "postgresql+psycopg",  
    username=settings.DB_USER,
    password=settings.DB_PASS,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

engine = create_engine(url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

