# Task 007: Fix GC/SI Bug, Drop Drags, A/B Test Signal Changes

## Objective
Fix the GC/SI position bug (free alpha), drop cost-drag instruments, and A/B test each V3 signal change in isolation to find what's helping vs hurting. Produce a clear recommendation on which changes to keep.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp` (current V3 state)
- V3 baseline: Sharpe 0.19, CAGR 1.45%, turnover 23.2x, max DD 18.42%
- V2 baseline: Sharpe 0.34, CAGR 3.62%, turnover 46.7x, max DD 25.63%
- V3 report: `results/performance_report_v3.md`
- V3 output: `results/backtest_output_v3.txt`
- Proposals: `docs/proposals/` (for original reasoning behind each change)
- Cleaned data: `data/cleaned/`
- venv: `.venv/`

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** The kitchen-sink approach in Task 006 degraded alpha. Now we isolate. Every signal change gets tested individually against a clean baseline. No assumptions — let the data decide what stays.

## Execution — Deploy Agent Teams

### Phase 1: Bug Fix + Drop Drags (deploy 2 agents in parallel)

#### Agent 1: Fix GC/SI Position Bug
- **Bug**: GC is sized for 698 days but zero trades are placed. SI same issue. These instruments have target positions computed but never executed
- Read `copper_gold_strategy.cpp` — trace the position sizing logic for GC and SI specifically
- Find WHY positions are sized but never placed. Likely causes:
  - Rebalance bands blocking (new position vs zero = infinite % change, but absolute change might be <2 contracts)
  - Missing from the trade execution universe
  - Data alignment issue (GC/SI data not matching the execution loop dates)
  - Position rounding to zero
- **Fix** the root cause. GC and SI should trade when the strategy sizes them
- **Validation**: After fix, GC and SI should show non-zero trade counts and P&L
- Document what the bug was and how you fixed it

#### Agent 2: Drop Cost-Drag Instruments
- **Drop 6J**: Net P&L -$14,388, 85 trades, 50.6% win rate. Pure cost drag — edge is zero, costs eat everything
- **Drop HG**: Net P&L -$7,467, 101 trades, 44.6% win rate. Same story — any gross edge is consumed by commissions
- **Consider MES**: Net P&L +$81, 83 trades, 14.5% win rate. Effectively breakeven. Drop unless there's a diversification argument
- **How to drop**: Remove these instruments from the trading universe / position sizing. Do NOT delete the data loading — we still want their prices for signal computation (Cu/Au ratio needs HG prices)
- **Constraint**: HG prices MUST still be loaded for the Cu/Au ratio calculation. Only remove HG from the TRADING universe, not the data universe

### Phase 2: A/B Testing (deploy 5 agents in parallel, AFTER Phase 1)

Create a clean A/B testing framework. Start from the Phase 1 output (bug fixed, drags dropped) as the NEW BASELINE. Then test each V3 signal change individually by toggling it on/off.

**Important**: Each agent gets its own copy of the .cpp to modify. After each agent runs its test, it reports metrics but does NOT save its modified .cpp. Only the baseline (Phase 1 output) persists. The final recommendation determines what we keep.

#### Agent 3: A/B Test — Cu/Au Detrending (504-day z-score)
- **Hypothesis**: Detrending was supposed to fix secular decline bias but tripled NEUTRAL days (229→740)
- **Test A (ON)**: Run backtest with detrending as-is (current V3 code)
- **Test B (OFF)**: Revert to raw Cu/Au ratio for regime classification (V2 behavior)
- Save both outputs. Report: Sharpe, CAGR, max DD, turnover, regime distribution, per-instrument P&L
- **Verdict**: Does detrending help or hurt? If NEUTRAL days are too high, try shorter lookback (252d instead of 504d) as Test C

#### Agent 4: A/B Test — Real Rate Signal
- **Hypothesis**: Real rate signal (treasury - breakeven) was supposed to confirm regime but may add noise
- **Test A (ON)**: Run with real rate signal as 4th composite sub-signal (current V3)
- **Test B (OFF)**: Remove real rate signal, revert to 3-signal composite (V2 behavior)
- Report same metrics as Agent 3
- **Verdict**: Does real rate signal add or destroy alpha?

#### Agent 5: A/B Test — Cu/Au Vol Filter
- **Hypothesis**: Vol filter reduces size in high-vol periods, but high-vol may be highest-alpha
- **Test A (ON)**: Run with vol filter (current V3)
- **Test B (OFF)**: Remove vol filter, use flat sizing regardless of Cu/Au vol
- Report same metrics as Agent 3
- **Verdict**: Is the vol filter a drag?

#### Agent 6: A/B Test — Regime Transition Smoothing (10-day blend)
- **Hypothesis**: Smoothing reduces whipsaw but may delay entry into correct regime
- **Test A (ON)**: Run with 10-day smoothing (current V3)
- **Test B (OFF)**: Revert to instant regime transitions (V2 behavior)
- Report same metrics as Agent 3
- **Verdict**: Does smoothing help or hurt on net?

#### Agent 7: A/B Test — dd_warn Hysteresis + Rebalance Bands
- **Hypothesis**: Turnover reduction is clearly good, but the specific thresholds may need tuning
- **Test A (current)**: dd_warn 15%, recovery 12%, rebalance bands 2 contracts / 30%
- **Test B (tighter bands)**: dd_warn 15%, recovery 12%, rebalance bands 1 contract / 20%
- **Test C (wider bands)**: dd_warn 15%, recovery 12%, rebalance bands 3 contracts / 40%
- Report: turnover, Sharpe, and trade count for each
- **Verdict**: What's the optimal band width?

### Phase 3: Synthesize & Implement Best Combo (deploy 2 agents sequentially)

#### Agent 8: Synthesize A/B Results + Implement Best Configuration
- Read all A/B test results from Agents 3-7
- Determine the OPTIMAL configuration: which changes to KEEP, which to REVERT
- Apply the winning combination to `copper_gold_strategy.cpp` (starting from Phase 1 baseline)
- Compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
- Run final backtest: capture to `results/backtest_output_v4.txt`

#### Agent 9: Write V4 Performance Report
- **Wait for Agent 8**
- Parse `results/backtest_output_v4.txt`
- Write `results/performance_report_v4.md` with:
  - Full metrics (CAGR, Sharpe, Sortino, max DD, PF, win rate, turnover)
  - NET returns after transaction costs
  - Per-instrument P&L table
  - A/B test summary table: what was tested, what was kept, what was reverted
  - V2 vs V3 vs V4 comparison table
  - Per-instrument breakdown: which instruments now carry alpha
  - Honest verdict: is this allocable? What Sharpe/CAGR would we need? What's still missing?

## Deliverables
1. `copper_gold_strategy.cpp` — optimal configuration based on A/B testing
2. `results/backtest_output_v4.txt` — V4 backtest output
3. `results/performance_report_v4.md` — comprehensive V4 report with A/B test results
4. `results/ab_tests/` — individual A/B test outputs (one file per test for auditability)

## Instructions
- **Phase 1 first**: Agents 1-2 in parallel. Bug fix + drop drags
- **Phase 2 second**: Agents 3-7 in parallel. Each runs its own A/B test independently
- **Phase 3 third**: Agent 8 then Agent 9. Synthesize + final run
- For A/B tests: each agent should save test outputs to `results/ab_tests/` (e.g., `detrend_on.txt`, `detrend_off.txt`)
- Agents 3-7 should each work on a COPY of the code for their test — do not clobber each other's changes
- The final .cpp after Agent 8 should be the ONE file that ships
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
