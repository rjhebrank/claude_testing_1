# Data Quality Issues: Copper-Gold Ratio Strategy

**Generated**: 2026-02-24
**Author**: Quant Data Quality Review
**Companion Document**: [`data-inventory.md`](data-inventory.md)

---

## Issue Summary Table

| # | Issue | Severity | Impact | Recommendation |
|---|-------|----------|--------|----------------|
| 1 | China CLI stale since 2023-12-01 | **CRITICAL** | China growth adjustment frozen for 26+ months; signal is dead weight | Source fresh data from OECD API or FRED `CHNLORSGPNOSTSAM` |
| 2 | Five macro files completely empty | **HIGH** | Planned China/SHFE signals never implemented; incomplete data pipeline | Populate from OECD, FRED, NBS China, SHFE; or archive |
| 3 | MES/MNQ only 6 years of history | **HIGH** | Equity index sleeve untradeable for 9 of 15 backtest years (2010-2019) | Acquire ES/NQ full-size contracts for backtesting; splice to micro for live |
| 4 | Futures vs. macro end-date mismatch | **MODERATE** | ~3-month gap where macro updates but futures do not (Nov 2025 vs. Feb 2026) | Refresh front-month futures data to match macro end dates |
| 5 | Dual SPX data sources with different characteristics | **LOW** | Potential confusion over which source is canonical for what purpose | Document ownership; standardize to one source per use case |

---

## Issue 1: Stale China Leading Indicator (CRITICAL)

### File
`data/raw/macro/china_leading_indicator.csv`

### Observation
The file contains 289 rows of monthly OECD Composite Leading Indicator data for China, spanning 2000-01-01 through **2023-12-01**. The last recorded value is **99.25388**.

```
2023-09-01,99.28123
2023-10-01,99.26818
2023-11-01,99.26003
2023-12-01,99.25388    <-- LAST VALUE
```

As of this review (2026-02-24), the data is **26 months stale**.

### Impact on Strategy
The strategy's `load_macro()` function loads this file and uses it for the China growth adjustment signal applied to copper positioning. Because the strategy uses forward-fill for missing dates, every trading day from January 2024 through present carries the same frozen value of 99.25388. This means:

- The China growth adjustment has been a **constant** for the entire 2024-2025 period -- it provides zero new information.
- Any backtest results from Jan 2024 onward reflect a strategy that effectively has its China adjustment **hard-coded**.
- In live trading, the signal would remain frozen indefinitely until the file is refreshed.
- The actual OECD CLI for China has moved meaningfully during this period (post-COVID recovery dynamics, property sector stress, stimulus cycles) -- none of which is captured.

### Also Notable
There is a suspicious data point at 2020-02-01 where the CLI drops to **85.39336** from 99.30965 the prior month, then jumps back to 99.89617 in March. This is a ~14-point single-month spike that looks like a data quality issue (possibly a COVID-related methodological revision later corrected by OECD). If the strategy computes month-over-month changes or z-scores on this series, that single outlier could distort signals for the surrounding lookback window.

### Recommendation
1. **Immediate**: Source updated OECD CLI data through one of:
   - OECD Data API: https://data.oecd.org/leadind/composite-leading-indicator-cli.htm (select China, monthly, amplitude-adjusted)
   - FRED series: `CHNLORSGPNOSTSAM` (OECD CLI: Normalised for China)
   - Python: `pandas_datareader.data.DataReader('CHNLORSGPNOSTSAM', 'fred')` or direct OECD SDMX API
2. **Validate** the Feb 2020 outlier (85.39) against the official OECD publication to determine if it is legitimate or a data error.
3. **Interim alternative**: If fresh CLI data cannot be sourced quickly, consider disabling the China adjustment entirely (set weight to zero) rather than running with a frozen signal. A frozen signal is worse than no signal -- it silently biases copper positioning without reflecting current conditions.

---

## Issue 2: Empty Macro Files (HIGH)

### Files Affected

| File | Column | Rows | Date Range | Granularity | Empty Data Rows |
|------|--------|------|------------|-------------|-----------------|
| `china_cli_alt.csv` | `china_cli_alt` | 193 | 2010-01-31 to 2025-12-31 | Monthly | 192 of 192 (100%) |
| `china_credit.csv` | `china_credit` | 193 | 2010-01-31 to 2025-12-31 | Monthly | 192 of 192 (100%) |
| `china_pmi.csv` | `china_pmi` | 194 | 2010-01-31 to 2026-01-31 | Monthly | 193 of 193 (100%) |
| `china_leading_indicator_update.csv` | `china_leading_indicator` | 193 | 2010-01-31 to 2025-12-31 | Monthly | 192 of 192 (100%) |
| `shfe_copper_inventory.csv` | `shfe_copper_inventory` | 829 | 2010-01-01 to 2026-01-30 | Weekly | 828 of 828 (100%) |

