# Data Inventory: Copper-Gold Ratio Economic Regime Strategy

**Generated**: 2026-02-24
**Project**: `copper_gold_strategy.cpp` v2.0
**Data Root**: `data/raw/`

---

## Executive Summary

The project contains **57 CSV files** across two directories:
- `data/raw/futures/` -- 43 files (futures continuous contracts and 2nd-month rolls)
- `data/raw/macro/` -- 15 files (macroeconomic indicators)

The strategy (`copper_gold_strategy.cpp`) actively loads **9 futures** and **10 macro** datasets. The remaining **34 futures** and **5 macro** files are present but unused by the current strategy code. Several critical data quality issues are flagged below.

---

## Summary Table: All Datasets

### Futures Data (`data/raw/futures/`)

| Filename | Description | Start Date | End Date | Rows | Granularity | Weekends? | Used by Strategy? |
|----------|-------------|------------|----------|------|-------------|-----------|-------------------|
| `HG.csv` | COMEX Copper front month ($/lb) | 2010-06-07 | 2025-11-12 | 4,781 | Daily | Yes (782) | **YES** |
| `GC.csv` | COMEX Gold front month ($/oz) | 2010-06-07 | 2025-11-12 | 4,765 | Daily | Yes | **YES** |
| `CL.csv` | NYMEX WTI Crude Oil front month ($/bbl) | 2010-06-07 | 2025-11-12 | 4,788 | Daily | Yes | **YES** |
| `SI.csv` | COMEX Silver front month ($/oz) | 2010-06-07 | 2025-11-12 | 4,741 | Daily | Yes | **YES** |
| `ZN.csv` | CBOT 10-Year T-Note front month | 2010-06-07 | 2025-11-12 | 4,792 | Daily | Yes | **YES** |
| `UB.csv` | CBOT Ultra Bond front month | 2010-06-07 | 2025-11-12 | 4,746 | Daily | Yes | **YES** |
| `6J.csv` | CME Japanese Yen front month | 2010-06-07 | 2025-11-12 | 4,788 | Daily | Yes | **YES** |
| `MES.csv` | Micro E-mini S&P 500 | 2019-05-05 | 2025-11-12 | 2,034 | Daily | Yes | **YES** |
| `MNQ.csv` | Micro E-mini Nasdaq-100 | 2019-05-05 | 2025-11-12 | 2,034 | Daily | Yes | **YES** |
| `6A.csv` | CME Australian Dollar | 2010-06-07 | 2025-11-12 | 4,787 | Daily | Yes | No |
| `6B.csv` | CME British Pound | 2010-06-07 | 2025-11-12 | 4,788 | Daily | Yes | No |
| `6C.csv` | CME Canadian Dollar | 2010-06-07 | 2025-11-12 | 4,784 | Daily | Yes | No |
| `6E.csv` | CME Euro FX | 2010-06-07 | 2025-11-12 | 4,788 | Daily | Yes | No |
| `6L.csv` | CME Brazilian Real | 2010-06-14 | 2025-11-12 | 4,138 | Daily | Yes | No |
| `6M.csv` | CME Mexican Peso | 2010-06-07 | 2025-11-12 | 4,747 | Daily | Yes | No |
| `6N.csv` | CME New Zealand Dollar | 2010-06-07 | 2025-11-12 | 4,782 | Daily | Yes | No |
| `6S.csv` | CME Swiss Franc | 2010-06-07 | 2025-11-12 | 4,780 | Daily | Yes | No |
| `GF.csv` | CME Feeder Cattle | 2010-06-07 | 2025-11-12 | 3,886 | Daily | Yes | No |
| `HE.csv` | CME Lean Hogs | 2010-06-07 | 2025-11-12 | 3,883 | Daily | Yes | No |
| `HO.csv` | NYMEX Heating Oil | 2010-06-07 | 2025-11-12 | 4,792 | Daily | Yes | No |
| `KE.csv` | KCBT Hard Red Winter Wheat | 2013-12-16 | 2025-11-12 | 2,999 | Daily | Yes | No |
| `LE.csv` | CME Live Cattle | 2010-06-07 | 2025-11-12 | 3,882 | Daily | Yes | No |
| `M2K.csv` | Micro E-mini Russell 2000 | 2019-05-05 | 2025-11-12 | 2,034 | Daily | Yes | No |
| `MYM.csv` | Micro E-mini Dow | 2019-05-05 | 2025-11-12 | 2,033 | Daily | Yes | No |
| `NG.csv` | NYMEX Natural Gas | 2010-06-07 | 2025-11-12 | 4,791 | Daily | Yes | No |
| `NQ.csv` | E-mini Nasdaq-100 (extended) | 2010-01-04 | 2026-02-05 | 4,058 | Daily (biz) | No | No |
| `PL.csv` | NYMEX Platinum | 2010-06-07 | 2025-11-12 | 4,767 | Daily | Yes | No |
| `RB.csv` | NYMEX RBOB Gasoline | 2010-06-07 | 2025-11-12 | 4,792 | Daily | Yes | No |
| `ZC.csv` | CBOT Corn | 2010-06-07 | 2025-11-12 | 3,983 | Daily | Yes | No |
| `ZF.csv` | CBOT 5-Year T-Note | 2010-06-07 | 2025-11-12 | 4,788 | Daily | Yes | No |
| `ZL.csv` | CBOT Soybean Oil | 2010-06-07 | 2025-11-12 | 3,997 | Daily | Yes | No |
| `ZM.csv` | CBOT Soybean Meal | 2010-06-07 | 2025-11-12 | 3,996 | Daily | Yes | No |
| `ZR.csv` | CBOT Rough Rice | 2010-06-07 | 2025-11-12 | 3,987 | Daily | Yes | No |
| `ZS.csv` | CBOT Soybeans | 2010-06-07 | 2025-11-12 | 3,982 | Daily | Yes | No |
| `ZT.csv` | CBOT 2-Year T-Note | 2010-06-07 | 2025-11-12 | 4,790 | Daily | Yes | No |
| `ZW.csv` | CBOT Chicago Wheat | 2010-06-07 | 2025-11-12 | 3,997 | Daily | Yes | No |
| `CL_2nd.csv` | WTI Crude 2nd month roll | 2010-01-04 | 2026-02-05 | 4,055 | Daily (biz) | No | No |
| `GC_2nd.csv` | Gold 2nd month roll | 2010-01-04 | 2026-02-05 | 4,055 | Daily (biz) | No | No |
| `HG_2nd.csv` | Copper 2nd month roll | 2010-01-04 | 2026-02-05 | 4,056 | Daily (biz) | No | No |
| `SI_2nd.csv` | Silver 2nd month roll | 2010-01-04 | 2026-02-05 | 4,055 | Daily (biz) | No | No |
| `ZB_2nd.csv` | 30-Year T-Bond 2nd month | 2010-01-05 | 2026-02-05 | 4,118 | Daily (biz) | No | No |
| `ZN_2nd.csv` | 10-Year T-Note 2nd month | 2010-01-04 | 2026-02-05 | 4,059 | Daily (biz) | No | No |
| `spx_backfill.csv` | S&P 500 index OHLCV (backfill) | 2010-01-04 | 2026-02-05 | 4,049 | Daily (biz) | No | No |

