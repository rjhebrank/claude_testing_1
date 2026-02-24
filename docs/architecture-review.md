# Architecture & Code Quality Review

**Codebase:** Copper-Gold Ratio Economic Regime Strategy v2.0
**File under review:** `copper_gold_strategy.cpp` (1,870 lines)
**Reviewer perspective:** Senior C++ engineer / quant infrastructure lead
**Date:** 2026-02-24

---

## 1. Project Structure

### File Layout

```
claude_testing_1/
  copper_gold_strategy.cpp          # 1,870-line monolithic C++ source (THE ENTIRE CODEBASE)
  copper_gold_strategy_v2.md        # Strategy design document (~843 lines)
  .gitignore                        # Only excludes .DS_Store
  tasks/001-full-codebase-analysis.md
  data/raw/
    futures/                        # 40+ CSVs (HG, GC, CL, SI, ZN, UB, 6J, MES, MNQ, + 2nd month, + extras)
    macro/                          # 16 CSVs (dxy, vix, treasury_10y, tips_10y, breakeven_10y, spx, etc.)
```

### Build System

**There is no build system.** No Makefile, no CMakeLists.txt, no build script, no compiler flags file, no dependency manifest of any kind. The project is presumably compiled with a bare `g++ copper_gold_strategy.cpp -o strategy` invocation from memory. This is a critical gap:

- No reproducible builds
- No documented compiler flags (optimization level, warnings, sanitizers)
- No indication of which C++ standard is targeted (the code uses C++17 structured bindings, so at minimum `-std=c++17` is required)
- No CI/CD pipeline

### Headers and Dependencies

The codebase has **zero external dependencies** beyond the C++ standard library. No header files, no separate translation units. The entire strategy lives in a single `.cpp` file with no modularity boundaries.

**Standard library headers used (lines 8-21):**
`<algorithm>`, `<cmath>`, `<ctime>`, `<fstream>`, `<unordered_set>`, `<iomanip>`, `<iostream>`, `<map>`, `<numeric>`, `<deque>`, `<sstream>`, `<string>`, `<unordered_map>`, `<vector>`

---

## 2. Code Organization

### Overall Structure: Monolithic

The entire 1,870-line file follows a top-to-bottom layout with no separation of concerns:

| Section | Lines | Description |
|---------|-------|-------------|
| Date utilities | 26-49 | `trim()`, `parse_date()`, `date_from_int()` |
| Data types | 54-59 | `OHLCVBar`, `TimeSeries`, `FuturesSeries` typedefs |
| CSV loaders | 64-137 | `load_futures()`, `load_macro()` |
| Forward-fill | 142-152 | `ffill()`, `ffill_fut_close()` |
| Rolling statistics | 157-246 | `rolling_mean()`, `rolling_std()`, `rolling_zscore()`, `compute_atr()`, `avg_pairwise_corr()` |
| Enums + string converters | 251-272 | `MacroTilt`, `Regime`, `DXYTrend`, `DXYFilter` |
| Contract specifications | 277-344 | `ContractSpec` namespace, `ASSET_WEIGHTS`, `SINGLE_NOTIONAL_LIMIT` |
| `DailySignal` struct | 348-375 | Output record (~25 fields) |
| `StrategyParams` struct | 380-427 | ~30 configurable parameters |
| `CopperGoldStrategy` class | 432-1677 | **1,245 lines** -- contains `load_data()` and `run()` |
| `main()` | 1682-1871 | CLI parsing + performance metrics |

### Key Architectural Problem: The God Method

`CopperGoldStrategy::run()` (lines 488-1666) is a **1,178-line method**. It contains:

- Date calendar construction
- Price extraction and validation
- Layer 1 signal computation (Cu/Gold ratio, ROC, MA crossover, Z-score, composite)
- Layer 2 regime classification (growth, inflation, liquidity)
- Layer 3 DXY filter
- Safe-haven override logic
- China filter
- BOJ intervention detection
- Correlation spike detection
- Size multiplier calculation
- P&L calculation
- Position-level stop loss
- Drawdown monitoring
- Rebalance trigger detection
- Full position sizing (two modes: notional-based and fixed)
- Position limits enforcement (per-instrument, per-asset-class, margin)
- Transaction cost deduction
- Signal struct population (duplicated twice: lines 1161-1195 for non-rebalance days, lines 1462-1498 for rebalance days)
- A 163-line diagnostic summary block (lines 1502-1662)

