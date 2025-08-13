import pandas as pd
import numpy as np
from scipy import stats

from backend.utils.logger import LOGGER

LOGGER_PREFIX = "[RiskCalculator]"


class PortfolioRiskCalculator:
    def __init__(self, df_pnl):
        self.trading_days = 252
        self.risk_free_rate = 0
        self.df_pnl = df_pnl.iloc[-self.trading_days:].copy().reset_index(drop=True)
        self.daily_returns = df_pnl["pnl_pct"].pct_change(2).dropna()
        

    def calculate_basic_metrics(self):
        total_return = self.df_pnl["pnl_pct"].iloc[-1]
        max_return = self.df_pnl["pnl_pct"].max()
        min_return = self.df_pnl["pnl_pct"].min()

        return {
            "total_return_pct": round(total_return, 2),
            "max_return_pct": round(max_return, 2),
            "min_return_pct": round(min_return, 2),
        }

    def calculate_volatility_metrics(self):
        if len(self.daily_returns) < 2:
            return {
                "daily_volatility_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "downside_volatility_pct": 0.0,
            }

        daily_vol = self.daily_returns.std()

        # Handle NaN case
        if pd.isna(daily_vol) or np.isinf(daily_vol):
            daily_vol = 0.0

        annualized_vol = daily_vol * np.sqrt(self.trading_days)

        downside_returns = self.daily_returns[self.daily_returns < 0]
        downside_vol = 0.0
        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            if not pd.isna(downside_std) and not np.isinf(downside_std):
                downside_vol = downside_std * np.sqrt(self.trading_days)

        return {
            "daily_volatility_pct": round(daily_vol * 100, 2),
            "annualized_volatility_pct": round(annualized_vol * 100, 2),
            "downside_volatility_pct": round(downside_vol * 100, 2),
        }

    def calculate_risk_adjusted_ratios(self):
        daily_rf_rate = self.risk_free_rate / self.trading_days

        # Sharpe Ratio
        excess_returns = self.daily_returns - daily_rf_rate
        daily_std = self.daily_returns.std()

        sharpe_ratio = 0.0
        if daily_std > 0 and not pd.isna(daily_std) and not np.isinf(daily_std):
            sharpe_calc = excess_returns.mean() / daily_std * np.sqrt(self.trading_days)
            if not pd.isna(sharpe_calc) and not np.isinf(sharpe_calc):
                sharpe_ratio = sharpe_calc

        # Sortino Ratio
        downside_returns = self.daily_returns[self.daily_returns < daily_rf_rate]
        sortino_ratio = 0.0

        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            if (
                downside_std > 0
                and not pd.isna(downside_std)
                and not np.isinf(downside_std)
            ):
                sortino_calc = (
                    (self.daily_returns.mean() - daily_rf_rate)
                    / downside_std
                    * np.sqrt(self.trading_days)
                )
                if not pd.isna(sortino_calc) and not np.isinf(sortino_calc):
                    sortino_ratio = sortino_calc

        return {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
        }

    def calculate_drawdown_metrics(self):
        cumulative_returns = (1 + self.df_pnl["pnl_pct"] / 100).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - running_max) / running_max * 100

        max_drawdown = drawdowns.min()

        is_drawdown = drawdowns < -0.01
        drawdown_periods = self._calculate_drawdown_periods(is_drawdown)

        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0
        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0

        total_return = self.df_pnl["pnl_pct"].iloc[-1]
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            "max_dd_pct": round(max_drawdown, 2),
            "avg_dd_duration_days": round(avg_drawdown_duration, 0),
            "max_dd_duration_days": round(max_drawdown_duration, 0),
            "calmar_ratio": round(calmar_ratio, 2),
        }

    def _calculate_drawdown_periods(self, is_drawdown_series):
        drawdown_periods = []
        current_dd_length = 0

        for is_dd in is_drawdown_series:
            if is_dd:
                current_dd_length += 1
            else:
                if current_dd_length > 0:
                    drawdown_periods.append(current_dd_length)
                current_dd_length = 0

        # Handle case nếu kết thúc trong drawdown
        if current_dd_length > 0:
            drawdown_periods.append(current_dd_length)

        return drawdown_periods

    def calculate_var_cvar(self, confidence_level=0.05):
        if len(self.daily_returns) == 0:
            return {
                f"var_{int((1-confidence_level)*100)}_daily_pct": 0.0,
                f"cvar_{int((1-confidence_level)*100)}_daily_pct": 0.0,
            }

        var = np.percentile(self.daily_returns, confidence_level * 100)

        if pd.isna(var) or np.isinf(var):
            var = 0.0

        tail_returns = self.daily_returns[self.daily_returns <= var]
        cvar = 0.0
        if len(tail_returns) > 0:
            cvar_calc = tail_returns.mean()
            if not pd.isna(cvar_calc) and not np.isinf(cvar_calc):
                cvar = cvar_calc

        return {
            f"var_{int((1-confidence_level)*100)}_daily_pct": round(var, 4),
            f"cvar_{int((1-confidence_level)*100)}_daily_pct": round(cvar, 4),
        }

    def calculate_performance_metrics(self):
        if len(self.daily_returns) == 0:
            return {
                "win_rate_pct": 0.0,
                "best_day_pct": 0.0,
                "worst_day_pct": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0,
            }

        win_rate = (self.daily_returns > 0).mean() * 100

        best_day = self.daily_returns.max()
        worst_day = self.daily_returns.min()

        if pd.isna(best_day) or np.isinf(best_day):
            best_day = 0.0
        if pd.isna(worst_day) or np.isinf(worst_day):
            worst_day = 0.0

        best_day_pct = min(best_day * 100, 1000) 
        worst_day_pct = max(worst_day * 100, -1000)  

        skewness = 0.0
        kurtosis = 0.0

        try:
            if len(self.daily_returns) > 2:
                skew_calc = stats.skew(self.daily_returns)
                if not pd.isna(skew_calc) and not np.isinf(skew_calc):
                    skewness = skew_calc

                kurt_calc = stats.kurtosis(self.daily_returns)
                if not pd.isna(kurt_calc) and not np.isinf(kurt_calc):
                    kurtosis = kurt_calc
        except:
            pass

        return {
            "win_rate_pct": round(win_rate, 2),
            "best_day_pct": round(best_day_pct, 2),
            "worst_day_pct": round(worst_day_pct, 2),
            "skewness": round(skewness, 2),
            "kurtosis": round(kurtosis, 2),
        }

    def calculate_rolling_metrics(self, window=21):
        daily_rf_rate = self.risk_free_rate / self.trading_days

        # Rolling Sharpe Ratio
        rolling_excess = self.daily_returns.rolling(window).mean() - daily_rf_rate
        rolling_vol = self.daily_returns.rolling(window).std()
        rolling_sharpe = (
            rolling_excess / rolling_vol * np.sqrt(self.trading_days)
        ).dropna()

        # Rolling Volatility
        rolling_volatility = (
            self.daily_returns.rolling(window).std() * np.sqrt(self.trading_days) * 100
        ).dropna()

        return rolling_sharpe, rolling_volatility

    def calculate_fitness_score(self, portfolio_metrics, benchmark_metrics):
        portfolio_return = portfolio_metrics["total_return_pct"]
        benchmark_return = benchmark_metrics["total_return_pct"]

        portfolio_vol = portfolio_metrics.get("annualized_volatility_pct", 0)
        benchmark_vol = benchmark_metrics.get("annualized_volatility_pct", 0)

        portfolio_drawdown = abs(portfolio_metrics.get("max_dd_pct", 0))
        benchmark_drawdown = abs(benchmark_metrics.get("max_dd_pct", 0))

        excess_return = portfolio_return - benchmark_return

        vol_penalty = (portfolio_vol - benchmark_vol) * 0.5
        drawdown_penalty = (portfolio_drawdown - benchmark_drawdown) * 0.3

        fitness_score = excess_return - vol_penalty - drawdown_penalty

        return round(fitness_score, 2)

    def calculate_all_metrics(self):
        # Combine all metrics
        risk_metrics = {}

        # Basic metrics
        risk_metrics.update(self.calculate_basic_metrics())

        # Volatility metrics
        vol_metrics = self.calculate_volatility_metrics()
        risk_metrics.update(vol_metrics)

        # Risk-adjusted ratios
        risk_ratios = self.calculate_risk_adjusted_ratios()
        risk_metrics.update(risk_ratios)

        # Drawdown metrics
        dd_metrics = self.calculate_drawdown_metrics()
        risk_metrics.update(dd_metrics)

        # VaR/CVaR
        var_metrics = self.calculate_var_cvar()
        risk_metrics.update(var_metrics)

        # Performance metrics
        perf_metrics = self.calculate_performance_metrics()
        risk_metrics.update(perf_metrics)

        return risk_metrics
