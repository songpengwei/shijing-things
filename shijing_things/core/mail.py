"""
邮件发送工具
"""
from email.message import EmailMessage
import smtplib

from shijing_things.core.config import get_settings


settings = get_settings()


def is_email_login_enabled() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_from_email
        and settings.smtp_username
        and settings.smtp_password
    )


def send_email(*, to_email: str, subject: str, html_content: str, text_content: str = "") -> None:
    if not is_email_login_enabled():
        raise RuntimeError("SMTP 未配置，无法发送邮件")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = to_email
    message.set_content(text_content or subject)
    message.add_alternative(html_content, subtype="html")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
