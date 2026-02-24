# Task 004: Fix 6 Critical Infrastructure Bugs

## Objective
Fix the 6 infrastructure bugs exposed by the backtest (Task 003). These are not signal problems — the engine itself is broken. No further strategy work until these are resolved and a clean backtest runs end-to-end.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp`
- Backtest results: `results/performance_report.md` (read this first for full diagnosis)
- Backtest output: `results/backtest_output.txt` (22K lines, search for `[ERROR]` and `HG` events)
- Cleaned data: `data/cleaned/`
- venv: `.venv/` (activate with `source .venv/bin/activate`)

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** These are the kind of bugs that blow up funds. A production trading system MUST reject bad data, liquidate on stop-outs, and never size positions on negative equity. Fix them like your capital depends on it — because it will.

## Execution — Deploy Agent Teams

### Phase 1: Data Fix (deploy 1 agent)

#### Agent 1: Fix Corrupted HG Data + Harden Cleaning Script
- **Bug #4**: The 2012-02-06 HG spike ($3.91 → $38,700) survived the cleaning pipeline because `clean_data.py` only flags zero/negative prices, not 10,000x moves
- **Find the bad data**: Search `data/raw/futures/HG.csv` and `data/raw/futures/HG_2nd.csv` around 2012-02-05 to 2012-02-07 for the spike. Identify exact rows
- **Fix the cleaning script** (`scripts/clean_data.py`): Add a price-move filter that flags/rejects single-bar moves exceeding a configurable threshold (e.g., >50% day-over-day for any price column). These rows should be forward-filled from the previous day, not deleted
- **Re-run the cleaning pipeline**: `source .venv/bin/activate && python3 scripts/clean_data.py` — verify the spike is now caught
- **Also re-run HG_2nd fix**: `python3 scripts/fix_hg2nd_units.py` — verify cleaned HG_2nd no longer has the spike
- **Output**: Updated `data/cleaned/` with the spike patched, updated `cleaning_report.csv`

### Phase 2: Engine Fixes (deploy 4 agents in parallel, AFTER Phase 1)

#### Agent 2: Add Data Validation Gate
- **Bug #1**: The engine logs `[ERROR]` for unrealistic price moves but continues execution — bad data flows into signal generation and position sizing
- **File**: `copper_gold_strategy.cpp` — find the existing `[ERROR]` logging for price validation
- **Fix**: When an `[ERROR]` is detected for unrealistic data:
  - Skip that bar entirely (do not update signals, do not trade)
  - Log `[DATA-REJECT]` with the instrument and date
  - Forward-fill the previous day's price for that instrument
  - Resume normal processing on the next bar
- **Constraint**: Do NOT halt the entire backtest — just skip the bad bar. In live trading we'd want to halt, but for backtesting we need to continue
- **Validation**: Grep output for `[DATA-REJECT]` — should fire on the 2012 HG event and nowhere else (if cleaning script did its job, it won't fire at all on cleaned data, which is correct)

#### Agent 3: Fix Drawdown Stop — Must Liquidate All Positions
- **Bug #2**: When drawdown stop triggers (`stop = 1`), the engine sets a flag but never flattens positions. Existing positions continue to accumulate losses
- **File**: `copper_gold_strategy.cpp` — find where `stop` flag is set
- **Fix**: When drawdown stop triggers:
  1. Immediately set ALL positions to zero (flatten everything)
  2. Log `[DRAWDOWN-STOP] Liquidating all positions. Equity: $X, Drawdown: Y%`
  3. Block all new position entries until a recovery condition is met (e.g., equity recovers above high-water-mark * 0.90, or a configurable cooldown period passes)
  4. When resuming, log `[DRAWDOWN-RESUME]`
- **Constraint**: The stop should be a circuit breaker, not a permanent kill. Design a reasonable re-entry condition

#### Agent 4: Add Negative Equity Guard
- **Bug #3**: When equity goes negative, the position sizing logic continues to calculate sizes, producing massive positions (5,800 → 8,485 contracts)
- **File**: `copper_gold_strategy.cpp` — find the position sizing / Kelly calculation section
- **Fix**:
  1. If equity <= 0, set ALL target positions to zero and log `[EQUITY-ZERO] Equity depleted, all positions zeroed`
  2. If equity < initial_capital * 0.10 (below 10% of starting capital), cap position sizes at 50% of normal to prevent ruin spiral
  3. Never allow position sizing to use negative equity as input
- **Validation**: Run a mental trace through the 2012 scenario — after HG spike causes massive loss, equity should not go negative, and if it does, positions must zero out

#### Agent 5: Investigate INFLATION Regime
- **Bug #5**: INFLATION regime fires 0 days in both backtest runs. After Task 002 changed threshold from 0.10 to 1.0, it may be overcorrected
- **File**: `copper_gold_strategy.cpp` — find the inflation regime classification logic
- **Investigation**:
  1. Read the breakeven_10y data (`data/cleaned/macro/breakeven_10y.csv`) — what's the actual range of values?
  2. Read the design doc (`copper_gold_strategy_v2.md`) for the intended inflation regime definition
  3. Determine the correct threshold. Is 1.0 (100bp) right? Should it be something else?
  4. Add diagnostic logging: `[INFLATION-CHECK] breakeven=X.XX, threshold=Y.YY, regime=Z`
- **Fix**: Set the threshold to the correct value based on the data and design doc. If the design doc is ambiguous, set it to a reasonable value and document your reasoning
- **Output**: Brief writeup of what the correct threshold should be and why

### Phase 3: Rerun Backtest & Validate (deploy 2 agents sequentially)

#### Agent 6: Compile & Run Clean Backtest
- Compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
- Run against cleaned data (which now has the spike patched from Phase 1)
- Capture output to `results/backtest_output_v2.txt`
- Verify:
  - No `[ERROR]` lines in output
  - `[DRAWDOWN-STOP]` fires at reasonable drawdown levels and liquidates
  - No negative equity
  - INFLATION regime fires at least some of the time
  - Strategy runs for the full 15.9 years without getting permanently frozen

#### Agent 7: Parse Results & Write Updated Performance Report
- **Wait for Agent 6**
- Parse `results/backtest_output_v2.txt`
- Write `results/performance_report_v2.md` with the same structure as v1 but updated
- Include a "v1 vs v2 Comparison" section showing the impact of infrastructure fixes
- Honest assessment: is the strategy now evaluable? What's the actual signal quality?

## Deliverables
1. Updated `scripts/clean_data.py` — with price-move spike detection
2. Updated `data/cleaned/` — spike patched
3. Updated `copper_gold_strategy.cpp` — all 4 engine fixes (data gate, liquidation, negative equity, inflation threshold)
4. `results/backtest_output_v2.txt` — clean backtest output
5. `results/performance_report_v2.md` — updated performance report

## Instructions
- **Phase 1 first**: Agent 1 fixes data. Must complete before engine fixes matter
- **Phase 2 second**: Agents 2-5 in parallel. All edit different sections of the .cpp
- **Phase 3 third**: Agent 6 then Agent 7 sequentially. Must have all fixes before running
- After all phases, verify compilation is clean (zero warnings)
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
