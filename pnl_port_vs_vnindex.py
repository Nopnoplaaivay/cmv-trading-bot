import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

# Cấu hình trang
st.set_page_config(page_title="So sánh PnL Danh mục vs VN-Index", layout="wide")
st.title("So sánh Performance Danh mục đầu tư vs VN-Index")

# Function để tạo dữ liệu sample
@st.cache_data
def generate_sample_data():
    """
    Tạo dữ liệu sample cho demo
    """
    # Tạo date range cho 1 năm
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d for d in dates if d.weekday() < 5]  # Chỉ lấy ngày làm việc
    
    # Danh sách cổ phiếu sample
    stocks = ['VIC', 'VCB', 'HPG', 'VHM', 'GAS', 'CTG', 'BID', 'MSN', 'PLX', 'TCB']
    
    # Tạo giá ban đầu cho từng mã
    initial_prices = {
        'VIC': 45000, 'VCB': 85000, 'HPG': 25000, 'VHM': 55000, 'GAS': 75000,
        'CTG': 35000, 'BID': 40000, 'MSN': 120000, 'PLX': 45000, 'TCB': 25000
    }
    
    # Tạo trọng số ban đầu (random nhưng tổng = 1)
    initial_weights = np.random.dirichlet(np.ones(len(stocks)))
    weights_dict = dict(zip(stocks, initial_weights))
    
    # Tạo dữ liệu giá cổ phiếu với random walk
    stock_prices_data = []
    vnindex_data = []
    portfolio_weights_data = []
    
    # VN-Index ban đầu
    vnindex_price = 1200.0
    
    for i, date in enumerate(dates):
        date_str = date.strftime('%Y-%m-%d')
        
        # Tạo giá cổ phiếu với random walk
        for stock in stocks:
            if i == 0:
                price = initial_prices[stock]
            else:
                # Random walk với drift nhỏ
                change = np.random.normal(0.001, 0.02)  # drift 0.1%, volatility 2%
                price = stock_prices_data[-len(stocks)]['Price'] * (1 + change) if i > 0 else initial_prices[stock]
                price = max(price, initial_prices[stock] * 0.5)  # Không cho giá giảm quá 50%
            
            stock_prices_data.append({
                'Date': date_str,
                'Symbol': stock,
                'Price': round(price, 0)
            })
        
        # Tạo VN-Index với random walk
        if i == 0:
            vnindex_price = 1200.0
        else:
            change = np.random.normal(0.0005, 0.015)  # drift nhỏ hơn, volatility 1.5%
            vnindex_price = vnindex_price * (1 + change)
            vnindex_price = max(vnindex_price, 1000)  # Floor price
        
        vnindex_data.append({
            'Date': date_str,
            'VNIndex_Price': round(vnindex_price, 2)
        })
        
        # Tạo trọng số danh mục (thay đổi nhỏ theo thời gian)
        for stock in stocks:
            if i == 0:
                weight = weights_dict[stock]
            else:
                # Thay đổi trọng số nhỏ (rebalancing)
                if i % 30 == 0:  # Rebalance mỗi 30 ngày
                    noise = np.random.normal(0, 0.02)  # 2% volatility
                    weight = max(0.01, min(0.4, weights_dict[stock] + noise))
                    weights_dict[stock] = weight
                else:
                    weight = weights_dict[stock]
            
            portfolio_weights_data.append({
                'Date': date_str,
                'Symbol': stock,
                'Weight': round(weight, 4)
            })
        
        # Normalize weights để tổng = 1
        if i % 30 == 0 or i == 0:
            total_weight = sum(weights_dict.values())
            for stock in stocks:
                weights_dict[stock] = weights_dict[stock] / total_weight
    
    # Tạo DataFrames
    weights_df = pd.DataFrame(portfolio_weights_data)
    prices_df = pd.DataFrame(stock_prices_data)
    vnindex_df = pd.DataFrame(vnindex_data)
    
    return weights_df, prices_df, vnindex_df