### Observation
All five files have properly formatted date scaffolding (correct headers, valid date sequences at appropriate frequencies) but **every single data row has an empty value field**. Example from `china_pmi.csv`:

```csv
date,china_pmi
2010-01-31,
2010-02-28,
2010-03-31,
...
2026-01-31,
```

These appear to be placeholder files where a data ingestion pipeline was scoped but never completed. A code audit confirmed that **no loading code in the strategy references these files** -- they are orphaned.

### Impact on Strategy
No direct impact on current strategy execution. The `load_macro()` function's empty-value guard (`val_s.empty() || val_s == "." || val_s == "NA"`) would skip every row if these files were loaded. However, these files represent **missing signals** that were clearly intended for the strategy:

- **China PMI**: Caixin/NBS Manufacturing PMI is one of the highest-signal macro indicators for copper demand. Its absence means the strategy lacks a real-time Chinese manufacturing activity signal.
- **China Credit Impulse**: Credit growth in China is a leading indicator for commodity demand (6-12 month lead). Without it, the strategy misses a key early-warning signal.
- **SHFE Copper Inventory**: Shanghai Futures Exchange warehouse copper stocks are a direct physical market indicator. Falling SHFE inventory = tighter physical market = bullish copper.
- **China CLI Alt / Update**: These appear to be alternate or updated versions of the stale `china_leading_indicator.csv`.

### Where to Source This Data

| File | Recommended Source | Details |
|------|-------------------|---------|
| `china_cli_alt.csv` | OECD SDMX API or FRED | Series `CHNLORSGPNOSTSAM` or `CHNLORSGPORIXOBSAM` |
| `china_credit.csv` | BIS credit statistics or Bloomberg | BIS total credit to non-financial sector (China); FRED series `QCNPAM770A` |
| `china_pmi.csv` | NBS China / Caixin via Macrobond or CEIC | Official NBS Manufacturing PMI (released 1st of month); Caixin PMI via IHS Markit |
| `china_leading_indicator_update.csv` | Same as Issue 1 (OECD CLI) | This file appears to be a planned replacement for the stale CLI |
| `shfe_copper_inventory.csv` | SHFE direct or Bloomberg `SHFCCOPD Index` | SHFE publishes weekly warehouse stocks every Friday; also available through LME/SHFE data vendors |

### Recommendation
1. **Short term**: Archive these five files to a `data/raw/macro/archive/` directory to reduce confusion. They contribute nothing and clutter the data directory.
2. **Medium term**: Prioritize populating `china_pmi.csv` and `shfe_copper_inventory.csv` -- these are the two highest-signal indicators for copper demand among the five and have well-established public sources.
3. **Design a data pipeline**: The fact that date scaffolding exists but values do not suggests someone planned an automated pull that was never implemented. Build a scheduled Python script (cron or GitHub Actions) that pulls these series monthly/weekly.

---

## Issue 3: MES/MNQ Short History (HIGH)

### Files
- `data/raw/futures/MES.csv` -- Micro E-mini S&P 500
- `data/raw/futures/MNQ.csv` -- Micro E-mini Nasdaq-100

### Observation
Both contracts launched on **2019-05-05** (CME Micro E-mini launch date). The files confirm this:

```
MES.csv:
  First row:  2019-05-05, open=2925.75, close=2893.75, volume=787
  Last row:   2025-11-12, open=6871.50, close=6858.00, volume=1,141,978
  Total rows: 2,034

MNQ.csv:
  First row:  2019-05-05, open=7748.75, close=7709.50, volume=188
  Last row:   2025-11-12, open=25650.50, close=25540.50, volume=1,782,274
  Total rows: 2,034
```

Both files cover approximately **6 years and 6 months** of history.

### Impact on Strategy
The strategy backtests from approximately 2010-06-07 (when most futures data begins). For the equity index sleeve:

- **2010-06-07 to 2019-05-04** (roughly 9 years): MES and MNQ have no data. The strategy either skips the equity sleeve entirely during this period or encounters NaN values.
- **2019-05-05 to 2025-11-12** (roughly 6.5 years): Normal operation.

