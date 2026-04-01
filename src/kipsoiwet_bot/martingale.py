from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Side(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


@dataclass(slots=True)
class RoundResult:
    timestamp: datetime
    side: Side
    price: float
    stake_usd: float
    won: bool
    pnl_usd: float
    cumulative_pnl_usd: float


@dataclass(slots=True)
class MartingaleEngine:
    target_profit_usd: float = 1.0
    initial_side: Side = Side.UP
    current_side: Side = field(init=False)
    cumulative_losses_usd: float = field(default=0.0, init=False)
    cumulative_pnl_usd: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.current_side = self.initial_side

    @staticmethod
    def odds_from_price(price: float) -> float:
        if price <= 0 or price >= 1:
            raise ValueError("price must be between 0 and 1")
        return 1 / price

    @staticmethod
    def profit_multiplier(price: float) -> float:
        # Buy $stake of shares at price p and win $1/share => net = stake*(1/p - 1)
        return (1 / price) - 1

    def next_stake(self, price: float) -> float:
        multiplier = self.profit_multiplier(price)
        if multiplier <= 0:
            raise ValueError("profit multiplier must be positive")
        raw_stake = (self.cumulative_losses_usd + self.target_profit_usd) / multiplier
        stake = round(raw_stake + 1e-8, 2)
        return max(stake, 0.01)

    def record_round(self, side: Side, price: float, won: bool, stake_usd: float | None = None) -> RoundResult:
        stake = stake_usd if stake_usd is not None else self.next_stake(price)
        if won:
            pnl = round(stake * self.profit_multiplier(price), 2)
            self.cumulative_losses_usd = 0.0
        else:
            pnl = -round(stake, 2)
            self.cumulative_losses_usd = round(self.cumulative_losses_usd + stake, 2)

        self.cumulative_pnl_usd = round(self.cumulative_pnl_usd + pnl, 2)
        return RoundResult(
            timestamp=datetime.now(tz=timezone.utc),
            side=side,
            price=price,
            stake_usd=stake,
            won=won,
            pnl_usd=pnl,
            cumulative_pnl_usd=self.cumulative_pnl_usd,
        )

    def set_side(self, side: Side) -> None:
        self.current_side = side

    def reset(self) -> None:
        self.current_side = self.initial_side
        self.cumulative_losses_usd = 0.0
        self.cumulative_pnl_usd = 0.0
