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
from shijing_things.core.session_auth import (
    clear_admin_session,
    get_comment_auth_label,
    is_admin_logged_in,
    is_comment_interactive_user,
    is_comment_user_logged_in,
)
from shijing_things.crud.crud import item as crud_item, poem as crud_poem, site_setting as crud_site_setting

router = APIRouter()
templates = Jinja2Templates(directory="shijing_things/templates")
settings = get_settings()
MANAGE_TABS = {"items", "comments", "users", "security"}


def is_logged_in(request: Request) -> bool:
    """检查用户是否已登录（管理员或 OAuth 用户）"""
    return is_admin_logged_in(request) or is_comment_user_logged_in(request)


def is_admin(request: Request) -> bool:
    """检查是否是管理员"""
    return is_admin_logged_in(request)


def is_oauth_user(request: Request) -> bool:
    """检查是否是可用于留言的登录用户"""
    return is_comment_interactive_user(request)


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
    category_options = [
        {"key": "all", "label": "全部", "icon": "🌿"},
        {"key": "草", "label": "草木", "icon": "🌱"},
        {"key": "木", "label": "树木", "icon": "🌳"},
        {"key": "鸟", "label": "鸟类", "icon": "🦅"},
        {"key": "兽", "label": "兽类", "icon": "🦌"},
        {"key": "虫", "label": "昆虫", "icon": "🦋"},
        {"key": "鱼", "label": "鱼类", "icon": "🐟"},
    ]

    items, total = crud_item.get_multi(
        db, skip=0, limit=1000, category=category, search=search
    )
    stats = crud_item.get_stats(db)
    homepage_preview_count = crud_site_setting.get_int(
        db,
        key="homepage_category_preview_count",
        default=8,
    )
    grouped_items = []

    if (category or "all") == "all":
        for category_option in category_options:
            category_key = category_option["key"]
            if category_key == "all":
                continue
            section_items = [item for item in items if item.category == category_key]
            if section_items:
                grouped_items.append({
                    "key": category_key,
                    "label": category_option["label"],
                    "icon": category_option["icon"],
                    "count": len(section_items),
                    "items": section_items,
                })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items,
        "grouped_items": grouped_items,
        "homepage_preview_count": homepage_preview_count,
        "total": total,
        "stats": stats,
        "current_category": category or "all",
        "search": search or "",
        "is_oauth_user": is_oauth_user(request),
        "github_login_url": f"/auth/login?next={request.url.path}",
        "wechat_login_url": f"/auth/login?provider=wechat&next={request.url.path}",
        "comment_login_page_url": f"/login?next={request.url.path}",
        "comment_user_name": request.session.get("comment_nickname") or request.session.get("comment_username") or "登录用户",
        "comment_user_avatar": request.session.get("comment_avatar_url") or "",
        "comment_auth_label": get_comment_auth_label(request),
        "google_login_url": f"/auth/login?provider=google&next={request.url.path}",
        "google_oauth_enabled": bool(settings.google_client_id and settings.google_client_secret),
        "wechat_oauth_enabled": bool(settings.wechat_app_id and settings.wechat_app_secret),
        "categories": category_options
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
        "is_admin": is_admin(request),
        "is_oauth_user": is_oauth_user(request),
        "github_login_url": f"/auth/login?next={request.url.path}",
        "wechat_login_url": f"/auth/login?provider=wechat&next={request.url.path}",
        "comment_login_page_url": f"/login?next={request.url.path}",
        "comment_user_name": request.session.get("comment_nickname") or request.session.get("comment_username") or "登录用户",
        "comment_user_avatar": request.session.get("comment_avatar_url") or "",
        "comment_auth_label": get_comment_auth_label(request),
        "google_login_url": f"/auth/login?provider=google&next={request.url.path}",
        "google_oauth_enabled": bool(settings.google_client_id and settings.google_client_secret),
        "wechat_oauth_enabled": bool(settings.wechat_app_id and settings.wechat_app_secret),
    })


# ==================== 登录相关 ====================

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = "/manage", error: Optional[str] = None):
    """登录页面"""
    # 管理员已登录时，访问管理员目标页直接跳转；留言用户不应阻塞管理员再次登录
    if is_admin(request) and next and next.startswith("/manage"):
        return RedirectResponse(url=next, status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": error,
        "is_admin_logged_in": is_admin(request),
        "admin_username": request.session.get("admin_username", ""),
        "is_comment_logged_in": is_comment_user_logged_in(request),
        "comment_user_name": request.session.get("comment_nickname") or request.session.get("comment_username") or "登录用户",
        "comment_auth_label": get_comment_auth_label(request),
        "admin_login_enabled": bool(settings.admin_username and settings.admin_password),
        "email_login_enabled": bool(
            settings.smtp_host
            and settings.smtp_username
            and settings.smtp_password
            and settings.smtp_from_email
        ),
        "email_login_code_expire_minutes": settings.email_login_code_expire_minutes,
        "github_oauth_enabled": bool(settings.github_client_id and settings.github_client_secret),
        "google_oauth_enabled": bool(settings.google_client_id and settings.google_client_secret),
        "wechat_oauth_enabled": bool(settings.wechat_app_id and settings.wechat_app_secret),
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
        request.session["admin_logged_in"] = True
        request.session["admin_username"] = username
        return RedirectResponse(url=next, status_code=302)
    else:
        return RedirectResponse(
            url=f"/login?next={next}&error=用户名或密码错误",
            status_code=302
        )


@router.get("/logout")
def logout(request: Request):
    """登出"""
    clear_admin_session(request)
    return RedirectResponse(url="/", status_code=302)


# ==================== 管理页面（需要管理员登录） ====================

def render_manage_page(
    request: Request,
    *,
    active_tab: str,
    db: Session,
    search: Optional[str] = None
):
    """渲染管理页面"""
    if not is_admin(request):
        return RedirectResponse(url=f"/login?next=/manage/{active_tab}", status_code=302)

    items = []
    total = 0
    if active_tab == "items":
        items, total = crud_item.get_multi(db, skip=0, limit=1000, search=search)

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
        "active_tab": active_tab,
        "manage_tab_urls": {
            "items": "/manage/items",
            "comments": "/manage/comments",
            "users": "/manage/users",
            "security": "/manage/security",
        },
        "username": request.session.get("admin_username", ""),
        "category_names": category_names,
    })


@router.get("/manage")
def manage_page_redirect():
    """管理首页重定向到事物管理"""
    return RedirectResponse(url="/manage/items", status_code=302)


@router.get("/manage/items", response_class=HTMLResponse)
def manage_items_page(
    request: Request,
    db: Session = Depends(get_db),
    search: Optional[str] = None
):
    return render_manage_page(request, active_tab="items", db=db, search=search)


@router.get("/manage/comments", response_class=HTMLResponse)
def manage_comments_page(request: Request, db: Session = Depends(get_db)):
    return render_manage_page(request, active_tab="comments", db=db)


@router.get("/manage/users", response_class=HTMLResponse)
def manage_users_page(request: Request, db: Session = Depends(get_db)):
    return render_manage_page(request, active_tab="users", db=db)


@router.get("/manage/security", response_class=HTMLResponse)
def manage_security_page(request: Request, db: Session = Depends(get_db)):
    return render_manage_page(request, active_tab="security", db=db)


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
        "username": request.session.get("admin_username", ""),
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
        "username": request.session.get("admin_username", ""),
    })
