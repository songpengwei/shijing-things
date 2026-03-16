from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.schemas import (
    ShijingItemCreate, ShijingItemUpdate, ShijingItemResponse, ShijingItemList
)
from app.crud.crud import item as crud_item

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ShijingItemList)
def list_items(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    category: Optional[str] = Query(None, description="分类筛选：草、木、鸟、兽、虫、鱼"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取事物列表
    - 支持分页
    - 支持按分类筛选
    - 支持搜索（名称、诗篇、出处、引用）
    """
    items, total = crud_item.get_multi(
        db, skip=skip, limit=limit, category=category, search=search
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    return crud_item.get_stats(db)


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return {"categories": crud_item.get_categories(db)}


@router.get("/{item_id}", response_model=ShijingItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    根据 ID 获取单个事物详情
    """
    db_item = crud_item.get(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"事物 ID {item_id} 不存在"
        )
    return db_item


@router.post("/", response_model=ShijingItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ShijingItemCreate, db: Session = Depends(get_db)):
    """
    创建新的事物
    """
    # 检查是否已存在同名事物
    existing = crud_item.get_by_name(db, name=item_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"事物 '{item_in.name}' 已存在"
        )
    
    return crud_item.create(db, obj_in=item_in)


@router.put("/{item_id}", response_model=ShijingItemResponse)
def update_item(
    item_id: int, 
    item_in: ShijingItemUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新事物信息
    """
    db_item = crud_item.get(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"事物 ID {item_id} 不存在"
        )
    
    return crud_item.update(db, db_obj=db_item, obj_in=item_in)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """
    删除事物
    """
    db_item = crud_item.delete(db, item_id=item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"事物 ID {item_id} 不存在"
        )
    return None
