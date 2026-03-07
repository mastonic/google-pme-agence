from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_pulse.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, index=True) # Usually Google Place ID
    name = Column(String, index=True)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    rating = Column(Float)
    user_ratings_total = Column(Float)
    photos = Column(JSON) # List of photo references
    website = Column(String) # Business website URL
    status = Column(String, default="scanned") # scanned, processing, completed, deployed, etc.
    potential_score = Column(Float, default=0.0)
    category = Column(JSON) # Store Google Places types
    template = Column(String) # Chosen template (e.g. BENTO_GRID, etc.)
    email_status = Column(String, default="not_sent") # not_sent, draft, sent, opened
    generated_copy = Column(JSON)
    deployment_url = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
