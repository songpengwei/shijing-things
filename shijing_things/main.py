"""
诗经事物 - FastAPI 主应用
整合 API 路由和页面路由
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from shijing_things.core.config import get_settings
from shijing_things.core.database import engine, Base
from shijing_things.routers import api, pages, auth

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建静态文件目录
os.makedirs(settings.static_dir, exist_ok=True)
os.makedirs(settings.img_dir, exist_ok=True)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="诗经草木鸟兽虫鱼 - 纯 HTML/JS/CSS 版本",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Session 中间件（用于登录状态）
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=3600 * 24,  # 24小时
    same_site=settings.session_same_site,
    https_only=settings.session_https_only
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# 注册路由
app.include_router(pages.router)      # 页面路由（HTML 渲染）
app.include_router(api.router)        # API 路由（JSON）
app.include_router(auth.router)       # 认证路由（OAuth/登录）


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/api")
def api_root():
    """API 根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs",
        "endpoints": {
            "items": "/api/items",
            "poems": "/api/poems"
        }
    }
