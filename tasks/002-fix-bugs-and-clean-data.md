# Task 002: Fix Consensus Bugs & Clean All CSV Data

## Objective
Fix the 4 critical bugs identified by the analysis team AND analyze, clean, and fix all CSV data quality issues. Produce a cleaned, production-ready codebase.

## Context
- Project root: `/home/riley/Code/claude_testing_1/`
- Main strategy: `copper_gold_strategy.cpp` (~1870 lines)
- Analysis docs: `docs/` (read these first for full context)
- Data: `data/raw/futures/` (40+ CSVs) and `data/raw/macro/` (16 CSVs)

## Mindset
**Every agent you deploy is an industrial-grade, professional-grade quant trader and researcher.** You are fixing a trading system that will manage real capital. Zero tolerance for sloppy fixes. Every change must be justified, documented, and safe. If a fix has ambiguity, flag it — don't guess.

## Execution — Deploy Agent Teams

### Phase 1: Bug Fixes (deploy all 4 agents in parallel)

#### Agent 1: Fix Inflation Threshold Bug
- **File**: `copper_gold_strategy.cpp`, line ~855
- **Bug**: Threshold is `0.10` (10bp) — fires on nearly every bar. Design spec likely intended `1.0` (100bp)
- **Evidence**: Lines 1656-1659 have a diagnostic warning about this exact issue
- **Fix**: Change threshold from `0.10` to `1.0`
- **Validation**: Grep for any other references to this threshold to ensure consistency
- **Document**: Add a brief comment at the fix site explaining the calibration

#### Agent 2: Fix Static Variable Leak
- **File**: `copper_gold_strategy.cpp`
- **Bug**: Three static locals inside `run()` leak state if called multiple times (breaks parameter sweeps, Monte Carlo):
  - Line ~1106: `static Regime pending_regime` (primary — regime debounce state)
  - Line ~1107: `static int pending_regime_count` (primary — debounce counter)
  - Line ~877: `static Regime last_debug_regime` (debug artifact — assigned but never read)
- **Fix**: Convert all three to class member variables. If no class exists, convert to non-static locals with state passed via function parameters
- **Validation**: Search entire file for ALL `static` locals inside functions — fix any others that leak state
- **Context**: Current `main()` only calls `run()` once, so this is a latent bug. But it MUST be fixed before any Monte Carlo or parameter sweep work. The debounce logic (pending_regime needs 3 consecutive days to confirm) must produce identical results on the first call — do not break the debounce

