"""
RESTful API 路由
提供 JSON 格式的数据接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import hashlib

from shijing_things.core.database import get_db
from shijing_things.core.config import get_settings
from shijing_things.core.session_auth import is_admin_logged_in, is_comment_user_logged_in
from shijing_things.models.models import Comment
from shijing_things.schemas.schemas import (
    ShijingItemCreate, ShijingItemUpdate, ShijingItemResponse, ShijingItemList,
    PoemCreate, PoemUpdate, PoemResponse, PoemList,
    CommentCreate, CommentUpdate, CommentResponse, CommentList, CommentStats,
    GuestUserCreate, GuestUserUpdate, GuestUserResponse,
    UserCommentLimit, UserAdminCreate, UserUpdate, UserResponse
)
from shijing_things.crud.crud import (
    item as crud_item, poem as crud_poem,
    comment as crud_comment, guest_user as crud_guest_user,
    rate_limit as crud_rate_limit, ip_blacklist as crud_ip_blacklist,
    spam_pattern as crud_spam_pattern, user as crud_user
)

router = APIRouter(prefix="/api")


def require_login(request: Request):
    """检查用户是否已登录，未登录返回 401"""
    if not (is_admin_logged_in(request) or is_comment_user_logged_in(request)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先登录"
        )
    return True


def require_admin(request: Request):
    """检查是否为管理员，未授权返回 403"""
    if not is_admin_logged_in(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return True


def get_oauth_comment_user(request: Request, db: Session):
    """获取当前已登录用户对应的留言身份"""
    auth_type = request.session.get("comment_auth_type")
    if auth_type not in {"oauth_github", "oauth_google", "oauth_wechat", "email_code"} or not request.session.get("comment_is_authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="留言需要先登录支持的账号"
        )

    user_id = request.session.get("comment_user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录"
        )

    db_user = crud_user.get(db, user_id=user_id)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录"
        )

    identifier = f"oauth_user_{db_user.id}"
    nickname = db_user.nickname or db_user.username or "登录用户"
    avatar_url = db_user.avatar_url or ""
    comment_user = crud_guest_user.get_or_create(
        db,
        identifier=identifier,
        nickname=nickname,
        avatar_url=avatar_url,
        default_max_comments=db_user.max_comments_per_page
    )
    if comment_user.max_comments_per_page != db_user.max_comments_per_page:
        comment_user.max_comments_per_page = db_user.max_comments_per_page
        db.add(comment_user)
        db.commit()
    return comment_user, identifier


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
def create_item(
    request: Request,
    item_in: ShijingItemCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """创建事物（需要管理员权限）"""
    existing = crud_item.get_by_name(db, name=item_in.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"事物 '{item_in.name}' 已存在")
    return crud_item.create(db, obj_in=item_in)


@router.put("/items/{item_id}", response_model=ShijingItemResponse)
def update_item(
    request: Request,
    item_id: int,
    item_in: ShijingItemUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """更新事物（需要管理员权限）"""
    db_item = crud_item.get(db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="事物不存在")
    return crud_item.update(db, db_obj=db_item, obj_in=item_in)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """删除事物（需要管理员权限）"""
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
def create_poem(
    request: Request,
    poem_in: PoemCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """创建诗篇（需要管理员权限）"""
    existing = crud_poem.get_by_title(db, title=poem_in.title)
    if existing:
        raise HTTPException(status_code=400, detail=f"诗篇 '{poem_in.title}' 已存在")
    return crud_poem.create(db, obj_in=poem_in)


@router.put("/poems/{poem_id}", response_model=PoemResponse)
def update_poem(
    request: Request,
    poem_id: int,
    poem_in: PoemUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """更新诗篇（需要管理员权限）"""
    db_poem = crud_poem.get(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return crud_poem.update(db, db_obj=db_poem, obj_in=poem_in)


@router.delete("/poems/{poem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poem(
    request: Request,
    poem_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """删除诗篇（需要管理员权限）"""
    db_poem = crud_poem.delete(db, poem_id=poem_id)
    if not db_poem:
        raise HTTPException(status_code=404, detail="诗篇不存在")
    return None


# ==================== 评论 API（公开） ====================

def generate_user_identifier(request: Request) -> str:
    """生成用户唯一标识（基于 IP + User-Agent）"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    # 创建哈希值作为标识符
    identifier_str = f"{client_ip}:{user_agent}"
    return hashlib.md5(identifier_str.encode()).hexdigest()


