"""
会话身份辅助函数
"""
from fastapi import Request

COMMENT_AUTH_TYPES = {"oauth_github", "oauth_google", "oauth_wechat", "email_code", "password"}
COMMENT_INTERACTIVE_AUTH_TYPES = {"oauth_github", "oauth_google", "oauth_wechat", "email_code"}


def is_admin_logged_in(request: Request) -> bool:
    """检查管理员是否已登录"""
    return request.session.get("admin_logged_in") is True


def is_comment_user_logged_in(request: Request) -> bool:
    """检查留言用户是否已登录"""
    return (
        request.session.get("comment_is_authenticated") is True
        and request.session.get("comment_auth_type") in COMMENT_AUTH_TYPES
        and bool(request.session.get("comment_user_id"))
    )


def is_comment_interactive_user(request: Request) -> bool:
    """检查是否是可直接留言的登录用户"""
    return (
        request.session.get("comment_is_authenticated") is True
        and request.session.get("comment_auth_type") in COMMENT_INTERACTIVE_AUTH_TYPES
        and bool(request.session.get("comment_user_id"))
    )


def get_comment_auth_label(request: Request) -> str:
    """获取留言用户登录方式文案"""
    auth_type = request.session.get("comment_auth_type")
    if auth_type == "oauth_wechat":
        return "微信"
    if auth_type == "oauth_google":
        return "Google"
    if auth_type == "email_code":
        return "邮箱验证码"
    if auth_type == "password":
        return "密码"
    return "GitHub"


def clear_admin_session(request: Request) -> None:
    """清理管理员登录态"""
    for key in ("admin_logged_in", "admin_username"):
        request.session.pop(key, None)


def clear_comment_session(request: Request) -> None:
    """清理留言用户登录态"""
    for key in (
        "comment_user_id",
        "comment_session_token",
        "comment_is_authenticated",
        "comment_auth_type",
        "comment_username",
        "comment_nickname",
        "comment_avatar_url",
        "oauth_state",
        "oauth_provider",
        "next_url",
    ):
        request.session.pop(key, None)
