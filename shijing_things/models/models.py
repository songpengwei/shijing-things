from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from shijing_things.core.database import Base


class ShijingItem(Base):
    """诗经事物模型 - 草木鸟兽虫鱼"""
    __tablename__ = "shijing_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(10), nullable=False, index=True)  # 草、木、鸟、兽、虫、鱼
    title = Column(String(100), nullable=False, index=True)  # 所属诗篇标题
    chapter = Column(String(50), nullable=False, index=True)  # 章节（如：国风、小雅）
    section = Column(String(50), nullable=False, index=True)  # 部分（如：周南、鹿鸣之什）
    poem_id = Column(Integer, nullable=False, index=True)  # 诗篇ID
    quote = Column(Text, nullable=False)  # 引用诗句
    description = Column(Text, nullable=True)  # 简要注释
    image_url = Column(String(255), nullable=True, default="")  # 图片路径
    
    # 详细释义
    modern_name = Column(String(255), nullable=True, default="")  # 今名
    taxonomy = Column(String(255), nullable=True, default="")  # 纲目属
    symbolism = Column(Text, nullable=True, default="")  # 寓意
    wiki_link = Column(String(255), nullable=True, default="")  # 百科链接

    def __repr__(self):
        return f"<ShijingItem(id={self.id}, name='{self.name}', category='{self.category}')>"


class Poem(Base):
    """诗经诗篇模型"""
    __tablename__ = "poems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True, index=True)  # 诗名
    chapter = Column(String(50), nullable=False, index=True)  # 章节（如：国风）
    section = Column(String(50), nullable=False, index=True)  # 部分（如：周南）
    content = Column(Text, nullable=False)  # 诗篇内容（JSON 数组字符串）
    full_source = Column(String(100), nullable=False)  # 完整来源（如：国风·周南·关雎）

    def __repr__(self):
        return f"<Poem(id={self.id}, title='{self.title}', chapter='{self.chapter}')>"


class GuestUser(Base):
    """访客用户模型 - 用于留言系统"""
    __tablename__ = "guest_users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), nullable=False)  # 昵称
    avatar_url = Column(String(255), nullable=True, default="")  # 头像URL
    identifier = Column(String(100), nullable=False, unique=True, index=True)  # 唯一标识（浏览器指纹/IP+UA哈希等）
    max_comments_per_page = Column(Integer, default=3)  # 每页面最大留言数（可配置）
    is_blocked = Column(Integer, default=0)  # 是否被禁言 0=正常 1=禁言
    
    # 防护相关字段
    last_comment_at = Column(DateTime, nullable=True)  # 上次留言时间（用于冷却时间检查）
    total_comments = Column(Integer, default=0)  # 总留言数（全局限制）
    trust_score = Column(Float, default=100.0)  # 信任分数（0-100，低于阈值需要审核）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联留言
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GuestUser(id={self.id}, nickname='{self.nickname}')>"


