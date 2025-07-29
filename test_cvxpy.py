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

success_count = 0
fallback_count = 0

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

# Convert to numpy arrays
x_t = np.array(x_t)
entropy_t = np.array(entropy_t)
expected_return_t = np.array(expected_return_t)
portfolio_variance_t = np.array(portfolio_variance_t)
mu_t = np.array(mu_t)

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

print("DONE")