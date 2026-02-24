# Task 003: Run Full Backtest & Produce Performance Report

## Objective
Compile and run the fixed `copper_gold_strategy.cpp` against the cleaned data. Capture all output and produce a comprehensive performance report so we know exactly what we're working with before making further improvements.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp` (bug-fixed: inflation threshold, static vars, Layer 4 term structure, dead code removed)
- Cleaned data: `data/cleaned/futures/` and `data/cleaned/macro/`
- Raw data: `data/raw/futures/` and `data/raw/macro/` (original, uncleaned)
- venv with pandas: `.venv/` (activate with `source .venv/bin/activate`)

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** You are evaluating a strategy for potential live capital allocation. The backtest report must be rigorous enough to present to a portfolio manager. No cherry-picking, no hand-waving. Show the warts.

## Execution — Deploy Agent Teams

### Agent 1: Compile & Run Backtest
- Compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
- Read the source code to understand what command-line arguments it expects (data directory path, initial capital, etc.)
- Run the strategy against **cleaned data** (`data/cleaned/`). If the strategy hardcodes `data/raw/`, you'll need to either:
  - Pass cleaned data path as an argument, OR
  - Temporarily symlink or update the path in code (document what you changed)
- Capture ALL stdout/stderr output to `results/backtest_output.txt`
- Create `results/` directory if needed
- If the run fails, diagnose why and fix (likely a path issue with cleaned vs raw data)

### Agent 2: Parse & Analyze Backtest Results
- **Wait for Agent 1 to complete** — this agent depends on backtest output
- Read `results/backtest_output.txt` and parse all performance metrics
- Write `results/performance_report.md` with:
  - **Summary stats**: Total return, CAGR, Sharpe ratio, Sortino ratio, max drawdown, max drawdown duration
  - **Annual breakdown**: Year-by-year returns
  - **Trade stats**: Total trades, win rate, avg win/loss, profit factor, avg holding period
  - **Per-instrument breakdown**: Which instruments made/lost money
  - **Risk metrics**: Worst month, worst quarter, longest losing streak, VaR/CVaR if calculable
  - **Layer analysis**: How often each signal layer (L1-L4) fired, contribution to P&L if visible from logs
  - **Regime analysis**: Time spent in each regime (risk-on, risk-off, liquidity shock), returns per regime
  - **Equity curve data**: If possible, extract equity curve values for later charting
- Be honest and critical — flag anything that looks suspicious (too good, too bad, or structurally broken)

### Agent 3: Compare Pre-Fix vs Post-Fix (optional but valuable)
- If feasible, also run the backtest against **raw data** (`data/raw/`) to compare
- This shows the impact of the bug fixes + data cleaning
- Document the delta in `results/performance_report.md` under a "Pre-Fix vs Post-Fix Comparison" section
- If this is too complex or the strategy can't easily switch data paths, skip and note why

## Deliverables
1. `results/backtest_output.txt` — Raw backtest output
2. `results/performance_report.md` — Full professional performance report
3. Any code changes needed to point at cleaned data (document in report)

## Instructions
- Deploy Agent 1 first. Agents 2 and 3 depend on Agent 1's output
- After Agent 1 completes, deploy Agents 2 and 3 in parallel
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
