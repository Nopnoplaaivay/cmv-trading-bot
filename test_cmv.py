import time
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.ndimage import gaussian_filter1d
import cvxpy as cp

# Read the CSV file
file_path = 'adjusted_close_price_5y.csv'
df = pd.read_csv(file_path)


start_time = time.time()
pivoted_df = df.pivot(index='date', columns='ticker', values='closePriceAdjusted')
T = pivoted_df.shape[0]
n_assets = pivoted_df.shape[1]


# covariance_matrix = pivoted_df.cov()
# pct_change_df = pivoted_df.pct_change(fill_method=None).fillna(0)
# pct_change_df.columns = [f"{col}_pct_change" for col in pct_change_df.columns]
# expected_return_df = pct_change_df.ewm(span=20, adjust=False).mean()
# expected_return_df.columns = [f"{col}_expected_return" for col in expected_return_df.columns]
# result_df = pd.concat([pivoted_df, pct_change_df, expected_return_df], axis=1)
# elapsed_time = time.time() - start_time
# print(f"Pivoting and calculating percentage change took {elapsed_time:.5f} seconds")

days = 63
# calculate cov matrix every 63 days
x_t = []
mu_t = []
entropy_t = []
expected_return_t = []
portfolio_variance_t = []
for i in range(days - 1, T):
    window = pivoted_df.iloc[i - days + 1:i + 1, :]
    returns_df = window.pct_change(fill_method=None).fillna(0)
    expected_returns_df = returns_df.ewm(span=21, adjust=False).mean()
    Q = window.cov().values
    mu = expected_returns_df.mean().values
    lambda_ = 0.01

    A = np.linalg.pinv(Q)  # Sử dụng nghịch đảo Moore-Penrose để ổn định hơn
    B = np.sum(A)
    C = A @ mu
    C_sum = np.sum(C)

    nu = (2 * lambda_ * (C_sum - 1)) / B

    x = (1 / (2 * lambda_)) * A @ (mu - nu * np.ones(n_assets))

    # Đảm bảo trọng số không âm (điều kiện không bán khống)
    x = np.clip(x, 0, None)

    # Chuẩn hóa lại để tổng trọng số bằng 1
    x_sum = np.sum(x)
    if x_sum > 1e-12:
        x_CEMV = x / x_sum
        # Đảm bảo tổng chính xác bằng 1 bằng cách điều chỉnh phần tử lớn nhất
        x_CEMV = x_CEMV / np.sum(x_CEMV)

        # Kiểm tra và điều chỉnh nếu vẫn có sai số
        if np.sum(x_CEMV) != 1.0:
            # Tìm phần tử lớn nhất và điều chỉnh
            max_idx = np.argmax(x_CEMV)
            x_CEMV[max_idx] += 1.0 - np.sum(x_CEMV)
    else:
        # Nếu tất cả trọng số đều gần bằng 0, phân phối đều
        x_CEMV = np.ones(n_assets) / n_assets

    # Đảm bảo không có trọng số âm (do điều chỉnh)
    x_CEMV = np.clip(x_CEMV, 0, None)

    # Chuẩn hóa lần cuối để đảm bảo tổng = 1
    x_CEMV = x_CEMV / np.sum(x_CEMV)

    # Entropy
    eps = 1e-12
    p = x_CEMV / (np.sum(x_CEMV) + eps)
    p = np.clip(p, 1e-10, None)
    entropy = -np.sum(p * np.log(p + eps))
    entropy_t.append(entropy)

    x_t.append(x_CEMV)
    mu_t.append(mu)
    portfolio_variance_t.append(x_CEMV.T @ Q @ x_CEMV)
    expected_return_t.append(mu @ x_CEMV)


# Convert to numpy arrays
x_t = np.array(x_t)
entropy_t = np.array(entropy_t)
expected_return_t = np.array(expected_return_t)
portfolio_variance_t = np.array(portfolio_variance_t)
mu_t = np.array(mu_t)

final_sums = np.sum(x_t, axis=1)  # Sum across assets for each time step
if np.any(final_sums > 1):
    print("There exists a time step where the sum of x_t is greater than 1.")
    print(final_sums)
    print(final_sums[final_sums > 1])
    print("Debug")
else:
    print("The sum of x_t is less than or equal to 1 for all time steps.")

# === Plotting ===
# fig = plt.figure(figsize=(16, 10))
# gs = gridspec.GridSpec(3, 3, figure=fig)
#
# ax1 = fig.add_subplot(gs[0, 0:3])
# ax2 = fig.add_subplot(gs[1, 0:3])
# ax3 = fig.add_subplot(gs[2, 0])
# ax4 = fig.add_subplot(gs[2, 1])
# ax5 = fig.add_subplot(gs[2, 2])
#
# markers = ['o', 's', '^', 'D', 'x']
# # Ensure time_steps matches the number of rows in x_t
# time_steps = np.arange(x_t.shape[0])

# # Subplot 1: Portfolio Weights
# bottom = np.zeros(x_t.shape[0])
# for i in range(n_assets):
#     ax1.bar(time_steps, x_t[:, i], bottom=bottom, label=f"Asset {i+1}", alpha=0.6)
#     bottom += x_t[:, i]
#     smoothed = gaussian_filter1d(x_t[:, i], sigma=5)
#     ax1.plot(time_steps, smoothed, lw=2, linestyle='-', marker=markers[i], markersize=5)
#
# ax1.set_xlabel("Time")
# ax1.set_ylabel("Weight")
# ax1.legend(ncol=8, loc='lower left', bbox_to_anchor=(0, 1))
# ax1.grid(True)
#
#
# # Subplot 2: Expected Returns
# bar_width = 0.1
# for i in range(n_assets):
#     offset = (i - n_assets / 2) * bar_width
#     ax2.bar(time_steps + offset, mu_t[:, i], width=bar_width, label=f"Asset {i+1}", alpha=0.6)
#     smoothed = gaussian_filter1d(mu_t[:, i], sigma=5)
#     ax2.plot(time_steps, smoothed, lw=2, linestyle='-', marker=markers[i], markersize=5)
#
# ax2.set_xlabel("Time")
# ax2.set_ylabel("Expected Return")
# ax2.legend(ncol=2, loc='lower left')
# ax2.grid(True)
#
# # Subplot 3: Entropy
# ax3.plot(entropy_t, label="Entropy", color="darkgreen", marker='x', markersize=3)
# ax3.set_title("(A)", fontsize=12, weight='bold')
# ax3.set_xlabel("Time", fontsize=12, weight='bold')
# ax3.legend()
# ax3.grid(True)
#
# # Subplot 4: Return and Risk
# ax4.plot(expected_return_t, label="Expected Return", color="blue", marker='o', markersize=3)
# ax4.plot(portfolio_variance_t, label="Portfolio Variance", color="red", marker='x', markersize=3)
# ax4.set_title("(B)", fontsize=12, weight='bold')
# ax4.set_xlabel("Time", fontsize=12, weight='bold')
# ax4.legend()
# ax4.grid(True)
#
# # Subplot 5: Efficient Frontier
# sc = ax5.scatter(portfolio_variance_t, expected_return_t, c=range(T), cmap='coolwarm', alpha=0.8)
# fig.colorbar(sc, ax=ax5, label='Time Step')
# ax5.set_title("(C)", fontsize=12, weight='bold')
# ax5.set_xlabel("Portfolio Variance (Risk)", fontsize=12, weight='bold')
# ax5.set_ylabel("Expected Return", fontsize=12, weight='bold')
# ax5.grid(True)
#
# plt.tight_layout()
# plt.show()

print("DONE")


