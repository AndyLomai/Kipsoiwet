from pathlib import Path

from kipsoiwet_bot.backtest import parse_backtest_rows, run_backtest
from kipsoiwet_bot.martingale import Side


def test_parse_backtest_rows(tmp_path: Path) -> None:
    p = tmp_path / "bt.txt"
    p.write_text("UP:W DOWN:L UP:WIN")
    rows = parse_backtest_rows(str(p))
    assert rows == [(Side.UP, True), (Side.DOWN, False), (Side.UP, True)]


def test_run_backtest_summary() -> None:
    rows = [(Side.UP, True), (Side.DOWN, False), (Side.UP, True)]
    summary = run_backtest(rows, up_price=0.57, down_price=0.44, target_profit_usd=1.0)
    assert summary.rounds == 3
    assert summary.wins == 2
    assert summary.losses == 1
