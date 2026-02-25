# Task 008: V5 — Close the Gap to Allocable

## Objective
Push from V4 (Sharpe 0.40) toward the V5 kill gate: **Sharpe ≥0.50, PF ≥1.15, Turnover <25x**. If V5 fails these thresholds, the Cu/Au signal has reached its ceiling and further development should be deprioritized.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp` (current V4 state)
- V4 baseline: Sharpe 0.40, CAGR 4.00%, PF 1.08, turnover 32.1x, max DD 16.4%, net P&L $868K
- V4 report: `results/performance_report_v4.md` — READ THIS FIRST, especially sections 6 and 7
- V4 output: `results/backtest_output_v4.txt`
- A/B test results: `results/ab_tests/` (11 files — reference for methodology)
- Available macro data: `data/cleaned/macro/` — includes `high_yield_spread.csv`, `vix.csv`, `treasury_10y.csv`, `breakeven_10y.csv`, `dxy.csv`, `spx.csv`, `fed_balance_sheet.csv`
- Available futures data: `data/cleaned/futures/` (42 instruments)
- Compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
- venv: `.venv/`

## V4 Diagnosis (from the report)
1. **Turnover 32.1x** (need <25x): UB+ZN = $192K of $230K costs (83%). 215 round-trips in these two instruments. Reducing UB/ZN trades by 30% saves ~$60K → pushes Sharpe toward 0.45
2. **CL is a -$68K drag**: Was V3's best instrument (+$152K), flipped to worst in V4. Raw ratio RISK_OFF bias structurally wrong-foots CL post-2022
3. **SI is -$360**: 62 round-trips generating $14K gross, consumed by $14K costs. Not worth trading
4. **73% concentration in UB**: Strategy is functionally a bond trade. Need diversification or accept it
5. **PF 1.08**: Every $1 lost earns $1.08. No margin for error. Need 1.15+

## Mindset
**Every agent is a professional quant researcher.** V3 taught us that bundling changes kills alpha. V4 taught us that A/B testing works. Apply both lessons: research first, propose specific changes, A/B test each in isolation, then combine only the winners.

## Execution — Deploy Agent Teams

### Phase 1: Research & Diagnose (deploy 4 agents in parallel)

#### Agent 1: Turnover Decomposition
- Read `copper_gold_strategy.cpp` and `results/backtest_output_v4.txt`
- Parse the backtest output to understand WHERE turnover is coming from:
  - Per-instrument trade frequency (trades/year for each instrument)
  - Per-instrument notional turnover contribution
  - What triggers each trade? Signal flips? Rebalance? DD stop? Regime change?
  - How many trades are "noise" (position changes of 1-2 contracts that barely move the needle)?
- **Propose specific, testable turnover reduction mechanisms:**
  - Instrument-specific rebalance bands (UB/ZN need wider bands than GC/MNQ due to higher notional)
  - Minimum holding period per instrument (not per signal — the signal can flip but we don't trade until the band is breached AND N days have passed)
  - Asymmetric bands (wider for increasing position, tighter for decreasing — let winners run, cut losers)
- Save analysis to `results/v5_research/turnover_analysis.md`

#### Agent 2: CL Signal Forensics
- Read `copper_gold_strategy.cpp` — trace CL's position sizing and signal logic specifically
- Read `results/ab_tests/` — was CL positive in any A/B test variant?
- Analyze CL's P&L by year (parse backtest output for CL-specific trades if possible)
- **Key question**: Is CL's alpha recoverable, or should we just drop it?
  - If the raw Cu/Au ratio structurally biases CL wrong: DROP IT (saves $15K costs + $53K gross losses = +$68K net)
  - If CL was profitable in certain regimes/years: propose an instrument-specific filter (e.g., only trade CL when term structure confirms direction)
- Also assess SI: with -$360 net on 62 trades, is there ANY argument for keeping it?
- Save analysis to `results/v5_research/cl_si_analysis.md`

#### Agent 3: New Signal Research — HY Spread + VIX
- Read available macro data files:
  - `data/cleaned/macro/high_yield_spread.csv` — HY-IG credit spread (risk appetite proxy)
  - `data/cleaned/macro/vix.csv` — VIX (fear gauge)
- Compute basic signal statistics:
  - Correlation with Cu/Au ratio (we want LOW correlation = independent signal)
  - Lead/lag relationship with regime changes
  - Distribution characteristics (stationarity, mean-reversion, trending)
- **Propose how each could be wired in** — NOT as standalone signals but as:
  - Regime confirmation (e.g., Cu/Au says RISK_OFF AND HY spread widening → higher conviction)
  - Size modulation (e.g., VIX > 30 → reduce all positions 50%)
  - Signal filter (e.g., only trade when Cu/Au signal AND HY signal agree)
- **CRITICAL**: Each proposed signal must be simple, testable, and not add more than 2-3 parameters. We learned from V3 that complexity kills.
- Write a short Python analysis script if needed (use `.venv/` with pandas)
- Save proposals to `results/v5_research/new_signals.md`

#### Agent 4: Position Sizing & Concentration Analysis
- Read `copper_gold_strategy.cpp` — understand the current position sizing model
- **UB concentration problem**: 73% of P&L from one instrument. Analyze:
  - Is this because UB gets the largest allocation? Or because UB has the best signal?
  - If we cap UB at 50% of risk budget, what happens to expected Sharpe?
  - Could we size by inverse-volatility (UB is low vol per contract → gets more contracts → dominates)?
- **Propose sizing changes:**
  - Instrument-level risk caps (max % of total P&L or VAR from any single instrument)
  - Risk-parity sizing (equal volatility contribution per instrument)
  - Signal-strength sizing (higher conviction → larger position, regardless of instrument)
- Save analysis to `results/v5_research/sizing_analysis.md`

### Phase 2: Implement & A/B Test (deploy agents in parallel, AFTER Phase 1)

Read ALL Phase 1 research outputs before proceeding. For each proposed change that Phase 1 identifies as promising, deploy one agent to implement and A/B test it. Follow the V4 methodology:
- Each agent gets its own copy of the .cpp
- Test ON vs OFF (and any variants)
- Report Sharpe, CAGR, PF, max DD, turnover, per-instrument P&L
- Save outputs to `results/ab_tests_v5/`

**Likely agents (finalize after reading Phase 1 research):**

#### Agent 5: A/B Test — Instrument-Specific Rebalance Bands
- Implement whatever turnover reduction Agent 1 recommends
- Test current (3/40%) vs instrument-specific bands vs proposed alternative

#### Agent 6: A/B Test — Drop CL (and possibly SI)
- Test A: Current (CL + SI active)
- Test B: Drop CL only
- Test C: Drop CL + SI
- This is the simplest possible improvement — just removing losers

#### Agent 7: A/B Test — HY Spread Signal Integration
- Implement whatever Agent 3 proposes for HY spread
- Test ON vs OFF

#### Agent 8: A/B Test — VIX Filter
- Implement whatever Agent 3 proposes for VIX
- Test ON vs OFF

#### Agent 9: A/B Test — Position Sizing Changes
- Implement whatever Agent 4 proposes (risk caps, risk parity, etc.)
- Test current sizing vs proposed alternative

### Phase 3: Synthesize & Final Run (deploy 2 agents sequentially, AFTER Phase 2)

#### Agent 10: Synthesize + Implement Best Configuration
- Read ALL A/B test results from Phase 2
- Determine optimal V5 configuration — which changes to KEEP, which to REVERT
- Apply winning combination to `copper_gold_strategy.cpp`
- Compile and run final backtest → `results/backtest_output_v5.txt`
- **V5 Kill Gate Check**: Does the result meet Sharpe ≥0.50, PF ≥1.15, Turnover <25x?

#### Agent 11: Write V5 Performance Report
- **Wait for Agent 10**
- Parse `results/backtest_output_v5.txt`
- Write `results/performance_report_v5.md` with:
  - Full metrics (CAGR, Sharpe, Sortino, max DD, PF, win rate, turnover)
  - NET returns after transaction costs
  - Per-instrument P&L table
  - V2 vs V3 vs V4 vs V5 comparison table
  - A/B test summary: what was tested, what was kept, what was reverted
  - **V5 Kill Gate verdict**: PASS or FAIL on each of the 3 criteria
  - If FAIL: what's the theoretical ceiling? Should we continue or deprioritize?
  - If PASS: what would a live deployment roadmap look like?

## Deliverables
1. `results/v5_research/` — 4 research reports from Phase 1
2. `results/ab_tests_v5/` — individual A/B test outputs from Phase 2
3. `copper_gold_strategy.cpp` — optimal V5 configuration
4. `results/backtest_output_v5.txt` — V5 backtest output
5. `results/performance_report_v5.md` — comprehensive V5 report with kill gate verdict

## Instructions
- **Phase 1 first**: Agents 1-4 in parallel. Pure research — no code changes
- **Phase 2 second**: Agents 5-9 in parallel (adjust based on Phase 1 findings). Each agent works on a COPY for A/B testing
- **Phase 3 third**: Agent 10 then Agent 11 sequentially
- A/B test EVERY change individually before combining. This is non-negotiable after the V3 lesson
- The final .cpp after Agent 10 should be the ONE file that ships
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
