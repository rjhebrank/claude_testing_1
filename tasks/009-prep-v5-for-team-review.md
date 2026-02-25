# Task 009: Prepare V5 for Team Review

## Objective
Prepare the V5 strategy for push to the team repo (`Copper_Gold_IP_Repo`). Clean up the code, write a strategy explainer doc, and produce a clean metrics summary.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Strategy: `copper_gold_strategy.cpp` (current V5 — 2,491 lines)
- Original teammate version: same file in `Copper_Gold_IP_Repo` on GitHub (user: `rjhebrank`)
- V5 report: `results/performance_report_v5.md`
- V5 output: `results/backtest_output_v5.txt`
- A/B tests: `results/ab_tests/` (V4) and `results/ab_tests_v5/` (V5)
- Research: `results/v5_research/`
- Original strategy doc: `copper_gold_strategy_v2.md` (teammate's original design doc)
- Proposals: `docs/proposals/` (5 files — reasoning behind each change)

## Deliverables — Deploy 3 Agents in Parallel

### Agent 1: Clean Up `copper_gold_strategy.cpp` for Team Review
- Read the current V5 `copper_gold_strategy.cpp` thoroughly
- Read the original version from the teammate (it's the same starting file — check git history with `git show HEAD~8:copper_gold_strategy.cpp` or similar to see the original V1 state)
- **Goal**: Make the V5 code presentable and consistent with the teammate's original coding style:
  - Update the header comment block: version should be `v5.0`, remove any references to being "consistent with v2.md" since this is now V5
  - Keep the same section separator style (`// ============================================================`)
  - Make sure all the V2→V5 changes have CLEAR inline comments explaining WHAT changed and WHY (brief — 1-2 lines max per change)
  - Remove any debug prints, TODO comments, or leftover development artifacts
  - Make sure commented-out code blocks are removed (dead code = confusion for reviewers)
  - Ensure the code compiles cleanly: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy`
  - Run the backtest after cleanup to verify output matches V5 numbers (Sharpe ~0.4979)
- **Do NOT change any logic** — this is cosmetic/documentation cleanup only. If the backtest numbers change, you broke something — revert.

### Agent 2: Write Strategy Explainer Doc
- Read `copper_gold_strategy_v2.md` (teammate's original design doc) for style reference
- Read `results/performance_report_v5.md` for all metrics and analysis
- Read `docs/proposals/` for the reasoning behind each change
- Read `results/v5_research/` for the research backing each decision
- **Write `copper_gold_strategy_v5.md`** — a comprehensive strategy document that a teammate can read to understand everything. Structure:

  1. **Executive Summary** — What this strategy does in 3-4 sentences. Cu/Au ratio as macro regime indicator, what instruments it trades, headline numbers.

  2. **What Changed from V2 to V5** — A clear, chronological changelog:
     - V2→V3: What we tried (all 10 proposals), what happened (kitchen sink hurt)
     - V3→V4: A/B testing revealed 3 harmful changes, reverted them, fixed GC/SI bug, dropped cost drags
     - V4→V5: Wider UB/ZN bands, HY spread confirmation filter
     - For each change: what it does, why we added/removed it, and the isolated A/B test result

  3. **Signal Architecture** — How the signal works end-to-end:
     - Layer 1: Cu/Au ratio → raw regime signal (RISK_ON / RISK_OFF)
     - Layer 2: Composite signal (Cu/Au + DXY + liquidity)
     - Layer 3: HY spread confirmation filter (NEW in V5)
     - Layer 4: Cu/Au vol filter for dynamic sizing
     - Layer 5: Drawdown management (dd_warn hysteresis, rebalance bands)
     - Include the actual thresholds and parameters used

  4. **Trading Universe** — Which instruments trade, which were dropped, and why:
     - Active: UB, ZN, GC, CL, SI, MNQ
     - Dropped: 6J (cost drag), HG (cost drag), MES (replaced by MNQ)
     - Per-instrument role and P&L contribution

  5. **Risk Management** — Drawdown stops, rebalance bands, vol filter, position limits

  6. **Performance Summary** — The version comparison table (V2 through V5), kill criteria status, per-instrument P&L table

  7. **Honest Assessment** — What works, what doesn't, what the theoretical ceiling is, what would be needed for live deployment

  8. **A/B Test Log** — Summary table of every A/B test run across V4 and V5, with verdicts. This is the audit trail showing disciplined process.

- **Style**: Match the teammate's `v2.md` style — professional but readable, no fluff. Use tables where appropriate. Be honest about limitations.

### Agent 3: Create Metrics Summary for Sharing
- **Write `results/v5_metrics_summary.md`** — a clean, concise 1-page summary designed to be screenshot-friendly:
  - Version progression table (V1 through V5): Sharpe, CAGR, Max DD, PF, Turnover, Net P&L, Win Rate, Kill Criteria Pass Count
  - V5 kill gate status table (the one from the user's message — Sharpe, PF, Turnover with pass/fail)
  - Per-instrument P&L table (instrument, net P&L, win%, role)
  - Key A/B test verdicts (1-line each)
  - 2-3 sentence bottom line
- **Formatting**: Use clean markdown tables, minimal prose, max visual clarity. This will be screenshotted and sent to teammates.

### Agent 4: Generate Equity Curve Chart
- Parse `results/backtest_output_v5.txt` — extract daily equity values (look for equity/P&L log lines)
- Use Python (`.venv/` with pandas + matplotlib — install matplotlib if needed: `uv pip install matplotlib`)
- **Generate `results/v5_equity_curve.png`** — a clean, professional equity curve chart:
  - X-axis: Date (2010-2025)
  - Y-axis: Portfolio equity ($)
  - Title: "Copper-Gold Macro Strategy — V5 Equity Curve"
  - Include a subtitle or annotation with headline numbers: "Sharpe 0.50 | CAGR 4.34% | Max DD 14.1%"
  - Draw a horizontal line at $1,000,000 (starting capital) for reference
  - Shade drawdown periods (or at minimum mark the max drawdown period)
  - Clean styling: white background, gridlines, readable font sizes
  - Figure size should be presentation-quality (e.g., 14x7 inches, 150 DPI)
- If daily equity isn't directly in the backtest output, reconstruct it from the trade log / P&L entries
- This chart will be screenshotted and shared with teammates

## Instructions
- Deploy all 4 agents in parallel — they're independent
- Agent 1 must verify compilation and backtest match after cleanup
- Agent 2 should read the original `v2.md` first for tone/style calibration
- Agent 3 should be concise — this is a screenshot, not a report
- Agent 4: install matplotlib if needed, generate a clean PNG
- Do NOT commit — Terminal 1 handles all git operations
