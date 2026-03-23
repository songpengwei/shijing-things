"""
认证路由 - 注册、登录、OAuth
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from shijing_things.core.database import get_db
from shijing_things.core.config import get_settings
from shijing_things.core.oauth import github_oauth, wechat_oauth, generate_oauth_state
from shijing_things.core.security import create_access_token
from shijing_things.crud.crud import user as crud_user, oauth_account as crud_oauth, user_session as crud_session
from shijing_things.schemas.schemas import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

OAUTH_PROVIDERS = {
    "github": {
        "client": github_oauth,
        "session_auth_type": "oauth_github",
    },
    "wechat": {
        "client": wechat_oauth,
        "session_auth_type": "oauth_wechat",
    },
}


def is_provider_enabled(provider: str) -> bool:
    if provider == "github":
        return bool(settings.github_client_id and settings.github_client_secret)
    if provider == "wechat":
        return bool(settings.wechat_app_id and settings.wechat_app_secret)
    return False


def set_authenticated_session(request: Request, *, user_id: int, session_token: str, auth_type: str, username: str = "", nickname: str = "", avatar_url: str = "") -> None:
    request.session["user_id"] = user_id
    request.session["session_token"] = session_token
    request.session["is_authenticated"] = True
    request.session["auth_type"] = auth_type
    request.session["username"] = username
    request.session["nickname"] = nickname
    request.session["avatar_url"] = avatar_url


# ==================== 注册/登录页面路由 ====================

@router.get("/login")
def login_page(request: Request, next: str = "/", provider: str = "github"):
    """OAuth 登录入口，默认 GitHub"""
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth provider not found")
    if not is_provider_enabled(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider} OAuth 未配置"
        )

    state = generate_oauth_state()
    request.session["oauth_state"] = state
    request.session["oauth_provider"] = provider
    request.session["next_url"] = next
    auth_url = OAUTH_PROVIDERS[provider]["client"].get_authorize_url(state)
    return RedirectResponse(url=auth_url, status_code=302)


def finalize_oauth_login(
    request: Request,
    *,
    db: Session,
    provider: str,
    provider_account_id: str,
    email: str,
    nickname: str,
    avatar_url: str,
    access_token: str
):
    existing_oauth = crud_oauth.get_by_provider_account(
        db, provider=provider, provider_account_id=provider_account_id
    )

    auth_type = OAUTH_PROVIDERS[provider]["session_auth_type"]

    if existing_oauth:
        db_user = crud_user.get(db, user_id=existing_oauth.user_id)
        if not db_user or not db_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

        existing_oauth.access_token = access_token
        if email:
            existing_oauth.provider_account_email = email
        db.add(existing_oauth)
        db.commit()

        crud_user.update_last_login(db, user_id=db_user.id)
        client_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")[:500]
        session = crud_session.create(db, user_id=db_user.id, ip_address=client_ip, user_agent=user_agent)
        set_authenticated_session(
            request,
            user_id=db_user.id,
            session_token=session.session_token,
            auth_type=auth_type,
            username=db_user.username or "",
            nickname=db_user.nickname,
            avatar_url=db_user.avatar_url or "",
        )
        next_url = request.session.get("next_url", "/")
        return RedirectResponse(url=next_url, status_code=302)

    if email:
        existing_user = crud_user.get_by_email(db, email=email)
        if existing_user:
            crud_oauth.create(
                db,
                user_id=existing_user.id,
                provider=provider,
                provider_account_id=provider_account_id,
                provider_account_email=email,
                access_token=access_token
            )
            crud_user.update_last_login(db, user_id=existing_user.id)
            client_ip = request.client.host if request.client else ""
            user_agent = request.headers.get("user-agent", "")[:500]
            session = crud_session.create(db, user_id=existing_user.id, ip_address=client_ip, user_agent=user_agent)
            set_authenticated_session(
                request,
                user_id=existing_user.id,
                session_token=session.session_token,
                auth_type=auth_type,
                username=existing_user.username or "",
                nickname=existing_user.nickname,
                avatar_url=existing_user.avatar_url or "",
            )
            next_url = request.session.get("next_url", "/")
            return RedirectResponse(url=next_url, status_code=302)

    db_user = crud_user.create_oauth_user(
        db,
        email=email or f"{provider}_{provider_account_id}@placeholder.local",
        nickname=nickname,
        avatar_url=avatar_url,
        provider=provider,
        provider_account_id=provider_account_id,
        provider_account_email=email
    )
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")[:500]
    session = crud_session.create(db, user_id=db_user.id, ip_address=client_ip, user_agent=user_agent)
    set_authenticated_session(
        request,
        user_id=db_user.id,
        session_token=session.session_token,
        auth_type=auth_type,
        username=db_user.username or "",
        nickname=db_user.nickname,
        avatar_url=db_user.avatar_url or "",
    )
    next_url = request.session.get("next_url", "/")
    return RedirectResponse(url=next_url, status_code=302)


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
    
    provider = "github"
    if request.session.get("oauth_provider") not in (None, provider):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider mismatch")

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
    
    return finalize_oauth_login(
        request,
        db=db,
        provider=provider,
        provider_account_id=github_id,
        email=github_email,
        nickname=github_name,
        avatar_url=github_avatar,
        access_token=access_token,
    )


@router.get("/wechat/callback")
async def wechat_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """微信 OAuth 回调处理"""
    stored_state = request.session.get("oauth_state")
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter")

    provider = "wechat"
    if request.session.get("oauth_provider") not in (None, provider):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider mismatch")

    token_data = await wechat_oauth.get_access_token(code)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get access token from WeChat")

    access_token = token_data.get("access_token", "")
    openid = token_data.get("openid", "")
    if not access_token or not openid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WeChat OAuth response")

    wechat_user = await wechat_oauth.get_user_info(access_token, openid)
    if not wechat_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from WeChat")

    provider_account_id = wechat_user.get("unionid") or openid
    nickname = wechat_user.get("nickname") or "微信用户"
    avatar_url = wechat_user.get("headimgurl", "")

    return finalize_oauth_login(
        request,
        db=db,
        provider=provider,
        provider_account_id=str(provider_account_id),
        email="",
        nickname=nickname,
        avatar_url=avatar_url,
        access_token=access_token,
    )


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
