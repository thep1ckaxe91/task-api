import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    """Base configuration for tasks-api."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production")
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_SECONDS = int(os.environ.get("JWT_EXPIRATION_SECONDS", "3600"))

    # Path to openapi.yaml
    OPENAPI_YAML_PATH = Path(os.environ.get("OPENAPI_YAML_PATH", BASE_DIR / "docs" / "openapi.yaml"))

    # JSON Formatting
    JSON_SORT_KEYS = False
    RESTFUL_JSON = {"ensure_ascii": False}


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    JWT_SECRET_KEY = "test-jwt-secret-key-32-bytes-minimum-rfc-7518-compliant!"


class ProductionConfig(Config):
    """Production environment configuration with strict validation."""

    DEBUG = False
    ENV = "production"

    @classmethod
    def validate(cls):
        jwt_key = os.environ.get("JWT_SECRET_KEY")
        if not jwt_key or jwt_key == "dev-jwt-secret-key-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be explicitly set and secure in production environment.")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
