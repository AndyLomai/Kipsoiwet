# Kipsoiwet Bot Instructions (Consolidated)

## Trading Method Rules
- Use Polymarket price model: odds = 1 / price.
- Profit multiplier for stake sizing: (1 / p) - 1.
- Martingale stake formula:
  stake = (cumulative_losses + target_profit) / ((1 / p) - 1)
- Default target profit per completed cycle: 1 USD.
- Bet execution window: within first 3 seconds of candle (latency-tolerant).
- If a round loses, cumulative losses are added and next stake is recalculated.
- Keep trading using the predetermined sequence until a win.
- After a win, cumulative losses reset and stake sizing restarts from the base formula.

## Setup
1. Clone repository:
   git clone https://github.com/AndyLomai/Kipsoiwet.git
   cd Kipsoiwet
2. Create virtual environment:
   python3.11 -m venv .venv
   source .venv/bin/activate
3. Install dependencies:
   pip install -e '.[dev]'

## Environment Configuration (.env)
TELEGRAM_BOT_TOKEN=your_bot_token
POLYMARKET_EVENT_SLUG=bitcoin-up-or-down-march-31-11am-et
TARGET_PROFIT_USD=1.0
BET_WINDOW_SECONDS=3.0
INITIAL_SIDE=UP
DRY_RUN=true


## Run on a PC (direct)

### Windows (PowerShell)
cd Kipsoiwet
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
$env:TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
python -m kipsoiwet_bot

### macOS / Linux
cd Kipsoiwet
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
python -m kipsoiwet_bot

## Run and Test
- Run tests:
  PYTHONPATH=src python -m pytest -q
- Start bot:
  python -m kipsoiwet_bot

## Telegram Commands
- /start
- /status
- /next
- /won
- /lost
- /reset


## Predetermined Full-Day Sequence Mode
- Prepare `SEQUENCE_FILE` with ordered outcomes (`UP`/`DOWN`) from the first trade onward. It can be one day or multi-week/month length.
- Add to `.env`: `SEQUENCE_FILE=./data/day_sequence.txt`
- In Telegram use:
  - `/daystatus` to view current slot and remaining outcomes
  - `/advance win` or `/advance loss` to settle the next candle according to the predetermined sequence
- The first trade is always forced to `UP` when sequence mode starts.

## Notes
- Keep DRY_RUN=true initially.
- If market snapshot arrives after BET_WINDOW_SECONDS, skip candle.
- Add risk controls before live execution: max drawdown, max streak, cooldown.
- No maximum stake cap is enforced by default in this version.
