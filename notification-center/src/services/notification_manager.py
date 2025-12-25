from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from datetime import datetime
import asyncio
import logging

from ..models import (
    NotificationChannel,
    NotificationSource,
    Notification,
    SourceChannelMapping,
    NotificationLevel,
    NotificationStatus
)
from .notification_service import NotificationService


class NotificationManager:
    """通知管理器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService()

    async def send_notification(
        self,
        source_name: str,
        title: str,
        content: str,
        level: NotificationLevel,
        channels: Optional[List[str]] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送通知

        Args:
            source_name: 通知源名称
            title: 通知标题
            content: 通知内容
            level: 通知级别
            channels: 指定的渠道列表，如果为空则使用默认渠道
            custom_data: 自定义数据

        Returns:
            发送结果
        """
        results = []
        notifications_created = []

        try:
            # 1. 获取通知源信息
            source_query = select(NotificationSource).where(
                NotificationSource.source_name == source_name,
                NotificationSource.is_active == True
            )
            source_result = await self.db.execute(source_query)
            source = source_result.scalar_one_or_none()

            if not source:
                return {
                    "success": False,
                    "message": f"通知源不存在或未激活: {source_name}"
                }

            # 2. 确定要使用的渠道
            if channels:
                # 使用指定的渠道
                channel_names = channels
            else:
                # 使用默认渠道
                channel_names = source.default_channels or []

            if not channel_names:
                return {
                    "success": False,
                    "message": "未指定通知渠道"
                }

            # 3. 获取渠道配置
            mappings_query = select(SourceChannelMapping, NotificationChannel).join(
                NotificationChannel,
                and_(
                    SourceChannelMapping.channel_type == NotificationChannel.channel_type,
                    SourceChannelMapping.channel_name == NotificationChannel.channel_name
                )
            ).where(
                SourceChannelMapping.source_name == source_name,
                SourceChannelMapping.is_enabled == True,
                NotificationChannel.channel_name.in_(channel_names),
                NotificationChannel.is_active == True
            ).order_by(SourceChannelMapping.priority)

            mappings_result = await self.db.execute(mappings_query)
            channel_mappings = mappings_result.all()

            if not channel_mappings:
                return {
                    "success": False,
                    "message": f"未找到可用的通知渠道: {', '.join(channel_names)}"
                }

            # 4. 并行发送通知
            tasks = []
            for mapping, channel in channel_mappings:
                # 创建通知记录
                notification = Notification(
                    source_name=source_name,
                    channel_type=channel.channel_type.value,
                    channel_name=channel.channel_name,
                    notification_level=level,
                    title=title,
                    content=content,
                    status=NotificationStatus.PENDING
                )
                self.db.add(notification)
                notifications_created.append(notification)
                await self.db.flush()

                # 发送任务
                task = self._send_and_update(
                    notification_id=notification.id,
                    channel_type=channel.channel_type.value,
                    channel_config=channel.config_value,
                    title=title,
                    content=content,
                    level=level,
                    custom_data=custom_data
                )
                tasks.append(task)

            await self.db.commit()

            # 5. 执行所有发送任务
            send_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 6. 汇总结果
            success_count = sum(1 for r in send_results if isinstance(r, dict) and r.get('success'))

            return {
                "overall_status": "success" if success_count > 0 else "failed",
                "success_count": success_count,
                "total_count": len(send_results),
                "channel_results": send_results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"通知发送失败: {e}")
            return {
                "success": False,
                "message": f"通知发送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _send_and_update(
        self,
        notification_id: int,
        channel_type: str,
        channel_config: Dict[str, Any],
        title: str,
        content: str,
        level: NotificationLevel,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发送通知并更新记录"""
        try:
            # 更新状态为处理中
            update_query = select(Notification).where(Notification.id == notification_id)
            result = await self.db.execute(update_query)
            notification = result.scalar_one()
            notification.status = NotificationStatus.PROCESSING
            await self.db.commit()

            # 发送通知
            send_result = await self.notification_service.send_notification(
                channel_type=channel_type,
                channel_config=channel_config,
                title=title,
                content=content,
                level=level.value,
                **(custom_data or {})
            )

            # 更新发送结果
            if send_result.get('success'):
                notification.status = NotificationStatus.SUCCESS
                notification.recipients = send_result.get('recipients')
                notification.sent_at = datetime.now()
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = send_result.get('message')

            notification.retry_count += 1
            await self.db.commit()

            return send_result

        except Exception as e:
            # 更新失败状态
            logger.error(f"渠道 {channel_type} 发送失败: {e}")
            try:
                update_query = select(Notification).where(Notification.id == notification_id)
                result = await self.db.execute(update_query)
                notification = result.scalar_one()
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(e)
                notification.retry_count += 1
                await self.db.commit()
            except:
                pass

            return {
                "success": False,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_notifications(
        self,
        source_name: Optional[str] = None,
        channel_type: Optional[str] = None,
        status: Optional[NotificationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取通知记录"""
        query = select(Notification)

        conditions = []
        if source_name:
            conditions.append(Notification.source_name == source_name)
        if channel_type:
            conditions.append(Notification.channel_type == channel_type)
        if status:
            conditions.append(Notification.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return [
            {
                "id": n.id,
                "source_name": n.source_name,
                "channel_type": n.channel_type,
                "channel_name": n.channel_name,
                "level": n.notification_level.value,
                "title": n.title,
                "content": n.content,
                "status": n.status.value,
                "recipients": n.recipients,
                "error_message": n.error_message,
                "retry_count": n.retry_count,
                "created_at": n.created_at.isoformat(),
                "sent_at": n.sent_at.isoformat() if n.sent_at else None
            }
            for n in notifications
        ]

    async def add_notification_source(
        self,
        source_name: str,
        source_description: str = "",
        default_channels: List[str] = None,
        default_level: NotificationLevel = NotificationLevel.INFO
    ) -> Dict[str, Any]:
        """添加通知源"""
        try:
            existing = await self.db.execute(
                select(NotificationSource).where(NotificationSource.source_name == source_name)
            )
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "message": f"通知源已存在: {source_name}"
                }

            source = NotificationSource(
                source_name=source_name,
                source_description=source_description,
                default_channels=default_channels or [],
                default_level=default_level
            )
            self.db.add(source)
            await self.db.commit()

            return {
                "success": True,
                "message": "通知源添加成功"
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"添加通知源失败: {str(e)}"
            }

    async def add_notification_channel(
        self,
        channel_type: str,
        channel_name: str,
        config_value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加通知渠道配置"""
        try:
            existing = await self.db.execute(
                select(NotificationChannel).where(
                    NotificationChannel.channel_type == channel_type,
                    NotificationChannel.channel_name == channel_name
                )
            )
            if existing.scalar_one_or_none():
                # 更新配置
                channel = existing.scalar_one()
                channel.config_value = config_value
                await self.db.commit()
                return {
                    "success": True,
                    "message": "通知渠道配置更新成功"
                }

            channel = NotificationChannel(
                channel_type=channel_type,
                channel_name=channel_name,
                config_value=config_value
            )
            self.db.add(channel)
            await self.db.commit()

            return {
                "success": True,
                "message": "通知渠道添加成功"
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"添加通知渠道失败: {str(e)}"
            }

    async def configure_source_channels(
        self,
        source_name: str,
        channel_names: List[str],
        enabled: bool = True
    ) -> Dict[str, Any]:
        """配置通知源的渠道映射"""
        try:
            # 先删除旧的映射
            await self.db.execute(
                select(SourceChannelMapping).where(
                    SourceChannelMapping.source_name == source_name
                )
            )
            await self.db.flush()

            # 添加新映射
            for i, channel_name in enumerate(channel_names):
                mapping = SourceChannelMapping(
                    source_name=source_name,
                    channel_type="",  # 需要从channel表获取
                    channel_name=channel_name,
                    is_enabled=enabled,
                    priority=i + 1
                )
                self.db.add(mapping)

            await self.db.commit()
            return {
                "success": True,
                "message": "通知源渠道配置成功"
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"配置通知源渠道失败: {str(e)}"
            }