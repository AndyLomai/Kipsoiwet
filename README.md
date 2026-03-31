# Kipsoiwet — Telegram Martingale Assistant for Polymarket

This repository now includes a working Python Telegram bot that helps you run your **UP/DOWN Polymarket martingale method** with your latest constraints:

- **Bet window:** act in the **first 3 seconds** of each candle to tolerate latency.
- **Target profit per completed cycle:** **$1.00**.
- **Price model:** Polymarket price-to-odds model (`odds = 1 / price`) from your documents.

> ⚠️ Important: this bot is a decision/execution assistant and state tracker. Keep `DRY_RUN=true` until you validate behavior in paper mode.

## Strategy math used

For a side price `p` (for example `0.57`):

- Decimal odds: `1 / p`
- Net profit multiplier on staked dollars: `(1 / p) - 1`
- Martingale stake for next round:

```text
stake = (cumulative_losses + target_profit) / ((1 / p) - 1)
```

With target profit `$1.00`:

- At `p=0.57`, stake is about `$1.33`
- If that loses, and next side price is `p=0.44`, next stake is about `$1.83`
- Prices are always live prices captured at bet time inside the execution window.

## Commands

After starting the bot in Telegram:

- `/start` — show config summary
- `/status` — show current side, cumulative losses, cumulative PnL
- `/next` — fetch live market prices and return recommended next bet (**only if data is received inside your 3-second window**)
- `/won` — record winning round (resets cumulative losses)
- `/lost` — record losing round (adds to cumulative losses)
- `/reset` — clear progression state
- `/daystatus` — show full-day predetermined-sequence progress
- `/advance` — settle the next 5-minute candle from the predefined UP/DOWN sequence

## Setup

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 2) Configure `.env`

```env
TELEGRAM_BOT_TOKEN=your_bot_token
POLYMARKET_EVENT_SLUG=bitcoin-up-or-down-march-31-11am-et
TARGET_PROFIT_USD=1.0
BET_WINDOW_SECONDS=3.0
INITIAL_SIDE=UP
DRY_RUN=true
SEQUENCE_FILE=./data/day_sequence.txt
```

### 3) Run

```bash
python -m kipsoiwet_bot
```


### Optional predetermined full-day sequence (your PDF column)

If your UP/DOWN results are predetermined, add:

```env
SEQUENCE_FILE=./data/day_sequence.txt
```

Then create `data/day_sequence.txt` containing `UP` or `DOWN` tokens in order, separated by spaces/newlines/commas. The file can be any length (single day, several weeks, or months).

Example:

```text
UP DOWN DOWN UP ...
```

Use `/advance win` or `/advance loss` for each candle. The bot will:

- use the next predetermined bet side from your sequence
- apply your provided result (`win` or `loss`)
- carry cumulative losses forward until a win, then restart stake sizing
- start whenever you initiate the first trade, then progress in 5-minute steps from that first trade onward until your sequence ends

## Project structure

- `src/kipsoiwet_bot/martingale.py` — martingale math + state transitions
- `src/kipsoiwet_bot/polymarket.py` — Polymarket market snapshot client
- `src/kipsoiwet_bot/bot.py` — Telegram command handlers and orchestration
- `tests/test_martingale.py` — tests for stake sizing and progression recovery

## Improving with your uploaded docs/PDF progression

When you upload your latest full-day progression document, extend this bot by:

1. Adding a parser that imports each candle result into `engine.record_round(...)`.
2. Exporting a day report (`CSV/PDF`) with: side, price, stake, win/loss, cycle id, and cumulative PnL.
3. Adding risk controls:
   - max consecutive losses
   - max daily drawdown
   - cooldown after N losses
4. Wiring authenticated order execution only after dry-run metrics are stable.

If you want, the next step can be a **backtest script** that reads your real progression file and outputs a full equity curve under this exact `$1 target / 3 second window` configuration.
