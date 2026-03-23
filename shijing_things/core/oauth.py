"""
OAuth 工具函数 - GitHub / Google / 微信 OAuth 流程
"""
from urllib.parse import urlencode
import httpx
from typing import Optional, Dict, Any
from shijing_things.core.config import get_settings

settings = get_settings()


class GitHubOAuth:
    """GitHub OAuth 客户端"""
    
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_API_URL = "https://api.github.com/user"
    USER_EMAILS_URL = "https://api.github.com/user/emails"
    
    def __init__(self):
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.redirect_uri = settings.github_redirect_uri
    
    def get_authorize_url(self, state: str) -> str:
        """获取 GitHub 授权 URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 获取用户邮箱权限
            "state": state,
        }
        query = urlencode(params)
        return f"{self.AUTHORIZE_URL}?{query}"
    
    async def get_access_token(self, code: str) -> Optional[str]:
        """用授权码换取访问令牌"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return data.get("access_token")
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取 GitHub 用户信息"""
        async with httpx.AsyncClient() as client:
            # 获取用户基本信息
            response = await client.get(
                self.USER_API_URL,
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json",
                },
            )
            
            if response.status_code != 200:
                return None
            
            user_data = response.json()
            
            # 如果用户没有公开邮箱，获取邮箱列表
            if not user_data.get("email"):
                emails_response = await client.get(
                    self.USER_EMAILS_URL,
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                    },
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    # 找主邮箱
                    for email in emails:
                        if email.get("primary") and email.get("verified"):
                            user_data["email"] = email.get("email")
                            break
                    # 如果没有主邮箱，用第一个验证过的
                    if not user_data.get("email"):
                        for email in emails:
                            if email.get("verified"):
                                user_data["email"] = email.get("email")
                                break
            
            return user_data


# 全局 GitHub OAuth 实例
github_oauth = GitHubOAuth()


class GoogleOAuth:
    """Google OAuth/OpenID Connect 客户端"""

    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_API_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                },
            )
            if response.status_code != 200:
                return None
            return response.json()

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_API_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code != 200:
                return None
            return response.json()


google_oauth = GoogleOAuth()


class WeChatOAuth:
    """微信开放平台网站应用 OAuth 客户端"""

    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    USER_API_URL = "https://api.weixin.qq.com/sns/userinfo"

    def __init__(self):
        self.app_id = settings.wechat_app_id
        self.app_secret = settings.wechat_app_secret
        self.redirect_uri = settings.wechat_redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "appid": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}#wechat_redirect"

    async def get_access_token(self, code: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.TOKEN_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("errcode"):
                return None
            return data

    async def get_user_info(self, access_token: str, openid: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_API_URL,
                params={
                    "access_token": access_token,
                    "openid": openid,
                    "lang": "zh_CN",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("errcode"):
                return None
            return data


wechat_oauth = WeChatOAuth()


def generate_oauth_state() -> str:
    """生成 OAuth state 参数（防止 CSRF）"""
    import secrets
    return secrets.token_urlsafe(32)
