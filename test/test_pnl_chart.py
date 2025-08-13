import time
import pandas as pd
import numpy as np
import cvxpy as cp
from scipy.linalg import pinv, LinAlgError

import matplotlib

matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.ndimage import gaussian_filter1d


def make_psd(matrix, min_eigenvalue=1e-8):
    """
    Make a matrix positive semi-definite by adjusting eigenvalues
    """
    try:
        eigenvals, eigenvecs = np.linalg.eigh(matrix)
        eigenvals = np.maximum(eigenvals, min_eigenvalue)
        return eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
    except:
        # Fallback: add small diagonal
        return matrix + np.eye(matrix.shape[0]) * min_eigenvalue


def solve_portfolio_cvxpy(mu, Q, lambda_):
    """
    Solve portfolio optimization using CVXPY with robust handling
    """
    n_assets = len(mu)

    try:
        # Make Q positive semi-definite
        Q_psd = make_psd(Q)

        # Define optimization variable
        x = cp.Variable(n_assets)

        # Objective: maximize expected return - lambda * variance
        objective = cp.Maximize(mu.T @ x - lambda_ * cp.quad_form(x, Q_psd))

        # Constraints
        constraints = [
            cp.sum(x) == 1,  # Sum to 1
            x >= 0  # Long-only
        ]

        # Create and solve problem
        prob = cp.Problem(objective, constraints)
        prob.solve(solver=cp.CLARABEL, verbose=False)

        if prob.status == cp.OPTIMAL and x.value is not None:
            weights = x.value
            # Additional normalization to ensure exact sum = 1
            weights = np.maximum(weights, 0)  # Ensure non-negative
            weights = weights / np.sum(weights)  # Normalize
            return weights, True
        else:
            return None, False

    except Exception as e:
        return None, False


def solve_portfolio_analytical(mu, Q, lambda_):
    """
    Analytical solution with robust handling
    """
    n_assets = len(mu)

    try:
        # Make Q invertible
        Q_reg = Q + np.eye(n_assets) * 1e-8

        A = pinv(Q_reg)  # Use pseudo-inverse for stability
        B = np.sum(A)
        C = A @ mu
        C_sum = np.sum(C)

        if abs(B) < 1e-12:
            # If B is too small, use equal weights
            return np.ones(n_assets) / n_assets

        nu = (2 * lambda_ * (C_sum - 1)) / B
        x = (1 / (2 * lambda_)) * A @ (mu - nu * np.ones(n_assets))

        # Ensure non-negative and normalize
        x = np.maximum(x, 0)
        x_sum = np.sum(x)

        if x_sum > 1e-12:
            return x / x_sum
        else:
            return np.ones(n_assets) / n_assets

    except Exception as e:
        return np.ones(n_assets) / n_assets


def normalize_weights_exact(weights):
    """
    Ensure weights sum to exactly 1.0
    """
    weights = np.maximum(weights, 0)  # Ensure non-negative
    weights_sum = np.sum(weights)

    if weights_sum > 1e-15:
        weights = weights / weights_sum

        # Fix any remaining floating point error
        residual = 1.0 - np.sum(weights)
        if abs(residual) > 1e-15:
            # Add residual to the largest weight
            max_idx = np.argmax(weights)
            weights[max_idx] += residual
    else:
        weights = np.ones(len(weights)) / len(weights)

    return weights


# Read the CSV file
file_path = 'adjusted_close_price_5y.csv'
df = pd.read_csv(file_path)

# Portfolio parameters
BOOK_SIZE = 10_000_000  # 10 million USD

start_time = time.time()
pivoted_df = df.pivot(index='date', columns='ticker', values='closePriceAdjusted')
T = pivoted_df.shape[0]
n_assets = pivoted_df.shape[1]

days = 63
x_t = []
mu_t = []
entropy_t = []
expected_return_t = []
portfolio_variance_t = []
portfolio_values = []  # Track portfolio value over time
daily_returns = []  # Track daily returns
dates = []  # Track dates for plotting

success_count = 0
fallback_count = 0
current_portfolio_value = BOOK_SIZE  # Initialize portfolio value

# Store prices for PnL calculation
price_data = pivoted_df.values
dates_index = pivoted_df.index

