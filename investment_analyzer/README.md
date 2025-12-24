# 投资分析系统

一个基于Python和富途API的个人投资管理系统，支持A股、港股、美股和ETF的投资记录与分析。

## 功能特点

- 支持多市场投资标的（A股、港股、美股、ETF）
- 自动获取和更新K线数据
- 交易记录管理
- 持仓分析
- 可视化图表展示
- 报表导出功能
- AI分析预留接口

## 安装与配置

### 1. 安装依赖
```bash
cd investment_analyzer
pip install -r requirements.txt
```

### 2. 安装富途OpenD
请从[富途开放平台](https://openapi.futunn.com/)下载并安装FutuOpenD客户端。

### 3. 启动系统

#### Web界面（推荐）
```bash
cd web
streamlit run app.py
```
访问 http://localhost:8501 使用图形界面。

#### 命令行工具
```bash
# 添加关注标的
python main.py --command add --code HK.00700 --name 腾讯控股

# 更新所有标的的K线数据
python main.py --command update

# 更新特定标的
python main.py --command update --code HK.00700 --days 365

# 导出报表
python main.py --command export
```

## 使用说明

### 1. 添加投资标的
- 支持格式：HK.00700（港股）、US.AAPL（美股）、SZ.000001（A股）、SH.600000（A股）
- 标的代码格式：
  - 港股：HK + 六位数字
  - 美股：US + 股票代码
  - A股：SH（上海）或 SZ（深圳）+ 六位数字

### 2. 更新K线数据
- 富途API有请求频率限制，建议每日收盘后更新一次
- 数据会自动存储到SQLite数据库中

### 3. 记录交易
在Web界面或代码中记录买入/卖出操作：
```python
manager.add_transaction(
    code='HK.00700',
    direction='BUY',
    quantity=100,
    price=350.0,
    trade_date='2024-01-15'
)
```

### 4. 查看分析
- 实时行情展示
- K线图表
- 持仓盈亏分析
- 收益率统计
- 持仓结构饼图

### 5. 导出报表
- 持仓明细Excel报表
- 交易记录Excel报表
- K线数据Excel报表

## 项目结构

```
investment_analyzer/
├── data/               # 数据存储
│   └── investment.db   # SQLite数据库
├── src/               # 源代码
│   ├── database.py    # 数据库操作
│   ├── futu_api.py    # 富途API封装
│   ├── analysis.py    # 数据分析
│   └── export.py      # 报表导出
├── web/               # Web界面
│   └── app.py        # Streamlit应用
├── reports/           # 导出的报表
├── requirements.txt   # 依赖包
└── main.py           # 命令行入口
```

## 注意事项

1. **API限制**：富途API有请求频率限制（默认每秒30次），批量更新时注意控制频率
2. **数据货币**：所有数据最终都会按汇率转换成人民币存储
3. **交易时间**：建议在交易日收盘后更新数据，避免盘中数据波动
4. **数据备份**：定期备份SQLite数据库文件（data/investment.db）

## 后期扩展

- AI分析模型集成（已预留ai_analysis表）
- 策略回测功能
- 移动端App
- 实时价格提醒
- 数据可视化更多选择

## License

MIT