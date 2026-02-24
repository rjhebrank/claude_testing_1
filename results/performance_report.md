# Copper-Gold Strategy v2.0 -- Backtest Performance Report

**Report Date**: 2026-02-24
**Data Source**: `results/backtest_output.txt` (cleaned data run)
**Backtest Period**: 2010-06-07 to 2025-11-12 (15.9 years, 4,011 trading days)
**Initial Capital**: $1,000,000

---

## Executive Summary

**This backtest is catastrophically broken and the results are entirely unusable.** Corrupted price data in HG (Copper), GC (Gold), and CL (Crude Oil) around 2012-02-06 caused a phantom $197M windfall profit, which the position sizer immediately reinvested at massively leveraged scale. When prices reverted to normal on 2012-02-13, the strategy suffered a $6.6 billion realized loss, driving equity permanently negative. The drawdown stop triggered but failed to liquidate existing positions, so the portfolio bled an additional $3 billion over the remaining 13.7 years. **No conclusions about strategy viability can be drawn from this run.**

---

## Summary Statistics Table

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Total Return | -933,479.20% | -- | CATASTROPHIC |
| CAGR | NaN (negative equity) | -- | UNDEFINED |
| Annualized Volatility | 4,829.99% | -- | MEANINGLESS |
| Sharpe Ratio | NaN | >= 0.8 | FAIL |
| Sortino Ratio | NaN | >= 1.0 | FAIL |
| Max Drawdown | 4,761.67% | < 20% | FAIL |
| Max DD Duration | ~13.7 years (2012-02-13 to end) | -- | PERMANENT |
| Win Rate | 50.24% | >= 45% | PASS (but misleading) |
| Profit Factor | 4.9955 | >= 1.3 | PASS (but misleading) |
| Annual Turnover | 0.0000x | < 15x | PASS (system was frozen) |
| Correlation to SPX | -0.0024 | < 0.5 | PASS (trivially) |
| Signal Flips/Year | 6.2 | <= 12 | PASS |

**Note on Win Rate and Profit Factor**: These metrics appear to pass thresholds, but they are computed over a period where the system was effectively dead (size_mult=0.00) for 96% of the backtest. The 50.2% win rate and 4.99 profit factor likely reflect only the pre-crash period (June 2010 -- Feb 2012), which is far too small a sample to be meaningful. Alternatively, they may be distorted by the phantom gains from corrupted data being counted as "wins."

---

## Data Integrity Issues

### The Core Problem: Corrupted Price Spikes (2012-02-03 to 2012-02-13)

The backtest detected and logged -- but did not halt for -- six unrealistic price moves across three instruments during a one-week window:

| Date | Instrument | From | To | Move |
|---|---|---|---|---|
| 2012-02-03 -> 2012-02-06 | HG (Copper) | $3.91 | $38,700.00 | +990,810% |
| 2012-02-03 -> 2012-02-06 | GC (Gold) | $1,728.50 | $17,227.00 | +897% |
| 2012-02-03 -> 2012-02-06 | CL (Crude Oil) | $97.77 | $9,718.00 | +9,840% |
| 2012-02-10 -> 2012-02-13 | HG (Copper) | $38,630.00 | $3.82 | -99.99% |
| 2012-02-10 -> 2012-02-13 | GC (Gold) | $17,250.00 | $1,720.20 | -90.03% |
| 2012-02-10 -> 2012-02-13 | CL (Crude Oil) | $9,905.00 | $100.59 | -98.98% |

This is almost certainly a data vendor artifact -- likely a decimal-place or unit error in the cleaned dataset. HG jumped from ~$3.91/lb to $38,700/lb (a factor of ~10,000x), while GC and CL each jumped by roughly 10x. The spike persisted for approximately one trading week before reverting.

### Cascade of Failures

The corrupted data triggered a devastating chain reaction in the backtest engine:

**Step 1 -- Phantom Windfall (2012-02-03 to 2012-02-06)**:
- Pre-spike equity: $1,035,639 (modest, reasonable)
- The strategy held small positions: 6J:-3, UB:-4, SI:1, CL:2, ZN:-5
- When CL "moved" from $97.77 to $9,718, the 2 CL contracts (at $1,000/point notional) generated roughly $19.2M in phantom P&L. Similar gains hit other instruments.
- Post-spike equity: **$197,589,347** -- a 19,000% "gain" in one day
- New peak equity was recorded at **$200,224,082**

