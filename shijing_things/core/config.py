from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


# 项目根目录（shijing_things 的父目录）
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "诗经事物 API"
    app_version: str = "1.0.0"
    database_url: str = f"sqlite:///{ROOT_DIR / 'shijing.db'}"
    static_dir: str = str(ROOT_DIR / "shijing_things" / "static")
    img_dir: str = str(ROOT_DIR / "shijing_things" / "static" / "img")
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