#### Agent 3: Wire In Term Structure Filter (Layer 4)
- **File**: `copper_gold_strategy.cpp`
- **Location**: This is NEW code. Insert after Layer 3 (DXY filter) concludes (~line 920), before position sizing logic (~line 964)
- **Bug**: Layer 4 (backwardation/contango filter) was specified in the design doc but never implemented. Second-month futures (`*_2nd.csv`) are loaded but unused
- **Read**: `copper_gold_strategy_v2.md` (lines ~234-304) for the Layer 4 design spec. Do NOT use `docs/strategy-logic.md` — it only documents existing code, not the missing layer
- **Data sources**: Load `GC_2nd`, `HG_2nd`, `SI_2nd`, `CL_2nd`, `ZN_2nd`, `ZB_2nd` from `data/raw/futures/`
- **CRITICAL HG_2nd conversion**: `HG_2nd.csv` is in cents/lb while `HG.csv` is in dollars/lb — divide HG_2nd values by 100.0 INLINE in the code before computing term structure spreads (the cleaned file from Phase 2 won't exist yet)
- **Implementation**: Compute front/back spread, classify curve (backwardation/contango/flat), apply trade expression matrix per the design spec, integrate as `size_mult` adjustment in the existing cascade
- **Validation**: Log term structure signals to verify they fire at reasonable frequencies

#### Agent 4: Remove Dead Code Pipelines
- **File**: `copper_gold_strategy.cpp`
- **Dead code identified**:
  - Redundant liquidity check at lines ~980-981 (unreachable when LIQUIDITY_SHOCK sets `size_mult = 0.0` at lines ~967-968, same threshold). Delete with a comment: `// Removed: duplicate liquidity check — LIQUIDITY_SHOCK already zeros size_mult using same threshold`
  - TIPS data: loaded at line ~468, declared at line ~1674, but never extracted or used in `run()`. Remove load + declaration
  - CNY/USD data: loaded at line ~472, declared at line ~1676, but never extracted or used in `run()`. Remove load + declaration
  - China empty CSVs (china_cli_alt, china_credit, china_pmi, china_leading_indicator_update, shfe_copper_inventory): **Verify first** — these files may NOT have loading code at all (they may just be data files that were never wired in). Only remove code if it exists. If no code references them, note "no code to remove" in your summary
- **Fix**: Remove all provably dead code paths cleanly. Don't leave commented-out blocks — delete them
- **Constraint**: Only remove code that is provably dead. If there's any doubt, leave it and add a `// TODO: appears unused, verify` comment
- **Output**: List every removal with file and line numbers in a brief summary when done

---

### Phase 2: Data Cleaning (deploy 3 agents in parallel, AFTER Phase 1 completes)

#### Agent 5: Data Quality Analyzer & Cleaning Script Author
- Analyze every CSV in `data/raw/futures/` and `data/raw/macro/`
- For each file, report: row count, date range, missing value count/percentage, weekend entries, gaps > 2 business days
- Write a Python cleaning script at `scripts/clean_data.py` that:
  - Removes weekend rows (Saturday/Sunday) from all futures CSVs
  - Forward-fills missing values (max 5 business days, then leave as NaN)
  - Flags but does NOT delete rows with suspicious values (zero price, negative price, volume = 0 on weekday)
  - Writes cleaned files to `data/cleaned/futures/` and `data/cleaned/macro/` (preserve originals)
  - Produces a `data/cleaned/cleaning_report.csv` summarizing what was changed per file
- **Do NOT run the script** — just write it. Terminal 1 will review first.

#### Agent 6: Fix HG_2nd Unit Mismatch
- **File**: `data/raw/futures/HG_2nd.csv`
- **Bug**: Values are in cents/lb (338-600) while `HG.csv` is in dollars/lb (2.76-5.08)
- **Fix**: Convert `HG_2nd.csv` values by dividing by 100 to match `HG.csv` units
- Write a small Python script at `scripts/fix_hg2nd_units.py` that reads the CSV, divides price columns by 100, writes to `data/cleaned/futures/HG_2nd.csv`
- **Do NOT modify the original** — write to cleaned directory

#### Agent 7: Handle Stale & Empty Data Files
- **Stale**: `china_leading_indicator.csv` — last update 2023-12-01, 2+ years stale. Document this in `docs/data-issues.md` with recommendation to source fresh data from OECD/FRED
- **Empty files** (date scaffolding only, no values):
  - `china_cli_alt.csv` (192 rows empty)
  - `china_credit.csv` (192 rows empty)
  - `china_pmi.csv` (193 rows empty)
  - `china_leading_indicator_update.csv` (192 rows empty)
  - `shfe_copper_inventory.csv` (828 rows empty)
- **Action**: Document all empty/stale files in `docs/data-issues.md`. For empty files that Agent 4 removed loading code for, note they can be archived. For files that COULD be sourced, document where to get them (OECD, FRED, SHFE direct)
- **Also document**: MES/MNQ short history (6yr vs 15yr backtest), end-date mismatches between futures and macro, dual SPX sources

---

## Deliverables
1. `copper_gold_strategy.cpp` — 4 bug fixes applied (Phase 1)
2. `scripts/clean_data.py` — Data cleaning script (Phase 2, do not run)
3. `scripts/fix_hg2nd_units.py` — HG_2nd unit conversion script (Phase 2, do not run)
4. `data/cleaned/` — Directory created, ready for cleaned output
5. `docs/data-issues.md` — Complete data quality issue log with sourcing recommendations

## Instructions
- **Phase 1 first**: Deploy Agents 1-4 in parallel. All 4 bug fixes to `copper_gold_strategy.cpp`
- **Phase 2 second**: After Phase 1 completes, deploy Agents 5-7 in parallel for data work
- **Phasing matters**: Agent 3 (term structure) needs to know Agent 4 (dead code) won't conflict — but since they touch different code sections, parallel is safe
- **Phase 3 — Validation** (after all agents complete):
  1. Attempt to compile: `g++ -std=c++17 -O2 -Wall copper_gold_strategy.cpp -o strategy` — if it fails, review and fix merge conflicts between agent edits
  2. If compilation succeeds, run a smoke test to verify no runtime crashes
  3. Review all agent outputs for consistency
- Do NOT commit — Terminal 1 (orchestrator) handles all git operations