**Step 2 -- Massive Position Scaling (2012-02-10)**:
- The position sizer, seeing $197M in equity, computed target positions proportionally
- GC_raw = 691.60 contracts (vs. 3.62 the previous week)
- The system sized into: 6J:-494, UB:-760, SI:7, GC:-130, CL:347
- Total commodity notional: $416,170,000

**Step 3 -- Price Reversion Wipeout (2012-02-13)**:
- Prices snapped back to normal levels (HG: $38,630 -> $3.82, etc.)
- The 347 CL contracts lost approximately $347 * $1,000 * ($9,905 - $100.59) = **$3.4 billion** on CL alone
- Total equity crashed to **-$6,377,259,132** -- negative $6.4 billion
- Peak-to-trough drawdown: 3,285% of peak equity

**Step 4 -- Zombie Portfolio (2012-02-13 to 2025-11-12)**:
- Drawdown stop triggered (dd=32.85, stop=1), setting size_mult=0.00
- However, **positions were NOT liquidated**. By 2012-02-13, the portfolio held: SI:-4,252, GC:-3,188, CL:-8,503, HG:-5,798, MNQ:-27,901
- These positions grew slightly each day (the sizing code appears to be adding to positions even while "stopped"), slowly bleeding equity further
- Over 13.7 years, equity deteriorated from -$6.4B to -$9.3B

### Cu/Gold Ratio Corruption

The diagnostic summary confirms the Cu/Gold ratio reached 572.9 (expected range: 0.2 to 1.2). This is a direct consequence of the HG spike ($38,700 / $1,728.50 * normal_ratio). This corrupted the L1 signal for the duration of the spike, though this is secondary to the position-sizing catastrophe.

---

## Regime Analysis

### Signal Distribution (over 4,011 days)

| Signal | Days | Percentage |
|---|---|---|
| RISK_ON | 1,671 | 41.7% |
| RISK_OFF | 2,072 | 51.6% |
| NEUTRAL | 268 | 6.7% |

### Regime Distribution

| Regime | Days | Percentage |
|---|---|---|
| GROWTH_POSITIVE | 2,853 | 71.1% |
| GROWTH_NEGATIVE | 731 | 18.2% |
| LIQUIDITY | 199 | 5.0% |
| NEUTRAL | 228 | 5.7% |
| INFLATION | 0 | 0.0% |

### Regime Issues

1. **INFLATION regime never triggered** (0 out of 4,011 days). The diagnostic notes that the inflation shock threshold (100bp change over 20 days) may be calibrated incorrectly. Expected frequency: 2-5% of days. This means an entire regime branch of the strategy was never tested.

2. **RISK_OFF dominated** (51.6%) -- the strategy spent more time defensive than offensive. However, since the stop was permanently engaged from Feb 2012 onward, the tilt signal was irrelevant for 96% of the backtest.

3. **GROWTH_POSITIVE dominated** (71.1%) -- this is somewhat expected for a 2010-2025 backtest but means the strategy was barely tested in adverse macro environments.

### Equity by Regime Transition (Spot-Check Table)

| Date | Cu/Au Ratio | Tilt | Regime | Liquidity | Size Mult | Equity |
|---|---|---|---|---|---|---|
| 2010-06-07 | 0.5567 | NEUTRAL | NEUTRAL | +1.00 | 0.50 | $1,000,000 |
| 2014-04-14 | 0.5735 | RISK_OFF | NEUTRAL | +0.64 | 0.00 | -$5,986,170,927 |
| 2018-02-22 | 0.6066 | RISK_OFF | GROWTH_POSITIVE | -0.65 | 0.00 | -$5,596,965,517 |
| 2022-01-04 | 0.6155 | NEUTRAL | GROWTH_POSITIVE | +1.23 | 0.00 | -$6,806,696,014 |
| 2025-11-12 | 0.3030 | RISK_OFF | GROWTH_POSITIVE | -1.01 | 0.00 | -$9,333,791,995 |

The size_mult=0.00 from 2014 onward confirms the strategy was permanently halted after the Feb 2012 crash.

---

## Layer Analysis

### L1 -- Copper/Gold Ratio (Primary Signal)

- Valid days: 4,011
- Ratio range: [0.284, 572.899] -- **corrupted** (max should be ~1.2)
- Total signal flips: 99 (6.2/year) -- within expected range
- The ratio itself appears functional outside the corrupted window; the 0.284 low and values near 0.55-0.62 are plausible

