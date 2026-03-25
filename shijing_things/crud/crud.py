from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime

from shijing_things.models.models import (
    ShijingItem, Poem, Comment, GuestUser, RateLimit, IPBlacklist, SpamPattern,
    User, OAuthAccount, UserSession, EmailLoginCode
)
from shijing_things.schemas.schemas import (
    ShijingItemCreate, ShijingItemUpdate, PoemCreate, PoemUpdate,
    CommentCreate, CommentUpdate, GuestUserCreate, GuestUserUpdate,
    UserAdminCreate
)


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


# ==================== GuestUser CRUD ====================

class CRUDGuestUser:
    """访客用户 CRUD 操作"""
    
    def get(self, db: Session, user_id: int) -> Optional[GuestUser]:
        """根据 ID 获取用户"""
        return db.query(GuestUser).filter(GuestUser.id == user_id).first()
    
    def get_by_identifier(self, db: Session, identifier: str) -> Optional[GuestUser]:
        """根据标识符获取用户"""
        return db.query(GuestUser).filter(GuestUser.identifier == identifier).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_blocked: Optional[int] = None
    ) -> tuple[List[GuestUser], int]:
        """获取多个用户"""
        query = db.query(GuestUser)
        
        if is_blocked is not None:
            query = query.filter(GuestUser.is_blocked == is_blocked)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    def create(self, db: Session, *, obj_in: GuestUserCreate) -> GuestUser:
        """创建新用户"""
        db_obj = GuestUser(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_or_create(
        self, 
        db: Session, 
        *, 
        identifier: str, 
        nickname: str,
        avatar_url: str = "",
        default_max_comments: int = 3
    ) -> GuestUser:
        """获取或创建用户"""
        user = self.get_by_identifier(db, identifier)
        if user:
            updated = False
            if user.nickname != nickname:
                user.nickname = nickname
                updated = True
            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
                updated = True
            if updated:
                db.commit()
                db.refresh(user)
            return user
        
        # 创建新用户
        user_in = GuestUserCreate(
            identifier=identifier,
            nickname=nickname,
            avatar_url=avatar_url,
            max_comments_per_page=default_max_comments
        )
        return self.create(db, obj_in=user_in)
    
    def check_cooldown(self, db: Session, *, user_id: int, cooldown_seconds: int = 30) -> tuple[bool, int]:
        """
        检查用户冷却时间
        返回: (是否通过, 还需等待秒数)
        """
        user = self.get(db, user_id=user_id)
        if not user or not user.last_comment_at:
            return True, 0
        
        elapsed = (datetime.utcnow() - user.last_comment_at).total_seconds()
        if elapsed >= cooldown_seconds:
            return True, 0
        
        return False, int(cooldown_seconds - elapsed)
    
    def update_after_comment(self, db: Session, *, user_id: int) -> None:
        """用户留言后更新统计"""
        user = self.get(db, user_id=user_id)
        if user:
            user.last_comment_at = datetime.utcnow()
            user.total_comments += 1
            db.add(user)
            db.commit()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: GuestUser, 
        obj_in: GuestUserUpdate
    ) -> GuestUser:
        """更新用户"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, user_id: int) -> Optional[GuestUser]:
        """删除用户"""
        obj = db.query(GuestUser).get(user_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# ==================== Comment CRUD ====================

class CRUDComment:
    """留言评论 CRUD 操作"""
    
    def get(self, db: Session, comment_id: int) -> Optional[Comment]:
        """根据 ID 获取评论"""
        return db.query(Comment).options(
            joinedload(Comment.user),
            joinedload(Comment.item)
        ).filter(Comment.id == comment_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        item_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_approved: Optional[int] = None,
        is_deleted: Optional[int] = None,
        parent_id: Optional[int] = None
    ) -> tuple[List[Comment], int]:
        """获取多条评论"""
        query = db.query(Comment).options(
            joinedload(Comment.user),
            joinedload(Comment.item)
        )
        
        if item_id is not None:
            query = query.filter(Comment.item_id == item_id)
        
        if user_id is not None:
            query = query.filter(Comment.user_id == user_id)
        
        if is_approved is not None:
            query = query.filter(Comment.is_approved == is_approved)
        
        if is_deleted is not None:
            query = query.filter(Comment.is_deleted == is_deleted)
        
        if parent_id is not None:
            query = query.filter(Comment.parent_id == parent_id)
        
        total = query.count()
        items = query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    def get_tree_by_item(
        self, 
        db: Session, 
        *, 
        item_id: int,
        is_approved: Optional[int] = 1,
        is_deleted: int = 0
    ) -> List[Comment]:
        """
        获取某事物的评论树（嵌套结构）
        只获取顶层评论（parent_id=None），子评论通过 replies 关系加载
        """
        query = db.query(Comment).options(
            joinedload(Comment.user),
            joinedload(Comment.item),
            joinedload(Comment.replies).joinedload(Comment.user)
        ).filter(
            Comment.item_id == item_id,
            Comment.parent_id == None  # 只获取顶层评论
        )
        
        if is_approved is not None:
            query = query.filter(Comment.is_approved == is_approved)
        
        query = query.filter(Comment.is_deleted == is_deleted)
        
        return query.order_by(Comment.created_at.desc()).all()
    
    def get_count_by_item_and_user(
        self, 
        db: Session, 
        *, 
        item_id: int, 
        user_id: int,
        exclude_deleted: bool = True
    ) -> int:
        """获取某用户在某事物上的留言数量"""
        query = db.query(Comment).filter(
            Comment.item_id == item_id,
            Comment.user_id == user_id
        )
        
        if exclude_deleted:
            query = query.filter(Comment.is_deleted == 0)
        
        return query.count()
    
    def create(self, db: Session, *, obj_in: CommentCreate, user_id: int) -> Comment:
        """创建评论"""
        db_obj = Comment(
            content=obj_in.content,
            item_id=obj_in.item_id,
            user_id=user_id,
            parent_id=obj_in.parent_id,
            is_approved=obj_in.is_approved if obj_in.is_approved is not None else 1
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Comment, 
        obj_in: CommentUpdate
    ) -> Comment:
        """更新评论"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, comment_id: int, soft: bool = True) -> Optional[Comment]:
        """删除评论（默认软删除）"""
        obj = db.query(Comment).get(comment_id)
        if obj:
            if soft:
                obj.is_deleted = 1
                obj.updated_at = datetime.utcnow()
                db.add(obj)
            else:
                db.delete(obj)
            db.commit()
        return obj
    
    def get_stats(self, db: Session) -> dict:
        """获取评论统计"""
        total = db.query(Comment).filter(Comment.is_deleted == 0).count()
        pending = db.query(Comment).filter(
            Comment.is_approved == 0, 
            Comment.is_deleted == 0
        ).count()
        approved = db.query(Comment).filter(
            Comment.is_approved == 1, 
            Comment.is_deleted == 0
        ).count()
        rejected = db.query(Comment).filter(
            Comment.is_approved == 2, 
            Comment.is_deleted == 0
        ).count()
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected
        }


