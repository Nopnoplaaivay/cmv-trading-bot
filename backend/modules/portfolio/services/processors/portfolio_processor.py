from decimal import Decimal
from typing import List, Dict, Optional

from backend.modules.portfolio.core import Position, Money, Weight


class PortfolioProcessor:
    @staticmethod
    def process_deals_to_positions(
        deals_list: List[Dict], net_asset_value: float, stock_value: float
    ) -> List[Position]:
        """Convert raw deals data into Position objects"""
        positions = []

        if not deals_list or net_asset_value <= 0:
            return positions

        for deal in deals_list:
            symbol = deal.get("symbol", "")
            if not symbol:
                continue

            accumulate_quantity = deal.get("accumulateQuantity", 0)
            market_price_value = deal.get("marketPrice", 0)
            cost_price_value = deal.get("averageCostPrice", 0)
            break_even_price = deal.get("breakEvenPrice", 0)
            realized_profit_value = deal.get("realizedProfit", 0)
            unrealized_profit_value = deal.get("unrealizedProfit", 0)

            if accumulate_quantity > 0 and market_price_value > 0:
                market_price = Money(Decimal(str(market_price_value)))
                cost_price = Money(Decimal(str(cost_price_value)))
                break_even_price = Money(Decimal(str(break_even_price)))
                realized_profit = Money(Decimal(str(realized_profit_value)))
                unrealized_profit = Money(Decimal(str(unrealized_profit_value)))

                market_value = market_price.amount * accumulate_quantity
                weight_pct = (market_value / Decimal(str(net_asset_value))) * 100
                weight_over_sv_pct = (market_value / Decimal(str(stock_value))) * 100
                weight = Weight(weight_pct)
                weight_over_sv = Weight(weight_over_sv_pct)

                position = Position(
                    symbol=symbol,
                    quantity=accumulate_quantity,
                    market_price=market_price,
                    cost_price=cost_price,
                    break_even_price=break_even_price,
                    weight=weight,
                    weight_over_sv=weight_over_sv,
                    realized_profit=realized_profit,
                    unrealized_profit=unrealized_profit,
                )
                positions.append(position)

        positions.sort(key=lambda x: x.weight.percentage, reverse=True)
        return positions