### Macro Data (`data/raw/macro/`)

| Filename | Description | Start Date | End Date | Rows | Granularity | Used by Strategy? |
|----------|-------------|------------|----------|------|-------------|-------------------|
| `dxy.csv` | US Dollar Index (DXY) | 2006-01-02 | 2026-01-30 | 5,241 | Daily (biz) | **YES** |
| `vix.csv` | CBOE VIX Volatility Index | 1990-01-02 | 2026-02-02 | 9,416 | Daily (biz) | **YES** |
| `high_yield_spread.csv` | US HY Corporate Bond Spread (bps) | 1996-12-31 | 2026-02-02 | 7,690 | Daily (biz) | **YES** |
| `breakeven_10y.csv` | 10Y Breakeven Inflation Rate (%) | 2003-01-02 | 2026-02-03 | 6,025 | Daily (biz) | **YES** |
| `treasury_10y.csv` | 10Y US Treasury Yield (%) | 1962-01-02 | 2026-02-02 | 16,721 | Daily (biz) | **YES** |
| `tips_10y.csv` | 10Y TIPS Real Yield (%) | 2003-01-02 | 2026-02-02 | 6,024 | Daily (biz) | **YES** |
| `spx.csv` | S&P 500 Index (close) | 1928-01-03 | 2026-02-03 | 25,423 | Daily | **YES** |
| `fed_balance_sheet.csv` | Fed Total Assets ($M) | 2003-01-01 | 2026-01-28 | 1,206 | Weekly | **YES** |
| `china_leading_indicator.csv` | OECD China CLI | 2000-01-01 | 2023-12-01 | 289 | Monthly | **YES** |
| `cny_usd.csv` | CNY/USD Exchange Rate | 1981-01-02 | 2026-02-03 | 16,470 | Daily (cal) | **YES** |
| `china_cli_alt.csv` | China CLI Alternate (EMPTY) | 2010-01-31 | 2025-12-31 | 193 | Monthly | No |
| `china_credit.csv` | China Credit Impulse (EMPTY) | 2010-01-31 | 2025-12-31 | 193 | Monthly | No |
| `china_pmi.csv` | China Manufacturing PMI (EMPTY) | 2010-01-31 | 2026-01-31 | 194 | Monthly | No |
| `china_leading_indicator_update.csv` | China CLI Update (EMPTY) | 2010-01-31 | 2025-12-31 | 193 | Monthly | No |
| `shfe_copper_inventory.csv` | SHFE Copper Warehouse Stocks (EMPTY) | 2010-01-01 | 2026-01-30 | 829 | Weekly | No |

