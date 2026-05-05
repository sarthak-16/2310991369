"""
Configuration Management for Campus Notification System
Handles environment-specific configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database (SQLite - local file-based)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///./campus_notifications.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False') == 'True'
    
    # Connection pooling (minimal for SQLite)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'connect_args': {'timeout': 10},
    }
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # API
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # Pagination defaults
    PAGINATION_DEFAULT_LIMIT = 20
    PAGINATION_MAX_LIMIT = 100
    
    # Notification settings
    PRIORITY_INBOX_DEFAULT_SIZE = 10
    NOTIFICATION_CACHE_TTL = 300  # 5 minutes
    UNREAD_COUNT_CACHE_TTL = 60   # 1 minute
    
    # Bulk notification settings
    BULK_NOTIFICATION_BATCH_SIZE = 100
    BULK_NOTIFICATION_RETRY_ATTEMPTS = 3
    BULK_NOTIFICATION_TIMEOUT = 30  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/notification_system.log')
    
    # Email
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    # External APIs
    NOTIFICATION_API_URL = os.getenv(
        'NOTIFICATION_API_URL',
        'http://20.207.122.201/evaluation-service/notifications'
    )
    NOTIFICATION_API_TOKEN = os.getenv('NOTIFICATION_API_TOKEN', '')
    API_REQUEST_TIMEOUT = 30  # seconds


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF token checking for testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # SQLite settings for production (with increased timeout)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'connect_args': {'timeout': 15},
    }
    
    # Higher cache TTL in production
    NOTIFICATION_CACHE_TTL = 600  # 10 minutes
    UNREAD_COUNT_CACHE_TTL = 120  # 2 minutes


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get appropriate configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
