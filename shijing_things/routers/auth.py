"""
认证路由 - 注册、登录、OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta

from shijing_things.core.database import get_db
from shijing_things.core.config import get_settings
from shijing_things.core.oauth import github_oauth, generate_oauth_state
from shijing_things.core.security import create_access_token, generate_session_token
from shijing_things.crud.crud import user as crud_user, oauth_account as crud_oauth, user_session as crud_session
from shijing_things.schemas.schemas import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


# ==================== 注册/登录页面路由 ====================

@router.get("/login")
def login_page(request: Request, next: str = "/"):
    """登录页面 - 支持 GitHub OAuth"""
    # 生成 state 防止 CSRF
    state = generate_oauth_state()
    request.session["oauth_state"] = state
    
    # 保存跳转地址
    request.session["next_url"] = next
    
    # 获取 GitHub 授权 URL
    github_auth_url = github_oauth.get_authorize_url(state)
    
    return {
        "message": "请使用以下方式登录",
        "methods": {
            "github": {
                "name": "GitHub",
                "url": github_auth_url,
                "icon": "github"
            }
        },
        "note": "GitHub 登录将自动创建账户"
    }


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """GitHub OAuth 回调处理"""
    # 验证 state 防止 CSRF
    stored_state = request.session.get("oauth_state")
    if not stored_state or state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # 获取访问令牌
    access_token = await github_oauth.get_access_token(code)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token from GitHub"
        )
    
    # 获取 GitHub 用户信息
    github_user = await github_oauth.get_user_info(access_token)
    if not github_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from GitHub"
        )
    
    github_id = str(github_user.get("id"))
    github_email = github_user.get("email", "")
    github_name = github_user.get("name") or github_user.get("login", "GitHub用户")
    github_avatar = github_user.get("avatar_url", "")
    
    # 检查是否已有该 GitHub 账户关联
    existing_oauth = crud_oauth.get_by_provider_account(
        db, provider="github", provider_account_id=github_id
    )
    
    if existing_oauth:
        # 已存在，更新信息并登录
        db_user = crud_user.get(db, user_id=existing_oauth.user_id)
        if db_user and db_user.is_active:
            # 更新 OAuth token
            existing_oauth.access_token = access_token
            db.add(existing_oauth)
            db.commit()
            
            # 更新登录时间
            crud_user.update_last_login(db, user_id=db_user.id)
            
            # 创建会话
            client_ip = request.client.host if request.client else ""
            user_agent = request.headers.get("user-agent", "")[:500]
            session = crud_session.create(
                db, user_id=db_user.id, ip_address=client_ip, user_agent=user_agent
            )
            
            # 设置 session cookie
            request.session["user_id"] = db_user.id
            request.session["session_token"] = session.session_token
            request.session["is_authenticated"] = True
            request.session["auth_type"] = "oauth_github"
            
            # 跳转回首页或指定页面
            next_url = request.session.get("next_url", "/")
            return RedirectResponse(url=next_url, status_code=302)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
    
    # 检查邮箱是否已被注册
    if github_email:
        existing_user = crud_user.get_by_email(db, email=github_email)
        if existing_user:
            # 邮箱已存在，自动关联 OAuth
            crud_oauth.create(
                db,
                user_id=existing_user.id,
                provider="github",
                provider_account_id=github_id,
                provider_account_email=github_email,
                access_token=access_token
            )
            
            # 登录
            crud_user.update_last_login(db, user_id=existing_user.id)
            
            client_ip = request.client.host if request.client else ""
            user_agent = request.headers.get("user-agent", "")[:500]
            session = crud_session.create(
                db, user_id=existing_user.id, ip_address=client_ip, user_agent=user_agent
            )
            
            request.session["user_id"] = existing_user.id
            request.session["session_token"] = session.session_token
            request.session["is_authenticated"] = True
            request.session["auth_type"] = "oauth_github"
            
            next_url = request.session.get("next_url", "/")
            return RedirectResponse(url=next_url, status_code=302)
    
    # 创建新用户
    db_user = crud_user.create_oauth_user(
        db,
        email=github_email or f"github_{github_id}@placeholder.local",
        nickname=github_name,
        avatar_url=github_avatar,
        provider="github",
        provider_account_id=github_id,
        provider_account_email=github_email
    )
    
    # 创建会话
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")[:500]
    session = crud_session.create(
        db, user_id=db_user.id, ip_address=client_ip, user_agent=user_agent
    )
    
    # 设置 session
    request.session["user_id"] = db_user.id
    request.session["session_token"] = session.session_token
    request.session["is_authenticated"] = True
    request.session["auth_type"] = "oauth_github"
    
    # 跳转
    next_url = request.session.get("next_url", "/")
    return RedirectResponse(url=next_url, status_code=302)


# ==================== API 认证路由 ====================

@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册（邮箱+密码）"""
    # 检查邮箱是否已存在
    if crud_user.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在
    if crud_user.get_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # 创建用户
    user = crud_user.create(
        db,
        email=user_in.email,
        username=user_in.username,
        password=user_in.password,
        nickname=user_in.nickname,
        avatar_url=user_in.avatar_url
    )
    
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录（邮箱/用户名+密码）"""
    user = crud_user.authenticate(
        db, username=user_in.username, password=user_in.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # 更新登录时间
    crud_user.update_last_login(db, user_id=user.id)
    
    # 创建会话
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")[:500]
    session = crud_session.create(
        db, user_id=user.id, ip_address=client_ip, user_agent=user_agent
    )
    
    # 创建 JWT token
    access_token = create_access_token(
        data={"sub": user.id, "session": session.session_token}
    )
    
    # 设置 session
    request.session["user_id"] = user.id
    request.session["session_token"] = session.session_token
    request.session["is_authenticated"] = True
    request.session["auth_type"] = "password"
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user
    }


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登出"""
    session_token = request.session.get("session_token")
    if session_token:
        crud_session.invalidate(db, token=session_token)
    
    request.session.clear()
    
    return {"message": "Successfully logged out"}


# ==================== 当前用户信息 ====================

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/status")
def auth_status(request: Request):
    """检查认证状态"""
    is_authenticated = request.session.get("is_authenticated", False)
    user_id = request.session.get("user_id")
    auth_type = request.session.get("auth_type")
    
    return {
        "is_authenticated": is_authenticated,
        "user_id": user_id,
        "auth_type": auth_type
    }
