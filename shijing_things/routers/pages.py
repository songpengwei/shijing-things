"""
页面路由 - 渲染 HTML 模板
"""
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from shijing_things.core.database import get_db
from shijing_things.crud.crud import item as crud_item, poem as crud_poem

router = APIRouter()
templates = Jinja2Templates(directory="shijing_things/templates")


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
    poem = crud_poem.get_by_title(db, title=item.poem)
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


@router.get("/manage", response_class=HTMLResponse)
def manage_page(request: Request, db: Session = Depends(get_db)):
    """管理页面"""
    items, _ = crud_item.get_multi(db, skip=0, limit=1000)
    return templates.TemplateResponse("manage.html", {
        "request": request,
        "items": items,
    })


@router.get("/manage/item/new", response_class=HTMLResponse)
def new_item_page(request: Request):
    """新建事物页面"""
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "item": None,
        "is_edit": False,
    })


@router.get("/manage/item/{item_id}", response_class=HTMLResponse)
def edit_item_page(item_id: int, request: Request, db: Session = Depends(get_db)):
    """编辑事物页面"""
    item = crud_item.get(db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="事物不存在")
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "item": item,
        "is_edit": True,
    })
