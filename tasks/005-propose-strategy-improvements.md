# Task 005: Propose Strategy Improvements Based on Available Data

## Objective
Analyze the current strategy's weaknesses and the available data, then produce concrete, implementable proposals to improve signal quality, reduce turnover, and add transaction cost modeling. All proposals must be backed by data we already have — no hand-waving about external data sources we'd need to acquire.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp`
- V2 backtest results: `results/performance_report_v2.md` (Sharpe 0.34, PF 1.08, 46.7x turnover)
- V2 backtest output: `results/backtest_output_v2.txt`
- Strategy design doc: `copper_gold_strategy_v2.md`
- Analysis docs: `docs/` (strategy-logic.md, data-inventory.md, architecture-review.md)
- Available data: `data/cleaned/futures/` (43 CSVs) and `data/cleaned/macro/` (15 CSVs)
- Available data inventory: `docs/data-inventory.md`

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** Think like a PM at a multi-strat pod shop reviewing a junior PM's strategy for allocation. Be specific, quantitative, and skeptical. Proposals must be implementable in C++ with the data we have on disk — not theoretical wish lists.

## Execution — Deploy Agent Teams (all 5 in parallel)

### Agent 1: Signal Enrichment Analyst
- Read the current signal pipeline in `copper_gold_strategy.cpp` and `docs/strategy-logic.md`
- Read the full data inventory in `docs/data-inventory.md` — know exactly what's available
- Analyze `data/cleaned/macro/` and `data/cleaned/futures/` to understand what signals could be extracted
- Propose 3-5 new signals or signal modifications using ONLY data we already have:
  - **Momentum signals**: trend-following overlays on the Cu/Au ratio or individual metals
  - **Carry/roll yield**: we now have `_2nd` month data and Layer 4 — can we extract carry signals?
  - **Cross-asset confirmation**: VIX, high yield spreads, breakeven inflation, treasury curve — all available in macro/
  - **Volatility regime**: realized vol of Cu/Au ratio as a signal filter or sizing input
  - **Mean reversion**: z-score of Cu/Au ratio against its own history
- For each proposal: describe the signal, what data it uses, expected effect on Sharpe/turnover, implementation complexity (lines of C++ code), and any risks
- Output: `docs/proposals/signal-enrichment.md`

### Agent 2: Turnover Reduction Analyst
- Current turnover is 46.7x — absurd for a macro strategy. Target: <15x
- Read `copper_gold_strategy.cpp` to understand current rebalancing logic
- Read `results/backtest_output_v2.txt` — analyze trade frequency, holding periods, how often positions flip
- Propose 3-5 turnover reduction mechanisms:
  - **Signal hysteresis / dead zone**: don't flip positions unless signal crosses a threshold (not just sign change)
  - **Position smoothing**: blend target position toward current position (e.g., move 25% per day toward target)
  - **Minimum holding period**: once a position is entered, hold for N bars minimum
  - **Rebalance bands**: only trade when target position differs from current by >X%
  - **Signal averaging**: use multi-day average of signal instead of point-in-time
- For each: expected turnover reduction, impact on signal capture, implementation complexity
- Output: `docs/proposals/turnover-reduction.md`

### Agent 3: Transaction Cost Modeler
- Currently NO transaction costs are modeled — the 3.62% CAGR is gross, not net
- Read the strategy code to understand how P&L is calculated
- Build a transaction cost model proposal:
  - **Futures commissions**: research typical per-contract costs for each instrument (CME/COMEX/CBOT/NYMEX). Use conservative estimates
  - **Slippage model**: estimate based on instrument liquidity. Use the volume data in the CSVs
  - **Market impact**: for the position sizes the strategy uses, estimate impact costs
  - **Spread costs**: bid-ask spread estimates per instrument
- Calculate: what would the V2 backtest return AFTER costs at current 46.7x turnover? At target 15x? At 5x?
- Propose where to add cost deductions in the C++ code
- Output: `docs/proposals/transaction-costs.md`

### Agent 4: Per-Instrument Alpha Decomposition
- Read `results/performance_report_v2.md` and `results/backtest_output_v2.txt`
- Decompose P&L by instrument: which instruments contribute alpha, which are just noise or losers?
- For each traded instrument:
  - Total P&L contribution
  - Win rate
  - Average trade size
  - Sharpe (instrument-level)
  - Is it worth trading this instrument or should we drop it?
- Identify: are there instruments we should ADD weight to? Remove entirely?
- Propose an optimized instrument universe based on the data
- Output: `docs/proposals/instrument-analysis.md`

### Agent 5: Regime Analysis & Adaptive Sizing
- Read `results/backtest_output_v2.txt` — grep for regime transitions and P&L around them
- Analyze: does the strategy make money in all regimes or only specific ones?
- For each regime (RISK_ON, RISK_OFF, INFLATION, LIQUIDITY_SHOCK):
  - Time spent (% of bars)
  - P&L generated
  - Win rate
  - Sharpe within regime
- Propose regime-adaptive improvements:
  - Should sizing differ by regime?
  - Should certain instruments only trade in certain regimes?
  - Is the regime classification itself correct, or should thresholds change?
  - Would a "regime confidence" score improve sizing?
- Output: `docs/proposals/regime-analysis.md`

## Deliverables
All output goes in `/home/riley/Code/claude_testing_1/docs/proposals/`:
1. `signal-enrichment.md` — 3-5 new signal proposals with data sources
2. `turnover-reduction.md` — 3-5 turnover reduction mechanisms
3. `transaction-costs.md` — Cost model + net return estimates
4. `instrument-analysis.md` — Per-instrument alpha decomposition
5. `regime-analysis.md` — Regime P&L breakdown + adaptive sizing proposals

## Instructions
- Deploy all 5 agents in parallel — they are independent
- Each agent reads the codebase and data, analyzes, and writes its proposal
- Create `docs/proposals/` directory before agents start
- Proposals must be **specific and implementable** — include pseudocode or C++ snippets where possible
- Rank proposals by expected Sharpe improvement per unit of implementation effort
- Do NOT implement any changes — this is research and proposal only
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
