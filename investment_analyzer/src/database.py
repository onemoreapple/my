import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class InvestmentDB:
    def __init__(self, db_path: str = "data/investment.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """创建所有数据表"""
        with self.conn:
            # 投资标的表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    en_name TEXT,
                    market TEXT NOT NULL,  -- CN/HK/US
                    type TEXT NOT NULL,   -- STOCK/ETF/INDEX
                    industry TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    list_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 日K线表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_klines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_code TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    open DECIMAL(12,4),
                    high DECIMAL(12,4),
                    low DECIMAL(12,4),
                    close DECIMAL(12,4),
                    volume BIGINT,
                    turnover DECIMAL(18,2),
                    adj_close DECIMAL(12,4),
                    pe_ratio DECIMAL(8,4),
                    pb_ratio DECIMAL(8,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(target_code, trade_date),
                    FOREIGN KEY (target_code) REFERENCES targets(code)
                )
            """)

            # 交易记录表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_code TEXT NOT NULL,
                    trade_date DATE NOT NULL,
                    direction TEXT NOT NULL,  -- BUY/SELL
                    quantity INTEGER NOT NULL,
                    price DECIMAL(12,4) NOT NULL,
                    commission DECIMAL(12,4) DEFAULT 0,
                    currency TEXT NOT NULL,  -- CNY/HKD/USD
                    exchange_rate DECIMAL(8,4) DEFAULT 1,
                    trade_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (target_code) REFERENCES targets(code)
                )
            """)

            # 资金账户表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    cn_balance DECIMAL(12,2) DEFAULT 0,
                    hk_balance DECIMAL(12,2) DEFAULT 0,
                    us_balance DECIMAL(12,2) DEFAULT 0,
                    total_balance_cny DECIMAL(12,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)

            # AI分析预留表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_code TEXT NOT NULL,
                    analysis_date DATE NOT NULL,
                    model_version TEXT,
                    prediction_type TEXT,  -- TREND/PRICE/RISK
                    score DECIMAL(4,2),
                    reasoning TEXT,  -- JSON格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (target_code) REFERENCES targets(code)
                )
            """)

            # 策略回测表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_return DECIMAL(8,4),
                    max_drawdown DECIMAL(8,4),
                    sharpe_ratio DECIMAL(8,4),
                    config TEXT,  -- JSON格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_klines_target_date ON daily_klines(target_code, trade_date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_target_date ON transactions(target_code, trade_date)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_target_date ON ai_analysis(target_code, analysis_date)")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()