This method does everything. There is no separation between signal generation, risk management, execution simulation, and reporting.

### Class Design

There is exactly **one class**: `CopperGoldStrategy`. Its public interface consists of two methods:

- `load_data()` -- loads all CSV files into member maps
- `run()` -- does literally everything else

Private members are just data containers (12 `TimeSeries` / `FuturesSeries` maps) plus the params struct and data directory path.

---

## 3. Data Flow Architecture

```
CSV files on disk
     |
     v
load_futures() / load_macro()     Lines 64-137
     |
     v
std::map<int, OHLCVBar> / std::map<int, double>   (keyed by day_key = epoch_seconds / 86400)
     |
     v
run() builds date calendar from union of all futures dates   Lines 496-506
     |
     v
extract_close() / extract_macro() -- forward-fills to aligned vectors   Lines 512-524
     |
     v
Pre-compute derived series (ratio, ROC, MAs, z-scores, ATR, returns)   Lines 576-662
     |
     v
Main loop (i = 0..n): per-day signal generation + position sizing + P&L   Lines 714-1501
     |
     v
Post-loop diagnostics + performance metrics   Lines 1502-1871
     |
     v
stdout (no file output)
```

### Critical Observation: No CSV Output

The strategy generates a full `std::vector<DailySignal>` with ~25 fields per day, but **never writes it to a file**. All results go to stdout as debug prints. There is no trade log, no position history file, no equity curve export. Analyzing results requires re-running the backtest and parsing console output.

---

## 4. Dependencies

**External:** None. Zero third-party libraries.

**Standard library usage patterns:**

- `std::map<int, ...>` for time-indexed data (ordered by day_key) -- appropriate for time series with efficient `upper_bound()` lookups
- `std::unordered_map<std::string, ...>` for symbol-keyed lookups -- appropriate
- `std::vector<double>` for aligned numerical arrays -- appropriate but see performance concerns
- `std::istringstream` for CSV parsing -- functional but slow
- `std::mktime()` / `std::gmtime()` for date handling -- **problematic** (see section 5)

---

## 5. Code Quality Assessment

### 5.1 Naming Conventions and Consistency

**Mixed and inconsistent naming throughout:**

- Functions: `parse_date`, `date_from_int`, `ffill`, `ffill_fut_close`, `rolling_mean`, `avg_pairwise_corr` -- snake_case, reasonable
- Variables: `be_chg`, `rr_chg`, `rr_z_val`, `fbs_raw`, `hy_zscore` -- heavy abbreviation that hurts readability
- `jy` for Japanese Yen futures (line 532) but the symbol is `"6J"` everywhere else
- `dd_warn` / `dd_stop` for drawdown flags -- not immediately obvious
- `dxy_mom` vs `dxy_momentum` (field name) -- inconsistency between local variable and struct field
- Lambda names like `contracts_for` and `make_ret` are clear

**Verdict:** Naming is functional for a single-author research prototype but would not pass a team code review.

### 5.2 Error Handling

**Minimal and inconsistent:**

- CSV loading: `try { ... } catch (...) { continue; }` (lines 88-102, 134) -- silently drops malformed rows with no logging. A row with a corrupt price field would be silently skipped. The `catch(...)` is the most dangerous pattern possible -- it catches bad_alloc, logic errors, everything.
- File opening: prints `[WARN]` to stderr but does not abort (lines 67-69, 118-120). The strategy can proceed with empty data for non-critical symbols.
- `load_data()` only validates that HG and GC are non-empty (line 485). All other symbols can be entirely empty and the strategy will silently run with NaN-filled vectors.
- `parse_date()` returns -1 on failure (line 37), which is checked in callers, but -1 is also a valid day_key for dates before epoch. Technically, a date parsing error could be confused with a date in late 1969.
- No validation of CSV column count. A CSV with 3 columns instead of 6 would produce empty strings for missing fields, which `std::stod("")` would catch, but only via the blanket catch-all.
- Command-line argument parsing (lines 1689-1691): `std::stod(argv[2])` will throw on non-numeric input with no try/catch.

### 5.3 Memory Management

No raw pointers, no manual `new`/`delete` -- all memory is managed through STL containers. This is correct. However:

- **Excessive copying:** `rolling_mean()`, `rolling_std()`, `rolling_zscore()` all return `std::vector<double>` by value. While NRVO should apply, the pattern of computing `rolling_mean` of the entire time series just to use a single element per iteration is wasteful (see Performance section).
- The `VIX percentile` computation (lines 807-818) and `VIX 90th percentile` (lines 927-935) both create a temporary `std::vector<double>` and sort it -- **inside the main loop**, executed on every single day. This is O(n * w * log(w)) where n is ~4,000 days and w is 60.
- `DailySignal` contains an `std::unordered_map<std::string, double>` for `target_contracts` (line 368). Creating ~4,000 of these with 9 string keys each means ~36,000 string allocations plus hash table overhead for the output vector alone.

### 5.4 Hardcoded Values That Should Be Configurable

While `StrategyParams` captures many parameters, numerous values are hardcoded in the body:

| Value | Location | Description |
|-------|----------|-------------|
| `25000.0`, `100.0` | Line 582-583 | HG/GC contract multipliers for notional normalization |
| `252` | Lines 629, 787, 1589, 1754 | Trading days per year -- repeated in 4+ places |
| `0.10` | Line 855 | Inflation shock threshold (breakeven change) |
| `0.5` | Lines 857, 859 | Growth signal thresholds for regime classification |
| `65` | Line 643 | China CLI rolling average window (supposed to be 3 months) |
| `60` | Line 806 | VIX percentile lookback window |
| `59` | Lines 808, 928 | Off-by-one version of the VIX window |
| `0.015` | Line 939 | Safe-haven gold return threshold (1.5%) |
| `-0.015` | Line 939 | Safe-haven equity drop threshold (-1.5%) |
| `50`, `200` | Lines 639-640 | DXY moving average windows |
| `20` | Line 193 | ATR window default (also in params, but default arg) |
| `3` | Line 1119 | Regime change confirmation count |
| `100` | Line 1452 | Large position warning threshold |
| `0.5` | Line 544 | Unrealistic price move threshold (50%) |
| `86400` | Lines 40, 44, 1099 | Seconds per day -- repeated |
| `0.90` | Line 932 | VIX percentile level for safe-haven detection |
| `10000` | Line 1049 | Large daily P&L print threshold |
| `126` | Line 1431 (comment) | Debug print interval (not actually used) |
| `0.50` | Lines 970, 972, 978 | Various half-size multipliers |
| `0.25` | Line 981 | Liquidity crunch position reduction factor |