class Comment(Base):
    """留言评论模型 - 支持树形回复"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # 留言内容
    item_id = Column(Integer, ForeignKey("shijing_items.id"), nullable=False, index=True)  # 所属事物ID
    user_id = Column(Integer, ForeignKey("guest_users.id"), nullable=False, index=True)  # 留言用户ID
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)  # 父留言ID（回复功能）
    
    # 状态管理
    is_approved = Column(Integer, default=1)  # 是否通过审核 0=待审核 1=通过 2=拒绝
    is_deleted = Column(Integer, default=0)  # 是否删除（软删除）
    
    # 元数据
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(String(500), nullable=True)  # User-Agent
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("GuestUser", back_populates="comments")
    item = relationship("ShijingItem")
    parent = relationship("Comment", remote_side=[id], backref="replies")

    # 索引优化查询
    __table_args__ = (
        Index('idx_comment_item_created', 'item_id', 'created_at'),
        Index('idx_comment_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, item_id={self.item_id}, user_id={self.user_id})>"


class RateLimit(Base):
    """频率限制模型 - 用于防止刷留言"""
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100), nullable=False, index=True)  # 用户标识
    ip_address = Column(String(50), nullable=False, index=True)  # IP地址
    action_type = Column(String(50), nullable=False, default="comment")  # 操作类型
    count = Column(Integer, default=1)  # 该时间段内的次数
    window_start = Column(DateTime, default=datetime.utcnow)  # 时间窗口开始
    created_at = Column(DateTime, default=datetime.utcnow)

    # 索引优化查询
    __table_args__ = (
        Index('idx_rate_limit_identifier_action', 'identifier', 'action_type'),
        Index('idx_rate_limit_ip_action', 'ip_address', 'action_type'),
    )

    def __repr__(self):
        return f"<RateLimit(id={self.id}, identifier='{self.identifier}', count={self.count})>"


class IPBlacklist(Base):
    """IP 黑名单模型"""
    __tablename__ = "ip_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), nullable=False, unique=True, index=True)
    reason = Column(String(255), nullable=True)  # 封禁原因
    is_permanent = Column(Integer, default=0)  # 是否永久封禁
    expire_at = Column(DateTime, nullable=True)  # 过期时间（NULL表示永久）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IPBlacklist(id={self.id}, ip='{self.ip_address}')>"


class SpamPattern(Base):
    """垃圾内容特征模型 - 用于内容过滤"""
    __tablename__ = "spam_patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(500), nullable=False)  # 正则或关键词
    pattern_type = Column(String(20), default="keyword")  # keyword/regex
    action = Column(String(20), default="block")  # block/review
    description = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SpamPattern(id={self.id}, pattern='{self.pattern[:30]}...')>"


class User(Base):
    """注册用户模型 - 支持邮箱注册和 OAuth 登录"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)  # 邮箱
    username = Column(String(50), unique=True, index=True, nullable=True)  # 用户名
    hashed_password = Column(String(255), nullable=True)  # 密码哈希
    nickname = Column(String(50), nullable=False)  # 显示昵称
    avatar_url = Column(String(255), nullable=True)  # 头像URL
    
    # 用户状态
    is_active = Column(Integer, default=1)  # 是否激活
    is_superuser = Column(Integer, default=0)  # 是否超级管理员
    
    # 留言权限（注册用户可以更多留言）
    max_comments_per_page = Column(Integer, default=10)  # 每页面最多10条（访客是3条）
    max_comments_per_day = Column(Integer, default=50)  # 每天最多50条
    
    # 统计
    total_comments = Column(Integer, default=0)
    last_comment_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)  # 最后登录时间

    # 关联 OAuth 账户
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class OAuthAccount(Base):
    """OAuth 账户关联模型"""
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(20), nullable=False, index=True)  # github, google, etc.
    provider_account_id = Column(String(100), nullable=False, index=True)  # OAuth provider 的用户ID
    provider_account_email = Column(String(255), nullable=True)  # OAuth 邮箱
    access_token = Column(String(500), nullable=True)  # 访问令牌（加密存储）
    refresh_token = Column(String(500), nullable=True)  # 刷新令牌
    expires_at = Column(DateTime, nullable=True)  # 令牌过期时间
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联用户
    user = relationship("User", back_populates="oauth_accounts")

    # 唯一约束：同一 provider 下的同一 account_id 只能绑定一个用户
    __table_args__ = (
        Index('idx_oauth_provider_account', 'provider', 'provider_account_id', unique=True),
    )

    def __repr__(self):
        return f"<OAuthAccount(id={self.id}, provider='{self.provider}', user_id={self.user_id})>"


class UserSession(Base):
    """用户会话模型 - 用于管理登录状态"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_valid = Column(Integer, default=1)  # 是否有效
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, token='{self.session_token[:10]}...')>"


class EmailLoginCode(Base):
    """邮箱验证码登录记录"""
    __tablename__ = "email_login_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False, default="login")
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_email_login_code_email_purpose", "email", "purpose"),
    )

    def __repr__(self):
        return f"<EmailLoginCode(id={self.id}, email='{self.email}', purpose='{self.purpose}')>"
