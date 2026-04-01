from pathlib import Path

from kipsoiwet_bot.session_log import SessionLogger


def test_session_logger_creates_and_appends(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "paper.csv"
    logger = SessionLogger(path=log_path)
    logger.write(event="next", side="UP", price=0.57, stake_usd=1.33)

    content = log_path.read_text(encoding="utf-8")
    assert "timestamp_utc,event,side,price,stake_usd,won,pnl_usd,cumulative_pnl_usd,note" in content
    assert ",next,UP,0.57,1.33" in content