# 实例化评论 CRUD 对象
guest_user = CRUDGuestUser()
comment = CRUDComment()


# ==================== RateLimit CRUD ====================

class CRUDRateLimit:
    """频率限制 CRUD 操作"""
    
    def check_rate_limit(
        self, 
        db: Session, 
        *, 
        identifier: str,
        ip_address: str,
        action_type: str = "comment",
        window_minutes: int = 60,
        max_requests: int = 10
    ) -> tuple[bool, int]:
        """
        检查频率限制
        返回: (是否允许, 当前次数)
        """
        from datetime import timedelta
        
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # 获取该时间窗口内的记录
        record = db.query(RateLimit).filter(
            RateLimit.identifier == identifier,
            RateLimit.action_type == action_type,
            RateLimit.window_start >= window_start
        ).first()
        
        if not record:
            # 创建新记录
            record = RateLimit(
                identifier=identifier,
                ip_address=ip_address,
                action_type=action_type,
                count=0,
                window_start=datetime.utcnow()
            )
            db.add(record)
            db.commit()
        
        return record.count < max_requests, record.count
    
    def increment(
        self,
        db: Session,
        *,
        identifier: str,
        action_type: str = "comment",
        ip_address: str = "unknown"
    ) -> None:
        """增加计数"""
        from datetime import timedelta
        
        window_start = datetime.utcnow() - timedelta(minutes=60)
        
        record = db.query(RateLimit).filter(
            RateLimit.identifier == identifier,
            RateLimit.action_type == action_type,
            RateLimit.window_start >= window_start
        ).first()
        
        if record:
            record.count += 1
            if ip_address and record.ip_address == "unknown":
                record.ip_address = ip_address
            db.add(record)
        else:
            record = RateLimit(
                identifier=identifier,
                ip_address=ip_address,
                action_type=action_type,
                count=1,
                window_start=datetime.utcnow()
            )
            db.add(record)
        db.commit()
    
    def check_ip_rate_limit(
        self,
        db: Session,
        *,
        ip_address: str,
        action_type: str = "comment",
        window_minutes: int = 60,
        max_requests: int = 20
    ) -> tuple[bool, int]:
        """检查IP频率限制"""
        from datetime import timedelta
        
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # 统计该 IP 在该时间窗口内的总请求数
        count = db.query(func.coalesce(func.sum(RateLimit.count), 0)).filter(
            RateLimit.ip_address == ip_address,
            RateLimit.action_type == action_type,
            RateLimit.window_start >= window_start
        ).scalar()
        
        return count < max_requests, count
    
    def cleanup_old_records(self, db: Session, *, hours: int = 24) -> int:
        """清理旧记录"""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = db.query(RateLimit).filter(RateLimit.created_at < cutoff).delete()
        db.commit()
        return result


