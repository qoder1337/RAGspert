import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASEDIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
APPDIR = os.path.abspath(os.path.dirname(__file__))


class AppSettings(BaseSettings):
    APP_ENV: str
    GEMINI_API_KEY: str
    EMBED_STORE: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASEDIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProductionConfig(AppSettings):
    EMBED_STORE: str = Field(..., validation_alias="PGVECTOR_EMBED_STORE")
    TABLE_PREFIX: str = "prod_"
    DEBUG: bool = False
    RELOAD: bool = False
    APP_NAME: str = "RAGspert with FastAPI (Production)"


class DevelopmentConfig(AppSettings):
    EMBED_STORE: str = Field(..., validation_alias="PGVECTOR_EMBED_STORE")
    TABLE_PREFIX: str = "dev_"
    DEBUG: bool = True
    RELOAD: bool = True
    APP_NAME: str = "RAGspert with FastAPI (Development)"


class TestingConfig(AppSettings):
    EMBED_STORE: str = Field(..., validation_alias="PGVECTOR_EMBED_STORE")
    TABLE_PREFIX: str = "test_"
    DEBUG: bool = True
    RELOAD: bool = True
    APP_NAME: str = "RAGspert with FastAPI (Testing)"


config_setting = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

choose_setting = os.getenv("APP_ENV", "development")
SET_CONF = config_setting[choose_setting]()
