from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Dict, Any


# Value Objects
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "VND"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {"amount": float(self.amount), "currency": self.currency}


@dataclass(frozen=True)
class Weight:
    percentage: Decimal

    def __post_init__(self):
        if not 0 <= self.percentage <= 100:
            raise ValueError("Weight must be between 0 and 100")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {"percentage": float(self.percentage)}


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: int
    market_price: Money
    cost_price: Money
    break_even_price: Money 
    weight: Weight
    weight_over_sv: Weight = None 
    realized_profit: Money = None
    unrealized_profit: Money = None

    @property
    def market_value(self) -> Money:
        return self.market_price * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "market_price": self.market_price.to_dict(),
            "cost_price": self.cost_price.to_dict(),
            "break_even_price": self.break_even_price.to_dict(),
            "weight": self.weight.to_dict(),
            "weight_over_sv": self.weight_over_sv.to_dict(),
            "market_value": self.market_value.to_dict(),
            "realized_profit": (
                self.realized_profit.to_dict() if self.realized_profit else None
            ),
            "unrealized_profit": (
                self.unrealized_profit.to_dict() if self.unrealized_profit else None
            ),
        }


@dataclass(frozen=True)
class TradeRecommendation:
    symbol: str
    action: str  # "BUY" or "SELL"
    current_weight: Weight
    target_weight: Weight
    amount: Money
    priority: str  # "HIGH", "MEDIUM", "LOW"
    reason: str
    action_price: Money = None  # Optional, if applicable
    action_quantity: int = None  # Optional, if applicable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "symbol": self.symbol,
            "action": self.action,
            "current_weight": self.current_weight.to_dict(),
            "target_weight": self.target_weight.to_dict(),
            "amount": self.amount.to_dict(),
            "priority": self.priority,
            "action_price": self.action_price.to_dict() if self.action_price else None,
            "action_quantity": self.action_quantity,
            "reason": self.reason,
        }
