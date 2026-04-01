from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .martingale import MartingaleEngine, Side


@dataclass(slots=True)
class BacktestSummary:
    rounds: int
    wins: int
    losses: int
    net_pnl_usd: float
    max_drawdown_usd: float
    peak_stake_usd: float


def parse_backtest_rows(path: str) -> list[tuple[Side, bool]]:
    """Parse rows from txt/csv as `UP:W`, `DOWN:L`, `UP:WIN`, ..."""
    raw = Path(path).read_text(encoding="utf-8")
    tokens = [x.strip() for x in raw.replace("\n", " ").replace(",", " ").split(" ") if x.strip()]
    rows: list[tuple[Side, bool]] = []
    for token in tokens:
        if ":" not in token:
            raise ValueError(f"Backtest token must be SIDE:RESULT, got '{token}'")
        side_t, res_t = token.split(":", 1)
        side = Side.UP if side_t.upper() in {"UP", "U", "1"} else Side.DOWN
        won = res_t.upper() in {"W", "WIN", "1", "TRUE", "T"}
        rows.append((side, won))
    return rows


def run_backtest(rows: list[tuple[Side, bool]], up_price: float, down_price: float, target_profit_usd: float = 1.0) -> BacktestSummary:
    engine = MartingaleEngine(target_profit_usd=target_profit_usd, initial_side=Side.UP)
    wins = 0
    losses = 0
    peak_stake = 0.0
    equity = 0.0
    peak_equity = 0.0
    max_drawdown = 0.0

    for side, won in rows:
        engine.set_side(side)
        price = up_price if side == Side.UP else down_price
        stake = engine.next_stake(price)
        peak_stake = max(peak_stake, stake)
        result = engine.record_round(side=side, price=price, won=won, stake_usd=stake)
        equity = result.cumulative_pnl_usd
        peak_equity = max(peak_equity, equity)
        max_drawdown = max(max_drawdown, peak_equity - equity)
        if won:
            wins += 1
        else:
            losses += 1

    return BacktestSummary(
        rounds=len(rows),
        wins=wins,
        losses=losses,
        net_pnl_usd=round(engine.cumulative_pnl_usd, 2),
        max_drawdown_usd=round(max_drawdown, 2),
        peak_stake_usd=round(peak_stake, 2),
    )
