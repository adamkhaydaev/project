# config.py
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from environs import Env
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # СИНХРОННЫЙ URL для SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    ADMIN_LOGIN: str = os.getenv("ADMIN_LOGIN", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")


settings = Settings()


@dataclass
class DatabaseConfig:
    database_url: str


@dataclass
class Config:
    db: DatabaseConfig
    secret_key: str
    debug: bool


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)  # Загружаем переменные окружения из файла .env

    return Config(
        db=DatabaseConfig(database_url=env("DATABASE_URL")),
        secret_key=env("SECRET_KEY"),
        debug=env.bool("DEBUG", default=False),
    )