---

## Detailed Dataset Profiles

### Futures Data (Strategy-Consumed)

All 9 strategy-consumed futures files share the same schema:

```
date,open,high,low,close,volume
```

- **Format**: YYYY-MM-DD, floating point OHLCV
- **Roll method**: Continuous front-month (likely unadjusted, given price levels)
- **Source**: Appears to be CME Group / exchange data

#### HG.csv -- COMEX Copper
- **Units**: Dollars per pound (e.g., 2.764 in 2010, 5.085 in 2025)
- **Contract**: 25,000 lbs, tick = $0.0005, tick value = $12.50
- **Role**: Primary signal -- numerator of Copper/Gold ratio
- **Note**: Includes weekend bars with low volume (~100-500 contracts)

#### GC.csv -- COMEX Gold
- **Units**: Dollars per troy ounce (e.g., 1241.2 in 2010, 4195.6 in 2025)
- **Contract**: 100 troy oz, tick = $0.10, tick value = $10.00
- **Role**: Primary signal -- denominator of Copper/Gold ratio

#### CL.csv -- NYMEX WTI Crude
- **Units**: Dollars per barrel (e.g., 70.99 in 2010, 58.20 in 2025)
- **Contract**: 1,000 barrels
- **Role**: Commodity sleeve position

#### SI.csv -- COMEX Silver
- **Units**: Dollars per troy ounce (e.g., 18.14 in 2010, 53.17 in 2025)
- **Contract**: 5,000 troy oz, tick = $0.005, tick value = $25.00
- **Role**: Commodity sleeve position

#### ZN.csv -- CBOT 10-Year T-Note
- **Units**: Points and 32nds (e.g., 112.828125 = 112-26/32)
- **Contract**: $100,000 face, tick = 1/64, tick value = $15.625
- **Role**: Fixed income sleeve

#### UB.csv -- CBOT Ultra Bond
- **Units**: Points and 32nds (e.g., 121.5625 = 121-18/32)
- **Contract**: $100,000 face, tick = 1/32, tick value = $31.25
- **Role**: Fixed income sleeve

#### 6J.csv -- CME Japanese Yen
- **Units**: USD per JPY (e.g., 0.006561 = ~152.4 JPY/USD)
- **Contract**: 12,500,000 JPY, tick = $0.000001, tick value = $12.50
- **Role**: FX sleeve, BOJ intervention detection

#### MES.csv -- Micro E-mini S&P 500
- **Units**: Index points (e.g., 6765.25)
- **Contract**: $5 x index, tick = 0.25, tick value = $1.25
- **Role**: Equity index sleeve
- **History**: Starts 2019-05-05 (contract launch) -- only ~6 years of history

#### MNQ.csv -- Micro E-mini Nasdaq-100
- **Units**: Index points (e.g., 25316.75)
- **Contract**: $2 x index, tick = 0.25, tick value = $0.50
- **Role**: Equity index sleeve
- **History**: Starts 2019-05-05 (contract launch) -- only ~6 years of history

### Futures Data (Available but Unused)

