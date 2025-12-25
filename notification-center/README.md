# Notification Center

email notification service

## 功能特性

- 发送邮件通知
- 支持HTML格式邮件
- 支持附件
- 模板系统
- RESTful API
- 健康检查

## Docker启动

```bash
docker-compose up -d notification-center
```

## API使用示例

### 发送邮件
```bash
curl -X POST "http://localhost:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "测试邮件",
    "content": "这是一封测试邮件",
    "to_emails": ["recipient@example.com"]
  }'
```

### 发送模板邮件
```bash
curl -X POST "http://localhost:8000/send-template-email" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "task_success",
    "data": {
      "task_name": "数据分析任务",
      "execution_time": "2024-01-01 12:00:00",
      "result": "处理了1000条记录"
    },
    "subject": "任务执行成功通知"
  }'
```

### 发送系统通知
```bash
curl -X POST "http://localhost:8000/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "系统异常，请及时处理",
    "subject": "系统告警",
    "level": "error"
  }'
```