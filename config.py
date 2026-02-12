import os
import sys

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    db_url = os.environ.get('DATABASE_URL')
    
    print(f"--- DEBUG: DATABASE_URL is {'SET' if db_url else 'NOT SET'} ---", file=sys.stderr)
    
    if db_url:
        db_url = db_url.strip()
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        SQLALCHEMY_DATABASE_URI = None 
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False