### L2 -- Macro Regime

- 4 of 5 regimes triggered (INFLATION never fired)
- GROWTH_POSITIVE dominated (71.1%), GROWTH_NEGATIVE at 18.2%
- Regime transitions appear to have worked mechanically, but were irrelevant post-crash

### L3 -- DXY Filter

- 5,240 DXY records loaded
- The composite score (shown in spot-check table) ranged from -0.340 to +1.000
- Appears to have functioned, contributing to tilt decisions

### L4 -- Term Structure

- 32 L4-TS log entries found (approximately 2 per year, logged at ~6-month intervals)
- Term structure multipliers (ts_mult) ranged from 0.00 to 1.00 per instrument
- HG: oscillated between CONTANGO (1.00), FLAT (0.50-0.75), and BACKWARDATION (0.00-1.00)
- CL: frequently BACKWARDATION in later years (2021-2025), reducing multiplier to 0.00
- ZN: mostly BACKWARDATION early, shifting to CONTANGO/FLAT later
- Yield curve: persistently BACKWARDATION throughout the entire period

---

## Per-Instrument Breakdown

### Pre-Crash Positions (2010-06 to 2012-02)

The strategy actively traded 6 instruments in small size:
- **6J** (Yen): 1-3 contracts, both long and short
- **UB** (Ultra Bonds): 2-4 contracts, both directions
- **SI** (Silver): 1 contract, mostly long
- **CL** (Crude Oil): 1-2 contracts, both directions
- **ZN** (10Y Notes): 2-5 contracts, mostly short in risk-on
- **HG** (Copper): 1 contract occasionally

### Post-Crash Zombie Positions (2012-02-13 onward)

Despite size_mult=0.00 and stop=1, the portfolio accumulated massive positions:

| Date | SI | GC | CL | HG | MNQ |
|---|---|---|---|---|---|
| 2012-02-13 | -4,252 | -3,188 | -8,503 | -5,798 | -27,901 |
| 2025-11-12 | -6,222 | -4,667 | -12,445 | -8,485 | -40,835 |

Positions **grew by ~50%** over 13 years despite the system being "stopped." This indicates a critical bug: the position calculation is using negative equity to compute notional cap (com_cap = 40% of equity = -$3.7B), and this negative cap is somehow resulting in short positions being added rather than the system being flat.

---

## Equity Curve

### Key Equity Data Points

| Date | Equity | Notes |
|---|---|---|
| 2010-06-07 | $1,000,000 | Start |
| 2011-07-xx | ~$1,146,338 | All-time peak (pre-crash) |
| 2012-01-03 | $1,030,837 | Pre-crash (10% below peak) |
| 2012-02-03 | $1,035,639 | Last clean equity |
| 2012-02-06 | $197,589,347 | Corrupted spike |
| 2012-02-10 | $197,601,347 | Position sizing based on phantom equity |
| 2012-02-13 | -$6,377,259,132 | Price reversion wipeout |
| 2013-01-02 | -$6,243,440,750 | |
| 2014-01-02 | -$5,894,071,571 | Slight improvement (mean reversion in positions?) |
| 2015-01-02 | -$5,474,085,635 | |
| 2016-01-04 | -$5,292,601,179 | Local "best" post-crash |
| 2017-01-03 | -$5,472,771,937 | Deteriorating again |
| 2018-01-02 | -$5,586,374,229 | |
| 2019-01-02 | -$5,438,770,081 | |
| 2020-01-02 | -$5,789,111,992 | |
| 2021-01-04 | -$6,248,683,509 | COVID + commodity rally hurting shorts |
| 2022-01-03 | -$6,806,051,371 | Commodity supercycle peak |
| 2023-01-03 | -$6,236,915,511 | |
| 2024-01-02 | -$6,780,903,301 | |
| 2025-01-02 | -$7,710,187,650 | Gold/copper rally deepening losses |
| 2025-11-12 | -$9,333,791,995 | Final |

The equity curve shows two distinct phases:
1. **Pre-crash (18 months)**: Modest performance. Peak equity of $1.146M represents a 14.6% return, then drawdown to ~$1.03M (10% below peak). Not enough data to evaluate the strategy.
2. **Post-crash (13.7 years)**: Permanently negative, slowly deteriorating as unliquidated short positions bleed against a rising commodity and equity market.

---

