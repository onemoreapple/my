# 进京证自动抓包工具

## 分析建议

由于需要获取APP的真实API接口，以下是详细步骤：

## 1. 准备工作

### 工具选择
- **Charles**（推荐，界面友好）
- **Fiddler**（Windows用户）
- **mitmproxy**（命令行）

### 手机端
1. 安卓/iOS设备
2. 安装"北京交警"官方APP
3. 安装抓包工具证书

## 2. 抓包步骤（以Charles为例）

### 2.1 Charles设置
1. 打开Charles → Proxy → Proxy Settings
2. 设置端口：8888
3. 勾选"Enable transparent HTTP proxying"

### 2.2 SSL设置
1. Proxy → SSL Proxying Settings
2. 添加：`*:*`
3. Help → SSL Proxying → Install Charles Root Certificate

### 2.3 手机连接
1. 手机和电脑在同一WiFi
2. 手机WiFi → 设置代理 → 手动配置
3. 服务器：电脑IP，端口：8888
4. 手机浏览器访问：http://chls.pro/ssl
5. 下载并安装证书

## 3. 需要捕获的操作

### 3.1 登录流程
1. 打开北京交警APP
2. 输入账号密码
3. 查看登录POST请求
4. 记录：
   - URL地址
   - Request Headers
   - Request Body（JSON格式）
   - Response结构

### 3.2 查询进京证
1. 点击"进京证办理"
2. 查看当前进京证查询接口
3. 记录API参数

### 3.3 申请流程
1. 点击"申请进京证"
2. 填写信息页面
3. 查看提交接口
4. 注意验证码处理方式

## 4. 关键信息记录

### API列表模板
```json
{
  "apis": {
    "base_url": "https://xxxx.com",
    "login": {
      "path": "/api/auth/login",
      "method": "POST",
      "headers": {
        "User-Agent": "Dalvik/2.1.0...",
        "X-App-Version": "3.2.1",
        "Content-Type": "application/json"
      },
      "params": {
        "username": "string",
        "password": "string",
        "deviceId": "string"
      }
    },
    "query_permit": {
      "path": "/api/permit/current",
      "method": "GET",
      "params": {
        "carPlate": "string"
      }
    },
    "apply_permit": {
      "path": "/api/permit/apply",
      "method": "POST",
      "params": {
        "carPlate": "string",
        "entryDate": "string",
        "exitDate": "string",
        "reason": "string"
      }
    }
  }
}
```

## 5. 注意事项

### 人机验证
- 滑块验证：记录滑动轨迹参数
- 图形验证码：获取验证码接口
- 短信验证：记录验证码接口

### 反爬虫措施
- 设备指纹（Device ID）
- 请求签名
- 时间戳验证

## 6. 安全提醒
1. 仅在自己的设备和账号进行测试
2. 不要保存他人账号信息
3. 测试后及时清理敏感数据

## 7. 替代方案

如果抓包困难，可以尝试：
1. 使用模拟器（如Android Studio）
2. 反编译APP（注意法律风险）
3. 查找是否有开放接口

## 常见问题

- 证书安装失败：检查系统设置
- 无法抓取HTTPS：确认SSL代理设置
- APP检测到代理：可能需要使用VPN

## 相关资源
- [Charles官方文档](https://www.charlesproxy.com/documentation/)
- [Android抓包教程](https://juejin.cn/post/6844903882895544332)

## 后续优化建议

1. **Token管理**
   - 实现60分钟自动刷新
   - 处理Token过期逻辑

2. **错误处理**
   - 网络超时重试
   - 验证失败自动处理

3. **性能优化**
   - 使用连接池
   - 缓存查询结果

4. **安全加固**
   - 数据加密存储
   - IP限制
   - 异常监控