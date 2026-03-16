from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "诗经事物 API"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./shijing.db"
    static_dir: str = "./static"
    img_dir: str = "./static/img"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