## Kill Criteria Assessment

| Kill Criterion | Threshold | Actual | Status |
|---|---|---|---|
| Signal Flips/Year | <= 20 | 6.2 | PASS |
| Sharpe Ratio | >= 0.8 | NaN | FAIL |
| Sortino Ratio | >= 1.0 | NaN | FAIL |
| Max Drawdown | < 20% | 4,761.67% | FAIL |

Only one kill criterion is logged in the output (flips/year). The Sharpe, Sortino, and Max Drawdown criteria all fail massively, but the kill criteria section in the output appears truncated -- it only shows the single passing criterion. This suggests either (a) the kill criteria evaluator only logs passing criteria, or (b) the output was cut off.

**The drawdown stop DID trigger** on 2012-02-13 at dd=32.85 (3,285% of peak). However, this "stop" only set size_mult to 0.00 -- it did not liquidate positions. The stop remained engaged for the remaining 13.7 years of the backtest (stop=1 on every subsequent [REB] line).

---

## Critical Issues & Recommendations

### P0 -- Must Fix Before Any Further Testing

1. **Data validation must halt the backtest**: The engine detected `[ERROR] Unrealistic price move` events but continued running. Any price move exceeding a configurable threshold (e.g., 50% single-day) must either (a) reject the bar and use the previous close, or (b) halt the backtest entirely. Logging and continuing is not acceptable.

2. **Drawdown stop must liquidate all positions to flat**: The stop triggered (stop=1, size_mult=0.00) but existing positions were never closed. This is the difference between a -10% drawdown and a -933,479% drawdown. When the stop triggers, all positions must be immediately set to zero.

3. **Position accumulation bug when equity is negative**: With size_mult=0.00 and negative equity, the system should hold zero positions. Instead, positions grew from ~5,000 to ~8,500 contracts (HG) over 13 years. The notional cap calculation (`com_cap = 40% * equity`) produces a negative number, which likely inverts position direction logic. This must be debugged and fixed.

4. **Re-clean the data for the 2012-02-03 to 2012-02-13 window**: The "cleaned" dataset still contains 10,000x price spikes. The data cleaning pipeline either missed this or introduced it. Investigate the raw data to determine whether this is a source data issue or a cleaning artifact.

### P1 -- Important for Strategy Evaluation

5. **Inflation regime never triggered**: 0 out of 4,011 days is wrong. The breakeven threshold (100bp/20d) needs recalibration. Without INFLATION regime coverage, the strategy is untested in inflationary environments -- a critical gap given 2021-2023 saw significant inflation.

6. **Pre-crash performance is inconclusive**: The strategy only had 18 months of active trading before the crash, with a peak return of +14.6% and a drawdown to +3%. This is far too little data to evaluate. Need a clean full-period run.

7. **Turnover of 0.0000x is suspicious**: This may be an artifact of the system being frozen for 96% of the backtest, or it may indicate a calculation bug.

### P2 -- Investigate After Clean Run

8. **RISK_OFF bias (51.6% of days)**: If the strategy is naturally bearish-leaning, this needs to be understood. In a secular bull market (2010-2025), persistent RISK_OFF may cause underperformance.

9. **Term structure layer (L4) frequency**: Only 32 log entries over 15.9 years suggests L4 is only recalculated at rebalance boundaries, not daily. Verify this is intentional.

10. **MES/MNQ positions appearing post-crash**: These instruments only have 1,696 bars (starting ~2019), yet MNQ appears in the post-crash zombie portfolio from 2012. This may indicate a separate bug in how unavailable instruments are handled.

---

## Conclusion

**This backtest run is void.** The results reflect a data integrity failure, not strategy performance. The three critical bugs (no data halt, no position liquidation on stop, negative-equity position accumulation) must be fixed, and the data must be re-cleaned before any meaningful evaluation is possible.

The 18-month pre-crash window (June 2010 -- Feb 2012) showed modest but inconclusive performance: peak equity +14.6%, ending at +3.6% before the spike. This is not enough to judge the strategy, but it is not obviously broken during that window.

**Recommended next steps**:
1. Fix the three P0 bugs
2. Re-clean the price data (or confirm raw data is clean and re-run on raw)
3. Re-run the full backtest
4. Compare against the raw data run (`backtest_output_raw.txt`) to isolate cleaning artifacts

---

## Cleaned vs Raw Data Comparison

