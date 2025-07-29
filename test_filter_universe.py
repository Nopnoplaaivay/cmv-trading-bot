import pandas as pd
import numpy as np

def create_sample_data(num_stocks=1700):
    """
    Hàm này tạo ra dữ liệu mẫu để mô phỏng 1700 cổ phiếu trên 3 sàn.
    Trong thực tế, bạn sẽ thay thế hàm này bằng việc đọc dữ liệu từ file CSV, Excel,
    hoặc API từ các nhà cung cấp như FiinTrade, VNDirect...
    """
    tickers = [f"STK{i:04d}" for i in range(num_stocks)]
    exchanges = np.random.choice(['HSX', 'HNX', 'UPCOM'], num_stocks, p=[0.3, 0.3, 0.4])

    data = {
        'Ticker': tickers,
        'Exchange': exchanges,
        # Vốn hóa (tỷ VNĐ), phân phối log-normal để có nhiều mã nhỏ và ít mã lớn
        'MarketCap': np.random.lognormal(8, 1.5, num_stocks),
        # GTGD trung bình/phiên (tỷ VNĐ)
        'AvgDailyValue': np.random.lognormal(1.5, 2, num_stocks),
        # P/E có cả giá trị âm (lỗ) và dương
        'PE': np.random.uniform(-10, 50, num_stocks),
        'PB': np.random.uniform(0.5, 10, num_stocks),
        'ROE': np.random.uniform(-0.2, 0.4, num_stocks), # Dưới dạng số thập phân
        'DE': np.random.uniform(0.1, 5, num_stocks),
        'RevenueGrowth': np.random.uniform(-0.1, 0.5, num_stocks), # Dưới dạng số thập phân
        'EPSGrowth': np.random.uniform(-0.2, 0.6, num_stocks) # Dưới dạng số thập phân
    }
    df = pd.DataFrame(data)
    # Giả lập một số giá trị NaN (dữ liệu thiếu)
    for col in ['PE', 'PB', 'ROE', 'DE']:
        df.loc[df.sample(frac=0.1).index, col] = np.nan
    return df

def filter_layer_1_basic(df, min_market_cap=1000, min_avg_value=5, allowed_exchanges=['HSX', 'HNX']):
    """
    Lớp lọc 1: Lọc cơ bản về thanh khoản, vốn hóa và sàn giao dịch.
    """
    print("--- Bắt đầu Lớp lọc 1: Lọc Cơ bản ---")
    print(f"Số lượng cổ phiếu ban đầu: {len(df)}")

    # 1. Loại bỏ các mã có dữ liệu bị thiếu cho các chỉ số quan trọng
    initial_count = len(df)
    df = df.dropna(subset=['MarketCap', 'AvgDailyValue'])
    print(f"Loại bỏ {initial_count - len(df)} mã do thiếu dữ liệu MarketCap/AvgDailyValue.")

    # 2. Lọc theo vốn hóa
    df = df[df['MarketCap'] >= min_market_cap]
    print(f"Số lượng cổ phiếu còn lại sau khi lọc Vốn hóa (> {min_market_cap} tỷ): {len(df)}")

    # 3. Lọc theo giá trị giao dịch
    df = df[df['AvgDailyValue'] >= min_avg_value]
    print(f"Số lượng cổ phiếu còn lại sau khi lọc GTGD (> {min_avg_value} tỷ/phiên): {len(df)}")

    # 4. Lọc theo sàn
    df = df[df['Exchange'].isin(allowed_exchanges)]
    print(f"Số lượng cổ phiếu còn lại sau khi lọc Sàn ({', '.join(allowed_exchanges)}): {len(df)}")
    print("--- Kết thúc Lớp lọc 1 ---\n")
    return df

def filter_layer_2_quality(df, min_roe=0.15, max_de=1.5):
    """
    Lớp lọc 2: Lọc theo tiêu chí Chất lượng.
    """
    print("--- Bắt đầu Lớp lọc 2: Lọc Chất lượng ---")
    initial_count = len(df)

    # Loại bỏ các mã thiếu dữ liệu cho lớp lọc này
    df = df.dropna(subset=['ROE', 'DE'])
    print(f"Loại bỏ {initial_count - len(df)} mã do thiếu dữ liệu ROE/DE.")

    # Lọc theo ROE và D/E
    df = df[(df['ROE'] >= min_roe) & (df['DE'] <= max_de)]
    print(f"Số lượng cổ phiếu còn lại sau khi lọc (ROE >= {min_roe*100}%, D/E <= {max_de}): {len(df)}")
    print("--- Kết thúc Lớp lọc 2 ---\n")
    return df