for i in range(days - 1, T):
    window = pivoted_df.iloc[i - days + 1:i + 1, :]
    returns_df = window.pct_change(fill_method=None).fillna(0)
    expected_returns_df = returns_df.ewm(span=21, adjust=False).mean()
    Q = window.cov().values
    mu = expected_returns_df.mean().values
    lambda_ = 0.01

    # Replace any NaN or inf values
    Q = np.nan_to_num(Q, nan=0.0, posinf=1e6, neginf=-1e6)
    mu = np.nan_to_num(mu, nan=0.0, posinf=1e6, neginf=-1e6)

    # Try CVXPY first
    x_CEMV, cvxpy_success = solve_portfolio_cvxpy(mu, Q, lambda_)

    if cvxpy_success:
        success_count += 1
    else:
        # Use analytical method
        x_CEMV = solve_portfolio_analytical(mu, Q, lambda_)
        fallback_count += 1

    # Final normalization to ensure exact sum = 1
    x_CEMV = normalize_weights_exact(x_CEMV)

    # Calculate daily return if not the first period
    if i > days - 1:  # We have a previous day to compare
        # Get prices for current and previous day
        prev_prices = price_data[i - 1]
        curr_prices = price_data[i]

        # Calculate daily return based on previous weights
        prev_weights = x_t[-1] if len(x_t) > 0 else np.ones(n_assets) / n_assets

        # Calculate price returns
        price_returns = (curr_prices - prev_prices) / prev_prices
        price_returns = np.nan_to_num(price_returns, nan=0.0, posinf=0.0, neginf=0.0)

        # Portfolio return
        portfolio_return = np.sum(prev_weights * price_returns)
        daily_returns.append(portfolio_return)

        # Update portfolio value
        current_portfolio_value *= (1 + portfolio_return)
        portfolio_values.append(current_portfolio_value)
        dates.append(dates_index[i])
    else:
        # First period - no return to calculate
        portfolio_values.append(BOOK_SIZE)
        daily_returns.append(0.0)
        dates.append(dates_index[i])

    x_t.append(x_CEMV)
    mu_t.append(mu)

    # Entropy calculation
    eps = 1e-12
    p = x_CEMV + eps  # Add small epsilon to avoid log(0)
    entropy = -np.sum(p * np.log(p))
    entropy_t.append(entropy)

    portfolio_variance_t.append(x_CEMV.T @ Q @ x_CEMV)
    expected_return_t.append(mu @ x_CEMV)

print(f"CVXPY successful: {success_count}/{T - days + 1} times")
print(f"Analytical fallback: {fallback_count}/{T - days + 1} times")

# Calculate PnL metrics
total_pnl = portfolio_values[-1] - BOOK_SIZE
total_return = (portfolio_values[-1] / BOOK_SIZE - 1) * 100
annualized_return = ((portfolio_values[-1] / BOOK_SIZE) ** (252 / len(portfolio_values)) - 1) * 100
volatility = np.std(daily_returns) * np.sqrt(252) * 100
sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0
max_drawdown = np.max(
    (np.maximum.accumulate(portfolio_values) - portfolio_values) / np.maximum.accumulate(portfolio_values)) * 100

# Portfolio Performance Summary
print(f"\n=== Portfolio Performance (Book Size: ${BOOK_SIZE:,.0f}) ===")
print(f"Final Portfolio Value: ${portfolio_values[-1]:,.2f}")
print(f"Total PnL: ${total_pnl:,.2f}")
print(f"Total Return: {total_return:.2f}%")
print(f"Annualized Return: {annualized_return:.2f}%")
print(f"Annualized Volatility: {volatility:.2f}%")
print(f"Sharpe Ratio: {sharpe_ratio:.3f}")
print(f"Maximum Drawdown: {max_drawdown:.2f}%")

# Convert to numpy arrays
x_t = np.array(x_t)
entropy_t = np.array(entropy_t)
expected_return_t = np.array(expected_return_t)
portfolio_variance_t = np.array(portfolio_variance_t)
mu_t = np.array(mu_t)
portfolio_values = np.array(portfolio_values)
daily_returns = np.array(daily_returns)