Both runs use **identical fixed code** (inflation threshold fix, static var fix, Layer 4 term structure, dead code removed). The only difference is the input data: `./data/cleaned` (weekends removed) vs `./data/raw` (all calendar days including weekends).

---

### Side-by-Side Metrics Table

| Metric                     | Cleaned Data           | Raw Data               | Delta / Notes                        |
|----------------------------|------------------------|------------------------|--------------------------------------|
| **Data directory**         | `./data/cleaned`       | `./data/raw`           |                                      |
| **Trading days**           | 4,011                  | 4,800                  | 789 fewer (weekend removal)          |
| **Date range**             | 2010-06-07 to 2025-11-12 | 2010-06-07 to 2025-11-12 | Same                              |
| **Initial capital**        | $1,000,000             | $1,000,000             | Same                                 |
| **Final equity**           | **-$9,333,791,995**    | **-$1,050,131,706**    | Cleaned is **8.9x worse**            |
| **Total return**           | -933,479.20%           | -105,113.17%           | Cleaned 8.9x worse                   |
| **Annualized return**      | NaN                    | NaN                    | Both overflow (negative equity)      |
| **Annualized volatility**  | 4,829.99%              | 931.26%                | Cleaned 5.2x higher                  |
| **Sharpe ratio**           | NaN                    | NaN                    | Both undefined                       |
| **Sortino ratio**          | NaN                    | NaN                    | Both undefined                       |
| **Max drawdown**           | 4,761.67%              | 5,191.31%              | Raw slightly deeper (% of peak)      |
| **Win rate**               | 50.24%                 | 50.44%                 | Essentially identical                |
| **Profit factor**          | 4.9955                 | 0.6244                 | Cleaned "better" (misleading*)       |
| **Annual turnover**        | 0.0000x                | 0.0000x                | Both zero (frozen after crash)       |
| **Correlation to SPX**     | -0.0024                | 0.0029                 | Both negligible                      |
| **Signal flips/year**      | 6.2                    | 6.8                    | Cleaned slightly fewer               |
| **Final signal**           | RISK_OFF               | RISK_ON                | **Different!**                       |
| **Final regime**           | GROWTH_POSITIVE        | GROWTH_POSITIVE        | Same                                 |
| **Kill criteria**          | 6.2 flips/yr PASS      | 6.8 flips/yr PASS      | Both pass (only criterion checked)   |

\* Profit factor of 4.99 in cleaned is misleading -- it is inflated by the massive phantom gains from the corrupted spike being counted as "profits." Raw's 0.62 is more honest since the spike profits were smaller relative to accumulated losses.

#### Signal & Regime Distribution

| Category        | Cleaned (4,011 days) | Raw (4,800 days) | Notes                                 |
|-----------------|---------------------|-------------------|---------------------------------------|
| RISK_ON         | 1,671 (41.7%)       | 2,076 (43.3%)    | Raw has proportionally more RISK_ON   |
| RISK_OFF        | 2,072 (51.7%)       | 2,425 (50.5%)    | Comparable                            |
| NEUTRAL         | 268 (6.7%)          | 299 (6.2%)       | Comparable                            |
| GROWTH+         | 2,853 (71.1%)       | 3,340 (69.6%)    | Comparable                            |
| GROWTH-         | 731 (18.2%)         | 916 (19.1%)      | Comparable                            |
| INFLATION       | 0 (0.0%)            | 0 (0.0%)         | **Both zero -- inflation logic broken**|
| LIQUIDITY       | 199 (5.0%)          | 227 (4.7%)       | Comparable                            |
| NEUTRAL regime  | 228 (5.7%)          | 317 (6.6%)       | Comparable                            |

#### Data Ingestion (Bars Loaded)

| Instrument | Cleaned | Raw   | Difference |
|------------|---------|-------|------------|
| HG         | 3,995   | 4,780 | -785       |
| GC         | 3,982   | 4,764 | -782       |
| CL         | 3,998   | 4,787 | -789       |
| SI         | 3,964   | 4,740 | -776       |
| ZN         | 4,003   | 4,791 | -788       |
| UB         | 4,002   | 4,745 | -743       |
| 6J         | 3,999   | 4,787 | -788       |
| MES        | 1,696   | 2,033 | -337       |
| MNQ        | 1,696   | 2,033 | -337       |

