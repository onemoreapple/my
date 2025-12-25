from os import getenv
from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/notification_center")

    # SMTP邮件配置
    smtp_host: str = getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(getenv("SMTP_PORT", "587"))
    smtp_username: str = getenv("SMTP_USERNAME", "")
    smtp_password: str = getenv("SMTP_PASSWORD", "")

    # 企业微信配置
    wechat_webhook_url: str = getenv("WECHAT_WEBHOOK_URL", "")

    # 飞书配置
    feishu_webhook_url: str = getenv("FEISHU_WEBHOOK_URL", "")

    # API配置
    api_host: str = getenv("API_HOST", "0.0.0.0")
    api_port: int = int(getenv("API_PORT", "8000"))

    class Config:
        env_file = ".env"


settings = Settings()