This means:
- The equity index sleeve contributes to backtest P&L for only **42% of the total backtest window**.
- Any portfolio-level metrics (Sharpe, max drawdown, correlation structure) are computed over a period where the equity sleeve was absent for the majority of the time.
- The strategy's behavior during the 2010-2012 European debt crisis, 2015 China devaluation, and 2018 vol shock is tested **without** the equity leg.
- The early-history low volumes (787 contracts on launch day for MES; 188 for MNQ) also make the first few weeks of data unreliable.

### Available Alternatives in the Dataset
The dataset already contains `NQ.csv` (full-size E-mini Nasdaq-100) with data from **2010-01-04 to 2026-02-05** (4,058 rows, business-day only). There is no `ES.csv` in the dataset but `spx_backfill.csv` contains S&P 500 index OHLCV from **2010-01-04 to 2026-02-05** (4,049 rows).

### Recommendation
1. **For backtesting**: Acquire full-size ES (E-mini S&P 500) continuous contract data back to 2010. The existing `NQ.csv` already covers Nasdaq. These full-size contracts have identical price levels to their micro counterparts (MES tracks ES point-for-point; MNQ tracks NQ).
2. **For live trading**: Continue using MES/MNQ due to their smaller notional value ($5/point for MES vs $50/point for ES), which allows finer position sizing.
3. **Splicing approach**: Use ES/NQ data for the 2010-2019 period and MES/MNQ from 2019 onward. No price adjustment is needed since micros track the same index; only volume and contract multiplier differ.
4. **Interim workaround**: Use `NQ.csv` (already in dataset) to replace MNQ for backtesting. Use `spx_backfill.csv` index data as a proxy for MES/ES with appropriate contract multiplier logic.

---

## Issue 4: End-Date Mismatches (MODERATE)

### Observation
The dataset has two distinct populations with different end dates:

**Population A -- Front-month futures (strategy-consumed)**: End around **2025-11-12**
| File | Last Date |
|------|-----------|
| HG.csv | 2025-11-12 |
| GC.csv | 2025-11-12 |
| CL.csv | 2025-11-12 |
| SI.csv | 2025-11-12 |
| ZN.csv | 2025-11-12 |
| UB.csv | 2025-11-12 |
| 6J.csv | 2025-11-12 |
| MES.csv | 2025-11-12 |
| MNQ.csv | 2025-11-12 |

**Population B -- Second-month futures, NQ, spx_backfill**: End around **2026-02-05**
| File | Last Date |
|------|-----------|
| NQ.csv | 2026-02-05 |
| spx_backfill.csv | 2026-02-05 |
| HG_2nd.csv | 2026-02-05 |
| GC_2nd.csv | 2026-02-05 |
| (all other _2nd files) | 2026-02-05 |

**Population C -- Macro data (strategy-consumed)**: End between **2026-01-28 and 2026-02-03**
| File | Last Date |
|------|-----------|
| dxy.csv | 2026-01-30 |
| vix.csv | 2026-02-02 |
| high_yield_spread.csv | 2026-02-02 |
| breakeven_10y.csv | 2026-02-03 |
| treasury_10y.csv | 2026-02-02 |
| tips_10y.csv | 2026-02-02 |
| spx.csv | 2026-02-03 |
| fed_balance_sheet.csv | 2026-01-28 |
| china_leading_indicator.csv | 2023-12-01 |
| cny_usd.csv | 2026-02-03 |

### Impact

The gap between Population A (futures, ending Nov 2025) and Population C (macro, ending Jan-Feb 2026) is approximately **2.5-3 months**. This means:

- If the strategy is run to the end of available data, macro signals update through early Feb 2026 but there are no futures prices to trade against after Nov 12, 2025.
- The forward-fill logic would propagate the Nov 12 futures close for 3 months of "trading" -- generating signals and paper positions against a stale price.
- This also means the most recent ~3 months of macro data cannot be validated against actual market outcomes.
- The two data populations were likely sourced from different vendors or at different times (the _2nd files and NQ appear to be from a more recent pull).

### Recommendation
1. Refresh all front-month futures files to at least 2026-02-05 to match the macro data end dates.
2. Ideally, establish a single data refresh date and update everything simultaneously to avoid future drift.
3. Add a data staleness check at strategy startup that warns if any consumed file's end date is more than 7 days behind the most recent file.

---

## Issue 5: Dual SPX Data Sources (LOW)

### Files
1. **`data/raw/macro/spx.csv`** -- Used by strategy (loaded via `load_macro()`)
   - Schema: `date,spx` (single close column)
   - Range: 1928-01-03 to 2026-02-03 (25,423 rows)
   - Precision: High-precision floats (e.g., `6978.029390550557`)
   - Includes weekend entries (~781 from pre-1952 Saturday trading)
   - Granularity: Daily (calendar-day in early decades, business-day in modern era)