Average reduction: ~785 bars for full-history instruments, ~337 for MES/MNQ (started later). This is consistent with removing weekend days from ~15.4 years of data (~789 weekend-day rows removed, suggesting the raw data included one weekend day per week -- likely Sunday forward-fills -- and the cleaning removed them).

#### Final Positions (Frozen at End)

| Instrument | Cleaned   | Raw      | Ratio   |
|------------|-----------|----------|---------|
| SI         | -6,222    | -700     | 8.9x    |
| GC         | -4,667    | -525     | 8.9x    |
| CL         | -12,445   | -1,400   | 8.9x    |
| HG         | -8,485    | -954     | 8.9x    |
| MNQ        | -40,835   | -4,594   | 8.9x    |
| MES        | -65,337   | -7,351   | 8.9x    |

All position sizes are exactly 8.9x larger in the cleaned run. This ratio is the direct consequence of the equity differential established at the 2012 spike event.

#### Peak Equity (Pre-Crash)

| Metric          | Cleaned          | Raw             | Ratio   |
|-----------------|------------------|-----------------|---------|
| Peak equity     | $200,224,082     | $20,625,981     | **9.7x**|
| Peak multiplier | 200x initial     | 20.6x initial   |         |

#### Max Contracts Ever Held

| Instrument | Cleaned | Raw   | Ratio   |
|------------|---------|-------|---------|
| Max GC     | 4,667   | 525   | 8.9x    |
| Max HG     | 8,485   | 954   | 8.9x    |

---

### Data Cleaning Impact

#### Row Count Difference
- **Cleaned**: 4,011 trading days
- **Raw**: 4,800 trading days
- **Removed**: 789 rows (16.4% of raw data)

This is consistent with the removal of one weekend day per week (789 rows / 15.4 years = ~51 per year, close to 52 weekends). The raw data likely included Sunday forward-fills or similar padding that the cleaning step removed.

#### Did Weekend Removal Change Signal Behavior?

Yes, **critically**, but through an indirect mechanism -- the drawdown stop threshold.

On 2012-02-02 (the day before the spike), the two runs had subtly different equity trajectories:

| Metric              | Cleaned          | Raw              |
|---------------------|------------------|------------------|
| Equity (2012-02-02) | $1,029,316       | $981,816         |
| Peak equity         | $1,146,338       | $1,132,873       |
| Drawdown            | 10.2%            | 13.3%            |
| Stop status         | stop=1           | stop=1           |

On 2012-02-03 (the Friday when the spike first hits):

| Metric              | Cleaned          | Raw              |
|---------------------|------------------|------------------|
| Equity              | $1,035,639       | $990,071         |
| **Drawdown**        | **10.0%**        | **13.0%**        |
| **Stop status**     | **stop=0** (RELEASED) | **stop=1** (ACTIVE) |
| **size_mult**       | **1.00**         | **0.50**         |

The cleaned data's slightly higher equity ($1,035K vs $990K) and lower drawdown (10.0% vs 13.0%) caused the drawdown stop to **release** in the cleaned run but remain **engaged** in the raw run. This single binary gate -- a 3-percentage-point drawdown difference -- is the root cause of the 9x outcome divergence.

#### Did the Corrupted 2012 Price Spike Get Cleaned?

**NO.** The corrupted spike is present in **both** datasets. The "cleaning" only removed weekends; it did not detect or remove corrupted prices.

**Cleaned** (weekends removed, spike appears on the next weekday, 2012-02-06):
```
[ERROR] HG: 2012-02-03 3.91 -> 2012-02-06 38700.00 (990,810%)
[ERROR] GC: 2012-02-03 1728.50 -> 2012-02-06 17227.00 (897%)
[ERROR] CL: 2012-02-03 97.77 -> 2012-02-06 9718.00 (9,840%)
```

**Raw** (weekend days present, spike hits on Sunday 2012-02-05):
```
[ERROR] HG: 2012-02-03 3.91 -> 2012-02-05 38900.00 (995,931%)
[ERROR] GC: 2012-02-03 1728.50 -> 2012-02-05 17334.00 (903%)
[ERROR] CL: 2012-02-03 97.77 -> 2012-02-05 9769.00 (9,892%)
```

Note the spike values are slightly different between runs (38,700 vs 38,900 for HG), suggesting the forward-fill on the weekend day in raw data may have had a marginally different value than the cleaned data's next-weekday value. But both are catastrophically corrupted -- the difference between 38,700 and 38,900 is irrelevant when the real price was $3.91.

---

