from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """通知基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def send(self, title: str, content: str, recipients: List[str], **kwargs) -> Dict[str, Any]:
        """发送通知的抽象方法"""
        pass

    @abstractmethod
    def get_recipients(self) -> List[str]:
        """获取接收者列表"""
        pass


class EmailNotifier(BaseNotifier):
    """邮件通知实现"""

    async def send(self, title: str, content: str, recipients: List[str], **kwargs) -> Dict[str, Any]:
        """发送邮件"""
        try:
            html_content = kwargs.get('html_content')
            attachments = kwargs.get('attachments', [])

            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = f"Notification System <{self.config['username']}>"
            msg['To'] = ', '.join(recipients)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # 添加文本内容
            text_part = MIMEText(content, 'plain', 'utf-8')
            msg.attach(text_part)

            # 添加HTML内容
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)

            # 添加附件
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

            # 发送邮件
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._send_sync, msg, recipients
            )

            return {
                "success": True,
                "message": "邮件发送成功",
                "recipients": recipients,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {
                "success": False,
                "message": f"邮件发送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _send_sync(self, msg: MIMEMultipart, recipients: List[str]) -> str:
        """同步发送邮件"""
        with smtplib.SMTP(self.config['host'], self.config['port']) as server:
            server.starttls()
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg, to_addrs=recipients)
            return "Email sent successfully"

    def get_recipients(self) -> List[str]:
        return self.config.get('recipients', [])


class WeChatNotifier(BaseNotifier):
    """企业微信通知实现"""

    async def send(self, title: str, content: str, recipients: List[str], **kwargs) -> Dict[str, Any]:
        """发送企业微信消息"""
        try:
            message_type = kwargs.get('message_type', 'text')
            mentioned_list = kwargs.get('mentioned_list', [])
            mentioned_mobile_list = kwargs.get('mentioned_mobile_list', [])

            # 构建消息内容
            if message_type == 'markdown':
                data = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"# {title}\n{content}"
                    }
                }
            elif message_type == 'text':
                data = {
                    "msgtype": "text",
                    "text": {
                        "content": f"{title}\n\n{content}",
                        "mentioned_list": mentioned_list,
                        "mentioned_mobile_list": mentioned_mobile_list
                    }
                }
            else:
                # 默认使用富文本
                data = {
                    "msgtype": "text",
                    "text": {
                        "content": f"{title}\n\n{content}"
                    }
                }

            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config['webhook_url'],
                    json=data,
                    timeout=10.0
                )
                result = response.json()

            if result.get('errcode') == 0:
                return {
                    "success": True,
                    "message": "企业微信消息发送成功",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"企业微信发送失败: {result.get('errmsg')}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"企业微信发送失败: {e}")
            return {
                "success": False,
                "message": f"企业微信发送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def get_recipients(self) -> List[str]:
        # 企业微信通过群组发送，不需要具体的接收者列表
        return []


class FeishuNotifier(BaseNotifier):
    """飞书通知实现"""

    async def send(self, title: str, content: str, recipients: List[str], **kwargs) -> Dict[str, Any]:
        """发送飞书消息"""
        try:
            at_mobiles = kwargs.get('at_mobiles', [])
            at_user_ids = kwargs.get('at_user_ids', [])
            message_type = kwargs.get('message_type', 'text')

            # 构建@内容
            at_content = ""
            if at_mobiles:
                at_content += " ".join([f"<at phone='{mobile}'></at>" for mobile in at_mobiles])
            if at_user_ids:
                at_content += " ".join([f"<at user_id='{uid}'></at>" for uid in at_user_ids])

            # 构建消息
            if message_type == 'rich_text':
                # 富文本格式
                title_element = [{"tag": "text", "text": title}]
                content_element = [{"tag": "text", "text": content}]
                if at_content:
                    content_element.append({"tag": "text", "text": f"\n{at_content}"})

                data = {
                    "msg_type": "rich_text",
                    "rich_text": {
                        "title": title,
                        "content": [
                            [{"tag": "text", "text": title, "style": {"bold": True}}],
                            content_element
                        ]
                    }
                }
            else:
                # 文本格式
                text = f"{title}\n\n{content}"
                if at_content:
                    text += f"\n{at_content}"

                data = {
                    "msg_type": "text",
                    "content": {"text": text}
                }

            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config['webhook_url'],
                    json=data,
                    timeout=10.0
                )
                result = response.json()

            if result.get('StatusCode') == 0 or result.get('code') == 0:
                return {
                    "success": True,
                    "message": "飞书消息发送成功",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"飞书发送失败: {result}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"飞书发送失败: {e}")
            return {
                "success": False,
                "message": f"飞书发送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def get_recipients(self) -> List[str]:
        # 飞书通过群组发送，接收者信息保存在配置中
        return self.config.get('at_mobiles', [])


class NotificationService:
    """通知服务主类"""

    def __init__(self):
        self.notifiers = {
            'email': EmailNotifier,
            'wechat': WeChatNotifier,
            'feishu': FeishuNotifier
        }

    def get_notifier(self, channel_type: str, config: Dict[str, Any]) -> BaseNotifier:
        """根据类型获取通知器"""
        if channel_type not in self.notifiers:
            raise ValueError(f"不支持的通知类型: {channel_type}")

        return self.notifiers[channel_type](config)

    async def send_notification(
        self,
        channel_type: str,
        channel_config: Dict[str, Any],
        title: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送通知"""
        notifier = self.get_notifier(channel_type, channel_config)
        recipients = notifier.get_recipients()

        return await notifier.send(
            title=title,
            content=content,
            recipients=recipients,
            **kwargs
        )