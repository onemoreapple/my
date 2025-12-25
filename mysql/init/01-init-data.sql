-- 初始化通知渠道
INSERT INTO notification_channels (channel_type, channel_name, config_value, is_active) VALUES
('email', 'work_email', JSON_OBJECT('host', 'smtp.gmail.com', 'port', 587, 'username', 'your-work@gmail.com', 'password', 'your-app-password', 'recipients', JSON_ARRAY('user1@company.com', 'user2@company.com')), true),
('wechat', 'wechat_alert', JSON_OBJECT('webhook_url', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key', 'message_type', 'text'), true),
('feishu', 'feishu_alert', JSON_OBJECT('webhook_url', 'https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url', 'at_mobiles', JSON_ARRAY('13800138000')), true);

-- 初始化通知源
INSERT INTO notification_sources (source_name, source_description, default_channels, default_level, is_active) VALUES
('beijing_permit', '北京进京证申请工具', JSON_ARRAY('email', 'wechat'), 'success', true),
('investment_analyzer', '投资分析工具', JSON_ARRAY('email'), 'info', true),
('system_alert', '系统告警', JSON_ARRAY('wechat', 'feishu'), 'error', true);

-- 初始化通知源和渠道的映射关系
INSERT INTO source_channel_mapping (source_name, channel_type, channel_name, is_enabled, priority) VALUES
('beijing_permit', 'email', 'work_email', true, 1),
('beijing_permit', 'wechat', 'wechat_alert', true, 2),
('investment_analyzer', 'email', 'work_email', true, 1),
('system_alert', 'wechat', 'wechat_alert', true, 1),
('system_alert', 'feishu', 'feishu_alert', true, 2);