@router.get("/comments/item/{item_id}", response_model=List[CommentResponse])
def get_comments_by_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    """获取某事物的所有评论（树形结构）"""
    comments = crud_comment.get_tree_by_item(db, item_id=item_id)
    return comments


@router.get("/comments/item/{item_id}/limit", response_model=UserCommentLimit)
def get_user_comment_limit(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前已登录用户在该事物的留言限制信息"""
    user, _ = get_oauth_comment_user(request, db)
    
    # 检查用户是否被禁言
    if user.is_blocked:
        return UserCommentLimit(
            max_allowed=user.max_comments_per_page,
            current_count=999999,  # 一个很大的数字表示不能留言
            can_comment=False,
            remaining=0
        )
    
    # 获取当前留言数
    current_count = crud_comment.get_count_by_item_and_user(
        db, item_id=item_id, user_id=user.id
    )
    
    max_allowed = user.max_comments_per_page
    remaining = max(0, max_allowed - current_count)
    
    return UserCommentLimit(
        max_allowed=max_allowed,
        current_count=current_count,
        can_comment=remaining > 0,
        remaining=remaining
    )


@router.post("/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    request: Request,
    comment_in: CommentCreate,
    db: Session = Depends(get_db)
):
    """创建评论（需要登录）"""
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")[:500]
    
    # ========== 第1层防护：IP 黑名单检查 ==========
    if settings.enable_ip_blacklist:
        is_blocked, reason = crud_ip_blacklist.is_blocked(db, ip_address=client_ip)
        if is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"您的IP已被限制访问，原因：{reason or '违反社区规定'}"
            )
    
    user, identifier = get_oauth_comment_user(request, db)
    
    # ========== 第2层防护：用户禁言检查 ==========
    if user.is_blocked:
        # 记录可疑行为
        crud_rate_limit.increment(
            db,
            identifier=identifier,
            action_type="blocked_attempt",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您已被禁言，无法发表评论"
        )
    
    # ========== 第3层防护：冷却时间检查 ==========
    can_comment, wait_seconds = crud_guest_user.check_cooldown(
        db, user_id=user.id, cooldown_seconds=settings.comment_cooldown_seconds
    )
    if not can_comment:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"操作过于频繁，请等待 {wait_seconds} 秒后再试"
        )
    
    # ========== 第4层防护：页面留言数量限制 ==========
    current_count = crud_comment.get_count_by_item_and_user(
        db, item_id=comment_in.item_id, user_id=user.id
    )
    if current_count >= user.max_comments_per_page:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"您在该页面已达到留言上限（{user.max_comments_per_page}条），无法继续留言"
        )
    
    # ========== 第5层防护：用户全局频率限制（每小时） ==========
    allowed, current_hour_count = crud_rate_limit.check_rate_limit(
        db,
        identifier=identifier,
        ip_address=client_ip,
        action_type="comment",
        window_minutes=60,
        max_requests=settings.max_comments_per_hour_per_user
    )
    if not allowed:
        # 触发频率限制，添加到黑名单观察列表
        crud_rate_limit.increment(
            db,
            identifier=identifier,
            action_type="rate_limit_triggered",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"您留言过于频繁，已达到每小时上限（{settings.max_comments_per_hour_per_user}条），请稍后再试"
        )
    
    # ========== 第6层防护：IP 频率限制（每小时） ==========
    ip_allowed, ip_hour_count = crud_rate_limit.check_ip_rate_limit(
        db,
        ip_address=client_ip,
        action_type="comment",
        window_minutes=60,
        max_requests=settings.max_comments_per_hour_per_ip
    )
    if not ip_allowed:
        # IP 频率过高，可能是在刷留言
        crud_ip_blacklist.add(
            db,
            ip_address=client_ip,
            reason=f"频率过高：{ip_hour_count}次/小时",
            is_permanent=False,
            expire_hours=1
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="当前IP留言过于频繁，已被临时限制，请1小时后再试"
        )
    
    # ========== 第7层防护：IP 每日限制 ==========
    ip_daily_allowed, ip_daily_count = crud_rate_limit.check_ip_rate_limit(
        db,
        ip_address=client_ip,
        action_type="comment",
        window_minutes=1440,  # 24小时
        max_requests=settings.max_comments_per_day_per_ip
    )
    if not ip_daily_allowed:
        # IP 日限额超限
        crud_ip_blacklist.add(
            db,
            ip_address=client_ip,
            reason=f"日限额超限：{ip_daily_count}次/天",
            is_permanent=False,
            expire_hours=24
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="当前IP今日留言已达上限，请明天再试"
        )
    
    # ========== 第8层防护：内容垃圾信息过滤 ==========
    if settings.enable_spam_filter:
        is_clean, matched_pattern, action = crud_spam_pattern.check_content(db, content=comment_in.content)
        if not is_clean:
            if action == "block":
                # 降低用户信任分数
                user.trust_score = max(0, user.trust_score - 20)
                db.add(user)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="留言包含违规内容，请修改后重试"
                )
            elif action == "review":
                comment_in.is_approved = 0

    if settings.comment_approval_required:
        comment_in.is_approved = 0
    
    # 检查关键词（简单版本）
    for keyword in settings.spam_keywords:
        if keyword in comment_in.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="留言包含敏感词，请修改后重试"
            )
    
    # ========== 第9层防护：重复内容检测 ==========
    # 检查用户最近10条留言是否有重复
    recent_comments = db.query(Comment).filter(
        Comment.user_id == user.id,
        Comment.is_deleted == 0
    ).order_by(Comment.created_at.desc()).limit(10).all()
    
    for recent in recent_comments:
        # 简单相似度检查：完全相同或编辑距离很近
        if recent.content == comment_in.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请勿重复提交相同的留言"
            )
        # 检查编辑距离（近似重复）
        if len(comment_in.content) > 10:
            similarity = calculate_similarity(recent.content, comment_in.content)
            if similarity > 0.85:  # 85%相似度
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="留言与之前的内容过于相似，请修改后重试"
                )
    
    # ========== 所有检查通过，创建评论 ==========
    comment = crud_comment.create(db, obj_in=comment_in, user_id=user.id)
    
    # 记录 IP 和 User-Agent
    comment.ip_address = client_ip
    comment.user_agent = user_agent
    db.add(comment)
    
    # 更新用户统计
    crud_guest_user.update_after_comment(db, user_id=user.id)
    db_user_id = request.session.get("comment_user_id")
    if db_user_id:
        crud_user.update_after_comment(db, user_id=db_user_id)
    
    # 更新频率限制计数
    crud_rate_limit.increment(
        db,
        identifier=identifier,
        action_type="comment",
        ip_address=client_ip
    )
    
    db.commit()
    db.refresh(comment)
    return comment


def calculate_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的相似度（基于编辑距离）"""
    if len(s1) < len(s2):
        return calculate_similarity(s2, s1)
    
    if len(s2) == 0:
        return 0.0
    
    # 简化的编辑距离计算
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    distance = previous_row[-1]
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len)