# ==================== IPBlacklist CRUD ====================

class CRUDIPBlacklist:
    """IP 黑名单 CRUD 操作"""
    
    def is_blocked(self, db: Session, *, ip_address: str) -> tuple[bool, Optional[str]]:
        """
        检查 IP 是否被封锁
        返回: (是否被封锁, 原因)
        """
        record = db.query(IPBlacklist).filter(
            IPBlacklist.ip_address == ip_address
        ).first()
        
        if not record:
            return False, None
        
        # 检查是否过期
        if not record.is_permanent and record.expire_at:
            if datetime.utcnow() > record.expire_at:
                # 已过期，删除记录
                db.delete(record)
                db.commit()
                return False, None
        
        return True, record.reason
    
    def add(self, db: Session, *, ip_address: str, reason: str = "", 
            is_permanent: bool = False, expire_hours: Optional[int] = None) -> IPBlacklist:
        """添加 IP 到黑名单"""
        expire_at = None
        if not is_permanent and expire_hours:
            from datetime import timedelta
            expire_at = datetime.utcnow() + timedelta(hours=expire_hours)
        
        # 检查是否已存在
        existing = db.query(IPBlacklist).filter(IPBlacklist.ip_address == ip_address).first()
        if existing:
            existing.reason = reason
            existing.is_permanent = 1 if is_permanent else 0
            existing.expire_at = expire_at
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        
        record = IPBlacklist(
            ip_address=ip_address,
            reason=reason,
            is_permanent=1 if is_permanent else 0,
            expire_at=expire_at
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    
    def remove(self, db: Session, *, ip_address: str) -> bool:
        """从黑名单移除"""
        record = db.query(IPBlacklist).filter(IPBlacklist.ip_address == ip_address).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        is_permanent: Optional[int] = None
    ) -> tuple[List[IPBlacklist], int]:
        """获取黑名单列表"""
        query = db.query(IPBlacklist)
        
        if is_permanent is not None:
            query = query.filter(IPBlacklist.is_permanent == is_permanent)
        
        total = query.count()
        items = query.order_by(IPBlacklist.created_at.desc()).offset(skip).limit(limit).all()
        
        return items, total


# ==================== SpamPattern CRUD ====================