Several of these duplicate values that already exist in the strategy spec (e.g., the inflation threshold `0.10` at line 855 vs the spec's "1.0" suggesting a units mismatch -- this is actually flagged by the diagnostic at lines 1656-1659).

### 5.5 Code Duplication

**DailySignal population appears twice:**

The exact same ~35 lines of code that populate a `DailySignal` struct appear at:
1. Lines 1161-1195 (non-rebalance path)
2. Lines 1462-1498 (rebalance path)

These blocks are identical field-by-field. Any change to the signal struct requires updating both copies.

**VIX window sorting appears twice:**

1. Lines 807-818 (VIX percentile for liquidity score)
2. Lines 927-935 (VIX 90th percentile for safe-haven detection)

Both create a sorted temporary vector of the last 60 VIX values. Could be a single function.

**Position sizing logic (test mode vs full mode) is structurally duplicated:**

Lines 1230-1277 (full mode) and 1361-1405 (fixed mode) contain the same regime/tilt branching logic with different position calculation. The trade expression matrix is implemented twice.

### 5.6 Dead Code and Debug Artifacts

| Item | Lines | Issue |
|------|-------|-------|
| Hardcoded date debug print | 839-846 | `if (dates[i] >= parse_date("2014-11-01"))` -- date-specific debug logging baked into main loop |
| Static local variable | 877-880 | `static Regime last_debug_regime` -- debug regime tracker that does nothing (no print, just assignment) |
| Commented-out warning | 1453-1454 | Large position warning commented out with `//` |
| `all_positions_zero()` | 108-113 | Defined near the top, far from where it is used (line 1074, 1135, 1143) |
| Duplicate comment | 704-705 | Identical comment on two consecutive lines |
| Unused `tips_ts_` | 468, 1674 | Loaded but only used indirectly through `real_rate` computation; `tips_ts_` variable named but `breakeven_ts_` is used for the subtraction at line 612 -- wait, `treasury_ts_ - breakeven_ts_` is used, TIPS is loaded but `tips_ts_` is never accessed in `run()`. It is loaded at line 468 but the real rate at line 612 uses `treasury[i] - breakeven[i]`, not TIPS. **TIPS data is loaded and never used.** |
| `cny_usd_ts_` | 472, 1676 | Loaded at line 472, declared at line 1676, but **never extracted into a vector in `run()` and never used in any computation**. The China filter only uses `china_cli` (line 945). The CNY/USD component from the strategy spec is not implemented. |
| `last_equity_debug` | 710, 1057-1061 | Debug variable tracking equity jumps -- left in production code |
| `infl_shock_days` | 711, 874 | Counter only used for the diagnostic summary |
| Print statements everywhere | Throughout | ~30+ `std::cout` debug/info/sizing lines that would flood production output |

### 5.7 Static Variables Inside Member Function

Lines 1106-1107:
```cpp
static Regime pending_regime = Regime::NEUTRAL;
static int pending_regime_count = 0;
```

These are **static local variables inside a member function of a class**. If `run()` is called more than once on the same or different `CopperGoldStrategy` instance, these statics will retain state from the previous call. This is a latent bug. The same issue exists with `last_debug_regime` at line 877. These should be either member variables or local variables reset at the top of `run()`.

---

## 6. Performance Concerns

### 6.1 O(n^2) Rolling Statistics

`rolling_mean()` (lines 157-165) and `rolling_std()` (lines 167-178) both use a naive nested loop:

```cpp
for (int i = window - 1; i < (int)v.size(); ++i) {
    double sum = 0.0;
    for (int j = i - window + 1; j <= i; ++j) sum += v[j];
    out[i] = sum / window;
}
```

This is O(n * window) for each call. For n = 4,800 days and window = 120, that is ~576,000 additions per call. With ~10 calls to these functions, total is ~6M operations. Not a bottleneck at this scale, but indicates the author is not thinking about algorithmic complexity. An O(n) sliding window would be trivial.

### 6.2 Per-Day VIX Sorting (Redundant)

Lines 807-818 sort a 60-element vector on every iteration of the main loop to compute a percentile. This is done ~4,000 times. A rolling sorted structure (e.g., a multiset with sliding window) would reduce this from O(n * w * log(w)) to O(n * log(w)).

The same pattern repeats at lines 927-935 for VIX 90th percentile.

### 6.3 Per-Day ATR Recomputation for Stop Loss

Lines 1012-1029 compute a 20-day ATR for **every symbol** on **every day** by iterating over the `fut_[sym]` map with `find()` calls. This is O(n * 9_symbols * 20_days * log(map_size)) -- completely unnecessary since ATR could be pre-computed once before the loop, exactly as is done for `gc_atr` and `si_atr` at lines 646-647 (but only for GC and SI, not for all symbols).

### 6.4 String Operations in Hot Path

- `date_from_int()` (line 43-48) calls `gmtime()` and `strftime()` -- called every time a date is printed. Inside the main loop, dates are printed in debug blocks (lines 839, 878, 1078, 1129, 1286) -- these involve heap allocation for `std::string` construction.
- `ContractSpec::get()` (lines 302-306) does a hash map lookup by string on every call. Called multiple times per symbol per day in sizing and margin calculations.

### 6.5 `std::map` vs `std::vector` for Time Series

`FuturesSeries = std::map<int, OHLCVBar>` uses a red-black tree. For sequential iteration and random access by date, a sorted `std::vector<std::pair<int, OHLCVBar>>` with binary search would be more cache-friendly. This matters when `find()` is called inside the inner loop (line 1017).

### 6.6 Overall Assessment

None of these performance concerns matter for a 4,800-day backtest that runs in under a second. They would matter if:
- The strategy moves to tick-level data (millions of rows)
- The code is used in a parameter optimization loop (thousands of runs)
- Live trading requires sub-millisecond signal computation

---

## 7. Tech Debt Inventory (Priority-Ordered)

### P0 -- Critical (Would block production deployment)

| # | Issue | Lines | Impact |
|---|-------|-------|--------|
| 1 | **No build system** | N/A | Cannot reproduce builds, no compiler warnings enforced, no sanitizers |
| 2 | **1,178-line God method** (`run()`) | 488-1666 | Untestable, undebuggable, impossible to modify safely |
| 3 | **No unit tests** | N/A | Zero test coverage. Rolling stats, signal logic, sizing, stops -- all untested |
| 4 | **Static locals in member function** | 1106-1107, 877 | Latent statefulness bug -- second `run()` call produces wrong results |
| 5 | **No output file** | N/A | Results exist only as console spam. No trade log, no position history, no equity curve file |
| 6 | **`catch(...)` swallowing errors** | 102, 134 | Corrupt data silently dropped. A single bad byte in a CSV could silently alter backtest results |
| 7 | **Loaded-but-unused data** (`tips_ts_`, `cny_usd_ts_`) | 468, 472 | Strategy spec says use CNY/USD in China filter, but it is never wired in. Missing signal component |

### P1 -- High (Significant risk to correctness or maintainability)

| # | Issue | Lines | Impact |
|---|-------|-------|--------|
| 8 | **DailySignal population duplicated** | 1161-1195 vs 1462-1498 | Divergence risk on any change |
| 9 | **~40 hardcoded magic numbers** | Throughout | Cannot run parameter sweeps without recompiling |
| 10 | **Date handling via `mktime`/`gmtime`** | 33-48 | Timezone-dependent, not thread-safe (`gmtime` returns static pointer), will break on 32-bit systems in 2038 |
| 11 | **No data validation beyond basic NaN checks** | 539-562 | Only checks for 50% daily moves. No detection of stale data, zero prices, negative prices, or volume anomalies |
| 12 | **Debug prints in main loop** | 839-846, 864-871, 1049-1051, 1078-1084, 1129-1139, 1286-1297 | Production output is unusable -- hundreds of debug lines mixed with results |
| 13 | **Inflation threshold likely wrong** | 855 | Uses `0.10` (10 basis points) but spec says `1.0` (100bp). Diagnostic at line 1656-1658 even warns about this |
| 14 | **No term structure filter implemented** | N/A | Layer 4 of the strategy spec (backwardation/contango using `*_2nd.csv` files) is entirely missing from the code. Data files exist but are unused |
| 15 | **Incomplete China filter** | 943-948 | Spec defines a composite of 5 signals (CLI + PMI + credit + SHFE inventory + CNY/USD). Code only uses CLI. The other 4 data sources are either not loaded or loaded and unused |

### P2 -- Medium (Would cause pain in ongoing development)

| # | Issue | Lines | Impact |
|---|-------|-------|--------|
| 16 | **No configuration file support** | N/A | Parameters are compiled in. Any change requires recompilation |
| 17 | **Single-threaded design** | N/A | Cannot parallelize parameter sweeps or multi-strategy testing |
| 18 | **Transaction cost model oversimplified** | 310-315 | Assumes fixed costs regardless of market conditions, time of day, or market impact |
| 19 | **No roll logic** | N/A | Strategy spec describes futures roll rules (5 days before first notice), but the code uses pre-rolled continuous data with no roll date tracking or roll cost modeling |
| 20 | **`snprintf` for formatting** | 1440, 1638 | C-style formatting mixed with C++ streams |
| 21 | **Profit factor calculation uses initial equity** | 1787-1788 | `double pnl = r * daily_equity[0]` -- should use `daily_equity[i]` for accurate gross profit/loss attribution |
| 22 | **No SPX/NQ backfill integration for MES/MNQ** | N/A | Spec mentions using `spx_backfill.csv` and `NQ.csv` for the pre-2019 period when MES/MNQ did not exist. Code does not implement this -- MES and MNQ are NaN before 2019, producing zero equity exposure for 9 years |

### P3 -- Low (Cleanup items)

| # | Issue | Lines | Impact |
|---|-------|-------|--------|
| 23 | Duplicate comment | 704-705 | Copy-paste artifact |
| 24 | Empty lines and spacing inconsistency | 1044-1046, 1055 | Minor formatting noise |
| 25 | UTF-8 emoji characters in source | 1546, 1579, 1594, etc. | Diagnostic output uses checkmarks and crosses -- may not render in all terminals |
| 26 | `.gitignore` only excludes `.DS_Store` | N/A | Should exclude build artifacts, editor files, etc. |

---

## 8. Research-to-Production Gap Analysis

### What exists today

A single-file research prototype that:
- Reads CSV data
- Computes signals across 5 (partially implemented) layers
- Runs a daily-resolution backtest with position sizing and risk management
- Prints diagnostic output and performance metrics to stdout

### What a production trading system requires

#### 8.1 Modularity

The monolithic file must be decomposed into at minimum:

```
src/
  data/
    csv_loader.h / .cpp       # CSV parsing, data validation
    time_series.h              # TimeSeries, FuturesSeries, forward-fill
  signals/
    cu_gold_ratio.h / .cpp     # Layer 1: ratio computation, ROC, MA, Z-score
    regime_classifier.h / .cpp # Layer 2: growth/inflation/liquidity
    dxy_filter.h / .cpp        # Layer 3: USD filter
    term_structure.h / .cpp    # Layer 4: backwardation/contango (NOT YET IMPLEMENTED)
    china_filter.h / .cpp      # Layer 5: China demand composite
  risk/
    position_sizer.h / .cpp    # Notional sizing, limits, margin
    stop_loss.h / .cpp         # ATR stops, drawdown stops
  execution/
    cost_model.h / .cpp        # Transaction costs, roll costs, slippage
    order_generator.h / .cpp   # Target position -> order generation
  backtest/
    engine.h / .cpp            # Daily loop, P&L, equity tracking
    metrics.h / .cpp           # Sharpe, Sortino, drawdown, etc.
  config/
    params.h                   # StrategyParams, ContractSpec
    config_loader.h / .cpp     # YAML/JSON config file parsing
  main.cpp                     # CLI entry point
```

#### 8.2 Testing

**Zero tests exist.** Required:

- **Unit tests** for every rolling statistic function (known-input/known-output)
- **Unit tests** for signal logic (given a specific ratio history, verify composite signal)
- **Unit tests** for regime classifier (given growth/inflation/liquidity values, verify regime)
- **Unit tests** for position sizer (given regime + tilt + filters, verify contract counts)
- **Integration tests** with a small synthetic dataset to verify end-to-end P&L
- **Regression tests** that lock current backtest output to detect unintended changes
- **Property-based tests**: equity should never go negative, positions should respect limits, stops should fire

#### 8.3 Logging

Replace the ~30 `std::cout` debug prints with a proper logging framework (e.g., spdlog, or even a simple severity-level logger). Requirements:

- Configurable log levels (DEBUG, INFO, WARN, ERROR)
- Structured log format (timestamp, component, message)
- File output with rotation
- Separate log streams for signal diagnostics vs trade execution vs system health

#### 8.4 Monitoring and Observability

Production requires:

- Real-time position and P&L dashboard
- Alerting on: drawdown thresholds, unusual position sizes, data feed staleness, signal flips
- Heartbeat monitoring (is the strategy process alive?)
- Reconciliation: expected vs actual positions, expected vs actual fills

#### 8.5 Configuration Management

- All parameters in a YAML/JSON/TOML config file, not compiled in
- Support for parameter overrides via command line
- Config versioning (which config produced which backtest results?)
- Parameter validation at load time (e.g., `zscore_window > 0`, `leverage_target > 0`)

#### 8.6 Error Recovery

- What happens if a CSV file is truncated mid-row?
- What happens if the data feed goes stale (no new data for a day)?
- What happens if equity goes to zero or negative?
- What happens if a position size calculation produces NaN or infinity?
- What happens if the system crashes mid-rebalance -- can it resume?

None of these scenarios are handled.

#### 8.7 Data Validation

Current validation (lines 539-562) only checks for >50% daily moves in HG, GC, CL. A production system needs:

- Completeness checks: expected number of rows per day
- Staleness detection: last data timestamp vs current time
- Cross-validation: prices across correlated instruments should move coherently
- Outlier detection: prices beyond 3-sigma historical moves
- Holiday calendar awareness
- Data source reconciliation (multiple feeds)

#### 8.8 Output and Audit Trail

The strategy produces no persistent output. Production requires:

- Trade log (CSV/database): timestamp, symbol, direction, quantity, price, cost, reason
- Daily signal log: all signal components, regime, filters, sizes
- Equity curve file
- Position snapshot file (for reconciliation)
- Configuration used for each run

#### 8.9 Live Trading Integration

The code is pure backtest -- there is no:

- Market data feed adapter (the system only reads historical CSVs)
- Order management system interface
- Fill handling / execution reporting
- Position reconciliation with broker
- Intraday risk monitoring

---

## 9. Specific Bug Candidates

### 9.1 Date Parsing Timezone Sensitivity

`parse_date()` (line 39) uses `std::mktime()` which interprets the `std::tm` struct in **local time**. But `date_from_int()` (line 45) uses `std::gmtime()` which interprets in **UTC**. This mismatch means:

- If run in a timezone with a non-zero UTC offset, `parse_date("2024-01-15")` and `date_from_int(parse_date("2024-01-15"))` may produce different date strings.
- The day_key (epoch_seconds / 86400) will differ depending on the machine's timezone.

This is a correctness bug. Results are not reproducible across timezones.

### 9.2 Off-by-One in VIX Window

Line 808 uses `for (int k = i - 59; k <= i; ++k)` which iterates over 60 elements (indices i-59 through i inclusive). But the guard at line 806 is `if (i >= 60)`, which means the first computation happens at i=60 using indices 1..60 -- correct. However, lines 928-929 use the same `i - 59` pattern but the guard is `if (i >= 59)`, which would start at i=59 using indices 0..59. This inconsistency between the two VIX window computations means they cover slightly different ranges.

### 9.3 Stopped-Out Positions Still Contribute to P&L

Lines 987-1043 show that `stopped_out_today` is populated (line 1039) after the P&L has already been computed. The ATR stop logic sets `qty = 0.0` on line 1037, but this modifies the `positions` map **after** `daily_pnl` was already accumulated at line 1000. This means:

- The stop triggers based on current price
- P&L for the day includes the losing position's full-day return
- The position is then zeroed

This is actually correct behavior (you can't stop out retroactively), but the code structure makes it look accidental rather than intentional, and there is no comment explaining this.

### 9.4 Equity Goes Negative Without Guard

There is no check preventing equity from going negative. If a catastrophic drawdown occurs (which the drawdown stop at 15% should prevent), the position sizer divides by equity (line 1212: `equity * p_.leverage_target * w`). Negative equity would produce negative notional allocations, flipping all positions. The drawdown stop should prevent this, but there is no defensive guard.

### 9.5 HG Notional Normalization Unit Ambiguity

Line 582: `double cu_notional = hg[i] * 25000.0;`

The CSV data shows HG prices like `2.764` (dollars per pound, since CME quotes copper in cents/lb and the data appears to be in dollars/lb given the magnitude). The spec says: "Cu_notional = HG_price * 25000 / 100 (convert cents to dollars)". But the code multiplies by 25000 without dividing by 100. If HG prices in the CSV are already in dollars/lb (not cents), then the division by 100 is not needed. But the comment at line 580 says "convert cents to dollars" while the code does not actually divide by 100. This suggests either the comment is wrong or the code is wrong. Given HG prices ~2.76, if these are dollars/lb, then `2.76 * 25000 = 69,000` (contract notional in dollars) which is plausible. If these are cents/lb (276 cents), then `276 * 25000 = 6,900,000` which would be way too high. So the data is in dollars/lb and the comment is misleading, but the code appears correct.

---

## 10. Summary Verdict

**This is a research-grade single-author prototype.** It successfully implements a multi-layer macro trading strategy with signal generation, regime classification, position sizing, risk management, and performance evaluation -- all in a single self-contained file with zero dependencies.

For what it is (a backtesting exploration tool), it works. The architecture matches the strategy spec document reasonably well, with notable gaps (no term structure filter, incomplete China filter, no SPX/NQ backfill for MES/MNQ).

**It is not remotely production-ready.** The distance from here to a deployable trading system is substantial:

| Dimension | Current State | Production Requirement |
|-----------|--------------|----------------------|
| Modularity | Single 1,870-line file | 15+ files across 6+ modules |
| Testing | Zero tests | >100 unit + integration tests |
| Build system | None | CMake + CI/CD pipeline |
| Configuration | Compiled-in constants | External config files with validation |
| Output | Console spam | Structured log files + trade database |
| Error handling | `catch(...)` or absent | Comprehensive, with recovery strategies |
| Data validation | Minimal | Multi-layer validation pipeline |
| Live trading | Not possible | OMS integration, market data feeds, reconciliation |

**Estimated effort to production-ready:** 4-8 engineer-weeks for a senior C++ quant developer, assuming the strategy logic itself is validated and frozen.

---

*Review conducted against commit on main branch, 2026-02-24.*
