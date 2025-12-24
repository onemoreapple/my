import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.analysis import InvestmentManager
import os

# 配置页面
st.set_page_config(
    page_title="投资分析系统",
    page_icon="📈",
    layout="wide"
)

# 初始化session state
def init_session():
    if 'manager' not in st.session_state:
        st.session_state.manager = InvestmentManager()
    if 'connected' not in st.session_state:
        st.session_state.connected = False

def main():
    init_session()
    st.title("📈 投资分析系统")

    # 侧边栏
    with st.sidebar:
        st.header("系统设置")

        # 连接富途API
        if st.button("连接富途API"):
            if st.session_state.manager.connect_futu():
                st.session_state.connected = True
                st.success("连接成功！")
            else:
                st.error("连接失败，请确保FutuOpenD正在运行")

        if st.session_state.connected:
            st.success("✅ 已连接")

        st.divider()

        # 功能导航
        page = st.selectbox(
            "选择功能",
            ["管理标的", "更新数据", "查看行情", "交易记录", "持仓分析"]
        )

    # 主内容区
    if page == "管理标的":
        show_targets_management()
    elif page == "更新数据":
        show_data_update()
    elif page == "查看行情":
        show_market_quote()
    elif page == "交易记录":
        show_transaction_history()
    elif page == "持仓分析":
        show_portfolio_analysis()

def show_targets_management():
    """管理关注的标的"""
    st.header("🎯 管理关注的标的")

    # 添加新标的
    with st.expander("添加新标的"):
        col1, col2, col3 = st.columns(3)

        with col1:
            code = st.text_input("标的代码", help="如: HK.00700, US.AAPL, SZ.000001")
        with col2:
            name = st.text_input("标的名称")
        with col3:
            asset_type = st.selectbox("类型", ["STOCK", "ETF", "INDEX"])

        if st.button("添加标的"):
            if code and name:
                try:
                    st.session_state.manager.add_target(code, name, asset_type=asset_type)
                    st.success(f"成功添加: {code} - {name}")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"添加失败: {str(e)}")

    # 显示已关注的标的
    targets = st.session_state.manager.get_active_targets()

    if targets:
        st.subheader("已关注的标的")
        target_df = pd.DataFrame(targets)

        # 添加操作按钮
        selected_target = st.dataframe(target_df[['code', 'name', 'market', 'type', 'industry']],
                                      use_container_width=True)
    else:
        st.info("暂无关注的标的")

def show_data_update():
    """数据更新"""
    st.header("🔄 数据更新")

    if not st.session_state.connected:
        st.warning("请先连接富途API")
        return

    # 更新特定标的
    targets = st.session_state.manager.get_active_targets()
    if not targets:
        st.info("请先添加关注的标的")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_code = st.selectbox("选择标的", [t['code'] for t in targets],
                                    format_func=lambda x: f"{x} - {next(t['name'] for t in targets if t['code'] == x)}")

    with col2:
        days_back = st.number_input("获取天数", value=365, min_value=30, max_value=1000)

    if st.button(f"更新 {selected_code} 的K线数据"):
        with st.spinner("正在更新数据..."):
            result = st.session_state.manager.update_target_klines(selected_code, days_back)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])

    # 批量更新
    st.divider()
    st.subheader("批量更新所有标的")

    if st.button("⚠️ 更新所有标的的K线数据（可能需要较长时间）"):
        with st.spinner("正在批量更新..."):
            results = st.session_state.manager.update_all_targets_klines(days_back)

            # 显示结果汇总
            success_count = sum(1 for r in results if r['success'])
            total_count = len(results)

            st.metric("更新成功", f"{success_count}/{total_count}")

            # 显示详细结果
            with st.expander("查看详细结果"):
                for result in results:
                    if result['success']:
                        st.success(f"✅ {result['code']}: {result['message']}")
                    else:
                        st.error(f"❌ {result['code']}: {result['message']}")

