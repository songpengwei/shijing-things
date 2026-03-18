from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from shijing_things.models.models import ShijingItem, Poem
from shijing_things.schemas.schemas import ShijingItemCreate, ShijingItemUpdate, PoemCreate, PoemUpdate


# ==================== ShijingItem CRUD ====================

class CRUDItem:
    """事物 CRUD 操作"""
    
    def get(self, db: Session, item_id: int) -> Optional[ShijingItem]:
        """根据 ID 获取单个事物"""
        return db.query(ShijingItem).filter(ShijingItem.id == item_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[ShijingItem]:
        """根据名称获取单个事物"""
        return db.query(ShijingItem).filter(ShijingItem.name == name).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[ShijingItem], int]:
        """
        获取多个事物
        返回: (items, total_count)
        """
        query = db.query(ShijingItem)
        
        # 分类筛选
        if category and category != "all":
            query = query.filter(ShijingItem.category == category)
        
        # 搜索筛选
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (ShijingItem.name.contains(search)) |
                (ShijingItem.title.contains(search)) |
                (ShijingItem.chapter.contains(search)) |
                (ShijingItem.section.contains(search)) |
                (ShijingItem.quote.contains(search))
            )
        
        # 获取总数
        total = query.count()
        
        # 分页
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    def create(self, db: Session, *, obj_in: ShijingItemCreate) -> ShijingItem:
        """创建新的事物"""
        db_obj = ShijingItem(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ShijingItem, 
        obj_in: ShijingItemUpdate
    ) -> ShijingItem:
        """更新事物"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, item_id: int) -> Optional[ShijingItem]:
        """删除事物"""
        obj = db.query(ShijingItem).get(item_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def get_categories(self, db: Session) -> List[str]:
        """获取所有分类"""
        categories = db.query(ShijingItem.category).distinct().all()
        return [c[0] for c in categories]
    
    def get_stats(self, db: Session) -> dict:
        """获取统计数据"""
        total = db.query(ShijingItem).count()
        
        # 按分类统计
        category_stats = db.query(
            ShijingItem.category,
            func.count(ShijingItem.id)
        ).group_by(ShijingItem.category).all()
        
        return {
            "total": total,
            "by_category": {cat: count for cat, count in category_stats}
        }


# ==================== Poem CRUD ====================

class CRUDPoem:
    """诗篇 CRUD 操作"""
    
    def get(self, db: Session, poem_id: int) -> Optional[Poem]:
        """根据 ID 获取诗篇"""
        return db.query(Poem).filter(Poem.id == poem_id).first()
    
    def get_by_title(self, db: Session, title: str) -> Optional[Poem]:
        """根据标题获取诗篇"""
        return db.query(Poem).filter(Poem.title == title).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        chapter: Optional[str] = None
    ) -> tuple[List[Poem], int]:
        """获取多个诗篇"""
        query = db.query(Poem)
        
        if chapter:
            query = query.filter(Poem.chapter == chapter)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    def create(self, db: Session, *, obj_in: PoemCreate) -> Poem:
        """创建诗篇"""
        db_obj = Poem(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Poem, 
        obj_in: PoemUpdate
    ) -> Poem:
        """更新诗篇"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, poem_id: int) -> Optional[Poem]:
        """删除诗篇"""
        obj = db.query(Poem).get(poem_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# 实例化 CRUD 对象
item = CRUDItem()
poem = CRUDPoem()
