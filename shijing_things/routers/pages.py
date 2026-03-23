"""
页面路由 - 渲染 HTML 模板
"""
import json
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from shijing_things.core.config import get_settings
from shijing_things.core.database import get_db
from shijing_things.crud.crud import item as crud_item, poem as crud_poem

router = APIRouter()
templates = Jinja2Templates(directory="shijing_things/templates")
settings = get_settings()


def is_logged_in(request: Request) -> bool:
    """检查用户是否已登录（管理员或 OAuth 用户）"""
    return request.session.get("logged_in") is True or request.session.get("is_authenticated") is True


def is_admin(request: Request) -> bool:
    """检查是否是管理员"""
    return request.session.get("logged_in") is True


def is_oauth_user(request: Request) -> bool:
    """检查是否是 OAuth 登录用户"""
    return request.session.get("is_authenticated") is True


def require_login(request: Request):
    """要求登录，未登录则跳转到登录页"""
    if not is_logged_in(request):
        return RedirectResponse(url="/login?next=" + str(request.url.path), status_code=302)
    return None


def require_admin(request: Request):
    """要求管理员权限"""
    if not is_admin(request):
        return RedirectResponse(url="/login?next=" + str(request.url.path), status_code=302)
    return None


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """首页 - 展示事物列表"""
    items, total = crud_item.get_multi(
        db, skip=0, limit=1000, category=category, search=search
    )
    stats = crud_item.get_stats(db)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items,
        "total": total,
        "stats": stats,
        "current_category": category or "all",
        "search": search or "",
        "categories": [
            {"key": "all", "label": "全部", "icon": "🌿"},
            {"key": "草", "label": "草木", "icon": "🌱"},
            {"key": "木", "label": "树木", "icon": "🌳"},
            {"key": "鸟", "label": "鸟类", "icon": "🦅"},
            {"key": "兽", "label": "兽类", "icon": "🦌"},
            {"key": "虫", "label": "昆虫", "icon": "🦋"},
            {"key": "鱼", "label": "鱼类", "icon": "🐟"},
        ]
    })


@router.get("/item/{item_id}", response_class=HTMLResponse)
def item_detail(item_id: int, request: Request, db: Session = Depends(get_db)):
    """事物详情页"""
    item = crud_item.get(db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="事物不存在")
    
    # 获取所属诗篇
    poem = crud_poem.get_by_title(db, title=item.title)
    poem_content = []
    if poem:
        try:
            poem_content = json.loads(poem.content)
        except:
            poem_content = []
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "item": item,
        "poem": poem,
        "poem_content": poem_content,
    })


# ==================== 登录相关 ====================

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = "/manage", error: Optional[str] = None):
    """登录页面"""
    # 如果已登录，直接跳转
    if is_logged_in(request):
        return RedirectResponse(url=next, status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": error,
        "admin_login_enabled": bool(settings.admin_username and settings.admin_password),
        "github_oauth_enabled": bool(settings.github_client_id and settings.github_client_secret),
    })


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = Form("/manage")
):
    """登录提交"""
    if not settings.admin_username or not settings.admin_password:
        return RedirectResponse(
            url=f"/login?next={next}&error=管理员密码登录未配置",
            status_code=302
        )

    if username == settings.admin_username and password == settings.admin_password:
        request.session["logged_in"] = True
        request.session["username"] = username
        return RedirectResponse(url=next, status_code=302)
    else:
        return RedirectResponse(
            url=f"/login?next={next}&error=用户名或密码错误",
            status_code=302
        )


@router.get("/logout")
def logout(request: Request):
    """登出"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)


# ==================== 管理页面（需要管理员登录） ====================

@router.get("/manage", response_class=HTMLResponse)
def manage_page(
    request: Request, 
    db: Session = Depends(get_db),
    search: Optional[str] = None
):
    """管理页面 - 仅管理员可访问"""
    # 检查管理员登录状态
    if not is_admin(request):
        return RedirectResponse(url="/login?next=/manage", status_code=302)
    
    items, total = crud_item.get_multi(db, skip=0, limit=1000, search=search)
    
    # 分类名称映射
    category_names = {
        "草": "草木",
        "木": "树木",
        "鸟": "鸟类",
        "兽": "兽类",
        "虫": "昆虫",
        "鱼": "鱼类"
    }
    
    return templates.TemplateResponse("manage.html", {
        "request": request,
        "items": items,
        "total": total,
        "search": search or "",
        "username": request.session.get("username", ""),
        "category_names": category_names,
    })


@router.get("/manage/item/new", response_class=HTMLResponse)
def new_item_page(request: Request):
    """新建事物页面 - 仅管理员可访问"""
    # 检查管理员登录状态
    if not is_admin(request):
        return RedirectResponse(url="/login?next=/manage/item/new", status_code=302)
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "item": None,
        "is_edit": False,
        "username": request.session.get("username", ""),
    })


@router.get("/manage/item/{item_id}", response_class=HTMLResponse)
def edit_item_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    """编辑事物页面 - 仅管理员可访问"""
    # 检查管理员登录状态
    if not is_admin(request):
        return RedirectResponse(url=f"/login?next=/manage/item/{item_id}", status_code=302)
    
    item = crud_item.get(db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="事物不存在")
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "item": item,
        "is_edit": True,
        "username": request.session.get("username", ""),
    })
