"""
RESTful API 路由
提供 JSON 格式的数据接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from shijing_things.core.database import get_db
from shijing_things.schemas.schemas import (
    ShijingItemCreate, ShijingItemUpdate, ShijingItemResponse, ShijingItemList,
    PoemCreate, PoemUpdate, PoemResponse, PoemList
)
from shijing_things.crud.crud import item as crud_item, poem as crud_poem

router = APIRouter(prefix="/api")


# ==================== 事物 API ====================

@router.get("/items/", response_model=ShijingItemList)
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取事物列表"""
    items, total = crud_item.get_multi(
        db, skip=skip, limit=limit, category=category, search=search
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/items/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    return crud_item.get_stats(db)


@router.get("/items/categories")
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return {"categories": crud_item.get_categories(db)}


@router.get("/items/{item_id}", response_model=ShijingItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """获取单个事物"""
    db_item = crud_item.get(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="事物不存在")
    return db_item


@router.post("/items/", response_model=ShijingItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ShijingItemCreate, db: Session = Depends(get_db)):
    """创建事物"""
    existing = crud_item.get_by_name(db, name=item_in.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"事物 '{item_in.name}' 已存在")
    return crud_item.create(db, obj_in=item_in)


@router.put("/items/{item_id}", response_model=ShijingItemResponse)
def update_item(item_id: int, item_in: ShijingItemUpdate, db: Session = Depends(get_db)):
    """更新事物"""
    db_item = crud_item.get(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="事物不存在")
    return crud_item.update(db, db_obj=db_item, obj_in=item_in)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """删除事物"""
    db_item = crud_item.delete(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="事物不存在")
    return None


# ==================== 诗篇 API ====================

@router.get("/poems/", response_model=PoemList)
def list_poems(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    chapter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取诗篇列表"""
    items, total = crud_poem.get_multi(db, skip=skip, limit=limit, chapter=chapter)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/poems/{poem_id}", response_model=PoemResponse)
def get_poem(poem_id: int, db: Session = Depends(get_db)):
    """获取诗篇"""
    db_poem = crud_poem.get(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return db_poem


@router.get("/poems/title/{title}", response_model=PoemResponse)
def get_poem_by_title(title: str, db: Session = Depends(get_db)):
    """根据标题获取诗篇"""
    db_poem = crud_poem.get_by_title(db, title=title)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return db_poem


@router.post("/poems/", response_model=PoemResponse, status_code=status.HTTP_201_CREATED)
def create_poem(poem_in: PoemCreate, db: Session = Depends(get_db)):
    """创建诗篇"""
    existing = crud_poem.get_by_title(db, title=poem_in.title)
    if existing:
        raise HTTPException(status_code=400, detail=f"诗篇 '{poem_in.title}' 已存在")
    return crud_poem.create(db, obj_in=poem_in)


@router.put("/poems/{poem_id}", response_model=PoemResponse)
def update_poem(poem_id: int, poem_in: PoemUpdate, db: Session = Depends(get_db)):
    """更新诗篇"""
    db_poem = crud_poem.get(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return crud_poem.update(db, db_obj=db_poem, obj_in=poem_in)


@router.delete("/poems/{poem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poem(poem_id: int, db: Session = Depends(get_db)):
    """删除诗篇"""
    db_poem = crud_poem.delete(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return None