# ==================== 评论 API（需要管理员权限） ====================

@router.get("/admin/comments/", response_model=CommentList)
def list_all_comments(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    item_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    is_approved: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取所有评论（需要管理员权限）"""
    items, total = crud_comment.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        item_id=item_id,
        user_id=user_id,
        is_approved=is_approved,
        is_deleted=0
    )
    return {"items": items, "total": total}


@router.get("/admin/comments/stats", response_model=CommentStats)
def get_comment_stats(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取评论统计（需要管理员权限）"""
    return crud_comment.get_stats(db)


@router.get("/admin/comments/{comment_id}", response_model=CommentResponse)
def get_comment_detail(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取评论详情（需要管理员权限）"""
    comment = crud_comment.get(db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return comment


@router.put("/admin/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    request: Request,
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """更新评论（需要管理员权限）"""
    db_comment = crud_comment.get(db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return crud_comment.update(db, db_obj=db_comment, obj_in=comment_in)


@router.delete("/admin/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    request: Request,
    comment_id: int,
    soft: bool = Query(True, description="是否软删除"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """删除评论（需要管理员权限）"""
    db_comment = crud_comment.delete(db, comment_id=comment_id, soft=soft)
    if not db_comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    return None


# ==================== 用户管理 API（需要管理员权限） ====================

@router.get("/admin/users/")
def list_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_active: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取所有正式用户（需要管理员权限）"""
    items, total = crud_user.get_multi(
        db, skip=skip, limit=limit, is_active=is_active
    )
    return {"items": items, "total": total}


@router.post("/admin/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_in: UserAdminCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """创建正式用户（需要管理员权限）"""
    if crud_user.get_by_email(db, email=user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud_user.get_by_username(db, username=user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud_user.create_from_admin(db, obj_in=user_in)


@router.get("/admin/users/{user_id}")
def get_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取正式用户详情（需要管理员权限）"""
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "user": user,
        "comments_count": user.total_comments or 0
    }


@router.put("/admin/users/{user_id}")
def update_user(
    request: Request,
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """更新正式用户（需要管理员权限）"""
    db_user = crud_user.get(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_data = user_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] and update_data["email"] != db_user.email:
        existing = crud_user.get_by_email(db, email=update_data["email"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")

    if "username" in update_data and update_data["username"] and update_data["username"] != db_user.username:
        existing = crud_user.get_by_username(db, username=update_data["username"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")

    return crud_user.update(db, db_obj=db_user, **update_data)


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """删除正式用户及其留言映射（需要管理员权限）"""
    db_user = crud_user.delete(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return None


# ==================== IP 黑名单管理 API（需要管理员权限） ====================

@router.get("/admin/security/ip-blacklist")
def list_ip_blacklist(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    is_permanent: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取 IP 黑名单列表"""
    items, total = crud_ip_blacklist.get_multi(
        db, skip=skip, limit=limit, is_permanent=is_permanent
    )
    return {"items": items, "total": total}


@router.post("/admin/security/ip-blacklist")
def add_ip_to_blacklist(
    request: Request,
    ip_address: str = Query(...),
    reason: str = Query(""),
    is_permanent: bool = Query(False),
    expire_hours: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """添加 IP 到黑名单"""
    record = crud_ip_blacklist.add(
        db,
        ip_address=ip_address,
        reason=reason,
        is_permanent=is_permanent,
        expire_hours=expire_hours
    )
    return record


@router.delete("/admin/security/ip-blacklist/{ip_address}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ip_from_blacklist(
    request: Request,
    ip_address: str,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """从黑名单移除 IP"""
    success = crud_ip_blacklist.remove(db, ip_address=ip_address)
    if not success:
        raise HTTPException(status_code=404, detail="IP 不在黑名单中")
    return None


# ==================== 垃圾内容特征管理 API（需要管理员权限） ====================

@router.get("/admin/security/spam-patterns")
def list_spam_patterns(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取垃圾内容特征列表"""
    items, total = crud_spam_pattern.get_multi(db, skip=skip, limit=limit)
    return {"items": items, "total": total}


@router.post("/admin/security/spam-patterns")
def add_spam_pattern(
    request: Request,
    pattern: str = Query(...),
    pattern_type: str = Query("keyword"),
    action: str = Query("block"),
    description: str = Query(""),
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """添加垃圾内容特征"""
    record = crud_spam_pattern.add(
        db,
        pattern=pattern,
        pattern_type=pattern_type,
        action=action,
        description=description
    )
    return record


@router.delete("/admin/security/spam-patterns/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spam_pattern(
    request: Request,
    pattern_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """删除垃圾内容特征"""
    success = crud_spam_pattern.delete(db, pattern_id=pattern_id)
    if not success:
        raise HTTPException(status_code=404, detail="特征不存在")
    return None


# ==================== 安全统计 API（需要管理员权限） ====================

@router.get("/admin/security/stats")
def get_security_stats(
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin)
):
    """获取安全防护统计"""
    from datetime import datetime, timedelta
    from shijing_things.models.models import RateLimit, GuestUser, IPBlacklist
    
    # 最近24小时的拦截统计
    since = datetime.utcnow() - timedelta(hours=24)
    
    rate_limit_triggers = db.query(RateLimit).filter(
        RateLimit.action_type == "rate_limit_triggered",
        RateLimit.created_at >= since
    ).count()
    
    blocked_attempts = db.query(RateLimit).filter(
        RateLimit.action_type == "blocked_attempt",
        RateLimit.created_at >= since
    ).count()
    
    active_blacklist = db.query(IPBlacklist).count()
    
    # 活跃用户统计
    active_users = db.query(GuestUser).filter(
        GuestUser.last_comment_at >= since
    ).count()
    
    # 低信任分用户
    low_trust_users = db.query(GuestUser).filter(GuestUser.trust_score < 50).count()
    
    return {
        "rate_limit_triggers_24h": rate_limit_triggers,
        "blocked_attempts_24h": blocked_attempts,
        "active_blacklist_count": active_blacklist,
        "active_users_24h": active_users,
        "low_trust_users": low_trust_users
    }


# 添加 Schema 导入
from shijing_things.models.models import RateLimit, IPBlacklist, SpamPattern, GuestUser, Comment
from datetime import datetime