#### Second-Month Contracts (*_2nd.csv)
Six files (`CL_2nd`, `GC_2nd`, `HG_2nd`, `SI_2nd`, `ZB_2nd`, `ZN_2nd`) contain second-month continuous contract data. These are business-day only (no weekends), start from 2010-01-04, and extend to 2026-02-05. They are not loaded by the strategy.

**CRITICAL**: `HG_2nd.csv` uses **cents per pound** (338.0 in 2010, 587.8 in 2026) while `HG.csv` uses **dollars per pound** (2.764 in 2010). This is a 100x unit mismatch -- if these files are ever joined for term structure or roll analysis, the units must be converted first.

#### Additional FX Futures (6A, 6B, 6C, 6E, 6L, 6M, 6N, 6S)
Eight additional CME FX futures not used by the strategy. Same schema and date range as strategy-consumed files.

#### Agriculture (GF, HE, KE, LE, ZC, ZL, ZM, ZR, ZS, ZW)
Ten agricultural futures. Same schema. `KE.csv` starts later (2013-12-16).

#### Energy (HO, NG, RB)
Three additional energy contracts not consumed by the strategy.

#### Other (M2K, MYM, NQ, PL, spx_backfill)
- `NQ.csv`: Full-size Nasdaq futures (2010-2026), business-day only, extends to 2026-02-05. Different date range than the front-month files.
- `spx_backfill.csv`: S&P 500 index OHLCV (not futures), business-day only, extends to 2026-02-05. Volume appears to be composite exchange volume.
- `M2K.csv`, `MYM.csv`: Micro Russell 2000 and Micro Dow, started 2019-05.
- `PL.csv`: Platinum futures.

### Macro Data (Strategy-Consumed)

#### dxy.csv -- US Dollar Index
- **Column**: `dxy`
- **Granularity**: Business-day
- **Role**: DXY trend/momentum filter for gold short suppression and regime confirmation
- **Note**: Ends 2026-01-30

#### vix.csv -- CBOE VIX
- **Column**: `vix`
- **Granularity**: Business-day
- **Role**: Liquidity score component (VIX percentile over 60d)
- **Note**: Deep history back to 1990

#### high_yield_spread.csv -- HY Spread
- **Column**: `high_yield_spread`
- **Granularity**: Business-day (some holidays with empty values, e.g., 1997-01-01)
- **Role**: Liquidity score component (z-score)
- **Note**: Contains ~99 weekend entries near series start; occasional empty values on holidays

#### breakeven_10y.csv -- 10Y Breakeven Inflation
- **Column**: `breakeven_10y`
- **Granularity**: Business-day
- **Role**: Inflation signal for regime detection (ROC-based)
- **Note**: Starts 2003

#### treasury_10y.csv -- 10Y Treasury Yield
- **Column**: `treasury_10y`
- **Granularity**: Business-day (calendar-day in early years)
- **Role**: Real rate computation (Treasury - TIPS), regime classification
- **Note**: Very deep history (1962), though strategy only needs overlap with TIPS from 2003

#### tips_10y.csv -- 10Y TIPS Yield
- **Column**: `tips_10y`
- **Granularity**: Business-day
- **Role**: Real rate computation (Treasury - TIPS)
- **Note**: Starts 2003

#### spx.csv -- S&P 500 Index
- **Column**: `spx`
- **Granularity**: Business-day (with ~781 weekend entries, likely from pre-1950s Saturday trading)
- **Role**: Growth signal (SPX momentum), correlation metric
- **Note**: Extremely deep history (1928). Float precision values (e.g., 6978.029390550557) suggest computed/derived data rather than raw exchange

#### fed_balance_sheet.csv -- Federal Reserve Total Assets
- **Column**: `fed_balance_sheet`
- **Granularity**: Weekly (Wednesdays)
- **Role**: Liquidity score component (YoY growth)
- **Units**: Millions of dollars (e.g., 6,587,568 = $6.59 trillion)

#### china_leading_indicator.csv -- OECD China CLI
- **Column**: `china_leading_indicator`
- **Granularity**: Monthly (1st of month)
- **Role**: China growth adjustment for copper positioning
- **CRITICAL**: Data ends 2023-12-01. Over 2 years stale. Strategy's forward-fill will use Dec 2023 value for all subsequent dates.

