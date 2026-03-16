from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.schemas import (
    PoemCreate, PoemUpdate, PoemResponse, PoemList
)
from app.crud.crud import poem as crud_poem

router = APIRouter(prefix="/poems", tags=["poems"])


@router.get("/", response_model=PoemList)
def list_poems(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    chapter: Optional[str] = Query(None, description="章节筛选"),
    db: Session = Depends(get_db)
):
    """
    获取诗篇列表
    - 支持分页
    - 支持按章节筛选
    """
    items, total = crud_poem.get_multi(db, skip=skip, limit=limit, chapter=chapter)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{poem_id}", response_model=PoemResponse)
def get_poem(poem_id: int, db: Session = Depends(get_db)):
    """
    根据 ID 获取诗篇详情
    """
    db_poem = crud_poem.get(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"诗篇 ID {poem_id} 不存在"
        )
    return db_poem


@router.get("/title/{title}", response_model=PoemResponse)
def get_poem_by_title(title: str, db: Session = Depends(get_db)):
    """
    根据标题获取诗篇详情
    """
    db_poem = crud_poem.get_by_title(db, title=title)
    if not db_poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"诗篇 '{title}' 不存在"
        )
    return db_poem


@router.post("/", response_model=PoemResponse, status_code=status.HTTP_201_CREATED)
def create_poem(poem_in: PoemCreate, db: Session = Depends(get_db)):
    """
    创建新的诗篇
    """
    # 检查是否已存在同标题诗篇
    existing = crud_poem.get_by_title(db, title=poem_in.title)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"诗篇 '{poem_in.title}' 已存在"
        )
    
    return crud_poem.create(db, obj_in=poem_in)


@router.put("/{poem_id}", response_model=PoemResponse)
def update_poem(
    poem_id: int, 
    poem_in: PoemUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新诗篇信息
    """
    db_poem = crud_poem.get(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"诗篇 ID {poem_id} 不存在"
        )
    
    return crud_poem.update(db, db_obj=db_poem, obj_in=poem_in)


@router.delete("/{poem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poem(poem_id: int, db: Session = Depends(get_db)):
    """
    删除诗篇
    """
    db_poem = crud_poem.delete(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"诗篇 ID {poem_id} 不存在"
        )
    return None
