# Task 006: Implement All 10 Proposals & Rerun Backtest

## Objective
Implement all 10 ranked proposals from Task 005, rerun the backtest, and produce a V3 performance report showing the impact. Target: net Sharpe toward 0.50+, turnover <15x, positive net returns after costs.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp`
- Proposals: `docs/proposals/` (5 files — read ALL of them for implementation details)
- V2 baseline: Sharpe 0.34, PF 1.08, turnover 46.7x, CAGR 3.62% gross (~0% net)
- Cleaned data: `data/cleaned/`
- venv: `.venv/` (activate with `source .venv/bin/activate`)
- Backtest output reference: `results/backtest_output_v2.txt`

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** You are turning a broken prototype into something that could receive a capital allocation. Every change must be precise, tested in your head against known edge cases, and not introduce new bugs. Read the proposals carefully — they contain pseudocode and specific line references.

## Execution — Deploy Agent Teams

### Phase 1: Quick Wins (deploy 3 agents in parallel)

#### Agent 1: Fix Transaction Costs
- Read `docs/proposals/transaction-costs.md` for full details
- **Fix #1 (Rank 1)**: UB commission bug — charging $2.50 instead of real $82.83 (33x undercount). Find the commission table in the .cpp and fix
- **Fix #10 (Rank 10)**: Update ALL instrument commission rates to realistic 2024/2025 levels per the proposal doc
- **Add slippage model**: Deduct per-contract slippage on every trade (use the estimates from the proposal). Simple approach: fixed cents-per-contract by instrument added to cost
- **Validation**: Log total transaction costs at end of run. Costs should be material (1-3% of equity per year at current turnover)

#### Agent 2: Turnover Reduction — Hysteresis + Rebalance Bands
- Read `docs/proposals/turnover-reduction.md` for full details
- **Fix #2 (Rank 2)**: Raise `dd_warn` threshold from 10% to 15% and add hysteresis (don't flip size_mult back until drawdown recovers to 12%). The dd_warn oscillator fires 61% of days — this is the single biggest turnover driver
- **Fix #5 (Rank 5)**: Add rebalance bands — only trade when target position differs from current by >2 contracts AND >30% of current position. Small position changes are pure noise + cost
- **Combined target**: 46.7x → <15x turnover
- **Constraint**: Do NOT reduce turnover by adding holding periods or delays — that changes signal timing. Only use dead zones and bands

#### Agent 3: Add Per-Instrument P&L Tracking
- **Fix #7 (Rank 7)**: Add per-instrument P&L tracking to the backtest output
- For each instrument, at end of run print:
  - Total P&L
  - Number of trades (round trips)
  - Win rate
  - Average win / average loss
  - Gross Sharpe contribution
  - Total commission paid
- Format as a clean table in stdout
- This enables all future optimization — we need to see what's making and losing money

### Phase 2: Signal Improvements (deploy 4 agents in parallel, AFTER Phase 1)

#### Agent 4: Wire In Real Rate Signal
- Read `docs/proposals/signal-enrichment.md` — specifically the real rate signal section
- **Fix #3 (Rank 3)**: The real rate (treasury_10y - breakeven_10y) is already computed somewhere in the code but never connected to signal generation
- Find where it's calculated, find where signals are generated, and wire it in
- Use it as a regime confirmation / signal weight: when real rates are rising (tightening), increase RISK_OFF conviction. When falling (easing), increase RISK_ON conviction
- **Data**: `data/cleaned/macro/treasury_10y.csv` and `data/cleaned/macro/breakeven_10y.csv`
- Do NOT make this a standalone signal — use it to MODIFY conviction on existing signals

#### Agent 5: Detrend Cu/Au Ratio
- Read `docs/proposals/signal-enrichment.md` — specifically the detrending section
- **Fix #4 (Rank 4)**: The Cu/Au ratio has a secular decline (0.56 → 0.30 over 15 years) that biases the strategy into RISK_OFF during a bull market
- Implement detrending: use a rolling lookback window (e.g., 252-day or 504-day moving average) and compute the ratio's z-score against its rolling mean/std
- Replace the raw ratio with the detrended z-score in regime classification
- **Constraint**: The lookback window must be long enough to not be a momentum signal (>200 days) but short enough to adapt to structural shifts (<3 years)

#### Agent 6: Cu/Au Realized Vol Filter + Drop MNQ Short
- Read `docs/proposals/signal-enrichment.md` (vol filter) and `docs/proposals/regime-analysis.md` (MNQ)
- **Fix #6 (Rank 6)**: Add realized volatility of the Cu/Au ratio as a dynamic sizing input. When ratio vol is high, reduce position sizes (uncertain regime). When low, increase (clear regime)
- Compute: 63-day rolling std of daily Cu/Au ratio returns. Normalize to z-score. Map to sizing multiplier: z > 1.5 → 50% size, z < 0.5 → 100% size, linear in between
- **Fix #8 (Rank 8)**: Drop MNQ from the short universe in RISK_OFF regime (persistent loser since 2019). MNQ can still go long in RISK_ON

#### Agent 7: Regime Transition Smoothing
- Read `docs/proposals/regime-analysis.md` — specifically the transition smoothing section
- **Fix #9 (Rank 9)**: Currently regime changes cause instant position flips (massive turnover + whipsaw). Implement a 10-day linear blend between old and new regime target positions
- When regime changes from A to B:
  - Day 1: 90% regime A targets + 10% regime B targets
  - Day 2: 80% A + 20% B
  - ...
  - Day 10: 0% A + 100% B
- This smooths the transition and eliminates whipsaw from noise around regime boundaries
- **Constraint**: Emergency regimes (LIQUIDITY_SHOCK) should still flip instantly — only smooth transitions between RISK_ON / RISK_OFF / INFLATION

### Phase 3: Rerun Backtest & Report (deploy 2 agents sequentially, AFTER Phase 2)

#### Agent 8: Compile & Run V3 Backtest
- Compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
- Must compile with zero errors, zero warnings
- Run against cleaned data
- Capture output to `results/backtest_output_v3.txt`
- Verify:
  - Per-instrument P&L table prints at end
  - Transaction costs are deducted from equity
  - Turnover is reported (should be <15x)
  - No ERROR lines
  - Regime transitions show smoothing behavior

#### Agent 9: Parse Results & Write V3 Performance Report
- **Wait for Agent 8**
- Parse `results/backtest_output_v3.txt`
- Write `results/performance_report_v3.md` with:
  - All standard metrics (CAGR, Sharpe, Sortino, max DD, PF, win rate)
  - **NET returns** (after transaction costs) — this is the headline number now
  - Turnover comparison: V2 vs V3
  - Per-instrument P&L table (from the new tracking)
  - Regime breakdown with P&L per regime
  - V2 vs V3 comparison table
  - Honest assessment: is this allocable? What's still missing?

## Deliverables
1. `copper_gold_strategy.cpp` — all 10 improvements implemented
2. `results/backtest_output_v3.txt` — V3 backtest output
3. `results/performance_report_v3.md` — full V3 performance report with net returns

## Instructions
- **Phase 1 first**: Agents 1-3 in parallel. These are independent code sections
- **Phase 2 second**: Agents 4-7 in parallel. Signal changes build on Phase 1's cost/turnover infrastructure
- **Phase 3 third**: Agent 8 then Agent 9 sequentially
- After Phase 2, review for merge conflicts between agents — 7 agents editing one file is risky. If conflicts exist, resolve them before Phase 3
- Compile check after each phase to catch issues early
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
