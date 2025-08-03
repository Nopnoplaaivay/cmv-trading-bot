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
        returns_df = df_portfolio.pct_change(periods=2).fillna(0)
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
        x_CEMV_limited = cls.normalize_weights_limit(x_CEMV, max_weight=0.15)
        x_CEMV_neutralized_limit = cls.neutralize_weights_limit(x_CEMV_limited, max_weight=0.15)

        return x_CEMV, x_CEMV_neutralized, x_CEMV_limited, x_CEMV_neutralized_limit

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
    def normalize_weights_limit(weights, max_weight=0.15):
        weights = np.maximum(weights, 0)

        # Apply max weight constraint iteratively
        max_iterations = 100
        tolerance = 1e-10

        for iteration in range(max_iterations):
            # Normalize to sum = 1
            weights_sum = np.sum(weights)
            if weights_sum > 1e-15:
                weights = weights / weights_sum
            else:
                weights = np.ones(len(weights)) / len(weights)
                break

            # Check if any weight exceeds max_weight
            over_limit_mask = weights > max_weight

            if not np.any(over_limit_mask):
                break  # All weights are within limit

            # Calculate excess weight to redistribute
            excess_weight = np.sum(weights[over_limit_mask] - max_weight)

            # Cap weights at max_weight
            weights[over_limit_mask] = max_weight

            # Redistribute excess to remaining assets
            remaining_mask = ~over_limit_mask
            n_remaining = np.sum(remaining_mask)

            if n_remaining > 0:
                # Calculate available capacity for remaining assets
                remaining_weights = weights[remaining_mask]
                available_capacity = np.maximum(0, max_weight - remaining_weights)
                total_capacity = np.sum(available_capacity)

                if total_capacity > tolerance:
                    # Redistribute proportionally to available capacity
                    redistribution = excess_weight * (
                        available_capacity / total_capacity
                    )
                    weights[remaining_mask] += redistribution
                else:
                    # If no capacity, distribute equally among all remaining
                    weights[remaining_mask] += excess_weight / n_remaining
            else:
                # All assets are at max weight, can't redistribute
                break

        # Final normalization
        weights_sum = np.sum(weights)
        if weights_sum > 1e-15:
            weights = weights / weights_sum

            # Adjust for exact sum = 1
            residual = 1.0 - np.sum(weights)
            if abs(residual) > 1e-15:
                # Add residual to asset with most room (furthest from max_weight)
                room_available = max_weight - weights
                max_room_idx = np.argmax(room_available)
                weights[max_room_idx] += residual
        else:
            weights = np.ones(len(weights)) / len(weights)

        return weights

    @staticmethod
    def neutralize_weights_limit(weights, max_weight=0.15):
        n_assets = len(weights)
        max_iterations = 100
        tolerance = 1e-10

        # Convert to market neutral: subtract mean to make sum ≈ 0
        mean_weight = np.mean(weights)
        market_neutral_weights = weights - mean_weight

        for iteration in range(max_iterations):
            # Clip to [-max_weight, max_weight] range
            clipped_weights = np.clip(market_neutral_weights, -max_weight, max_weight)

            # Check if sum is close enough to zero
            current_sum = np.sum(clipped_weights)
            if abs(current_sum) <= tolerance:
                break

            # Find positions that are not at limits and can absorb the imbalance
            at_upper_limit = np.abs(clipped_weights - max_weight) < tolerance
            at_lower_limit = np.abs(clipped_weights + max_weight) < tolerance
            at_limit = at_upper_limit | at_lower_limit

            adjustable_mask = ~at_limit
            n_adjustable = np.sum(adjustable_mask)

            if n_adjustable == 0:
                # All positions are at limits, can't achieve perfect neutrality
                break

            # Calculate how much each adjustable position can absorb
            if current_sum > 0:  # Need to reduce sum (move towards negative)
                # Calculate available downward capacity
                available_capacity = clipped_weights[adjustable_mask] + max_weight
                available_capacity = np.maximum(0, available_capacity)
            else:  # Need to increase sum (move towards positive)
                # Calculate available upward capacity
                available_capacity = max_weight - clipped_weights[adjustable_mask]
                available_capacity = np.maximum(0, available_capacity)

            total_capacity = np.sum(available_capacity)

            if total_capacity > tolerance:
                # Distribute adjustment proportionally to available capacity
                adjustment_per_unit = min(abs(current_sum) / total_capacity, 1.0)
                if current_sum > 0:
                    adjustments = -available_capacity * adjustment_per_unit
                else:
                    adjustments = available_capacity * adjustment_per_unit

                clipped_weights[adjustable_mask] += adjustments
            else:
                # Distribute equally among adjustable positions
                adjustment_per_position = -current_sum / n_adjustable
                clipped_weights[adjustable_mask] += adjustment_per_position

            market_neutral_weights = clipped_weights

        # Final clipping and verification
        final_weights = np.clip(market_neutral_weights, -max_weight, max_weight)

        # If still not neutral enough, make a final adjustment to the position with most room
        final_sum = np.sum(final_weights)
        if abs(final_sum) > tolerance:
            # Find position with most room to absorb the remaining imbalance
            if final_sum > 0:
                # Need to reduce sum - find position furthest from lower limit
                room_to_decrease = final_weights + max_weight
                max_room_idx = np.argmax(room_to_decrease)
                adjustment = min(final_sum, room_to_decrease[max_room_idx])
                final_weights[max_room_idx] -= adjustment
            else:
                # Need to increase sum - find position furthest from upper limit
                room_to_increase = max_weight - final_weights
                max_room_idx = np.argmax(room_to_increase)
                adjustment = min(-final_sum, room_to_increase[max_room_idx])
                final_weights[max_room_idx] += adjustment

        return final_weights




    @staticmethod
    def make_psd(matrix, min_eigenvalue=1e-8):
        try:
            eigenvals, eigenvecs = np.linalg.eigh(matrix)
            eigenvals = np.maximum(eigenvals, min_eigenvalue)
            return eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        except:
            return matrix + np.eye(matrix.shape[0]) * min_eigenvalue