def show_market_quote():
    """查看行情"""
    st.header("📊 查看行情")

    targets = st.session_state.manager.get_active_targets()
    if not targets:
        st.info("请先添加关注的标的")
        return

    # 选择标的
    selected_code = st.selectbox("选择标的", [t['code'] for t in targets],
                                format_func=lambda x: f"{x} - {next(t['name'] for t in targets if t['code'] == x)}")

    # 获取K线数据
    df = st.session_state.manager.get_kline_data(selected_code)

    if not df.empty:
        # 显示基本信息
        target = next(t for t in targets if t['code'] == selected_code)
        col1, col2, col3 = st.columns(3)

        with col1:
            latest_price = df['close'].iloc[-1]
            st.metric("最新价", f"{latest_price:.2f}")

        with col2:
            price_change = df['close'].iloc[-1] - df['close'].iloc[-2]
            price_change_pct = price_change / df['close'].iloc[-2] * 100
            st.metric("涨跌", f"{price_change:.2f} ({price_change_pct:.2f}%)")

        with col3:
            volume = df['volume'].iloc[-1]
            st.metric("成交量", f"{volume:,}")

        # K线图
        st.subheader("K线图")

        fig = go.Figure(data=go.Candlestick(
            x=df['trade_date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="K线"
        ))

        fig.update_layout(
            title=f"{target['name']} ({selected_code})",
            yaxis_title="价格",
            xaxis_title="日期",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # 收益率分析
        st.subheader("收益率分析")
        col1, col2, col3 = st.columns(3)

        with col1:
            returns_30d = st.session_state.manager.calculate_returns(selected_code, 30)
            if 'total_return' in returns_30d:
                st.metric("30日收益率", f"{returns_30d['total_return']:.2f}%")

        with col2:
            returns_90d = st.session_state.manager.calculate_returns(selected_code, 90)
            if 'total_return' in returns_90d:
                st.metric("90日收益率", f"{returns_90d['total_return']:.2f}%")

        with col3:
            returns_1y = st.session_state.manager.calculate_returns(selected_code, 365)
            if 'total_return' in returns_1y:
                st.metric("1年收益率", f"{returns_1y['total_return']:.2f}%")

    else:
        st.warning("暂无数据，请先更新")

def show_transaction_history():
    """交易记录"""
    st.header("📋 交易记录")

    # 筛选条件
    col1, col2, col3 = st.columns(3)

    with col1:
        targets = st.session_state.manager.get_active_targets()
        codes = ['全部'] + [t['code'] for t in targets]
        selected_code = st.selectbox("选择标的", codes)

    with col2:
        start_date = st.date_input("开始日期", datetime.now() - timedelta(days=365))

    with col3:
        end_date = st.date_input("结束日期", datetime.now())

    # 获取交易记录
    transactions = st.session_state.manager.get_transactions(
        code=selected_code if selected_code != '全部' else None,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

    if transactions:
        # 转换为DataFrame
        df = pd.DataFrame(transactions)

        # 添加买入/卖出颜色标记
        def highlight_direction(val):
            color = 'lightcoral' if val == 'SELL' else 'lightgreen'
            return f'background-color: {color}'

        styled_df = df.style.applymap(highlight_direction, subset=['direction'])

        st.dataframe(styled_df[['trade_date', 'target_code', 'name', 'direction',
                                'quantity', 'price', 'commission', 'currency']],
                    use_container_width=True)

        # 统计信息
        st.divider()
        st.subheader("统计信息")

        col1, col2 = st.columns(2)

        with col1:
            total_buy = df[df['direction'] == 'BUY']['price'].sum() * df[df['direction'] == 'BUY']['quantity'].sum()
            st.metric("总买入金额", f"{total_buy:,.2f} CNY")

        with col2:
            total_sell = df[df['direction'] == 'SELL']['price'].sum() * df[df['direction'] == 'SELL']['quantity'].sum()
            st.metric("总卖出金额", f"{total_sell:,.2f} CNY")

    else:
        st.info("暂无交易记录")

def show_portfolio_analysis():
    """持仓分析"""
    st.header("💼 持仓分析")

    # 获取当前持仓
    positions = st.session_state.manager.get_holding_positions()

    if positions:
        # 持仓汇总
        st.subheader("持仓汇总")

        df = pd.DataFrame(positions)
        df['profit_loss'] = (df['latest_price'] * df['quantity']) - (df['avg_cost'] * df['quantity'])
        df['profit_loss_pct'] = (df['profit_loss'] / (df['avg_cost'] * df['quantity'])) * 100

        # 应用颜色样式
        def style_profit(val):
            color = 'lightcoral' if val < 0 else 'lightgreen'
            return f'background-color: {color}'

        styled_df = df.style.applymap(style_profit, subset=['profit_loss', 'profit_loss_pct'])

        st.dataframe(styled_df[['name', 'code', 'quantity', 'avg_cost', 'latest_price',
                                'market_value', 'profit_loss','profit_loss_pct']],
                    use_container_width=True)

        # 持仓结构饼图
        st.subheader("持仓结构")

        fig = go.Figure(data=[go.Pie(
            labels=df['name'],
            values=df['market_value'],
            textinfo='label+percent',
            textposition='auto'
        )])

        st.plotly_chart(fig, use_container_width=True)

        # 盈亏分布
        col1, col2, col3 = st.columns(3)

        with col1:
            total_value = df['market_value'].sum()
            st.metric("总市值", f"{total_value:,.2f} CNY")

        with col2:
            total_profit = df['profit_loss'].sum()
            st.metric("总盈亏", f"{total_profit:,.2f} CNY")

        with col3:
            profit_rate = (total_profit / (total_value - total_profit)) * 100
            st.metric("总收益率", f"{profit_rate:.2f}%")

    else:
        st.info("暂无持仓")

if __name__ == "__main__":
    main()