2. **`data/raw/futures/spx_backfill.csv`** -- Not used by strategy
   - Schema: `date,open,high,low,close,volume` (full OHLCV)
   - Range: 2010-01-04 to 2026-02-05 (4,049 rows)
   - Precision: Standard 2-decimal (e.g., `6939.03`)
   - Business-day only (no weekends)
   - Includes composite exchange volume (e.g., `1399691253.0`)

### Comparison for Overlapping Period

For 2026-01-30:
- `spx.csv`: close = 6939.029520163502
- `spx_backfill.csv`: close = 6939.03

The values agree to 2 decimal places. The high-precision floats in `spx.csv` suggest it was derived from a computed or interpolated source (possibly total return calculations or adjusted for dividends), while `spx_backfill.csv` appears to be raw exchange data.

### Impact on Strategy
The strategy loads `spx.csv` for its growth signal (SPX momentum). The presence of a second SPX-like file in the futures directory creates potential confusion:

- A future developer might accidentally load `spx_backfill.csv` thinking it is the canonical SPX source, introducing a subtle schema difference (OHLCV vs. close-only).
- If the strategy ever needed OHLCV data for SPX (e.g., for intraday range calculations or volume analysis), the backfill file would be the correct source, but this is not documented.
- The `spx_backfill.csv` file ends 2 days later (2026-02-05 vs 2026-02-03) and uses standard precision, making it arguably the cleaner source for the overlap period.

### Recommendation
1. **Document clearly** in a data manifest which file is used where: `spx.csv` is the macro signal source (growth momentum), `spx_backfill.csv` is a OHLCV reference dataset.
2. **Consider consolidating**: If the strategy only needs close prices, and `spx_backfill.csv` covers the backtest period (2010+), it could replace `spx.csv` for the relevant window. The deep history (1928-2009) in `spx.csv` is not needed by the strategy.
3. **Rename for clarity**: `spx_backfill.csv` is an ambiguous name. Rename to `SPX_INDEX_OHLCV.csv` or move to `data/raw/macro/` with a clear designation.

---

## Appendix: Complete End-Date Audit (Strategy-Consumed Files Only)

| File | Last Date | Days Behind Latest (2026-02-05) | Status |
|------|-----------|----------------------------------|--------|
| china_leading_indicator.csv | 2023-12-01 | ~797 days | **STALE** |
| HG.csv | 2025-11-12 | ~86 days | Behind |
| GC.csv | 2025-11-12 | ~86 days | Behind |
| CL.csv | 2025-11-12 | ~86 days | Behind |
| SI.csv | 2025-11-12 | ~86 days | Behind |
| ZN.csv | 2025-11-12 | ~86 days | Behind |
| UB.csv | 2025-11-12 | ~86 days | Behind |
| 6J.csv | 2025-11-12 | ~86 days | Behind |
| MES.csv | 2025-11-12 | ~86 days | Behind |
| MNQ.csv | 2025-11-12 | ~86 days | Behind |
| fed_balance_sheet.csv | 2026-01-28 | ~8 days | OK |
| dxy.csv | 2026-01-30 | ~6 days | OK |
| vix.csv | 2026-02-02 | ~3 days | OK |
| high_yield_spread.csv | 2026-02-02 | ~3 days | OK |
| treasury_10y.csv | 2026-02-02 | ~3 days | OK |
| tips_10y.csv | 2026-02-02 | ~3 days | OK |
| spx.csv | 2026-02-03 | ~2 days | OK |
| breakeven_10y.csv | 2026-02-03 | ~2 days | OK |
| cny_usd.csv | 2026-02-03 | ~2 days | OK |

---

## Priority Action Items

1. **P0 (Before next backtest run)**: Refresh `china_leading_indicator.csv` from OECD/FRED. Validate the Feb 2020 outlier.
2. **P0 (Before next backtest run)**: Refresh all 9 front-month futures files to at least 2026-02-05.
3. **P1 (Before trusting equity sleeve results)**: Acquire ES continuous contract data (2010-2019) to extend equity index coverage, or use NQ.csv + spx_backfill.csv as proxies.
4. **P2 (Data pipeline buildout)**: Populate `china_pmi.csv` and `shfe_copper_inventory.csv` with real data from NBS/SHFE sources.
5. **P3 (Housekeeping)**: Archive the 5 empty macro files and 26 unused futures files. Document the dual SPX sources.
