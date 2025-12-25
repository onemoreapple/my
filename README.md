# 工具集 Docker 部署指南

本项目包含多个工具的Docker化部署方案：

## 📦 服务列表

1. **通知中心** (Notification Center) - 端口 8000
   - 邮件发送服务
   - RESTful API
   - 模板系统
   - 健康检查

2. **投资分析工具** (Investment Analyzer) - 端口 8501
   - Streamlit Web界面
   - 股票数据分析
   - 图表展示

3. **北京车牌许可** (Beijing Permit) - 后台运行
   - 自动化申请工具
   - Chrome + ChromeDriver
   - 日志记录

## 🚀 快速启动

### 1. 配置环境变量

复制并编辑环境配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置邮件服务：
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DEFAULT_RECIPIENT=your-email@gmail.com
```

### 2. 启动所有服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问服务

- **首页**: http://localhost
- **通知中心API**: http://localhost/api/notify/
- **投资分析工具**: http://localhost/investment/
- **API文档**: http://localhost/docs

## 📋 API 使用示例

### 发送测试邮件
```bash
curl -X POST "http://localhost:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "测试邮件",
    "content": "这是一封测试邮件",
    "to_emails": ["recipient@example.com"]
  }'
```

### 在Python中调用通知服务
```python
import requests

def send_notification(message, subject="系统通知"):
    url = "http://notification-center:8000/notify"
    data = {
        "message": message,
        "subject": subject,
        "level": "info"
    }
    response = requests.post(url, json=data)
    return response.json()

# 使用示例
result = send_notification("任务执行成功！", "任务通知")
```

## 🔧 管理命令

```bash
# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart notification-center

# 进入容器
docker-compose exec notification-center bash

# 查看资源使用
docker stats

# 更新服务
docker-compose pull
docker-compose up -d --force-recreate
```

## 📁 目录结构

```
.
├── notification-center/          # 通知服务
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
├── investment_analyzer/          # 投资分析
│   ├── src/
│   ├── web/
│   └── Dockerfile
├── beijing_permit/              # 北京车牌
│   ├── Dockerfile
│   └── *.py
├── nginx/                       # 反向代理配置
│   └── conf.d/
├── docker-compose.yml           # Docker编排文件
└── .env                         # 环境配置
```

## 🔍 故障排查

### 1. 邮件发送失败
- 检查 `.env` 中的SMTP配置
- Gmail需要使用应用专用密码
- 查看通知服务日志：`docker-compose logs notification-center`

### 2. 服务无法访问
- 确认端口是否被占用
- 检查防火墙设置
- 查看服务状态：`docker-compose ps`

### 3. 北京车牌工具问题
- 需要配置虚拟显示
- 检查Chrome/ChromeDriver版本

## 📝 注意事项

1. 生产环境部署前请修改默认密码
2. 建议使用HTTPS保护通信
3. 定期备份日志和数据
4. 监控服务资源使用情况