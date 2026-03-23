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
    
    # 留言系统配置
    default_max_comments_per_page: int = 3  # 默认每页面最多留言数
    comment_approval_required: bool = False  # 是否需要审核
    
    # 安全防护配置
    comment_cooldown_seconds: int = 30  # 两次留言之间的冷却时间（秒）
    max_comments_per_hour_per_user: int = 10  # 每小时每用户最大留言数
    max_comments_per_hour_per_ip: int = 20  # 每小时每IP最大留言数
    max_comments_per_day_per_ip: int = 50  # 每天每IP最大留言数
    enable_ip_blacklist: bool = True  # 是否启用IP黑名单
    enable_spam_filter: bool = True  # 是否启用垃圾内容过滤
    spam_keywords: list = ["广告", "加微信", "加QQ", "转账", "赌博", "色情"]  # 垃圾关键词
    
    # GitHub OAuth 配置
    github_client_id: str = ""  # GitHub OAuth App Client ID
    github_client_secret: str = ""  # GitHub OAuth App Client Secret
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"  # 回调地址
    
    # 应用安全配置
    secret_key: str = "shijing-things-secret-key-change-in-production"  # JWT 密钥
    access_token_expire_minutes: int = 60 * 24 * 7  # Token 过期时间（7天）
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