class CRUDSpamPattern:
    """垃圾内容特征 CRUD 操作"""
    
    def check_content(self, db: Session, *, content: str) -> tuple[bool, Optional[str], str]:
        """
        检查内容是否包含垃圾信息
        返回: (是否通过, 匹配到的模式, 建议操作)
        """
        patterns = db.query(SpamPattern).filter(SpamPattern.is_active == 1).all()
        
        for pattern in patterns:
            if pattern.pattern_type == "keyword":
                if pattern.pattern.lower() in content.lower():
                    return False, pattern.pattern, pattern.action
            elif pattern.pattern_type == "regex":
                import re
                try:
                    if re.search(pattern.pattern, content, re.IGNORECASE):
                        return False, pattern.pattern, pattern.action
                except re.error:
                    continue
        
        return True, None, "pass"
    
    def add(self, db: Session, *, pattern: str, pattern_type: str = "keyword",
            action: str = "block", description: str = "") -> SpamPattern:
        """添加垃圾特征"""
        record = SpamPattern(
            pattern=pattern,
            pattern_type=pattern_type,
            action=action,
            description=description
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> tuple[List[SpamPattern], int]:
        """获取所有特征"""
        total = db.query(SpamPattern).count()
        items = db.query(SpamPattern).offset(skip).limit(limit).all()
        return items, total
    
    def delete(self, db: Session, *, pattern_id: int) -> bool:
        """删除特征"""
        record = db.query(SpamPattern).get(pattern_id)
        if record:
            db.delete(record)
            db.commit()
            return True
        return False


# 实例化防护 CRUD 对象
rate_limit = CRUDRateLimit()
ip_blacklist = CRUDIPBlacklist()
spam_pattern = CRUDSpamPattern()


# ==================== User CRUD (注册用户) ====================

class CRUDUser:
    """注册用户 CRUD 操作"""
    
    def get(self, db: Session, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[int] = None
    ) -> tuple[List[User], int]:
        """获取多个用户"""
        query = db.query(User)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total
    
    def create(self, db: Session, *, email: str, username: str, password: str,
               nickname: str, avatar_url: str = "", is_active: int = 1,
               max_comments_per_page: int = 10, max_comments_per_day: int = 50) -> User:
        """创建新用户"""
        from shijing_things.core.security import get_password_hash
        
        db_obj = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            nickname=nickname,
            avatar_url=avatar_url,
            is_active=is_active,
            max_comments_per_page=max_comments_per_page,
            max_comments_per_day=max_comments_per_day,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_from_admin(self, db: Session, *, obj_in: UserAdminCreate) -> User:
        return self.create(
            db,
            email=obj_in.email,
            username=obj_in.username,
            password=obj_in.password,
            nickname=obj_in.nickname,
            avatar_url=obj_in.avatar_url or "",
            is_active=obj_in.is_active,
            max_comments_per_page=obj_in.max_comments_per_page,
            max_comments_per_day=obj_in.max_comments_per_day,
        )
    
    def create_oauth_user(
        self, 
        db: Session, 
        *, 
        email: str,
        nickname: str,
        avatar_url: str = "",
        provider: str,
        provider_account_id: str,
        provider_account_email: str = ""
    ) -> User:
        """创建 OAuth 用户"""
        # 创建用户
        db_obj = User(
            email=email,
            username=f"{provider}_{provider_account_id}",  # 自动生成用户名
            nickname=nickname,
            avatar_url=avatar_url,
            hashed_password=None,  # OAuth 用户没有密码
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # 创建 OAuth 关联
        oauth_account = OAuthAccount(
            user_id=db_obj.id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_account_email=provider_account_email or email,
        )
        db.add(oauth_account)
        db.commit()
        
        return db_obj

    def ensure_unique_username(self, db: Session, *, base_username: str) -> str:
        """生成唯一用户名"""
        candidate = base_username[:50] or "user"
        if not self.get_by_username(db, candidate):
            return candidate

        suffix = 1
        while True:
            trimmed = base_username[: max(1, 50 - len(str(suffix)) - 1)] or "user"
            candidate = f"{trimmed}_{suffix}"
            if not self.get_by_username(db, candidate):
                return candidate
            suffix += 1
    
    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """验证用户名/邮箱和密码"""
        from shijing_things.core.security import verify_password
        
        # 支持用户名或邮箱登录
        user = self.get_by_username(db, username)
        if not user:
            user = self.get_by_email(db, username)
        
        if not user:
            return None
        if not user.hashed_password:
            return None  # OAuth 用户不能使用密码登录
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user
    
    def update(self, db: Session, *, db_obj: User, **kwargs) -> User:
        """更新用户信息"""
        from shijing_things.core.security import get_password_hash
        
        for field, value in kwargs.items():
            if field == "password":
                setattr(db_obj, "hashed_password", get_password_hash(value))
            else:
                setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_last_login(self, db: Session, *, user_id: int) -> None:
        """更新最后登录时间"""
        user = self.get(db, user_id=user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            db.add(user)
            db.commit()

    def update_after_comment(self, db: Session, *, user_id: int) -> None:
        """用户留言后更新统计"""
        user = self.get(db, user_id=user_id)
        if user:
            user.last_comment_at = datetime.utcnow()
            user.total_comments += 1
            db.add(user)
            db.commit()

    def delete(self, db: Session, *, user_id: int) -> Optional[User]:
        """删除用户及其 OAuth 关联、会话和留言映射"""
        db_obj = self.get(db, user_id=user_id)
        if not db_obj:
            return None

        shadow_identifier = f"github_user_{user_id}"
        alt_shadow_identifier = f"oauth_user_{user_id}"
        shadows = db.query(GuestUser).filter(
            GuestUser.identifier.in_([shadow_identifier, alt_shadow_identifier])
        ).all()
        for shadow in shadows:
            db.delete(shadow)

        db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDOAuthAccount:
    """OAuth 账户 CRUD 操作"""
    
    def get_by_provider_account(
        self, 
        db: Session, 
        *, 
        provider: str, 
        provider_account_id: str
    ) -> Optional[OAuthAccount]:
        """根据 provider 和 account_id 获取 OAuth 账户"""
        return db.query(OAuthAccount).filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id
        ).first()
    
    def create(
        self,
        db: Session,
        *,
        user_id: int,
        provider: str,
        provider_account_id: str,
        provider_account_email: str = "",
        access_token: str = "",
        refresh_token: str = "",
        expires_at: datetime = None
    ) -> OAuthAccount:
        """创建 OAuth 账户关联"""
        db_obj = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_account_email=provider_account_email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CRUDUserSession:
    """用户会话 CRUD 操作"""
    
    def create(
        self,
        db: Session,
        *,
        user_id: int,
        ip_address: str = "",
        user_agent: str = ""
    ) -> UserSession:
        """创建新会话"""
        from shijing_things.core.security import generate_session_token
        from datetime import timedelta
        from shijing_things.core.config import get_settings
        
        settings = get_settings()
        
        session = UserSession(
            user_id=user_id,
            session_token=generate_session_token(),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def get_by_token(self, db: Session, *, token: str) -> Optional[UserSession]:
        """根据 token 获取会话"""
        return db.query(UserSession).filter(
            UserSession.session_token == token,
            UserSession.is_valid == 1,
            UserSession.expires_at > datetime.utcnow()
        ).first()
    
    def invalidate(self, db: Session, *, token: str) -> bool:
        """使会话失效"""
        session = self.get_by_token(db, token=token)
        if session:
            session.is_valid = 0
            db.add(session)
            db.commit()
            return True
        return False
    
    def invalidate_all_user_sessions(self, db: Session, *, user_id: int) -> int:
        """使用户的所有会话失效（登出所有设备）"""
        result = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_valid == 1
        ).update({"is_valid": 0})
        db.commit()
        return result


class CRUDEmailLoginCode:
    """邮箱验证码登录 CRUD"""

    def get_latest_active(self, db: Session, *, email: str, purpose: str = "login") -> Optional[EmailLoginCode]:
        return db.query(EmailLoginCode).filter(
            EmailLoginCode.email == email,
            EmailLoginCode.purpose == purpose,
            EmailLoginCode.consumed_at.is_(None),
            EmailLoginCode.expires_at > datetime.utcnow()
        ).order_by(EmailLoginCode.created_at.desc()).first()

    def create(
        self,
        db: Session,
        *,
        email: str,
        code_hash: str,
        expires_at: datetime,
        purpose: str = "login",
        ip_address: str = ""
    ) -> EmailLoginCode:
        record = EmailLoginCode(
            email=email,
            code_hash=code_hash,
            expires_at=expires_at,
            purpose=purpose,
            ip_address=ip_address
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def consume(self, db: Session, *, record: EmailLoginCode) -> EmailLoginCode:
        record.consumed_at = datetime.utcnow()
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


# 实例化 User CRUD 对象
user = CRUDUser()
oauth_account = CRUDOAuthAccount()
user_session = CRUDUserSession()
email_login_code = CRUDEmailLoginCode()