### Layer 4 Term Structure Impact

#### L4 Signal Frequency
- **Cleaned**: 32 L4-TS updates across 4,011 trading days (fires every ~125 trading days)
- **Raw**: 39 L4-TS updates across 4,800 calendar days (fires every ~123 calendar days)
- Raw produces 22% more L4 signals due to having more data points

#### L4 Signals Bracketing the 2012 Spike

**Cleaned** -- L4 signals nearest the spike:
- **2011-11-21**: `CL=FLAT(0.50) HG=CONTANGO(1.00) GC=CONTANGO SI=BACKWARDATION ZN=BACKWARDATION`
- Next L4: **2012-05-15**: `CL=CONTANGO(0.25) HG=CONTANGO(0.50) GC=CONTANGO SI=CONTANGO ZN=BACKWARDATION`
- Gap: **~6 months** with no L4 recalculation. During the spike (Feb 2012), the Nov 2011 multipliers were in effect: **HG ts_mult=1.00** (full size for copper).

**Raw** -- L4 signals nearest the spike:
- **2012-01-20**: `CL=CONTANGO(0.25) HG=CONTANGO(0.50) GC=FLAT SI=BACKWARDATION ZN=BACKWARDATION`
- Next L4: **2012-06-15**: `CL=CONTANGO(1.00) HG=BACKWARDATION(0.00) GC=FLAT SI=CONTANGO ZN=FLAT`
- The raw run had an L4 update just **2 weeks before** the spike, which set **HG ts_mult=0.50** (half size for copper).

This means the raw run would have halved HG position size from L4 alone. However, this L4 difference was **moot** in practice because the drawdown stop was already engaged in the raw run (size_mult=0.50), overriding the L4 multiplier. The L4 divergence matters only in scenarios where the stop is not active.

#### L4 Divergence Through Full Backtest

Comparing all L4 signals at the same approximate dates, the two runs frequently disagree on term structure state for the same commodity. Examples:

| Approx Date  | Commodity | Cleaned TS State | Raw TS State   |
|--------------|-----------|-------------------|----------------|
| 2010-11      | HG        | CONTANGO (1.00)  | CONTANGO (0.50)|
| 2011-03      | HG        | (no signal)      | BACKWARDATION (0.00)|
| 2013-05      | CL        | CONTANGO (0.25)  | (different date)|
| 2014-04      | CL        | BACKWARDATION (0.00) | BACKWARDATION (0.00)|
| 2018-03      | HG        | BACKWARDATION (0.00) | CONTANGO (1.00)|

The divergence is expected: removing ~789 weekend data points changes the rolling windows used to compute contango/backwardation, shifting the term structure assessment. However, since both runs were frozen by the drawdown stop from Feb 2012 onward (size_mult=0.00), these differences had zero impact on actual positions.

---

### Root Cause Analysis: Why Is the Cleaned Run 9x WORSE?

#### The Butterfly Effect Chain

A single 3-percentage-point drawdown difference on 2012-02-02 cascaded into a 9x difference in final equity through this chain:

```
Weekend removal
  -> Slightly different equity path (cleaned: $1,029K, raw: $982K on 2012-02-02)
  -> Different drawdown depth (cleaned: 10.2%, raw: 13.3%)
  -> Drawdown stop gate toggled differently (cleaned: released, raw: active)
  -> Different size_mult on 2012-02-03 (cleaned: 1.00, raw: 0.50)
  -> 2x difference in positions entering the corrupted spike
  -> 10x difference in phantom profit (cleaned: $197M, raw: $20M)
  -> 10x difference in positions at 2012-02-10 rebalance (cleaned: 692 GC, raw: 71 GC)
  -> 9x difference in loss when spike reverts (cleaned: -$6.4B, raw: -$704M)
  -> 9x difference in negative equity
  -> 9x difference in negative notional cap (feedback loop)
  -> 9x difference in final zombie positions and final equity
```

#### Hypothesis Testing

**Hypothesis 1: Weekend padding diluted the 2012 spike damage in raw data**
**PARTIALLY CONFIRMED.** The weekend rows in raw data created a slightly different equity trajectory that kept drawdown at 13.3% (vs 10.2% in cleaned), which kept the drawdown stop engaged. The stop limited size_mult to 0.50, halving position sizes entering the spike. Additionally, the raw data's weekend forward-fills spread the spike across more days (appearing on Sunday 2012-02-05), giving one extra day of exposure before the Friday 2012-02-10 rebalance -- but this effect was minor compared to the size_mult difference.

