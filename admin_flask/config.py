import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'bread_and_butter.db')
    
    # Flask configuration
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'  # Listen on all interfaces for Android emulator
    PORT = int(os.environ.get('FLASK_PORT') or 5002)