def rank_and_select_universe(df, n=200, ranking_factors=None):
    """
    Lớp lọc 3: Xếp hạng các cổ phiếu còn lại và chọn ra N mã tốt nhất.
    """
    if ranking_factors is None:
        # Ví dụ về các yếu tố xếp hạng kết hợp Giá trị và Chất lượng
        ranking_factors = {
            'ROE': {'weight': 0.4, 'ascending': False},  # ROE càng cao càng tốt
            'PE': {'weight': 0.4, 'ascending': True},   # P/E càng thấp càng tốt
            'DE': {'weight': 0.2, 'ascending': True}    # D/E càng thấp càng tốt
        }

    print("--- Bắt đầu Lớp lọc 3: Xếp hạng & Lựa chọn ---")
    print(f"Số lượng cổ phiếu đầu vào để xếp hạng: {len(df)}")

    # Loại bỏ các mã thiếu dữ liệu cho các yếu tố xếp hạng
    df = df.dropna(subset=ranking_factors.keys())
    print(f"Số lượng cổ phiếu còn lại sau khi loại bỏ NaN: {len(df)}")

    df_ranked = df.copy()
    df_ranked['CompositeScore'] = 0

    # Tính hạng cho từng yếu tố và cộng vào điểm tổng hợp theo trọng số
    for factor, props in ranking_factors.items():
        rank_col_name = f"{factor}_Rank"
        df_ranked[rank_col_name] = df_ranked[factor].rank(ascending=props['ascending'], method='first')
        df_ranked['CompositeScore'] += df_ranked[rank_col_name] * props['weight']

    # Sắp xếp theo điểm tổng hợp (điểm thấp hơn là tốt hơn)
    df_ranked = df_ranked.sort_values(by='CompositeScore', ascending=True)

    # Chọn ra N cổ phiếu hàng đầu
    final_universe = df_ranked.head(n)

    print(f"Đã chọn ra {len(final_universe)} cổ phiếu cuối cùng.")
    print("--- Kết thúc Lớp lọc 3 ---\n")
    return final_universe


# --- CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":
    # 1. Tải hoặc tạo dữ liệu
    # Trong thực tế, bạn sẽ đọc dữ liệu từ một file hoặc API ở đây
    # all_stocks_df = pd.read_csv('path/to/your/financial_data.csv')
    all_stocks_df = create_sample_data(1700)
    print("Đã tạo dữ liệu mẫu thành công.")
    print(f"Tổng số cổ phiếu trên 3 sàn: {len(all_stocks_df)}\n")

    # 2. Áp dụng Lớp lọc 1: Cơ bản
    # Bạn có thể tùy chỉnh các ngưỡng ở đây
    filtered_df_layer1 = filter_layer_1_basic(
        df=all_stocks_df,
        min_market_cap=1000,
        min_avg_value=5,
        allowed_exchanges=['HSX', 'HNX', 'UPCOM'] # Lấy cả 3 sàn
    )

    # 3. Áp dụng Lớp lọc 2: Chiến lược (ví dụ: Chất lượng)
    # Bước này là tùy chọn. Nếu bạn muốn xếp hạng tất cả mã từ Lớp 1, hãy bỏ qua bước này.
    filtered_df_layer2 = filter_layer_2_quality(
        df=filtered_df_layer1,
        min_roe=0.15,
        max_de=1.5
    )

    # 4. Áp dụng Lớp lọc 3: Xếp hạng và chọn 200 mã
    # Bạn có thể định nghĩa các yếu tố và trọng số của riêng mình
    # Ví dụ: kết hợp Giá trị (P/E) và Chất lượng (ROE, D/E)
    my_ranking_factors = {
        'ROE': {'weight': 0.4, 'ascending': False},  # ROE cao -> hạng thấp -> tốt
        'PE':  {'weight': 0.4, 'ascending': True},   # P/E thấp -> hạng thấp -> tốt
        'DE':  {'weight': 0.2, 'ascending': True}    # D/E thấp -> hạng thấp -> tốt
    }

    # Đầu vào cho bước xếp hạng là kết quả từ Lớp lọc 2
    final_universe = rank_and_select_universe(
        df=filtered_df_layer2,
        n=200,
        ranking_factors=my_ranking_factors
    )

    # 5. Xem kết quả
    print("--- DANH MỤC 200 CỔ PHIẾU CUỐI CÙNG ---")
    print(f"Shape of the final universe: {final_universe.shape}")
    print("5 cổ phiếu có thứ hạng cao nhất:")
    print(final_universe[['Ticker', 'Exchange', 'MarketCap', 'PE', 'ROE', 'DE', 'CompositeScore']].head())