def calculate_portfolio_value(weights_df, prices_df):
    """
    Tính giá trị danh mục theo thời gian
    """
    # Merge weights và prices
    portfolio_data = pd.merge(weights_df, prices_df, on=['Date', 'Symbol'], how='inner')
    
    # Tính giá trị từng mã theo ngày (giả sử đầu tư 1 tỷ VND)
    base_investment = 1000000000  # 1 tỷ VND
    portfolio_data['Value'] = portfolio_data['Weight'] * portfolio_data['Price'] * base_investment / portfolio_data['Price']
    portfolio_data['Investment_Value'] = portfolio_data['Weight'] * base_investment
    
    # Tổng giá trị danh mục theo ngày
    daily_portfolio = portfolio_data.groupby('Date').agg({
        'Investment_Value': 'sum',
        'Price': 'first'  # Lấy giá đầu tiên để tính
    }).reset_index()
    
    # Tính lại giá trị thực tế
    portfolio_data['Current_Value'] = (portfolio_data['Investment_Value'] / 
                                     portfolio_data.groupby('Date')['Investment_Value'].transform('first').iloc[0]) * portfolio_data['Price']
    
    portfolio_value = portfolio_data.groupby('Date')['Investment_Value'].sum().reset_index()
    portfolio_value.columns = ['Date', 'Portfolio_Value']
    
    return portfolio_value