# Calculate PnL metrics
total_pnl = portfolio_values[-1] - BOOK_SIZE
total_return = (portfolio_values[-1] / BOOK_SIZE - 1) * 100
annualized_return = ((portfolio_values[-1] / BOOK_SIZE) ** (252 / len(portfolio_values)) - 1) * 100
volatility = np.std(daily_returns) * np.sqrt(252) * 100
sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0
max_drawdown = np.max(
    (np.maximum.accumulate(portfolio_values) - portfolio_values) / np.maximum.accumulate(portfolio_values)) * 100

# Check weight sums
final_sums = np.sum(x_t, axis=1)

print(f"\n=== Weight Sum Analysis ===")
print(f"Number of time steps: {len(final_sums)}")
print(f"Min sum: {np.min(final_sums):.15f}")
print(f"Max sum: {np.max(final_sums):.15f}")
print(f"Mean sum: {np.mean(final_sums):.15f}")
print(f"Std dev: {np.std(final_sums):.2e}")

# Check for exact equality to 1.0
exact_ones = np.sum(final_sums == 1.0)
print(f"Exactly equal to 1.0: {exact_ones}/{len(final_sums)}")

# Check within tolerance
tolerance = 1e-12
deviations = np.abs(final_sums - 1.0)
max_deviation = np.max(deviations)
within_tolerance = np.sum(deviations <= tolerance)

print(f"Max deviation: {max_deviation:.2e}")
print(f"Within tolerance ({tolerance:.0e}): {within_tolerance}/{len(final_sums)}")

if max_deviation <= tolerance:
    print("✓ SUCCESS: All portfolio weights sum to 1 within tolerance!")
else:
    problematic = np.where(deviations > tolerance)[0]
    print(f"❌ {len(problematic)} time steps still have sum > 1 + tolerance")
    for idx in problematic[:5]:  # Show first 5
        print(f"  Step {idx}: sum = {final_sums[idx]:.15f}")

# Plot PnL Chart
plt.figure(figsize=(15, 10))

# Create subplots
gs = gridspec.GridSpec(3, 2, height_ratios=[2, 1, 1], hspace=0.3, wspace=0.3)

# 1. Portfolio Value Over Time
ax1 = plt.subplot(gs[0, :])
plt.plot(dates, portfolio_values, linewidth=2, color='blue', label='Portfolio Value')
plt.axhline(y=BOOK_SIZE, color='red', linestyle='--', alpha=0.7, label='Initial Value')
plt.title(f'Portfolio Value Over Time (Starting: ${BOOK_SIZE:,.0f})', fontsize=14, fontweight='bold')
plt.ylabel('Portfolio Value ($)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# Format y-axis to show values in millions
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x / 1e6:.1f}M'))

# 2. Daily Returns
ax2 = plt.subplot(gs[1, 0])
plt.plot(dates, np.array(daily_returns) * 100, linewidth=1, color='green', alpha=0.7)
plt.title('Daily Returns (%)', fontsize=12, fontweight='bold')
plt.ylabel('Return (%)', fontsize=10)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# 3. Rolling Sharpe Ratio (30-day window)
ax3 = plt.subplot(gs[1, 1])
window_size = 30
if len(daily_returns) > window_size:
    rolling_sharpe = []
    for i in range(window_size, len(daily_returns)):
        window_returns = daily_returns[i - window_size:i]
        if np.std(window_returns) > 0:
            sharpe = np.mean(window_returns) / np.std(window_returns) * np.sqrt(252)
        else:
            sharpe = 0
        rolling_sharpe.append(sharpe)

    plt.plot(dates[window_size:], rolling_sharpe, linewidth=1, color='orange')
    plt.title(f'{window_size}-Day Rolling Sharpe Ratio', fontsize=12, fontweight='bold')
    plt.ylabel('Sharpe Ratio', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

# 4. Drawdown
ax4 = plt.subplot(gs[2, :])
running_max = np.maximum.accumulate(portfolio_values)
drawdown = (running_max - portfolio_values) / running_max * 100
plt.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
plt.plot(dates, drawdown, linewidth=1, color='red')
plt.title('Portfolio Drawdown (%)', fontsize=12, fontweight='bold')
plt.ylabel('Drawdown (%)', fontsize=10)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

print("DONE")