import pandas as pd
from datetime import datetime
from analysis import InvestmentManager
import os

class ExportManager:
    def __init__(self, db_path: str = "data/investment.db"):
        self.manager = InvestmentManager(db_path)

    def export_positions_to_excel(self, filename: str = None) -> str:
        """导出持仓到Excel"""
        if not filename:
            filename = f"reports/positions_{datetime.now().strftime('%Y%m%d')}.xlsx"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        positions = self.manager.get_holding_positions()

        if positions:
            df = pd.DataFrame(positions)

            # 计算更多指标
            df['total_cost'] = df['avg_cost'] * df['quantity']
            df['market_value'] = df['latest_price'] * df['quantity']
            df['profit_loss'] = df['market_value'] - df['total_cost']
            df['profit_loss_pct'] = (df['profit_loss'] / df['total_cost']) * 100

            # 导出到Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='持仓明细', index=False)

                # 汇总数据
                summary = pd.DataFrame({
                    '指标': ['总市值', '总成本', '总盈亏', '盈亏比例(%)'],
                    '数值': [
                        df['market_value'].sum(),
                        df['total_cost'].sum(),
                        df['profit_loss'].sum(),
                        (df['profit_loss'].sum() / df['total_cost'].sum()) * 100
                    ]
                })
                summary.to_excel(writer, sheet_name='汇总', index=False)

        return filename

    def export_transactions_to_excel(self, start_date: str = None,
                                    end_date: str = None,
                                    filename: str = None) -> str:
        """导出交易记录到Excel"""
        if not filename:
            filename = f"reports/transactions_{datetime.now().strftime('%Y%m%d')}.xlsx"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        transactions = self.manager.get_transactions(start_date=start_date, end_date=end_date)

        if transactions:
            df = pd.DataFrame(transactions)

            # 添加金额列
            df['amount'] = df['quantity'] * df['price']

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='交易记录', index=False)

                # 按标的汇总
                if not df.empty:
                    summary_by_target = df.groupby('target_code').agg({
                        'quantity': 'sum',
                        'amount': 'sum',
                        'commission': 'sum'
                    }).reset_index()
                    summary_by_target['type'] = summary_by_target.apply(
                        lambda x: '买入' if x['quantity'] > 0 else '卖出',
                        axis=1
                    )
                    summary_by_target.to_excel(writer, sheet_name='按标的汇总', index=False)

        return filename

    def export_kline_to_excel(self, code: str, start_date: str = None,
                              end_date: str = None, filename: str = None) -> str:
        """导出K线数据到Excel"""
        if not filename:
            filename = f"reports/kline_{code}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        df = self.manager.get_kline_data(code, start_date, end_date)

        if not df.empty:
            # 添加技术指标
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            df['ma60'] = df['close'].rolling(60).mean()

            df.to_excel(filename, index=False)

        return filename