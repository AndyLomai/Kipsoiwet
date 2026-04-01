from kipsoiwet_bot.martingale import MartingaleEngine, Side


def test_next_stake_targets_one_usd_at_57c() -> None:
    engine = MartingaleEngine(target_profit_usd=1.0, initial_side=Side.UP)
    stake = engine.next_stake(0.57)
    assert stake == 1.33


def test_loss_then_win_recovers_and_restarts_stake_math() -> None:
    engine = MartingaleEngine(target_profit_usd=1.0, initial_side=Side.UP)

    loss = engine.record_round(side=Side.UP, price=0.57, won=False, stake_usd=1.33)
    assert loss.pnl_usd == -1.33
    assert engine.cumulative_losses_usd == 1.33

    next_stake = engine.next_stake(0.44)
    assert next_stake == 1.83

    win = engine.record_round(side=Side.DOWN, price=0.44, won=True, stake_usd=next_stake)
    assert win.pnl_usd == 2.33
    assert win.cumulative_pnl_usd == 1.0
    assert engine.cumulative_losses_usd == 0.0

    restart_stake = engine.next_stake(0.57)
    assert restart_stake == 1.33
