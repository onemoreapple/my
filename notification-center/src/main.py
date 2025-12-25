from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

from .notifier import notification_manager, EmailNotifier
from .config import settings

app = FastAPI(
    title="Notification Center API",
    description="发送邮件和系统通知的API服务",
    version="1.0.0"
)


# 请求模型
class EmailRequest(BaseModel):
    subject: str
    content: str
    to_emails: Optional[List[EmailStr]] = None
    html_content: Optional[str] = None
    attachments: Optional[List[str]] = None
    sender_name: Optional[str] = None


class TemplateEmailRequest(BaseModel):
    template_name: str
    data: Dict[str, Any]
    subject: str
    to_emails: Optional[List[EmailStr]] = None


class NotificationRequest(BaseModel):
    message: str
    subject: str = "系统通知"
    level: str = "info"
    channels: Optional[List[str]] = None
    recipients: Optional[List[EmailStr]] = None


# 响应模型
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Notification Center",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/send-email", response_model=APIResponse)
async def send_email(request: EmailRequest):
    """发送邮件"""
    try:
        email_notifier = EmailNotifier()
        result = await email_notifier.send_email(
            subject=request.subject,
            content=request.content,
            to_emails=request.to_emails,
            html_content=request.html_content,
            attachments=request.attachments,
            sender_name=request.sender_name
        )

        if result["success"]:
            return APIResponse(
                success=True,
                message="邮件发送成功",
                data=result,
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-template-email", response_model=APIResponse)
async def send_template_email(request: TemplateEmailRequest):
    """发送模板邮件"""
    try:
        email_notifier = EmailNotifier()
        result = await email_notifier.send_template_email(
            template_name=request.template_name,
            data=request.data,
            subject=request.subject,
            to_emails=request.to_emails
        )

        if result["success"]:
            return APIResponse(
                success=True,
                message="模板邮件发送成功",
                data=result,
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notify", response_model=APIResponse)
async def notify(request: NotificationRequest, background_tasks: BackgroundTasks):
    """发送系统通知"""
    try:
        # 后台任务发送通知
        background_tasks.add_task(
            notification_manager.notify,
            message=request.message,
            subject=request.subject,
            level=request.level,
            channels=request.channels,
            recipients=request.recipients
        )

        return APIResponse(
            success=True,
            message="通知正在发送",
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查SMTP配置
        import smtplib
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            # 只是测试连接，不登录
            server.ehlo()

        return {
            "status": "healthy",
            "smtp_config": "ok",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "smtp_config": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )