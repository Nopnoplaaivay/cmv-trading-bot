import math
from decimal import Decimal
from typing import List, Dict, Optional

from backend.modules.portfolio.core import Position, TradeRecommendation, Money, Weight


class RecommendationEngine:
    def __init__(self, weight_tolerance: float = 1.0):
        self.weight_tolerance = weight_tolerance

    def generate_recommendations(
        self,
        current_positions: List[Position],
        target_weights: List[Dict],
        available_cash: Money,
        net_asset_value: Money,
    ) -> List[TradeRecommendation]:
        """Generate trade recommendations based on current vs target portfolio"""
        recommendations = []

        # Create lookup dictionaries
        current_dict = {pos.symbol: pos for pos in current_positions}
        target_dict = {weight["symbol"]: weight for weight in target_weights}

        all_symbols = set(current_dict.keys()) | set(target_dict.keys())

        for symbol in all_symbols:
            current_weight = current_dict.get(
                symbol,
                Position(
                    symbol=symbol,
                    quantity=0,
                    market_price=Money(Decimal("0")),
                    cost_price=Money(Decimal("0")),
                    break_even_price=Money(Decimal("0")),
                    weight=Weight(Decimal("0")),
                ),
            ).weight.percentage

            target_weight = Decimal(str(target_dict.get(symbol, {}).get("weight", 0)))
            weight_diff = target_weight - current_weight

            if abs(weight_diff) < self.weight_tolerance:
                continue

            priority = self.calculate_priority(abs(weight_diff))

            if weight_diff > self.weight_tolerance:  # Need to buy
                required_value = (target_weight / 100) * net_asset_value.amount
                current_value = current_dict.get(
                    symbol,
                    Position(
                        symbol=symbol,
                        quantity=0,
                        market_price=Money(Decimal("0")),
                        cost_price=Money(Decimal("0")),
                        break_even_price=Money(Decimal("0")),
                        weight=Weight(Decimal("0")),
                    ),
                ).market_value.amount

                cash_needed = Money(required_value - current_value)
                action_price = target_dict[symbol]["marketPrice"]
                action_quantity = math.floor(float(cash_needed.amount) / action_price)

                if cash_needed.amount > 0:
                    recommendation = TradeRecommendation(
                        symbol=symbol,
                        action="BUY",
                        current_weight=Weight(current_weight),
                        target_weight=Weight(target_weight),
                        amount=cash_needed,
                        priority=priority,
                        reason=f"Increase weight from {current_weight:.1f}% to {target_weight:.1f}%",
                        action_price=Money(action_price),
                        action_quantity=action_quantity,
                    )
                    recommendations.append(recommendation)

            elif weight_diff < -self.weight_tolerance:  # Need to sell
                current_value = (
                    current_dict.get(symbol).market_value.amount
                    if symbol in current_dict
                    else Decimal("0")
                )
                target_value = (target_weight / 100) * net_asset_value.amount
                cash_to_raise = Money(current_value - target_value)

                recommendation = TradeRecommendation(
                    symbol=symbol,
                    action="SELL",
                    current_weight=Weight(current_weight),
                    target_weight=Weight(target_weight),
                    amount=cash_to_raise,
                    priority=priority,
                    reason=f"Reduce weight from {current_weight:.1f}% to {target_weight:.1f}%",
                    action_price=Money(current_value),
                    action_quantity=int(cash_to_raise.amount / current_value),
                )
                recommendations.append(recommendation)

        recommendations.sort(
            key=lambda x: (
                x.priority == "HIGH",
                abs(x.target_weight.percentage - x.current_weight.percentage),
            ),
            reverse=True,
        )
        return recommendations

    def calculate_priority(self, weight_diff: Decimal) -> str:
        if weight_diff > 3:
            return "HIGH"
        elif weight_diff > 1.5:
            return "MEDIUM"
        else:
            return "LOW"
