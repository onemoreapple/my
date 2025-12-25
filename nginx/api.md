# 通知中心 API

发送通知的通知服务，支持多渠道推送。

## 发送通知

```bash
curl -X POST "http://localhost:8000/api/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "beijing_permit",
    "title": "进京证申请完成",
    "content": "您的进京证已申请成功，有效期7天。",
    "level": "success",
    "channels": ["email", "wechat"]
  }'
```

## 配置通知渠道

```bash
curl -X POST "http://localhost:8000/api/config/channels" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "email",
    "channel_name": "work_email",
    "config": {
      "host": "smtp.gmail.com",
      "port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "recipients": ["recipient@example.com"]
    }
  }'
```

## 查询通知记录

```bash
curl "http://localhost:8000/api/notifications?source=beijing_permit&limit=10"
```