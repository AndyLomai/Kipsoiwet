from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import BotConfig
from .day_sequence import PredeterminedDay, load_outcomes
from .martingale import MartingaleEngine, Side
from .polymarket import PolymarketClient
from .session_log import SessionLogger


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BotState:
    engine: MartingaleEngine
    market: PolymarketClient
    config: BotConfig
    day_sequence: PredeterminedDay | None = None
    session_logger: SessionLogger | None = None


def _state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    state = context.application.bot_data.get("state")
    if not state:
        raise RuntimeError("Bot state not initialized")
    return state


def _log(state: BotState, **kwargs: object) -> None:
    if state.session_logger:
        state.session_logger.write(**kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    await update.message.reply_text(
        "Kipsoiwet bot ready.\n"
        f"Target profit: ${state.config.target_profit_usd:.2f}\n"
        f"Bet window: first {state.config.bet_window_seconds:.1f}s"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    await update.message.reply_text(
        "Current status\n"
        f"Side: {state.engine.current_side.value}\n"
        f"Cum losses: ${state.engine.cumulative_losses_usd:.2f}\n"
        f"Cum PnL: ${state.engine.cumulative_pnl_usd:.2f}"
    )


async def next_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    t0 = time.perf_counter()

    snapshot = await state.market.get_snapshot()
    elapsed = time.perf_counter() - t0
    if elapsed > state.config.bet_window_seconds:
        await update.message.reply_text(
            f"⚠️ Snapshot arrived in {elapsed:.2f}s, outside {state.config.bet_window_seconds:.1f}s window. Skip this candle."
        )
        return

    price = state.market.side_price(snapshot, state.engine.current_side)
    stake = state.engine.next_stake(price)
    _log(state, event="next", side=state.engine.current_side.value, price=price, stake_usd=stake, note=f"latency={elapsed:.2f}s")
    await update.message.reply_text(
        f"Next trade (within {elapsed:.2f}s):\n"
        f"Market: {snapshot.market_slug}\n"
        f"Side: {state.engine.current_side.value}\n"
        f"Price: {price:.3f}\n"
        f"Stake: ${stake:.2f}\n"
        f"Target net per cycle: ${state.engine.target_profit_usd:.2f}"
    )


async def won(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    snapshot = await state.market.get_snapshot()
    side = state.engine.current_side
    price = state.market.side_price(snapshot, side)
    result = state.engine.record_round(side=side, price=price, won=True)
    _log(state, event="won", side=result.side.value, price=result.price, stake_usd=result.stake_usd, won=True, pnl_usd=result.pnl_usd, cumulative_pnl_usd=result.cumulative_pnl_usd)
    await update.message.reply_text(
        f"✅ Win recorded. PnL +${result.pnl_usd:.2f}. Total: ${result.cumulative_pnl_usd:.2f}. Cumulative losses reset; restart stake formula."
    )


async def lost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    snapshot = await state.market.get_snapshot()
    side = state.engine.current_side
    price = state.market.side_price(snapshot, side)
    result = state.engine.record_round(side=side, price=price, won=False)
    _log(state, event="lost", side=result.side.value, price=result.price, stake_usd=result.stake_usd, won=False, pnl_usd=result.pnl_usd, cumulative_pnl_usd=result.cumulative_pnl_usd)
    await update.message.reply_text(
        f"❌ Loss recorded. PnL ${result.pnl_usd:.2f}. Cum losses: ${state.engine.cumulative_losses_usd:.2f}. Continue with next side from your predefined sequence."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    state.engine.reset()
    await update.message.reply_text("State reset to initial side and zero losses.")



async def day_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    if not state.day_sequence:
        await update.message.reply_text("No predetermined day sequence loaded. Set SEQUENCE_FILE in .env.")
        return

    await update.message.reply_text(
        f"Day progression\nCurrent slot: {state.day_sequence.current_time_label()}\nRemaining candles: {state.day_sequence.remaining()}"
    )


async def advance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    if not state.day_sequence:
        await update.message.reply_text("No predetermined day sequence loaded. Set SEQUENCE_FILE in .env.")
        return

    if state.day_sequence.done():
        await update.message.reply_text("✅ Sequence exhausted. Load a longer file to continue multi-day progression.")
        return

    if not context.args or context.args[0].lower() not in {"win", "loss"}:
        await update.message.reply_text("Usage: /advance win  OR  /advance loss")
        return

    round_won = context.args[0].lower() == "win"
    slot = state.day_sequence.current_time_label()
    snapshot = await state.market.get_snapshot()
    result = state.day_sequence.advance(
        engine=state.engine,
        up_price=snapshot.up_price,
        down_price=snapshot.down_price,
        round_won=round_won,
    )
    _log(state, event="advance", side=result.side.value, price=result.price, stake_usd=result.stake_usd, won=result.won, pnl_usd=result.pnl_usd, cumulative_pnl_usd=result.cumulative_pnl_usd, note=f"slot={slot}")
    await update.message.reply_text(
        f"{slot} settled: {'WIN' if result.won else 'LOSS'} | side={result.side.value} stake=${result.stake_usd:.2f} pnl=${result.pnl_usd:.2f} total=${result.cumulative_pnl_usd:.2f}"
    )


async def logfile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = _state(context)
    if state.session_logger:
        await update.message.reply_text(f"Session log file: {state.session_logger.path}")
    else:
        await update.message.reply_text("Session logging not configured.")

def build_app() -> Application:
    config = BotConfig.from_env()
    market_slug = os.getenv("POLYMARKET_EVENT_SLUG", "bitcoin-up-or-down-march-31-11am-et")
    engine = MartingaleEngine(
        target_profit_usd=config.target_profit_usd,
        initial_side=Side(config.initial_side),
    )
    market = PolymarketClient(market_slug=market_slug)

    day_sequence = None
    if config.sequence_file:
        bet_sequence = load_outcomes(config.sequence_file)
        day_sequence = PredeterminedDay(bet_sequence=bet_sequence, interval_minutes=5)

    app = Application.builder().token(config.telegram_token).build()
    session_logger = SessionLogger(path=Path(config.session_log_file))
    app.bot_data["state"] = BotState(engine=engine, market=market, config=config, day_sequence=day_sequence, session_logger=session_logger)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("next", next_bet))
    app.add_handler(CommandHandler("won", won))
    app.add_handler(CommandHandler("lost", lost))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("daystatus", day_status))
    app.add_handler(CommandHandler("advance", advance))
    app.add_handler(CommandHandler("logfile", logfile))
    return app


def main() -> None:
    app = build_app()
    logger.info("Starting Kipsoiwet bot")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
