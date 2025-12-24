import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from src.database import InvestmentDB
from src.futu_api import FutuAPIWrapper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvestmentManager:
    def __init__(self, db_path: str = "data/investment.db"):
        """投资管理主类"""
        self.db = InvestmentDB(db_path)
        self.futu_api = None

    def connect_futu(self, host='127.0.0.1', port=11111) -> bool:
        """连接富途API"""
        self.futu_api = FutuAPIWrapper()
        return self.futu_api.connect(host, port)

    def disconnect_futu(self):
        """断开富途API连接"""
        if self.futu_api:
            self.futu_api.disconnect()

    def add_target(self, code: str, name: str = None, market: str = None,
                   asset_type: str = 'STOCK', industry: str = None):
        """添加关注标的

        Args:
            code: 股票代码（如 HK.00700, US.AAPL, SZ.000001）
            name: 标的名称
            market: 市场（CN/HK/US）
            asset_type: 类型（STOCK/ETF/INDEX）
            industry: 行业
        """
        # 如果没有提供市场，从代码推断
        if not market:
            if code.startswith('HK.'):
                market = 'HK'
            elif code.startswith('US.'):
                market = 'US'
            elif code.startswith(('SH.', 'SZ.')):
                market = 'CN'
            else:
                raise ValueError(f"无法从代码推断市场: {code}")

        # 如果没有提供名称，从API获取
        name = name or code

        sql = """
        INSERT OR REPLACE INTO targets
        (code, name, market, type, industry, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.conn.execute(sql, (code, name, market, asset_type, industry, datetime.now()))
        self.db.conn.commit()
        logger.info(f"已添加标的: {code} - {name}")

    def get_active_targets(self) -> List[Dict]:
        """获取所有关注的标的"""
        cur = self.db.conn.execute(
            "SELECT * FROM targets WHERE is_active = 1 ORDER BY code"
        )
        return [dict(row) for row in cur.fetchall()]

    def update_target_klines(self, code: str, days_back: int = 365) -> Dict:
        """更新单个标的的K线数据"""
        if not self.futu_api:
            raise ConnectionError("未连接富途API")

        # 获取数据
        result = self.futu_api.update_daily_klines(code, days_back)

        if not result['success']:
            return result

        df = result['data']
        updated_count = 0

        # 批量插入或更新数据
        with self.db.conn:
            for _, row in df.iterrows():
                sql = """
                INSERT OR REPLACE INTO daily_klines
                (target_code, trade_date, open, high, low, close,
                 volume, turnover, adj_close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                try:
                    self.db.conn.execute(sql, (
                        code,
                        row['time_key'],
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        int(row['volume']),
                        float(row['turnover'] if col_exists(row, 'turnover') else 0),
                        float(row['close'])  # 暂时用收盘价代替复权价
                    ))
                    updated_count += 1
                except Exception as e:
                    logger.error(f"插入K线数据失败: {e}")

        return {
            'success': True,
            'updated_count': updated_count,
            'message': f"成功更新 {updated_count} 条K线数据"
        }

    def update_all_targets_klines(self, days_back: int = 365):
        """更新所有标的的K线数据"""
        targets = self.get_active_targets()
        results = []

        for target in targets:
            logger.info(f"正在更新 {target['code']} 的K线数据...")
            try:
                result = self.update_target_klines(target['code'], days_back)
                result['code'] = target['code']
                result['name'] = target['name']
                results.append(result)
            except Exception as e:
                results.append({
                    'code': target['code'],
                    'name': target['name'],
                    'success': False,
                    'message': str(e)
                })

        return results

    def add_transaction(self, code: str, direction: str, quantity: int,
                        price: float, trade_date: str = None,
                        commission: float = 0, trade_id: str = None):
        """添加交易记录

        Args:
            code: 标的代码
            direction: 交易方向 BUY/SELL
            quantity: 数量
            price: 价格
            trade_date: 交易日期（默认今天）
            commission: 手续费
            trade_id: 交易ID
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y-%m-%d')

        # 获取标的的市场信息以确定货币
        target = self.db.conn.execute(
            "SELECT market FROM targets WHERE code = ?", (code,)
        ).fetchone()

        if not target:
            raise ValueError(f"未找到标的: {code}")

        # 根据市场确定货币
        market_to_currency = {'HK': 'HKD', 'US': 'USD', 'CN': 'CNY'}
        currency = market_to_currency[target['market']]

        sql = """
        INSERT INTO transactions
        (target_code, trade_date, direction, quantity, price,
         commission, currency, trade_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.conn.execute(sql, (
            code, trade_date, direction.upper(), quantity,
            price, commission, currency, trade_id
        ))
        self.db.conn.commit()
        logger.info(f"添加交易记录: {direction} {code} {quantity}股@{price}")

    def get_transactions(self, code: str = None, start_date: str = None,
                        end_date: str = None) -> List[Dict]:
        """获取交易记录"""
        sql = """
        SELECT t.*, tr.name
        FROM transactions t
        JOIN targets tr ON t.target_code = tr.code
        WHERE 1=1
        """
        params = []

        if code:
            sql += " AND t.target_code = ?"
            params.append(code)
        if start_date:
            sql += " AND t.trade_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND t.trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY t.trade_date DESC"

        cur = self.db.conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def get_holding_positions(self, date: str = None) -> List[Dict]:
        """获取持仓情况"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        # 计算每个标的的持仓
        sql = """
        SELECT
            target_code,
            name,
            market,
            SUM(CASE WHEN direction = 'BUY' THEN quantity ELSE -quantity END) as quantity,
            AVG(CASE WHEN direction = 'BUY' THEN quantity ELSE -quantity END) as avg_cost
        FROM transactions t
        JOIN targets tr ON t.target_code = tr.code
        WHERE trade_date <= ?
        GROUP BY target_code, name, market
        HAVING quantity > 0
        """
        cur = self.db.conn.execute(sql, (date,))
        positions = [dict(row) for row in cur.fetchall()]

        # 获取最新价格
        for pos in positions:
            latest_price = self.get_latest_price(pos['target_code'])
            pos['latest_price'] = latest_price
            pos['market_value'] = pos['quantity'] * latest_price if latest_price else 0

        return positions

    def get_latest_price(self, code: str) -> Optional[float]:
        """获取最新收盘价"""
        cur = self.db.conn.execute(
            "SELECT close FROM daily_klines WHERE target_code = ? ORDER BY trade_date DESC LIMIT 1",
            (code,)
        )
        row = cur.fetchone()
        return row['close'] if row else None

    def get_kline_data(self, code: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """获取K线数据"""
        sql = """
        SELECT * FROM daily_klines
        WHERE target_code = ?
        """
        params = [code]

        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY trade_date"

        df = pd.read_sql_query(sql, self.db.conn, params=params)
        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df

    def calculate_returns(self, code: str, period: int = 30) -> Dict:
        """计算指定期间的收益率"""
        df = self.get_kline_data(code)
        if len(df) < period:
            return {'error': f'数据不足，需要至少{period}天'}

        latest_close = df['close'].iloc[-1]
        past_close = df['close'].iloc[-period-1] if len(df) > period else df['close'].iloc[0]

        total_return = (latest_close - past_close) / past_close * 100

        # 计算涨跌天数
        df['daily_return'] = df['close'].pct_change() * 100
        up_days = len(df[df['daily_return'] > 0])
        down_days = len(df[df['daily_return'] < 0])
        total_days = len(df[df['daily_return'] != 0])

        return {
            'code': code,
            'period_days': period,
            'total_return': round(total_return, 2),
            'up_days': up_days,
            'down_days': down_days,
            'win_rate': round(up_days / total_days * 100, 2) if total_days > 0 else 0
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.futu_api:
            self.futu_api.disconnect()
        self.db.close()


def col_exists(row: pd.Series, col: str) -> bool:
    """检查列是否存在"""
    return col in row