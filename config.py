import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database configuration with Railway support
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Parse Railway DATABASE_URL
        url = urlparse(DATABASE_URL)
        DB_HOST = url.hostname
        DB_PORT = url.port or 3306
        DB_NAME = url.path[1:] if url.path else 'railway'  # Remove leading slash
        DB_USER = url.username
        DB_PASSWORD = url.password
    else:
        # Fallback to individual env vars
        DB_HOST = os.environ.get('DB_HOST') or 'localhost'
        DB_PORT = os.environ.get('DB_PORT') or '3306'
        DB_NAME = os.environ.get('DB_NAME') or 'flask_app'
        DB_USER = os.environ.get('DB_USER') or 'root'
        DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')    # PayOS configuration
    PAYOS_CLIENT_ID = os.environ.get('PAYOS_CLIENT_ID')
    PAYOS_API_KEY = os.environ.get('PAYOS_API_KEY')
    PAYOS_CHECKSUM_KEY = os.environ.get('PAYOS_CHECKSUM_KEY')
    PAYOS_RETURN_URL = os.environ.get('PAYOS_RETURN_URL') or 'http://localhost:5000/payment/return'
    PAYOS_CANCEL_URL = os.environ.get('PAYOS_CANCEL_URL') or 'http://localhost:5000/payment/cancel'
      # File download configuration
    DOWNLOAD_FILE_PATH = os.environ.get('DOWNLOAD_FILE_PATH') or 'downloads/app.exe'
    DOWNLOAD_FILE_URL = os.environ.get('DOWNLOAD_FILE_URL')  # Google Drive direct download URL
    DOWNLOAD_FILE_NAME = os.environ.get('DOWNLOAD_FILE_NAME') or 'App.exe'
    
    # Payment amount (in VND for PayOS)
    PAYMENT_AMOUNT = int(os.environ.get('PAYMENT_AMOUNT', '50000'))  # 50,000 VND
    PAYMENT_CURRENCY = 'VND'
