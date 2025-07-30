from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import cvxpy as cp
from scipy.linalg import pinv


class PortfolioOptimizer:
    success_count = 0
    fallback_count = 0

    @classmethod
    def optimize(cls, df_portfolio: pd.DataFrame):
        returns_df = df_portfolio.pct_change(fill_method=None).fillna(0)
        expected_returns_df = returns_df.ewm(span=21, adjust=False).mean()
        Q = df_portfolio.cov().values
        mu = expected_returns_df.mean().values
        lambda_ = 0.01

        Q = np.nan_to_num(Q, nan=0.0, posinf=1e6, neginf=-1e6)
        mu = np.nan_to_num(mu, nan=0.0, posinf=1e6, neginf=-1e6)

        x_CEMV, cvxpy_success = cls.solve_portfolio_cvxpy(mu, Q, lambda_)

        if cvxpy_success:
            cls.success_count += 1
        else:
            x_CEMV = cls.solve_portfolio_analytical(mu, Q, lambda_)
            cls.fallback_count += 1

        x_CEMV = cls.normalize_weights_exact(x_CEMV)
        x_CEMV_neutralized = cls.neutralize_weights_exact(x_CEMV)

        return x_CEMV, x_CEMV_neutralized

    @classmethod
    def solve_portfolio_cvxpy(cls, mu, Q, lambda_):
        n_assets = len(mu)

        try:
            Q_psd = cls.make_psd(Q)
            x = cp.Variable(n_assets)
            objective = cp.Maximize(mu.T @ x - lambda_ * cp.quad_form(x, Q_psd))

            constraints = [cp.sum(x) == 1, x >= 0]

            prob = cp.Problem(objective, constraints)
            prob.solve(solver=cp.CLARABEL, verbose=False)

            if prob.status == cp.OPTIMAL and x.value is not None:
                weights = x.value
                weights = np.maximum(weights, 0)
                weights = weights / np.sum(weights)
                return weights, True
            else:
                return None, False

        except Exception as e:
            return None, False

    @classmethod
    def solve_portfolio_analytical(cls, mu, Q, lambda_):
        n_assets = len(mu)

        try:
            Q_reg = Q + np.eye(n_assets) * 1e-8

            A = pinv(Q_reg)
            B = np.sum(A)
            C = A @ mu
            C_sum = np.sum(C)

            if abs(B) < 1e-12:
                return np.ones(n_assets) / n_assets

            nu = (2 * lambda_ * (C_sum - 1)) / B
            x = (1 / (2 * lambda_)) * A @ (mu - nu * np.ones(n_assets))

            x = np.maximum(x, 0)
            x_sum = np.sum(x)

            if x_sum > 1e-12:
                return x / x_sum
            else:
                return np.ones(n_assets) / n_assets

        except Exception as e:
            return np.ones(n_assets) / n_assets

    @staticmethod
    def normalize_weights_exact(weights):
        weights = np.maximum(weights, 0)
        weights_sum = np.sum(weights)

        if weights_sum > 1e-15:
            weights = weights / weights_sum
            residual = 1.0 - np.sum(weights)
            if abs(residual) > 1e-15:
                max_idx = np.argmax(weights)
                weights[max_idx] += residual
        else:
            weights = np.ones(len(weights)) / len(weights)

        return weights

    @staticmethod
    def neutralize_weights_exact(weights):
        """
        Normalize weights to create market neutral portfolio:
        - Sum of weights = 0 (dollar neutral)
        - Weights in range [-1, 1]
        - Positive weights = Long positions
        - Negative weights = Short positions
        """
        n_assets = len(weights)

        # Convert to market neutral: subtract mean to make sum = 0
        mean_weight = np.mean(weights)
        market_neutral_weights = weights - mean_weight

        # Clip to [-1, 1] range
        clipped_weights = np.clip(market_neutral_weights, -1, 1)

        # Ensure exact sum = 0 by adjusting the weight with largest absolute value
        current_sum = np.sum(clipped_weights)
        if abs(current_sum) > 1e-15:
            # Find index with largest absolute weight to adjust
            max_abs_idx = np.argmax(np.abs(clipped_weights))
            clipped_weights[max_abs_idx] -= current_sum

            # If adjustment pushes outside [-1, 1], redistribute the excess
            if clipped_weights[max_abs_idx] > 1:
                excess = clipped_weights[max_abs_idx] - 1
                clipped_weights[max_abs_idx] = 1
                # Distribute excess to other positions
                other_indices = np.arange(n_assets) != max_abs_idx
                clipped_weights[other_indices] -= excess / (n_assets - 1)
            elif clipped_weights[max_abs_idx] < -1:
                excess = clipped_weights[max_abs_idx] + 1
                clipped_weights[max_abs_idx] = -1
                # Distribute excess to other positions
                other_indices = np.arange(n_assets) != max_abs_idx
                clipped_weights[other_indices] -= excess / (n_assets - 1)

        return clipped_weights

    @staticmethod
    def make_psd(matrix, min_eigenvalue=1e-8):
        try:
            eigenvals, eigenvecs = np.linalg.eigh(matrix)
            eigenvals = np.maximum(eigenvals, min_eigenvalue)
            return eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        except:
            return matrix + np.eye(matrix.shape[0]) * min_eigenvalue