def calculate_pnl(df, value_column, base_value=1000000000):
    """
    Tính PnL từ giá trị danh mục hoặc chỉ số
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    # Normalize về base value cho ngày đầu tiên
    first_value = df[value_column].iloc[0]
    df['Normalized_Value'] = (df[value_column] / first_value) * base_value
    
    # Tính PnL so với ngày đầu tiên
    df['PnL'] = df['Normalized_Value'] - base_value
    df['PnL_Percent'] = (df['Normalized_Value'] / base_value - 1) * 100
    
    return df

def create_comparison_chart(portfolio_pnl, vnindex_pnl):
    """
    Tạo biểu đồ so sánh PnL
    """
    fig = go.Figure()
    
    # Đường PnL danh mục
    fig.add_trace(go.Scatter(
        x=portfolio_pnl['Date'],
        y=portfolio_pnl['PnL_Percent'],
        mode='lines',
        name='Portfolio PnL (%)',
        line=dict(color='blue', width=2),
        hovertemplate='<b>Portfolio</b><br>Date: %{x}<br>PnL: %{y:.2f}%<extra></extra>'
    ))
    
    # Đường PnL VN-Index
    fig.add_trace(go.Scatter(
        x=vnindex_pnl['Date'],
        y=vnindex_pnl['PnL_Percent'],
        mode='lines',
        name='VN-Index PnL (%)',
        line=dict(color='red', width=2),
        hovertemplate='<b>VN-Index</b><br>Date: %{x}<br>PnL: %{y:.2f}%<extra></extra>'
    ))
    
    # Đường zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title="So sánh Performance: Portfolio vs VN-Index (2024)",
        xaxis_title="Thời gian",
        yaxis_title="PnL (%)",
        hovermode='x unified',
        legend=dict(x=0.02, y=0.98),
        height=600,
        showlegend=True
    )
    
    return fig

def calculate_metrics(pnl_data):
    """
    Tính các chỉ số thống kê
    """
    total_return = pnl_data['PnL_Percent'].iloc[-1]
    max_return = pnl_data['PnL_Percent'].max()
    min_return = pnl_data['PnL_Percent'].min()
    volatility = pnl_data['PnL_Percent'].std()
    
    # Tính max drawdown
    running_max = pnl_data['PnL_Percent'].expanding().max()
    drawdown = pnl_data['PnL_Percent'] - running_max
    max_drawdown = drawdown.min()
    
    # Sharpe ratio giả định (không có risk-free rate)
    sharpe_ratio = total_return / volatility if volatility > 0 else 0
    
    return {
        'Total Return (%)': round(total_return, 2),
        'Max Return (%)': round(max_return, 2),
        'Min Return (%)': round(min_return, 2),
        'Volatility (%)': round(volatility, 2),
        'Max Drawdown (%)': round(max_drawdown, 2),
        'Sharpe Ratio': round(sharpe_ratio, 2)
    }

def calculate_portfolio_turnover(weights_df):
    """
    Tính turnover ratio của danh mục
    """
    weights_pivot = weights_df.pivot(index='Date', columns='Symbol', values='Weight').fillna(0)
    weights_pivot = weights_pivot.sort_index()
    
    # Tính turnover cho mỗi ngày (tổng absolute weight changes)
    daily_turnover = []
    for i in range(1, len(weights_pivot)):
        prev_weights = weights_pivot.iloc[i-1]
        curr_weights = weights_pivot.iloc[i]
        turnover = np.sum(np.abs(curr_weights - prev_weights)) / 2  # Chia 2 vì mua/bán
        daily_turnover.append(turnover)
    
    # Annual turnover
    avg_daily_turnover = np.mean(daily_turnover) if daily_turnover else 0
    annual_turnover = avg_daily_turnover * 252  # 252 trading days
    
    return annual_turnover

def calculate_fitness_score(portfolio_metrics, benchmark_metrics):
    """
    Tính fitness score của danh mục so với benchmark
    Công thức: (Return - Benchmark Return) - Risk Penalty
    """
    portfolio_return = portfolio_metrics['Total Return (%)']
    benchmark_return = benchmark_metrics['Total Return (%)']
    
    portfolio_vol = portfolio_metrics['Volatility (%)']
    benchmark_vol = benchmark_metrics['Volatility (%)']
    
    portfolio_drawdown = abs(portfolio_metrics['Max Drawdown (%)'])
    benchmark_drawdown = abs(benchmark_metrics['Max Drawdown (%)'])
    
    # Excess return
    excess_return = portfolio_return - benchmark_return
    
    # Risk penalty (higher volatility and drawdown = lower score)
    vol_penalty = (portfolio_vol - benchmark_vol) * 0.5
    drawdown_penalty = (portfolio_drawdown - benchmark_drawdown) * 0.3
    
    # Final fitness score
    fitness_score = excess_return - vol_penalty - drawdown_penalty
    
    return round(fitness_score, 2)

def calculate_advanced_metrics(pnl_data, weights_df=None, is_portfolio=False):
    """
    Tính các chỉ số thống kê nâng cao
    """
    # Basic metrics
    total_return = pnl_data['PnL_Percent'].iloc[-1]
    max_return = pnl_data['PnL_Percent'].max()
    min_return = pnl_data['PnL_Percent'].min()
    
    # Daily returns
    pnl_data = pnl_data.sort_values('Date')
    daily_returns = pnl_data['PnL_Percent'].pct_change().dropna()
    
    # Volatility (annualized)
    daily_vol = daily_returns.std()
    annualized_vol = daily_vol * np.sqrt(252)
    
    # Sharpe ratio (assuming risk-free rate = 5% annually)
    risk_free_rate = 5.0  # 5% annual
    daily_rf_rate = risk_free_rate / 252
    excess_returns = daily_returns - daily_rf_rate
    sharpe_ratio = (excess_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
    
    # Max Drawdown calculation
    cumulative_returns = (1 + pnl_data['PnL_Percent'] / 100).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Drawdown duration
    is_drawdown = drawdown < -0.01  # More than 0.01% drawdown
    drawdown_periods = []
    current_dd_length = 0
    
    for dd in is_drawdown:
        if dd:
            current_dd_length += 1
        else:
            if current_dd_length > 0:
                drawdown_periods.append(current_dd_length)
            current_dd_length = 0
    
    avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0
    max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
    
    # Calmar Ratio (Annual Return / Max Drawdown)
    annual_return = total_return
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Sortino Ratio (downside deviation)
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)
    sortino_ratio = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0
    
    # Win Rate
    win_rate = (daily_returns > 0).mean() * 100
    
    # VaR and CVaR (95% confidence)
    var_95 = np.percentile(daily_returns, 5)
    cvar_95 = daily_returns[daily_returns <= var_95].mean()
    
    metrics = {
        'Total Return (%)': round(total_return, 2),
        'Annualized Volatility (%)': round(annualized_vol, 2),
        'Sharpe Ratio': round(sharpe_ratio, 2),
        'Sortino Ratio': round(sortino_ratio, 2),
        'Calmar Ratio': round(calmar_ratio, 2),
        'Max Drawdown (%)': round(max_drawdown, 2),
        'Avg DD Duration (days)': round(avg_drawdown_duration, 0),
        'Max DD Duration (days)': round(max_drawdown_duration, 0),
        'Win Rate (%)': round(win_rate, 2),
        'VaR 95% (daily)': round(var_95, 4),
        'CVaR 95% (daily)': round(cvar_95, 4)
    }
    
    # Add turnover ratio for portfolio
    if is_portfolio and weights_df is not None:
        turnover_ratio = calculate_portfolio_turnover(weights_df)
        metrics['Annual Turnover (%)'] = round(turnover_ratio * 100, 2)
    
    return metrics

# Main App
st.markdown("### 🚀 Demo với Dữ liệu Sample")
st.info("Ứng dụng sử dụng dữ liệu sample được tạo tự động cho năm 2024 với 10 mã cổ phiếu phổ biến trên HOSE")

# Tạo dữ liệu sample
with st.spinner("Đang tạo dữ liệu sample..."):
    weights_df, prices_df, vnindex_df = generate_sample_data()

st.success("✅ Đã tạo thành công dữ liệu sample!")

# Hiển thị thông tin về dữ liệu
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Số ngày giao dịch", len(vnindex_df))
with col2:
    st.metric("Số mã cổ phiếu", len(weights_df['Symbol'].unique()))
with col3:
    st.metric("Khoảng thời gian", "01/2024 - 12/2024")

# Tab layout
tab1, tab2, tab3, tab4 = st.tabs(["📈 So sánh PnL", "📊 Data Preview", "📋 Thống kê", "💾 Download"])

with tab1:
    # Tính toán PnL
    with st.spinner("Đang tính toán PnL..."):
        # Tính giá trị danh mục
        portfolio_value = calculate_portfolio_value(weights_df, prices_df)
        
        # Tính PnL cho danh mục
        portfolio_pnl = calculate_pnl(portfolio_value, 'Portfolio_Value')
        
        # Tính PnL cho VN-Index
        vnindex_pnl = calculate_pnl(vnindex_df, 'VNIndex_Price', base_value=1000000000)
    
    # Hiển thị biểu đồ
    chart = create_comparison_chart(portfolio_pnl, vnindex_pnl)
    st.plotly_chart(chart, use_container_width=True)
    
    # Performance summary
    st.subheader("📊 Tóm tắt Performance")
    
    portfolio_final_pnl = portfolio_pnl['PnL_Percent'].iloc[-1]
    vnindex_final_pnl = vnindex_pnl['PnL_Percent'].iloc[-1]
    outperformance = portfolio_final_pnl - vnindex_final_pnl
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Portfolio Return", f"{portfolio_final_pnl:.2f}%")
    with col2:
        st.metric("VN-Index Return", f"{vnindex_final_pnl:.2f}%")
    with col3:
        st.metric("Outperformance", f"{outperformance:.2f}%", 
                 delta=f"{outperformance:.2f}%")

with tab2:
    # Preview dữ liệu
    st.subheader("👀 Preview Dữ liệu Sample")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Trọng số Danh mục (5 ngày đầu tiên)**")
        preview_weights = weights_df[weights_df['Date'].isin(weights_df['Date'].unique()[:5])]
        st.dataframe(preview_weights, use_container_width=True)
        
        st.write("**Giá Cổ phiếu (5 ngày đầu tiên)**")
        preview_prices = prices_df[prices_df['Date'].isin(prices_df['Date'].unique()[:5])]
        st.dataframe(preview_prices, use_container_width=True)
    
    with col2:
        st.write("**VN-Index (10 ngày đầu tiên)**")
        st.dataframe(vnindex_df.head(10), use_container_width=True)
        
        st.write("**Thống kê cơ bản**")
        stats_df = pd.DataFrame({
            'Metric': ['Tổng số record', 'Ngày bắt đầu', 'Ngày kết thúc', 'Avg daily volume'],
            'Weights': [len(weights_df), weights_df['Date'].min(), weights_df['Date'].max(), len(weights_df)//252],
            'Prices': [len(prices_df), prices_df['Date'].min(), prices_df['Date'].max(), len(prices_df)//252],
            'VN-Index': [len(vnindex_df), vnindex_df['Date'].min(), vnindex_df['Date'].max(), 1]
        })
        st.dataframe(stats_df, use_container_width=True)

with tab3:
    # Thống kê chi tiết
    st.subheader("📈 Phân tích Chi tiết Performance")
    
    # Tính metrics
    portfolio_metrics = calculate_metrics(portfolio_pnl)
    vnindex_metrics = calculate_metrics(vnindex_pnl)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Portfolio Metrics**")
        for metric, value in portfolio_metrics.items():
            if 'Ratio' in metric:
                st.metric(metric, f"{value}")
            else:
                st.metric(metric, f"{value}%")
    
    with col2:
        st.write("**📊 VN-Index Metrics**")
        for metric, value in vnindex_metrics.items():
            if 'Ratio' in metric:
                st.metric(metric, f"{value}")
            else:
                st.metric(metric, f"{value}%")
    
    # Bảng so sánh
    st.subheader("🔍 Bảng So sánh Chi tiết")
    comparison_df = pd.DataFrame({
        'Metric': list(portfolio_metrics.keys()),
        'Portfolio': [f"{v}%" if 'Ratio' not in k else f"{v}" for k, v in portfolio_metrics.items()],
        'VN-Index': [f"{v}%" if 'Ratio' not in k else f"{v}" for k, v in vnindex_metrics.items()],
        'Difference': [f"{portfolio_metrics[k] - vnindex_metrics[k]:.2f}%" if 'Ratio' not in k 
                      else f"{portfolio_metrics[k] - vnindex_metrics[k]:.2f}" 
                      for k in portfolio_metrics.keys()]
    })
    st.dataframe(comparison_df, use_container_width=True)

with tab4:
    # Download options
    st.subheader("💾 Download Dữ liệu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📁 Dữ liệu PnL**")
        portfolio_csv = portfolio_pnl.to_csv(index=False)
        st.download_button(
            label="📥 Download Portfolio PnL",
            data=portfolio_csv,
            file_name="portfolio_pnl_sample.csv",
            mime="text/csv"
        )
        
        vnindex_csv = vnindex_pnl.to_csv(index=False)
        st.download_button(
            label="📥 Download VN-Index PnL",
            data=vnindex_csv,
            file_name="vnindex_pnl_sample.csv",
            mime="text/csv"
        )
    
    with col2:
        st.write("**📁 Dữ liệu Sample Raw**")
        weights_csv = weights_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Weights Data",
            data=weights_csv,
            file_name="portfolio_weights_sample.csv",
            mime="text/csv"
        )
        
        prices_csv = prices_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Prices Data",
            data=prices_csv,
            file_name="stock_prices_sample.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")
st.markdown("""
**📝 Lưu ý về dữ liệu sample:**
- Dữ liệu được tạo bằng thuật toán random walk với các tham số thực tế
- 10 mã cổ phiếu: VIC, VCB, HPG, VHM, GAS, CTG, BID, MSN, PLX, TCB
- Trọng số danh mục được rebalance mỗi 30 ngày
- Giả định đầu tư ban đầu: 1 tỷ VND
- Dữ liệu chỉ để demo, không phản ánh thực tế thị trường
""")

# Sidebar info
st.sidebar.markdown("### ℹ️ Thông tin App")
st.sidebar.info("""
**Tính năng:**
- ✅ Tạo dữ liệu sample tự động
- ✅ Tính toán PnL real-time  
- ✅ So sánh với VN-Index
- ✅ Thống kê chi tiết
- ✅ Export CSV results
- ✅ Interactive charts
""")

st.sidebar.markdown("### 🔄 Refresh Data")
if st.sidebar.button("🔄 Tạo lại dữ liệu sample"):
    st.cache_data.clear()
    st.rerun()