import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password

    async def send_email(
        self,
        subject: str,
        content: str,
        to_emails: Optional[List[str]] = None,
        html_content: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        sender_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送邮件通知

        Args:
            subject: 邮件主题
            content: 邮件内容（纯文本）
            to_emails: 收件人列表，如果为空则使用默认收件人
            html_content: HTML格式的邮件内容（可选）
            attachments: 附件路径列表（可选）
            sender_name: 发送者名称（可选）

        Returns:
            包含发送结果的字典
        """
        try:
            # 使用默认收件人
            if not to_emails:
                to_emails = [settings.default_recipient]
                if not to_emails[0]:
                    raise ValueError("未设置默认收件人地址")

            sender = f"{sender_name or 'System'} <{self.smtp_username}>"

            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(to_emails)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # 添加文本内容
            text_part = MIMEText(content, 'plain', 'utf-8')
            msg.attach(text_part)

            # 添加HTML内容（如果提供）
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)

            # 添加附件（如果提供）
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEApplication(f.read())
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=file_path.split('/')[-1]
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.error(f"添加附件失败: {file_path}, 错误: {e}")

            # 在线程池中执行同步的SMTP操作
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._send_sync, msg, to_emails
            )

            return {
                "success": True,
                "message": "邮件发送成功",
                "recipients": to_emails,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {
                "success": False,
                "message": f"邮件发送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _send_sync(self, msg: MIMEMultipart, to_emails: List[str]) -> str:
        """同步发送邮件的辅助函数"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg, to_addrs=to_emails)
            return "Email sent successfully"

    async def send_template_email(
        self,
        template_name: str,
        data: Dict[str, Any],
        subject: str,
        to_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发送基于模板的邮件

        Args:
            template_name: 模板名称
            data: 模板数据
            subject: 邮件主题
            to_emails: 收件人列表

        Returns:
            发送结果
        """
        # 简单的模板系统（可以后续升级为Jinja2）
        templates = {
            "task_success": """
任务执行成功！

任务详情：
- 任务名称: {task_name}
- 执行时间: {execution_time}
- 结果: {result}

系统自动通知
            """,
            "alert": """
⚠️ 告警通知

告警详情：
- 告警级别: {level}
- 告警内容: {message}
- 时间: {timestamp}

请及时处理！
            """
        }

        template = templates.get(template_name, templates["task_success"])
        content = template.format(**data)

        return await self.send_email(
            subject=subject,
            content=content,
            to_emails=to_emails
        )


class NotificationManager:
    """通知管理器，支持多种通知方式"""

    def __init__(self):
        self.email_notifier = EmailNotifier()

    async def notify(
        self,
        message: str,
        subject: str = "系统通知",
        level: str = "info",
        channels: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发送通知

        Args:
            message: 通知内容
            subject: 通知主题
            level: 通知级别 (info, warning, error, success)
            channels: 通知渠道 (email, sms, webhook等)
            recipients: 收件人列表

        Returns:
            通知发送结果
        """
        if not channels:
            channels = ["email"]

        results = []

        for channel in channels:
            if channel == "email":
                result = await self.email_notifier.send_email(
                    subject=f"[{level.upper()}] {subject}",
                    content=message,
                    to_emails=recipients
                )
                results.append(result)

            # 可以在这里添加其他通知渠道
            # elif channel == "sms":
            #     result = await self.sms_notifier.send_sms(...)
            #     results.append(result)

        return {
            "overall_status": "success" if all(r["success"] for r in results) else "failed",
            "channel_results": results,
            "timestamp": datetime.now().isoformat()
        }


# 全局通知管理器实例
notification_manager = NotificationManager()