**Hypothesis 2: Different position sizes due to different equity trajectories**
**CONFIRMED -- PRIMARY CAUSE.** The quantitative breakdown:

| Step                        | Cleaned                | Raw                    | Ratio  |
|-----------------------------|------------------------|------------------------|--------|
| Equity pre-spike (2/3)      | $1,035,639             | $990,071               | 1.05x  |
| Size multiplier (2/3)       | 1.00                   | 0.50                   | 2.0x   |
| Positions entering spike    | 6J:-3, UB:-4, CL:2    | 6J:-1, UB:-2, CL:1    | ~2x    |
| Equity post-spike (2/10)    | $197,601,347           | $20,291,856            | 9.7x   |
| GC contracts (2/10)         | -692                   | -71                    | 9.7x   |
| Equity post-revert (2/13)   | -$6,377,259,132        | -$703,832,386          | 9.1x   |
| Final equity (11/12/2025)   | -$9,333,791,995        | -$1,050,131,706        | 8.9x   |

The initial 2x size_mult difference was amplified to ~10x by the multiplicative interaction between position size and the 10x-10,000x corrupted price moves. The 10x spike profits then scaled the 2012-02-10 rebalance positions by 10x, which produced 9x larger losses on reversion.

**Hypothesis 3: Cleaning removed data the strategy needed**
**NO.** The strategy does not depend on weekend data. The only effect of weekend removal was the subtle equity path divergence that toggled the drawdown stop. The signal generation, regime classification, and term structure calculations all produced comparable distributions (see tables above).

---

### Verdict

**Neither run is trustworthy.** Both are completely dominated by a single corrupted data event in February 2012 that overwhelms all genuine signal content.

#### Which Run is More Representative?

The **raw data run** (-$1.05B) is marginally "better" in the sense that its drawdown stop remained engaged and limited the spike exposure. But this is **pure luck** -- a 3% drawdown difference determined whether the stop was active. In a real trading scenario, the stop state would depend on exact fills, slippage, and timing that neither simulation captures.

Neither run tells us anything about the strategy's actual merit. The 18-month pre-crash window (Jun 2010 -- Feb 2012) is the only window with genuine trading, and it showed:
- Cleaned: peak +14.6%, ending at +3.6% before spike
- Raw: peak +13.3%, ending at -1.0% before spike
- Both inconclusive -- too short a sample

#### What Must Be Fixed Before Either Run Is Meaningful

| Priority | Issue | Description |
|----------|-------|-------------|
| **P0** | **Corrupted price data** | Remove or clamp the 2012-02-05 through 2012-02-10 spike. HG, GC, and CL all show 10x-10,000x moves that are data errors. Either interpolate through the week or exclude it entirely. Both cleaned and raw datasets need this fix. |
| **P0** | **Negative equity guard** | When equity <= 0, all position sizes must floor at zero. The `com_cap = equity * 0.40` formula produces negative values that feed into short positions, creating an irreversible death spiral. |
| **P0** | **Price move circuit breaker** | When `[ERROR] Unrealistic price move` is detected, the engine must halt or clamp -- not log and continue. A configurable threshold (e.g., 50% single-day move) should freeze positions and skip the bar. |
| **P1** | **Position size hard limits** | Cap contracts per instrument regardless of equity. A $1M account should never hold 692 GC contracts ($416M notional). |
| **P1** | **Drawdown stop must liquidate** | The stop sets size_mult=0.00 but never closes existing positions. When stop triggers, all positions must go to zero immediately. |
| **P1** | **Drawdown stop hysteresis** | The stop released at dd=10.0% in cleaned but stayed at dd=13.0% in raw. The threshold is too fragile. Add hysteresis: engage at (e.g.) 15%, only release at (e.g.) 5%. This prevents a 3% equity path difference from producing a 9x outcome divergence. |
| **P2** | **Inflation regime** | Zero INFLATION days in both runs. The threshold fix still produces no triggers. Either the breakeven data lacks sufficient moves or the threshold needs further calibration. |
| **P2** | **L4 recalculation frequency** | L4 fires every ~125 days. Consider whether this should be more frequent, or at least confirm the interval is intentional. |

After these fixes, rerun both cleaned and raw datasets. Expect results in the range of -20% to +30% annualized for a commodity macro strategy -- not billions in losses.
