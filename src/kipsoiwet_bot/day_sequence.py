from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .martingale import MartingaleEngine, RoundResult, Side


def _parse_outcome(token: str) -> Side:
    t = token.strip().upper()
    if t in {"UP", "U", "1", "WIN_UP"}:
        return Side.UP
    if t in {"DOWN", "D", "0", "WIN_DOWN"}:
        return Side.DOWN
    raise ValueError(f"Unrecognized outcome token: {token}")


def load_outcomes(path: str) -> list[Side]:
    data = Path(path).read_text()
    raw = [x for x in data.replace(",", " ").replace("\n", " ").split(" ") if x.strip()]
    return [_parse_outcome(tok) for tok in raw]


@dataclass(slots=True)
class PredeterminedDay:
    bet_sequence: list[Side]
    interval_minutes: int = 5
    index: int = 0
    start_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.bet_sequence:
            raise ValueError("Outcomes sequence cannot be empty")

    def current_time_label(self) -> str:
        if self.start_at is None:
            return "Not started"
        t = self.start_at + timedelta(minutes=self.interval_minutes * self.index)
        day_num = (self.index * self.interval_minutes) // (24 * 60) + 1
        return f"Day {day_num} {t.strftime('%I:%M %p')}"

    def remaining(self) -> int:
        return len(self.bet_sequence) - self.index

    def done(self) -> bool:
        return self.index >= len(self.bet_sequence)

    def advance(self, engine: MartingaleEngine, up_price: float, down_price: float, round_won: bool) -> RoundResult:
        if self.done():
            raise ValueError("Day sequence finished")

        if self.start_at is None:
            self.start_at = datetime.now(timezone.utc)

        side = Side.UP if self.index == 0 else self.bet_sequence[self.index]
        engine.set_side(side)
        price = up_price if side == Side.UP else down_price
        result = engine.record_round(side=side, price=price, won=round_won)
        self.index += 1
        return result
