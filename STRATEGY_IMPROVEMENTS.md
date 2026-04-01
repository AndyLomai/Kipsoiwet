# Strategy Improvements Applied

Based on your instructions and attached documents, this implementation applies:

1. **Entry timing adjusted to 3 seconds for latency tolerance**
   - Bot rejects a `/next` recommendation if market snapshot latency exceeds `BET_WINDOW_SECONDS` (default `3.0s`).

2. **Target profit set to $1.00**
   - `TARGET_PROFIT_USD` default is `1.0`.
   - All stake sizing uses this per-cycle target.

3. **Polymarket price interpretation fixed**
   - Paying `57¢` means gross payout `$1`, net profit `43¢` per share.
   - Formula implemented with `profit_multiplier = (1 / p) - 1`.

4. **Loss recovery cycle automation**
   - On a loss: cumulative losses increase.
   - Continue following the predefined sequence each round until a win occurs.
   - On a win: cumulative losses reset, so the next stake restarts from base formula.
   - Stake cap removed; stake is formula-driven from live price and cumulative losses.

5. **Safer operating mode by default**
   - Starts in `DRY_RUN=true` mode so recommendations can be validated before adding live execution.

## Recommended next improvements

- Add a parser for your real full-day progression PDF/DOC exports and replay into the engine.
- Add daily risk caps (`max_drawdown`, `max_steps_per_cycle`).
- Add exchange/API health checks with skip logic when stale data is detected.
- Add persistent storage (SQLite) so bot restarts do not lose progression state.


6. **Predetermined full-day sequence support**
   - Bot can now follow a fixed or extended UP/DOWN sequence starting at the user-initiated first trade time and continuing for as many candles as provided using `SEQUENCE_FILE` and `/advance`.

7. **Paper-session CSV logging**
   - Bot now records `next/won/lost/advance` actions to a CSV log file for 5-hour dry-run analysis.

8. **UI and backtesting expansion**
   - Added Telegram menu keyboard plus `/testrun` and `/backtest` to support richer paper testing workflows.