#### cny_usd.csv -- CNY/USD Exchange Rate
- **Column**: `cny_usd`
- **Granularity**: Calendar-day (includes weekends with forward-filled values)
- **Role**: China adjustment factor
- **Note**: 4,706 weekend entries out of 16,470 total (~29%). History back to 1981.

### Macro Data (Available but Unused -- All Empty)

These 5 files have correct date scaffolding but **zero actual data values** (every row has an empty value field after the comma):

| File | Rows | Date Range | Granularity | Notes |
|------|------|------------|-------------|-------|
| `china_cli_alt.csv` | 193 | 2010-01 to 2025-12 | Monthly | 192/192 data rows empty |
| `china_credit.csv` | 193 | 2010-01 to 2025-12 | Monthly | 192/192 data rows empty |
| `china_pmi.csv` | 194 | 2010-01 to 2026-01 | Monthly | 193/193 data rows empty |
| `china_leading_indicator_update.csv` | 193 | 2010-01 to 2025-12 | Monthly | 192/192 data rows empty |
| `shfe_copper_inventory.csv` | 829 | 2010-01 to 2026-01 | Weekly | 828/828 data rows empty |

These appear to be placeholder files where data ingestion was planned but never completed. The `load_macro()` function in the strategy gracefully skips empty values (`val_s.empty() || val_s == "." || val_s == "NA"`), so these would not cause errors if loaded, but would contribute no signal.

---

## Data Quality Assessment

### CRITICAL Issues

1. **China Leading Indicator is 2+ years stale** (`china_leading_indicator.csv` ends 2023-12-01). The strategy loads this file and uses it for the China growth adjustment signal. The forward-fill logic means every date after Dec 2023 uses the same frozen value (99.25388). This signal is effectively dead -- it provides no information for the entire 2024-2025 backtest period and would be meaningless in live trading.

2. **HG_2nd.csv unit mismatch**: Copper 2nd month contract is priced in cents/lb (338-600) while front month `HG.csv` is in dollars/lb (2.76-5.08). A 100x conversion factor is required before any cross-file analysis (term structure, roll yield, etc.).

3. **Five China/SHFE macro files are completely empty**: `china_cli_alt.csv`, `china_credit.csv`, `china_pmi.csv`, `china_leading_indicator_update.csv`, and `shfe_copper_inventory.csv` contain date scaffolding with zero data values. These represent a failed or incomplete data pipeline.

4. **MES and MNQ have only ~6 years of history** (from May 2019 contract launch). The strategy backtests from 2010 but these contracts did not exist before 2019. The strategy presumably has 9 years of NaN for these symbols, meaning the equity index sleeve was untradeable for more than half the backtest period.

### MODERATE Issues

5. **Weekend entries in front-month futures data**: The 35 front-month files (everything except `_2nd`, `NQ`, `spx_backfill`) include Saturday and Sunday bars. GC.csv has 782 weekend rows out of 4,764 data rows (~16%). Weekend bars have extremely low volume (often <1,000 contracts, sometimes single digits). The strategy's `load_futures()` function does not filter these out. This inflates bar counts and could distort rolling calculations (e.g., a 20-day rolling window is actually ~14 business days).

6. **Two distinct data populations with different end dates**:
   - Front-month futures + some macro: end around 2025-11-12
   - `_2nd` files, `NQ`, `spx_backfill`, most macro: end around 2026-02-03 to 2026-02-05
   - This means a ~3 month gap where macro signals update but futures prices do not, if the strategy were run to present day.

