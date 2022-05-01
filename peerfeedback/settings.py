# -*- coding: utf-8 -*-
"""Application configuration."""
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get("PEERFEEDBACK_SECRET", "super-secret")
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = "redis"  # Can be "memcached", "redis", etc.
    CACHE_REDIS_URL = os.environ.get("REDIS_URL") + "/1"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = SECRET_KEY
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    ERROR_404_HELP = False

    CANVAS_API_URL = os.environ.get("CANVAS_API_URL")
    CANVAS = dict(
        client_id=os.environ.get("CANVAS_CONSUMER_KEY"),
        client_secret=os.environ.get("CANVAS_CONSUMER_SECRET"),
        request_token_url=None,
        access_token_url=os.environ.get("CANVAS_ACCESS_TOKEN_URL"),
        authorize_url=os.environ.get("CANVAS_AUTHORIZE_URL"),
        api_base_url=os.environ.get("CANVAS_BASE_URL"),
    )

    BUNDLE_ERRORS = True
    SEND_NOTIFICATION_EMAILS = True
    RQ_REDIS_URL = os.environ.get("REDIS_URL") + "/0"
    RQ_QUEUES = ["default", "high", "low", "scheduled", "cron"]
    RQ_SCHEDULER_QUEUE = "scheduled"
    CRON_PATTERN = "10 * * * *"  # every hour at XX:10
    LOGIN_TYPE = os.environ.get("LOGIN_TYPE", "canvas_oauth")
    CAS_SERVER = os.environ.get("CAS_SERVER")
    CAS_AFTER_LOGIN = "user.post_login"
    S3_BUCKET = os.environ.get("S3_BUCKET")
    S3_KEY = os.environ.get("S3_KEY")
    S3_SECRET = os.environ.get("S3_SECRET")
    SEND_SUPPORT_EMAILS = True
    MLAPP_URL = os.environ.get("MLAPP_URL")


class ProdConfig(Config):
    """Production configuration."""

    ENV = "prod"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    SEND_NOTIFICATION_EMAILS = True


class DevConfig(Config):
    """Development configuration."""

    ENV = "dev"
    DEBUG = True
    DB_NAME = "dev.db"
    # Put the db file in project root
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = "postgresql://docker:docker@db:5432/docker"
    DEBUG_TB_ENABLED = True
    SEND_NOTIFICATION_EMAILS = False
    SEND_SUPPORT_EMAILS = False


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql://docker:docker@localhost:5432/testdb"
    )
    SEND_NOTIFICATION_EMAILS = False
    CANVAS_API_URL = "http://localhost:8888/"
    CACHE_TYPE = "null"
    CACHE_NO_NULL_WARNING = True
    SEND_SUPPORT_EMAILS = False
    WTF_CSRF_ENABLED = False
    WTF_CSRF_METHODS = []
