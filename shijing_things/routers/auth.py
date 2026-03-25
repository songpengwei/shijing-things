"""
认证路由 - 注册、登录、OAuth
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import secrets

from shijing_things.core.database import get_db
from shijing_things.core.config import get_settings
from shijing_things.core.mail import send_email, is_email_login_enabled
from shijing_things.core.oauth import github_oauth, google_oauth, wechat_oauth, generate_oauth_state
from shijing_things.core.security import create_access_token, get_password_hash, verify_password
from shijing_things.core.session_auth import clear_comment_session
from shijing_things.crud.crud import (
    user as crud_user, oauth_account as crud_oauth, user_session as crud_session,
    email_login_code as crud_email_login_code
)
from shijing_things.schemas.schemas import (
    UserCreate, UserLogin, UserResponse, Token, EmailCodeRequest,
    EmailCodeVerify, MessageResponse, LoginRedirectResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

OAUTH_PROVIDERS = {
    "github": {
        "client": github_oauth,
        "session_auth_type": "oauth_github",
    },
    "google": {
        "client": google_oauth,
        "session_auth_type": "oauth_google",
    },
    "wechat": {
        "client": wechat_oauth,
        "session_auth_type": "oauth_wechat",
    },
}


def is_provider_enabled(provider: str) -> bool:
    if provider == "github":
        return bool(settings.github_client_id and settings.github_client_secret)
    if provider == "google":
        return bool(settings.google_client_id and settings.google_client_secret)
    if provider == "wechat":
        return bool(settings.wechat_app_id and settings.wechat_app_secret)
    return False


def set_authenticated_session(request: Request, *, user_id: int, session_token: str, auth_type: str, username: str = "", nickname: str = "", avatar_url: str = "") -> None:
    request.session["comment_user_id"] = user_id
    request.session["comment_session_token"] = session_token
    request.session["comment_is_authenticated"] = True
    request.session["comment_auth_type"] = auth_type
    request.session["comment_username"] = username
    request.session["comment_nickname"] = nickname
    request.session["comment_avatar_url"] = avatar_url


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user_session(request: Request, *, db: Session, user_id: int, auth_type: str, username: str = "", nickname: str = "", avatar_url: str = "") -> None:
    client_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")[:500]
    session = crud_session.create(db, user_id=user_id, ip_address=client_ip, user_agent=user_agent)
    set_authenticated_session(
        request,
        user_id=user_id,
        session_token=session.session_token,
        auth_type=auth_type,
        username=username,
        nickname=nickname,
        avatar_url=avatar_url,
    )


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
        create_user_session(
            request,
            db=db,
            user_id=db_user.id,
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
            create_user_session(
                request,
                db=db,
                user_id=existing_user.id,
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
    create_user_session(
        request,
        db=db,
        user_id=db_user.id,
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


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Google OAuth 回调处理"""
    stored_state = request.session.get("oauth_state")
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter")

    provider = "google"
    if request.session.get("oauth_provider") not in (None, provider):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider mismatch")

    token_data = await google_oauth.get_access_token(code)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get access token from Google")

    access_token = token_data.get("access_token", "")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google OAuth response")

    google_user = await google_oauth.get_user_info(access_token)
    if not google_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from Google")

    return finalize_oauth_login(
        request,
        db=db,
        provider=provider,
        provider_account_id=str(google_user.get("sub")),
        email=google_user.get("email", ""),
        nickname=google_user.get("name") or google_user.get("email", "Google用户"),
        avatar_url=google_user.get("picture", ""),
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

@router.post("/email/request-code", response_model=MessageResponse)
def request_email_login_code(
    payload: EmailCodeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """发送邮箱登录验证码"""
    if not is_email_login_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="邮箱验证码登录未配置")

    email = normalize_email(payload.email)
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入有效邮箱地址")

    latest_code = crud_email_login_code.get_latest_active(db, email=email)
    if latest_code:
        cooldown_deadline = latest_code.created_at + timedelta(seconds=settings.email_login_code_cooldown_seconds)
        if cooldown_deadline > datetime.utcnow():
            wait_seconds = int((cooldown_deadline - datetime.utcnow()).total_seconds()) + 1
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"请求过于频繁，请在 {wait_seconds} 秒后重试")

    plain_code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=settings.email_login_code_expire_minutes)
    client_ip = request.client.host if request.client else ""
    crud_email_login_code.create(
        db,
        email=email,
        code_hash=get_password_hash(plain_code),
        expires_at=expires_at,
        ip_address=client_ip
    )

    subject = "诗经事物登录验证码"
    text_content = (
        f"您的登录验证码是：{plain_code}\n\n"
        f"该验证码将在 {settings.email_login_code_expire_minutes} 分钟后失效。"
    )
    html_content = (
        f"<p>您的登录验证码是：</p>"
        f"<p style='font-size:28px;font-weight:700;letter-spacing:4px;'>{plain_code}</p>"
        f"<p>该验证码将在 {settings.email_login_code_expire_minutes} 分钟后失效。</p>"
    )
    try:
        send_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"验证码发送失败：{exc}") from exc

    return {"message": "验证码已发送，请查收邮箱"}


@router.post("/email/verify-code", response_model=LoginRedirectResponse)
def verify_email_login_code(
    payload: EmailCodeVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """校验邮箱验证码并登录"""
    email = normalize_email(payload.email)
    code = payload.code.strip()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入验证码")

    record = crud_email_login_code.get_latest_active(db, email=email)
    if not record or not verify_password(code, record.code_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已失效")

    crud_email_login_code.consume(db, record=record)

    user = crud_user.get_by_email(db, email=email)
    if user and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")

    if not user:
        local_part = email.split("@")[0] or "user"
        username = crud_user.ensure_unique_username(db, base_username=f"email_{local_part}")
        user = crud_user.create(
            db,
            email=email,
            username=username,
            password=secrets.token_urlsafe(24),
            nickname=local_part[:50] or email,
            avatar_url=""
        )

    crud_user.update_last_login(db, user_id=user.id)
    create_user_session(
        request,
        db=db,
        user_id=user.id,
        auth_type="email_code",
        username=user.username or "",
        nickname=user.nickname,
        avatar_url=user.avatar_url or "",
    )

    next_url = payload.next or "/"
    return {"message": "登录成功", "redirect_url": next_url}

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
    request.session["comment_user_id"] = user.id
    request.session["comment_session_token"] = session.session_token
    request.session["comment_is_authenticated"] = True
    request.session["comment_auth_type"] = "password"
    request.session["comment_username"] = user.username or ""
    request.session["comment_nickname"] = user.nickname
    request.session["comment_avatar_url"] = user.avatar_url or ""
    
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
    session_token = request.session.get("comment_session_token")
    if session_token:
        crud_session.invalidate(db, token=session_token)

    clear_comment_session(request)
    
    return {"message": "Successfully logged out"}


# ==================== 当前用户信息 ====================

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    user_id = request.session.get("comment_user_id")
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
    is_authenticated = request.session.get("comment_is_authenticated", False)
    user_id = request.session.get("comment_user_id")
    auth_type = request.session.get("comment_auth_type")
    
    return {
        "is_authenticated": is_authenticated,
        "user_id": user_id,
        "auth_type": auth_type
    }
