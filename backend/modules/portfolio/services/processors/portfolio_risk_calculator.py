import pandas as pd
import numpy as np
from scipy import stats


class PortfolioRiskCalculator:
    def __init__(self, df_pnl):
        self.trading_days = 252
        self.risk_free_rate = 0
        self.df_pnl = df_pnl.iloc[-self.trading_days:].copy()
        self.daily_profit_pct = df_pnl["daily_profit_pct"].iloc[-self.trading_days:].copy()
        

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
        if len(self.daily_profit_pct) < 2:
            return {
                "daily_volatility_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "downside_volatility_pct": 0.0,
            }

        daily_vol = self.daily_profit_pct.std()

        # Handle NaN case
        if pd.isna(daily_vol) or np.isinf(daily_vol):
            daily_vol = 0.0

        annualized_vol = daily_vol * np.sqrt(self.trading_days)

        downside_returns = self.daily_profit_pct[self.daily_profit_pct < 0]
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

        excess_returns = self.daily_profit_pct - daily_rf_rate
        daily_std = self.daily_profit_pct.std()

        sharpe_ratio = 0.0
        if daily_std > 0 and not pd.isna(daily_std) and not np.isinf(daily_std):
            sharpe_calc = excess_returns.mean() / daily_std * np.sqrt(self.trading_days)
            if not pd.isna(sharpe_calc) and not np.isinf(sharpe_calc):
                sharpe_ratio = sharpe_calc

        downside_returns = self.daily_profit_pct[self.daily_profit_pct < daily_rf_rate]
        sortino_ratio = 0.0

        if len(downside_returns) > 0:
            downside_std = downside_returns.std()
            if (
                downside_std > 0
                and not pd.isna(downside_std)
                and not np.isinf(downside_std)
            ):
                sortino_calc = (
                    (self.daily_profit_pct.mean() - daily_rf_rate)
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
        max_drawdown = self.df_pnl["drawdown_pct"].max() * 100

        df_pnl = self.df_pnl.copy()

        total_return = self.df_pnl["pnl_pct"].iloc[-1]
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            "max_dd_pct": round(max_drawdown, 2),
            "calmar_ratio": round(calmar_ratio, 2),
        }


    def calculate_var_cvar(self, confidence_level=0.05):
        if len(self.daily_profit_pct) == 0:
            return {
                f"var_{int((1-confidence_level)*100)}_daily_pct": 0.0,
                f"cvar_{int((1-confidence_level)*100)}_daily_pct": 0.0,
            }

        var = np.percentile(self.daily_profit_pct, confidence_level * 100)
        if pd.isna(var) or np.isinf(var):
            var = 0.0

        tail_returns = self.daily_profit_pct[self.daily_profit_pct <= var]
        cvar = tail_returns.mean() if len(tail_returns) > 0 else 0.0
        if pd.isna(cvar) or np.isinf(cvar):
            cvar = 0.0

        return {
            f"var_{int((1-confidence_level)*100)}_daily_pct": round(var * 100, 4),
            f"cvar_{int((1-confidence_level)*100)}_daily_pct": round(cvar * 100, 4),
        }

    def calculate_performance_metrics(self):
        if len(self.daily_profit_pct) == 0:
            return {
                "win_rate_pct": 0.0,
                "best_day_pct": 0.0,
                "worst_day_pct": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0,
            }

        win_rate = (self.daily_profit_pct > 0).mean() * 100
        best_day = self.daily_profit_pct.max()
        worst_day = self.daily_profit_pct.min()

        best_day_pct = min(best_day * 100, 1000)
        worst_day_pct = max(worst_day * 100, -1000)

        skewness = 0.0
        kurtosis = 0.0
        try:
            if len(self.daily_profit_pct) > 2:
                skew_calc = stats.skew(self.daily_profit_pct)
                if not pd.isna(skew_calc) and not np.isinf(skew_calc):
                    skewness = skew_calc

                kurt_calc = stats.kurtosis(self.daily_profit_pct)
                if not pd.isna(kurt_calc) and not np.isinf(kurt_calc):
                    kurtosis = kurt_calc
        except Exception as e:
            print(f"Error calculating skewness/kurtosis: {e}")

        return {
            "win_rate_pct": round(win_rate, 2),
            "best_day_pct": round(best_day_pct, 2),
            "worst_day_pct": round(worst_day_pct, 2),
            "skewness": round(skewness, 2),
            "kurtosis": round(kurtosis, 2),
        }

    def calculate_rolling_metrics(self, window=21):
        daily_rf_rate = self.risk_free_rate / self.trading_days
        rolling_excess = self.daily_profit_pct.rolling(window).mean() - daily_rf_rate
        rolling_vol = self.daily_profit_pct.rolling(window).std()
        rolling_sharpe = (rolling_excess / rolling_vol * np.sqrt(self.trading_days)).dropna()
        rolling_volatility = (self.daily_profit_pct.rolling(window).std() * np.sqrt(self.trading_days) * 100).dropna()
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
        risk_metrics = {}
        risk_metrics.update(self.calculate_basic_metrics())
        risk_metrics.update(self.calculate_volatility_metrics())
        risk_metrics.update(self.calculate_risk_adjusted_ratios())
        risk_metrics.update(self.calculate_drawdown_metrics())
        risk_metrics.update(self.calculate_var_cvar())
        risk_metrics.update(self.calculate_performance_metrics())

        return risk_metrics
