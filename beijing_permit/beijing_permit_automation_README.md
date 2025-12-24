# 进京证自动办理脚本使用说明

## 概述
本脚本用于自动办理北京市进京证，每天定时检查进京证状态，在需要时自动办理并发送邮件通知。

## 功能特点
- 🔐 自动登录认证
- 📅 每天定时检查（默认早上8点）
- 📝 智能判断是否需要办理（剩余2天时自动办理）
- 📧 邮件通知功能
- 📊 日志记录
- 🔄 Token自动刷新

## 安装依赖
```bash
pip install requests schedule python-dotenv
```

## 配置方法

### 1. 创建配置文件 `.env`
```bash
cp .env.example .env
```

### 2. 编辑 `.env` 文件
```env
# 北京交管局账号（实际使用的信息）
BEIJING_USERNAME=your_username
BEIJING_PASSWORD=your_password
BEIJING_PHONE=13800138000
BEIJING_CAR_PLATE=京AXXXXX

# 邮件通知配置
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
RECIPIENT_EMAIL=recipient@email.com
```

## 重要：API接口获取

### 方法一：Fiddler抓包
1. 手机安装Fiddler证书
2. 配置代理抓包
3. 打开"北京交警"APP
4. 执行登录、查询、申请等操作
5. 分析捕获的API请求

### 方法二：Charles抓包
1. 安装Charles
2. 配置SSL证书
3. 手机设置代理
4. 捕获API请求

### 需要获取的关键信息：
- 登录API地址和参数
- 查询进京证API地址和参数
- 申请进京证API地址和参数
- Token刷新机制
- 请求头信息（User-Agent等）
- 人机验证处理方式

## 运行脚本

### 直接运行
```bash
python beijing_permit_automation.py
```

### 后台运行
```bash
nohup python beijing_permit_automation.py &
```

### 使用systemd（Linux）
```bash
# 创建服务文件
sudo nano /etc/systemd/system/beijing-permit.service
```

```ini
[Unit]
Description=Beijing Permit Automation
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/script
ExecStart=/usr/bin/python3 beijing_permit_automation.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable beijing-permit.service
sudo systemctl start beijing-permit.service
```

## 日志查看
```bash
tail -f beijing_permit.log
```

## 安全注意事项
1. ✅ 使用环境变量存储敏感信息
2. ✅ 不要提交.env文件到版本控制
3. ✅ 定期更换密码
4. ✅ 使用应用专用密码（不是邮箱密码）
5. ✅ 考虑使用加密存储

## 故障排除

### 常见问题
1. **登录失败**
   - 检查账号密码是否正确
   - 确认API地址是否更新
   - 查看是否需要验证码

2. **API请求失败**
   - 检查User-Agent是否正确
   - 确认请求头格式
   - 查看Token是否过期

3. **邮件发送失败**
   - 检查SMTP设置
   - 使用应用专用密码
   - 确认防火墙设置

### 调试模式
```python
# 在脚本开头添加
logging.basicConfig(level=logging.DEBUG)
```

## 扩展功能
- 支持多辆车
- 集成企业微信通知
- Web界面管理
- Docker容器化
- 数据库存储历史记录

## 免责声明
本脚本仅用于学习和个人使用。请遵守北京市交通管理规定，合理使用进京证功能。使用本脚本所产生的任何后果由使用者自行承担。