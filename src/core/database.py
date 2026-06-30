# src/core/database.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Password123")
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_NAME = os.getenv("DB_NAME", "v_parkalert")

# 1. Connect to master to ensure target database exists
master_url = f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/master?charset=utf8"
try:
    master_engine = create_engine(master_url, isolation_level="AUTOCOMMIT")
    with master_engine.connect() as conn:
        db_exists = conn.execute(
            text("SELECT database_id FROM sys.databases WHERE name = :dbname"),
            {"dbname": DB_NAME}
        ).fetchone()
        if not db_exists:
            print(f"Database {DB_NAME} does not exist. Creating it...")
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"Database {DB_NAME} created successfully.")
except Exception as e:
    print(f"Warning: Could not check/create database: {e}")

# 2. Establish connection to main database
DATABASE_URL = f"mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}?charset=utf8"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
