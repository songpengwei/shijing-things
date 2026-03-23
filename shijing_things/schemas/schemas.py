from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, List
from datetime import datetime

# 分类类型
category_type = Literal['草', '木', '鸟', '兽', '虫', '鱼']
CategoryType = category_type


# ==================== ShijingItem Schemas ====================

class ShijingItemBase(BaseModel):
    """事物基础模型"""
    name: str
    category: category_type
    title: str  # 诗篇标题（原 poem）
    chapter: str  # 章节（原 source）
    section: str  # 部分（新增）
    poem_id: int  # 诗篇ID（新增）
    quote: str
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    modern_name: Optional[str] = ""
    taxonomy: Optional[str] = ""
    symbolism: Optional[str] = ""
    wiki_link: Optional[str] = ""


class ShijingItemCreate(ShijingItemBase):
    """创建事物请求模型"""
    pass


class ShijingItemUpdate(BaseModel):
    """更新事物请求模型"""
    name: Optional[str] = None
    category: Optional[category_type] = None
    title: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    poem_id: Optional[int] = None
    quote: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    modern_name: Optional[str] = None
    taxonomy: Optional[str] = None
    symbolism: Optional[str] = None
    wiki_link: Optional[str] = None


class ShijingItemResponse(ShijingItemBase):
    """事物响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class ShijingItemList(BaseModel):
    """事物列表响应"""
    items: list[ShijingItemResponse]
    total: int
    skip: int
    limit: int


# ==================== Poem Schemas ====================

class PoemBase(BaseModel):
    """诗篇基础模型"""
    title: str
    chapter: str
    section: str
    content: str  # JSON 字符串存储列表
    full_source: str


class PoemCreate(PoemBase):
    """创建诗篇请求模型"""
    pass


class PoemUpdate(BaseModel):
    """更新诗篇请求模型"""
    title: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    content: Optional[str] = None
    full_source: Optional[str] = None


class PoemResponse(PoemBase):
    """诗篇响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class PoemList(BaseModel):
    """诗篇列表响应"""
    items: list[PoemResponse]
    total: int
    skip: int
    limit: int


# ==================== Comment Schemas ====================

class GuestUserBase(BaseModel):
    """访客用户基础模型"""
    nickname: str
    avatar_url: Optional[str] = ""


class GuestUserCreate(GuestUserBase):
    """创建访客用户请求模型"""
    identifier: str  # 唯一标识
    max_comments_per_page: int = 3


class GuestUserUpdate(BaseModel):
    """更新访客用户请求模型"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    max_comments_per_page: Optional[int] = None
    is_blocked: Optional[int] = None


class GuestUserResponse(GuestUserBase):
    """访客用户响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    identifier: str
    max_comments_per_page: int
    is_blocked: int
    created_at: datetime
    updated_at: datetime


class GuestUserSimple(BaseModel):
    """访客用户简化信息（用于评论展示）"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nickname: str
    avatar_url: Optional[str] = ""


class CommentBase(BaseModel):
    """留言基础模型"""
    content: str
    item_id: int
    parent_id: Optional[int] = None


class CommentCreate(BaseModel):
    """创建留言请求模型"""
    content: str
    item_id: int
    parent_id: Optional[int] = None
    nickname: str  # 用户昵称
    identifier: str  # 用户唯一标识
    is_approved: Optional[int] = 1


class CommentUpdate(BaseModel):
    """更新留言请求模型"""
    content: Optional[str] = None
    is_approved: Optional[int] = None
    is_deleted: Optional[int] = None


class CommentResponse(CommentBase):
    """留言响应模型"""
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    
    id: int
    user_id: int
    user: GuestUserSimple  # 嵌套用户信息
    is_approved: int
    is_deleted: int
    created_at: datetime
    updated_at: datetime
    replies: List['CommentResponse'] = []  # 子回复


class CommentWithReplies(CommentResponse):
    """带回复的留言模型"""
    pass


class CommentList(BaseModel):
    """留言列表响应"""
    items: list[CommentResponse]
    total: int


class CommentStats(BaseModel):
    """留言统计"""
    total: int
    pending: int
    approved: int
    rejected: int


class UserCommentLimit(BaseModel):
    """用户留言限制信息"""
    max_allowed: int
    current_count: int
    can_comment: bool
    remaining: int


# ==================== User Schemas (注册用户) ====================

class UserBase(BaseModel):
    """用户基础模型"""
    email: Optional[str] = None
    username: Optional[str] = None
    nickname: str
    avatar_url: Optional[str] = ""


class UserCreate(BaseModel):
    """创建用户请求模型"""
    email: str
    username: str
    password: str
    nickname: str
    avatar_url: Optional[str] = ""


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str  # 可以是用户名或邮箱
    password: str


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: int
    is_superuser: int
    max_comments_per_page: int
    max_comments_per_day: int
    total_comments: int
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserInDB(UserResponse):
    """包含敏感信息的用户模型（仅内部使用）"""
    hashed_password: Optional[str] = None


# ==================== OAuth Schemas ====================

class OAuthAccountResponse(BaseModel):
    """OAuth 账户响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    provider: str
    provider_account_email: Optional[str] = None
    created_at: datetime


class OAuthCallback(BaseModel):
    """OAuth 回调请求模型"""
    code: str
    state: str


# ==================== Token Schemas ====================

class Token(BaseModel):
    """Token 响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    """Token Payload"""
    sub: Optional[int] = None  # user_id
    exp: Optional[datetime] = None
