from datetime import datetime, timezone

from kipsoiwet_bot.day_sequence import PredeterminedDay
from kipsoiwet_bot.martingale import MartingaleEngine, Side


def test_first_trade_always_starts_up() -> None:
    seq = [Side.DOWN, Side.DOWN, Side.UP]
    day = PredeterminedDay(bet_sequence=seq)
    engine = MartingaleEngine(target_profit_usd=1.0, initial_side=Side.DOWN)

    first = day.advance(engine, up_price=0.57, down_price=0.44, round_won=False)
    assert first.side == Side.UP
    assert first.won is False
    assert day.index == 1


def test_day_sequence_progresses_and_can_win() -> None:
    seq = [Side.UP, Side.DOWN]
    day = PredeterminedDay(bet_sequence=seq, start_at=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc))
    engine = MartingaleEngine(target_profit_usd=1.0, initial_side=Side.UP)

    first = day.advance(engine, up_price=0.57, down_price=0.44, round_won=True)
    assert first.side == Side.UP
    assert first.won is True
    assert day.current_time_label() == "Day 1 12:10 AM"


def test_time_label_before_start() -> None:
    day = PredeterminedDay(bet_sequence=[Side.UP])
    assert day.current_time_label() == "Not started"
