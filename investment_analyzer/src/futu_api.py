from futu import *
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

class FutuAPIWrapper:
    def __init__(self):
        """初始化富途API连接"""
        self.quote_ctx = None
        self.trade_ctx = None
        self.is_connected = False

    def connect(self, host='127.0.0.1', port=11111, market='HK'):
        """连接富途开放平台"""
        try:
            # 初始化行情上下文
            self.quote_ctx = OpenQuoteContext(host=host, port=port)

            # 测试连接
            ret, data = self.quote_ctx.get_market_state([market])
            if ret == RET_OK:
                self.is_connected = True
                logging.info(f"成功连接到富途开放平台，{market}市场状态：{data.iloc[0]['market_state']}")
                return True
            else:
                logging.error(f"连接失败: {data}")
                return False

        except Exception as e:
            logging.error(f"连接富途API时发生错误: {str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.is_connected = False
        logging.info("已断开富途API连接")

    def get_stock_basic_info(self, code_list: List[str]) -> List[Dict]:
        """获取股票基础信息"""
        if not self.is_connected:
            raise ConnectionError("未连接到富途API")

        ret, data = self.quote_ctx.get_stock_basicinfo(Market.HK, SECURITY_TYPE_ALL)
        if ret == RET_OK:
            return data.to_dict('records')
        else:
            logging.error(f"获取基础信息失败: {data}")
            return []

    def get_market_config(self, code: str) -> Dict:
        """获取标的的市场配置信息（用于判断市场）"""
        # 根据代码前缀判断市场
        if code.startswith(('HK.', hk_code_pattern := '^0[0-9]{4}')):
            return {'market': Market.HK, 'currency': 'HKD'}
        elif code.startswith(('US.', us_code_pattern := '^[A-Z]+')):
            return {'market': Market.US, 'currency': 'USD'}
        elif code.startswith(('SH.', sh_code_pattern := '^6[0-9]{5}')):
            return {'market': Market.SH, 'currency': 'CNY'}
        elif code.startswith(('SZ.', sz_code_pattern := '^[0-3][0-9]{5}')):
            return {'market': Market.SZ, 'currency': 'CNY'}
        else:
            raise ValueError(f"无法识别股票代码格式: {code}")

    def get_kline_data(self, code: str, start_date: str, end_date: str, ktype=KLType.K_DAY) -> pd.DataFrame:
        """获取K线数据

        Args:
            code: 股票代码，格式如 'HK.00700', 'US.AAPL', 'SZ.000001'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            ktype: K线类型，默认日线

        Returns:
            DataFrame: 包含OHLCV等信息的K线数据
        """
        if not self.is_connected:
            raise ConnectionError("未连接到富途API")

        # 获取市场配置
        market_config = self.get_market_config(code)
        market = market_config['market']

        # 获取K线数据
        ret, data = self.quote_ctx.get_history_kline(
            code=code,
            start=start_date,
            end=end_date,
            ktype=ktype,
            autype=AuType.Qfq  # 默认前复权
        )

        if ret == RET_OK:
            # 添加货币信息
            data['currency'] = market_config['currency']
            return data
        else:
            logging.error(f"获取K线数据失败 [{code}]: {data}")
            return pd.DataFrame()

    def batch_get_quotes(self, code_list: List[str]) -> pd.DataFrame:
        """批量获取实时行情"""
        if not self.is_connected:
            raise ConnectionError("未连接到富途API")

        ret, data = self.quote_ctx.get_market_snapshot(code_list)
        if ret == RET_OK:
            return data
        else:
            logging.error(f"批量获取行情失败: {data}")
            return pd.DataFrame()

    def search_stocks(self, keyword: str, market: str = 'ALL') -> pd.DataFrame:
        """搜索股票"""
        if not self.is_connected:
            raise ConnectionError("未连接到富途API")

        # 根据市场参数选择
        market_map = {
            'HK': Market.HK,
            'US': Market.US,
            'SH': Market.SH,
            'SZ': Market.SZ,
            'ALL': Market.ALL
        }

        ret, data = self.quote_ctx.get_stock_basicinfo(
            market=market_map.get(market, Market.ALL),
            stock_type=[StockType.STOCK, StockType.ETF]
        )

        if ret == RET_OK:
            # 简单筛选
            if keyword:
                mask = data['code'].str.contains(keyword, case=False) | \
                       data['name'].str.contains(keyword, case=False)
                return data[mask]
            return data
        else:
            logging.error(f"搜索股票失败: {data}")
            return pd.DataFrame()

    def update_daily_klines(self, code: str, days_back: int = 365) -> Dict:
        """更新日线数据

        Args:
            code: 股票代码
            days_back: 向前获取的天数

        Returns:
            Dict: 包含更新结果信息
        """
        try:
            # 计算日期范围
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            # 获取数据
            data = self.get_kline_data(code, start_date, end_date)

            if data.empty:
                return {'success': False, 'message': '未获取到数据'}

            return {
                'success': True,
                'data': data,
                'start_date': start_date,
                'end_date': end_date,
                'count': len(data)
            }

        except Exception as e:
            logging.error(f"更新日线数据时发生错误: {str(e)}")
            return {'success': False, 'message': str(e)}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()