7. **CNY/USD includes calendar-day data**: 4,706 weekend entries (29% of rows) with forward-filled weekend values. Not a functional issue (the strategy's forward-fill handles it), but inflates the dataset size and differs from other macro series which are business-day only.

8. **SPX macro file has weekend entries**: 781 weekend rows, likely from historical Saturday trading sessions (pre-1952). Not a problem for the backtest period (2010+) but the deep history introduces format inconsistency.

9. **High yield spread has occasional empty values on holidays** (e.g., 1997-01-01). The `load_macro()` function skips these gracefully.

### MINOR Issues

10. **Inconsistent start dates across futures**: Most start 2010-06-07 but `KE.csv` starts 2013-12-16, micro contracts start 2019-05-05, and `_2nd` files start 2010-01-04. Not a problem for strategy-consumed files (which all start 2010-06-07 or later), but worth noting for universe expansion.

11. **Volume field precision differs**: Front-month files have integer volumes while `_2nd` files and `NQ` have float volumes (e.g., `762923.0`). The strategy parses both correctly via `std::stod()`.

12. **Macro file `spx.csv` uses high-precision floats** (e.g., `6978.029390550557`) suggesting a computed/interpolated source rather than raw exchange data. The `spx_backfill.csv` in futures uses standard 2-decimal pricing. Two different SPX sources exist with different characteristics.

---

## Strategy Data Dependency Map

```
copper_gold_strategy.cpp
|
+-- Futures (9 symbols loaded via load_futures)
|   |-- HG.csv    --> Copper/Gold ratio numerator, commodity sleeve
|   |-- GC.csv    --> Copper/Gold ratio denominator, commodity sleeve
|   |-- CL.csv    --> Commodity sleeve
|   |-- SI.csv    --> Commodity sleeve
|   |-- ZN.csv    --> Fixed income sleeve
|   |-- UB.csv    --> Fixed income sleeve
|   |-- 6J.csv    --> FX sleeve, BOJ intervention
|   |-- MES.csv   --> Equity index sleeve
|   |-- MNQ.csv   --> Equity index sleeve
|
+-- Macro (10 series loaded via load_macro)
|   |-- dxy.csv                      --> DXY trend filter
|   |-- vix.csv                      --> Liquidity score (VIX percentile)
|   |-- high_yield_spread.csv        --> Liquidity score (z-score)
|   |-- breakeven_10y.csv            --> Inflation signal
|   |-- treasury_10y.csv             --> Real rate (nominal component)
|   |-- tips_10y.csv                 --> Real rate (real component)
|   |-- spx.csv                      --> Growth signal (SPX momentum)
|   |-- fed_balance_sheet.csv        --> Liquidity score (Fed BS growth)
|   |-- china_leading_indicator.csv  --> China adjustment [STALE]
|   |-- cny_usd.csv                  --> China adjustment
|
+-- NOT LOADED (34 futures + 5 macro files available but unused)
```

---

## Recommendations

### Immediate (Pre-Production)

1. **Source fresh China CLI data**: The OECD CLI for China is available through their API or FRED. The `china_leading_indicator.csv` file must be updated to at least late 2025 before any backtest results in the 2024-2025 period can be trusted. Alternatively, evaluate whether to disable the China adjustment entirely until the pipeline is fixed.

2. **Filter weekend bars from front-month futures**: Add a weekday check in `load_futures()` to skip Saturday/Sunday rows. These low-volume bars distort rolling statistics. A one-line fix: check `std::tm.tm_wday` after parsing and skip if 0 (Sunday) or 6 (Saturday).

3. **Standardize futures end dates**: The front-month files end 2025-11-12 while `_2nd` files and some macro extend to Feb 2026. Refresh the front-month data to match.

### Medium-Term (Strategy Enhancement)

4. **Populate the empty China/SHFE files**: The five empty files (`china_cli_alt`, `china_credit`, `china_pmi`, `china_leading_indicator_update`, `shfe_copper_inventory`) appear to have been scoped for the strategy but never filled. SHFE copper inventory and China PMI are highly relevant to the copper leg. Completing this data pipeline would strengthen the China adjustment signal.

5. **Consider using `_2nd` month data**: The strategy does not use second-month contracts. These could support: (a) term structure / roll yield signals (contango/backwardation as a carry indicator), (b) roll-adjusted continuous series for more accurate long-horizon backtesting. Note the HG_2nd unit mismatch must be resolved first.

6. **Replace MES/MNQ with ES/NQ for backtest depth**: The micro contracts only start May 2019. Using the full-size ES and NQ contracts (already have `NQ.csv` with data from 2010) would extend the equity sleeve backtest by 9 years. The strategy can apply a contract multiplier adjustment.

### Housekeeping

7. **Remove or archive unused futures files**: 26 futures files (FX, agriculture, energy, metals) are not consumed by the strategy. If they are not planned for future use, move them to an archive directory to reduce confusion.

8. **Reconcile SPX data sources**: `data/raw/macro/spx.csv` and `data/raw/futures/spx_backfill.csv` both contain S&P 500 data with different schemas (single close column vs OHLCV), different precision, and different date ranges. Clarify which is canonical and document the source for each.
