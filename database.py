# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# read .env into environment variables
load_dotenv()

# single full URL from .env 
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    
)

# create an engine (connection pool) and a session factory
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for our ORM models
Base = declarative_base()
