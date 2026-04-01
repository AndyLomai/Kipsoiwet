from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # optional during lightweight test runs
    def load_dotenv() -> None:
        return


load_dotenv()


@dataclass(slots=True)
class BotConfig:
    telegram_token: str
    target_profit_usd: float = 1.0
    initial_side: str = "UP"
    bet_window_seconds: float = 3.0
    dry_run: bool = True
    sequence_file: str = ""
    session_log_file: str = "logs/paper_session.csv"

    @classmethod
    def from_env(cls) -> "BotConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        return cls(
            telegram_token=token,
            target_profit_usd=float(os.getenv("TARGET_PROFIT_USD", "1.0")),
            initial_side=os.getenv("INITIAL_SIDE", "UP").upper(),
            bet_window_seconds=float(os.getenv("BET_WINDOW_SECONDS", "3.0")),
            dry_run=os.getenv("DRY_RUN", "true").lower() == "true",
            sequence_file=os.getenv("SEQUENCE_FILE", ""),
            session_log_file=os.getenv("SESSION_LOG_FILE", "logs/paper_session.csv"),
        )
