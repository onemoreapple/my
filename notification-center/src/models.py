from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, BIGINT, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from .database import Base
import enum


class ChannelType(enum.Enum):
    EMAIL = "email"
    WECHAT = "wechat"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"


class NotificationLevel(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_type = Column(Enum(ChannelType), nullable=False)
    channel_name = Column(String(50), nullable=False)
    config_value = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())


class NotificationSource(Base):
    __tablename__ = "notification_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(50), nullable=False, unique=True)
    source_description = Column(String(200))
    default_channels = Column(JSON, nullable=False)
    default_level = Column(Enum(NotificationLevel), default=NotificationLevel.INFO)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    source_name = Column(String(50), ForeignKey('notification_sources.source_name'), nullable=False)
    channel_type = Column(String(20), nullable=False)
    channel_name = Column(String(50), nullable=False)
    notification_level = Column(Enum(NotificationLevel), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    recipients = Column(JSON)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=func.now())
    sent_at = Column(TIMESTAMP)


class SourceChannelMapping(Base):
    __tablename__ = "source_channel_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(50), ForeignKey('notification_sources.source_name'), nullable=False)
    channel_type = Column(String(20), nullable=False)
    channel_name = Column(String(50), nullable=False)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, default=func.now())