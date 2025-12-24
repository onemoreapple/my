#!/usr/bin/env python3
"""
投资分析系统主程序
功能：数据更新、分析、导出等
"""

from datetime import datetime, timedelta
from src.analysis import InvestmentManager
from src.export import ExportManager
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="投资分析系统")
    parser.add_argument('--command', choices=['update', 'export', 'add'], required=True,
                       help='选择要执行的命令')
    parser.add_argument('--code', help='股票代码')
    parser.add_argument('--days', type=int, default=365, help='获取数据天数')
    parser.add_argument('--name', help='股票名称')

    args = parser.parse_args()

    with InvestmentManager() as manager:
        if args.command == 'add':
            # 添加关注标的
            if not args.code or not args.name:
                logger.error("添加标的需要提供 --code 和 --name 参数")
                return

            try:
                manager.add_target(args.code, args.name)
                logger.info(f"成功添加标的: {args.code} - {args.name}")
            except Exception as e:
                logger.error(f"添加失败: {str(e)}")

        elif args.command == 'update':
            # 更新K线数据
            if manager.connect_futu():
                if args.code:
                    # 更新单个标的
                    logger.info(f"正在更新 {args.code} 的K线数据...")
                    result = manager.update_target_klines(args.code, args.days)
                    if result['success']:
                        logger.info(result['message'])
                    else:
                        logger.error(result['message'])
                else:
                    # 更新所有标的
                    logger.info("正在批量更新所有标的...")
                    results = manager.update_all_targets_klines(args.days)
                    for r in results:
                        if r['success']:
                            logger.info(f"✅ {r['code']}: {r['message']}")
                        else:
                            logger.error(f"❌ {r['code']}: {r.get('message', 'Unknown error')}")
            else:
                logger.error("连接富途API失败")

        elif args.command == 'export':
            # 导出报表
            exporter = ExportManager()

            if args.code:
                # 导出特定标的的K线数据
                filename = exporter.export_kline_to_excel(
                    args.code,
                    start_date=(datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
                )
                logger.info(f"K线数据已导出到: {filename}")
            else:
                # 导出持仓和交易记录
                pos_file = exporter.export_positions_to_excel()
                trans_file = exporter.export_transactions_to_excel(
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                )
                logger.info(f"持仓数据已导出到: {pos_file}")
                logger.info(f"交易记录已导出到: {trans_file}")

if __name__ == "__main__":
    main()