from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class SessionLogger:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with self.path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp_utc",
                    "event",
                    "side",
                    "price",
                    "stake_usd",
                    "won",
                    "pnl_usd",
                    "cumulative_pnl_usd",
                    "note",
                ])

    def write(
        self,
        event: str,
        side: str = "",
        price: float | str = "",
        stake_usd: float | str = "",
        won: bool | str = "",
        pnl_usd: float | str = "",
        cumulative_pnl_usd: float | str = "",
        note: str = "",
    ) -> None:
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now(timezone.utc).isoformat(),
                    event,
                    side,
                    price,
                    stake_usd,
                    won,
                    pnl_usd,
                    cumulative_pnl_usd,
                    note,
                ]
            )
