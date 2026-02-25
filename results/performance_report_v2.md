# Copper-Gold Macro Strategy -- V2 Backtest Performance Report

**Report Date**: 2026-02-24
**Analyst**: Quantitative Strategy Review
**Backtest Period**: 2010-06-07 to 2025-11-12 (15.9 years, 4,011 trading days)
**Initial Capital**: $1,000,000
**Final Equity**: $1,761,940
**Data Source**: `results/backtest_output_v2.txt` (v2 infrastructure-fixed run)

---

## 1. Executive Summary

The v2 backtest represents the first trustworthy read on this strategy's economics. Six critical infrastructure bugs -- including corrupted price data that caused a $6.4B phantom loss in v1, a drawdown stop that failed to liquidate positions, and a negative-equity death spiral -- have been fixed. The strategy now runs cleanly for the full 15.9-year period with no data errors, no negative equity, and properly functioning drawdown stops. This alone is a significant milestone: we can finally evaluate the signal on its merits rather than debugging catastrophic engine failures.

The news, however, is sobering. On clean infrastructure, the Copper-Gold ratio strategy delivers a 76.2% total return over 15.9 years -- a 3.6% annualized return with a Sharpe ratio of 0.34 and a Sortino of 0.33. For context, a 60/40 portfolio over the same period would have delivered roughly 7-8% annualized with a comparable Sharpe above 0.5. The strategy's max drawdown of 25.6% exceeds the 20% target, the profit factor of 1.08 means the strategy barely earns more than it loses, and turnover at 46.7x per year is extreme for what is ostensibly a macro regime-following strategy. Five of the seven kill criteria fail their thresholds.

**Bottom line**: The strategy is not investable in its current form. The Cu/Au ratio signal may contain genuine information -- the -0.17 correlation to SPX and the non-random regime switching (6 flips/year) are encouraging structural properties -- but the signal-to-noise ratio is far too low to generate adequate risk-adjusted returns. Continued development is justified only if (a) the signal generation can be materially improved, (b) position sizing and risk management can be tightened, and (c) out-of-sample validation can demonstrate the alpha is real. Without those improvements, this is an expensive way to underperform cash.

---

## 2. V2 Performance Summary Table

| Metric | Value | Target / Threshold | Status |
|---|---|---|---|
| **Total Return** | 76.19% | -- | -- |
| **CAGR** | 3.62% | -- | Weak |
| **Annualized Volatility** | 10.67% | -- | Moderate |
| **Sharpe Ratio** | 0.34 | >= 0.80 | FAIL |
| **Sortino Ratio** | 0.33 | >= 1.00 | FAIL |
| **Max Drawdown** | 25.63% | < 20% | FAIL |
| **Max DD Duration** | ~18 months (est.) | -- | Long |
| **Win Rate** | 45.65% | >= 45% | PASS (marginal) |
| **Profit Factor** | 1.075 | >= 1.30 | FAIL |
| **Annual Turnover** | 46.66x | < 15x | FAIL |
| **Correlation to SPX** | -0.166 | < 0.50 | PASS |
| **Signal Flips/Year** | 6.0 | <= 12 | PASS |
| **Kill Criteria Passed** | 3 of 8 | -- | FAIL overall |
| **Final Margin Utilization** | 10.5% | -- | Conservative |

**Kill Criteria Summary**: Only win rate (marginally), SPX correlation, and signal flip frequency pass their thresholds. Sharpe, Sortino, max drawdown, profit factor, and turnover all fail. The strategy does not meet its own minimum viability criteria.

---

## 3. V1 vs V2 Comparison

| Metric | V1 (Broken) | V2 (Fixed) | Notes |
|---|---|---|---|
| **Final Equity** | -$9,333,791,995 | $1,761,940 | V1 was catastrophically broken |
| **Total Return** | -933,479% | +76.2% | V1 meaningless |
| **CAGR** | NaN (negative equity) | 3.62% | First valid number |
| **Annualized Vol** | 4,830% | 10.67% | V1 dominated by data corruption |
| **Sharpe Ratio** | NaN | 0.34 | Low but at least real |
| **Sortino Ratio** | NaN | 0.33 | Low but at least real |
| **Max Drawdown** | 4,762% | 25.63% | V1: never recovered; V2: within range |
| **Win Rate** | 50.24% (misleading) | 45.65% | V1 inflated by phantom gains |
| **Profit Factor** | 4.996 (misleading) | 1.075 | V1 inflated by corrupted spike |
| **Turnover** | 0.00x (frozen) | 46.66x | V1 stopped trading after crash |
| **SPX Correlation** | -0.002 (trivial) | -0.166 | V2 shows genuine decorrelation |
| **Signal Flips/Year** | 6.2 | 6.0 | Consistent |
| **Active Trading Days** | ~4% (18 months) | 88.1% | V1 was a zombie for 13.7 years |

**Key takeaway**: V1 results were entirely unusable. Every metric was either undefined (NaN), artificially inflated by corrupted data, or irrelevant because the system was frozen. V2 is the first run that tells us anything about the actual strategy. The v1 report should be discarded entirely.

### Bugs Fixed Between V1 and V2

1. **Price data corruption removed**: The 2012-02-03 to 2012-02-13 HG/GC/CL spike (10x-10,000x phantom moves) has been cleaned from the dataset.
2. **Drawdown stop now liquidates positions**: When the stop triggers, all positions are immediately set to zero. In v1, positions were retained and bled for 13.7 years.
3. **Negative equity guard**: Equity <= 0 now floors all position sizes at zero, preventing the death spiral where negative `com_cap` generated phantom short positions.
4. **Price move circuit breaker**: Unrealistic price moves are now halted rather than logged and ignored.
5. **Position size hard limits**: Per-instrument contract caps prevent a $1M account from holding 692 GC contracts.
6. **Drawdown stop hysteresis**: Stop engages at the threshold and requires a cooldown period before releasing, preventing fragile on/off toggling.

---

## 4. Drawdown Stop Analysis

The v2 backtest shows the drawdown management system working as designed, though the strategy experiences frequent periods of elevated drawdown. The drawdown stop triggers at the 10% threshold (setting `stop=1`) and reduces `size_mult` to 0.50 or 0.00, with cooldown periods before re-entry.

### Drawdown Episode 1: Late 2014 -- Mid 2016 (The Commodity Crush)

- **Peak equity**: $1,438,871 (mid-2014)
- **Trough equity**: ~$1,264,000 (Nov 2014)
- **Max drawdown**: ~12.2% from peak
- **Stop triggered**: 2014-11-25 (`stop=1`, `size_mult=0.50`)
- **Duration**: Stop remained engaged intermittently through mid-2016 (~18 months of reduced sizing)
- **Behavior**: The system correctly reduced position size to 0.50x and periodically went fully flat (`size_mult=0.00`) when the drawdown stop combined with other filters. Multiple extended flat periods (e.g., 2015-06-29 through 2015-07-13: fully flat for 2 weeks). Recovery was slow -- equity did not surpass the $1,438K peak until approximately Q2 2016.
- **Assessment**: The stop preserved capital during the 2014-2015 commodity selloff but the 18-month recovery is concerning. The strategy was effectively sidelined during a period when a well-calibrated macro model should have been profiting from the clear RISK_OFF regime.

### Drawdown Episode 2: Mid 2020 -- Late 2022 (COVID Recovery Whipsaw)

- **Peak equity**: $2,058,813 (late March 2020 -- ironically during COVID crash)
- **Second peak**: $2,276,857 (mid-2021)
- **Trough equity**: ~$1,751,335 (Sep 3, 2020) and ~$1,940,466 (Sep 26, 2022)
- **Max drawdown from 2020 peak**: ~14.9%
- **Max drawdown from 2021 peak**: ~14.8%
- **Stop triggered**: Intermittently, with `stop=1` and `size_mult=0.50` appearing through late 2021 and mid-2022
- **Duration**: Extended flat periods (e.g., Dec 2021 through Jan 2022: fully flat for ~6 weeks with `flat=1`)
- **Assessment**: The strategy reached its local high during the COVID crash (benefiting from safe-haven positioning), then struggled as the recovery rally and subsequent inflation/rate hiking cycle whipsawed the signal. The drawdown stop correctly limited exposure but could not prevent a ~15% drawdown.

### Drawdown Episode 3: Late 2023 -- 2025 (Terminal Drawdown)

- **Peak equity**: $2,067,316 (late 2023)
- **Trough equity**: ~$1,706,730 (Nov 2025)
- **Max drawdown**: ~17.4% from peak (and still declining at backtest end)
- **Stop triggered**: Multiple `stop=1` episodes in 2024-2025 with `size_mult=0.50`
- **Duration**: Equity never recovered above the 2023 peak through the end of backtest
- **Assessment**: This is an ongoing drawdown at the end of the backtest. The strategy has been bleeding capital since late 2023, and the final equity of $1,761,940 is well below the $2,276,857 all-time peak set in mid-2021. The 25.6% max drawdown reported in the summary metrics is measured from this all-time peak to some intra-period trough (likely computed from daily equity marks, not just from [DD] log entries which use weekly snapshots).

### Drawdown Stop Calibration Assessment

The drawdown stop system (10% threshold, 0.50x reduction, cooldown period) appears **too conservative for a 10.7% vol strategy**. It triggers frequently -- `stop=1` appeared on 1,030 out of 1,679 rebalance days (61.3%). This means the strategy is running at reduced capacity more than half the time. The frequent stop engagement suppresses returns while not preventing the 25.6% max drawdown, which exceeds the 20% target anyway. The stop needs recalibration: either raise the threshold (e.g., 15%) to let the strategy trade through normal volatility, or tighten the position sizing to reduce the drawdown itself.

---

## 5. Regime Analysis

### Signal Distribution (L1: Cu/Au Ratio Tilt)

| Tilt Signal | Days | Percentage |
|---|---|---|
| RISK_ON | 1,712 | 42.7% |
| RISK_OFF | 2,070 | 51.6% |
| NEUTRAL | 229 | 5.7% |
| **Total** | **4,011** | **100%** |

The strategy exhibits a persistent RISK_OFF bias (51.6% vs 42.7% RISK_ON). Over a 15.9-year period that included one of the strongest equity bull markets in history, spending the majority of time defensively positioned is a structural headwind. The Cu/Au ratio has been on a secular decline (from 0.56 to 0.30 over the backtest period), which drives the RISK_OFF lean. This is not necessarily wrong -- it reflects genuine deterioration in the global growth/risk appetite signal -- but it means the strategy is structurally underweight risk assets in an environment that rewarded risk-taking.

### Macro Regime Distribution (L2)

| Regime | Days | Percentage |
|---|---|---|
| GROWTH_POSITIVE | 2,853 | 71.1% |
| GROWTH_NEGATIVE | 648 | 16.2% |
| NEUTRAL | 211 | 5.3% |
| LIQUIDITY | 199 | 5.0% |
| INFLATION_SHOCK | 100 | 2.5% |
| **Total** | **4,011** | **100%** |

**Observations**:

1. **GROWTH_POSITIVE dominates** (71.1%). This is expected for 2010-2025 and limits the strategy's ability to be tested in adverse environments.

2. **INFLATION_SHOCK finally triggers** in v2, appearing on 100 days (2.5%). This was 0% in v1, confirming the inflation threshold fix (lowered from 100bp to 15bp for 20-day breakeven change) is working. However, 2.5% is still low for a period that included 2021-2023 inflation.

3. **GROWTH_NEGATIVE at 16.2%** provides some adverse-environment testing, but the concentration in GROWTH_POSITIVE means the strategy has limited out-of-sample coverage for recessionary environments.

4. **No observable return advantage by regime** can be extracted from the logs. The strategy does not log per-regime P&L, making it impossible to determine whether the macro tilt adds value. This is a significant gap in the diagnostic framework.

---

## 6. Layer Analysis

### L1 -- Copper/Gold Ratio (Primary Signal)

- **Valid days**: 4,011
- **Cu/Au ratio range**: [0.284, 0.854] -- within the expected [0.2, 1.2] range (fixed from v1's corrupted 572.9 max)
- **Signal flips**: 96 total, 6.0 per year
- **RISK_ON days**: 1,712 (42.7%)
- **RISK_OFF days**: 2,070 (51.6%)
- **NEUTRAL days**: 229 (5.7%)
- **Assessment**: The L1 signal changes state roughly every 2 months. This is a reasonable cadence for a macro signal. However, the persistent RISK_OFF bias suggests the signal may be structurally misaligned with modern markets where the Cu/Au ratio has been in secular decline since 2011.

### L2 -- Macro Regime Overlay

- **5 regimes triggered** (all 5, compared to only 4 in v1)
- Distribution heavily skewed toward GROWTH_POSITIVE (71%)
- Regime transitions triggered rebalances (`regime=1` flag): zero instances found in the logs, suggesting L2 changes are absorbed into the weekly Friday rebalance rather than triggering standalone events
- **Assessment**: The regime classification appears to be working mechanically, but without per-regime P&L attribution, its value-add is unknown.

### L3 -- DXY Filter

- **Filter triggered**: 13 rebalance events with `filter=1` out of 1,679 total rebalances (0.8%)
- When the DXY filter triggers, `size_mult` drops (observed values: 0.12x, 0.25x) -- a meaningful position reduction
- **Assessment**: The DXY filter fires extremely rarely (0.8% of rebalances). Its impact on portfolio-level returns is negligible given this low frequency. Either the DXY threshold is set too tight (rarely breached) or the filter concept needs rethinking.

### L4 -- Term Structure

- **32 L4-TS updates** over 15.9 years (approximately every 6 months)
- **Term structure state distribution** across commodities:
  - CL: Predominantly CONTANGO early (2010-2017), shifting to BACKWARDATION later (2021-2025)
  - HG: Mixed, oscillating between CONTANGO/FLAT/BACKWARDATION
  - SI: Mostly CONTANGO/BACKWARDATION, mixed
  - ZN: Predominantly BACKWARDATION early, shifting to CONTANGO/FLAT later
  - YC (Yield Curve): Persistently BACKWARDATION throughout the entire period
- **ts_mult impact**: When a commodity enters BACKWARDATION and the strategy is long, the multiplier drops to 0.00 (eliminates position). When in CONTANGO (favorable for long carry), multiplier is 1.00.
- **CL frequently zeroed out**: From 2022 onward, CL ts_mult = 0.00 due to persistent backwardation in oil futures. This means the strategy was systematically underweight crude oil in recent years.
- **Assessment**: The term structure layer is functioning but only recalculates every ~6 months (125 trading days). This is very slow for a signal that can shift within weeks. The layer appears to add value conceptually (avoiding adverse carry positions) but the update frequency limits its responsiveness.

---

## 7. Per-Instrument Breakdown

The backtest does not log per-instrument P&L, so exact attribution is not available. However, position frequency and direction can be inferred from the 1,399 position logs:

| Instrument | Long Appearances | Short Appearances | Total | Direction Bias | Notes |
|---|---|---|---|---|---|
| **6J (Yen)** | ~majority | ~minority | High | Predominantly long | Appears in nearly every active position set |
| **UB (Ultra Bond)** | ~majority | ~minority | High | Predominantly long | Consistent large allocation (4-8 contracts) |
| **ZN (10Y Note)** | ~majority | ~minority | High | Predominantly long | 4-9 contracts typically |
| **GC (Gold)** | ~mixed | ~mixed | High | Positive GC_final common | 1 contract typically |
| **SI (Silver)** | ~mixed | ~mixed | Moderate | Mixed | 1-2 contracts |
| **CL (Crude Oil)** | 567 long | 388 short | 955 total | Slight long bias | 1-4 contracts; frequently zeroed by L4 |
| **HG (Copper)** | 63 long | 111 short | 174 total | Short bias | Infrequent; 1-3 contracts |
| **MES (E-mini S&P)** | 5 long | 22 short | 27 total | Short bias | Only available from ~2019 |
| **MNQ (Micro Nasdaq)** | 9 long | 62 short | 71 total | Strong short bias | Only available from ~2019 |

**Observations**:

1. **The strategy is structurally a bond-long, equity-short, yen-long portfolio** in RISK_OFF mode (51.6% of the time). This is essentially a risk-parity-like safe-haven trade. In a bull market, this is a structural drag.

2. **MES/MNQ short bias** (2019-2025): When the strategy does trade equities, it overwhelmingly shorts them. Over a period where the S&P 500 roughly doubled and the Nasdaq tripled, this is a major performance headwind.

3. **Commodity allocation is thin**: GC typically 1 contract, SI 1-2, CL 1-4. The notional cap (`com_cap = 40% * equity`) limits commodity exposure, but the binding constraint appears to be the small contract counts after L4 term structure filtering.

4. **No per-instrument P&L available**: This is a critical gap. Without knowing which instruments are making money and which are losing, it is impossible to determine whether the signal works for some asset classes but not others.

---

## 8. Critical Assessment

### The Sharpe of 0.34 Is Not Investable

A Sharpe ratio of 0.34 is below the threshold for institutional interest, which typically requires 0.5 minimum for consideration and 0.8+ for allocation. At 0.34, the strategy's excess return is indistinguishable from noise over realistic sample sizes. A t-statistic test yields: t = Sharpe * sqrt(years) = 0.34 * sqrt(15.9) = 1.36, well below the 1.96 threshold for 95% confidence. **We cannot reject the null hypothesis that this strategy has zero alpha.**

### Turnover of 46.7x Is Extreme

For a macro regime-following strategy that flips signal 6 times per year, 46.7x annual turnover is wildly excessive. This implies the portfolio is being fully turned over nearly every trading week. The cause appears to be the combination of:
- Weekly Friday rebalances
- Daily rebalances triggered by tilt changes, drawdown stops, and DXY filter activations (tilt=1 triggered 96 times, stop=1 on 1,030/1,679 rebalances, filter=1 on 13 rebalances)
- Position direction changes on tilt flips (e.g., UB:7 long to UB:-4 short in a single rebalance)
- Frequent flat periods (`flat=1` on 285/1,679 rebalances = 17%)

At the contract sizes traded (5-8 bond futures, 3-4 CL, etc.), each full portfolio turn costs approximately $500-$2,000 in commissions plus slippage. At 46.7x per year, this adds approximately 2-4% annual drag that is NOT reflected in the backtest (which assumes zero transaction costs). **Adjusting for realistic execution costs, the 3.6% CAGR would likely drop to 0-2%.**

### Max Drawdown of 25.6% Exceeds the 20% Target

The drawdown stop triggers at 10% and reduces sizing, but the strategy still reaches 25.6% peak-to-trough. This means the risk management framework is not achieving its stated objective. The issue is compounded by the fact that the stop is engaged 61% of the time -- it is always applying the brakes but never preventing the large drawdowns. This suggests the stop threshold is too low (triggers on normal vol) while the position sizing is too aggressive for the signal quality.

### Profit Factor of 1.075 Is Razor-Thin

A profit factor of 1.075 means for every dollar lost, the strategy earns $1.075. This leaves essentially zero margin for transaction costs, slippage, data delays, or model degradation. In live trading, a profit factor below 1.30 typically turns negative after costs. The strategy is essentially breakeven before costs and likely unprofitable after them.

### Is the Alpha Real?

Several indicators suggest there may be a genuine signal buried in the noise:

**Positive signals**:
- SPX correlation of -0.17 indicates the strategy is not simply short/long the market
- Signal flip rate of 6/year is stable and not overfit
- The strategy survived 15.9 years without a permanent capital impairment (unlike v1)
- Win rate of 45.6% with a positive (if thin) profit factor suggests slight positive expectancy
- The Cu/Au ratio has documented academic support as a macro risk appetite indicator

**Negative signals**:
- Sharpe 0.34 is statistically indistinguishable from zero
- RISK_OFF bias (52%) during a secular bull market suggests structural misalignment
- No per-instrument P&L makes it impossible to isolate where value is created
- The strategy's best equity mark ($2.28M in 2021) occurred during a historically unusual period (post-COVID stimulus, zero rates)
- The terminal drawdown (2023-2025) suggests the signal may be degrading

**Verdict**: The alpha, if it exists, is small, inconsistent, and likely insufficient to survive transaction costs. The strategy structure (macro regime -> position tilt) is sound in principle, but the Cu/Au ratio alone does not generate enough predictive power to produce investable returns.

---

## 9. Recommendations

### Near-Term (Required Before Any Further Capital Allocation)

1. **Implement per-instrument P&L tracking**: The single most important missing diagnostic. Without knowing which instruments contribute positively and which are drag, optimization is blind. Log daily mark-to-market by instrument.

2. **Add transaction cost modeling**: The 46.7x turnover likely eliminates all gross returns. Model round-trip costs per instrument (commission + estimated slippage at observed contract sizes) and report net-of-cost metrics.

3. **Reduce turnover**: The weekly full-portfolio rebalance is unnecessary for a signal that flips 6 times per year. Consider:
   - Rebalance monthly instead of weekly
   - Add a rebalance band (only trade if positions deviate >20% from target)
   - Eliminate same-direction rebalances (e.g., do not adjust from 7 UB to 8 UB)

4. **Recalibrate the drawdown stop**: A 10% threshold that fires 61% of the time is not a stop -- it is a permanent position limiter. Either raise to 15-20% (let the strategy trade through normal vol) or reduce base position sizing so 10% drawdowns are rare.

### Medium-Term (Signal Improvement)

5. **Enrich the signal ensemble**: The Cu/Au ratio alone has insufficient predictive power. Consider adding:
   - Credit spreads (HY-IG) as a complementary risk appetite measure
   - VIX term structure (contango/backwardation)
   - ISM/PMI momentum
   - Global money supply growth

6. **Address the RISK_OFF structural bias**: The secular decline in Cu/Au since 2011 means the strategy is perpetually bearish. Consider detrending the ratio or using a relative measure (e.g., ratio relative to its 2-year rolling median).

7. **Increase L4 term structure update frequency**: Every 6 months is too slow. Monthly updates would be more responsive to shifting carry regimes.

8. **Expand INFLATION_SHOCK coverage**: At 2.5% of days during 2010-2025 (which included significant inflation), this regime is under-triggered. The 2021-2023 inflation period should have produced more INFLATION_SHOCK days.

### Long-Term (Validation)

9. **Out-of-sample testing**: The entire 15.9-year period was used for development. Split into in-sample (2010-2020) and out-of-sample (2020-2025), re-fit parameters on in-sample, and validate on out-of-sample. If the Sharpe degrades further, the in-sample results are likely overfit.

10. **Monte Carlo robustness**: Run parameter perturbation analysis. If small changes to thresholds (e.g., Cu/Au breakpoints, drawdown stop levels, regime definitions) cause large changes in outcomes, the strategy is fragile.

11. **Benchmark comparison**: Compare against naive alternatives:
    - 60/40 SPX/AGG
    - Risk parity (equal vol allocation across instruments)
    - Buy-and-hold gold
    - Simple momentum (12-1 month) on the same instrument universe

    If the Cu/Au strategy cannot beat these simpler approaches, the complexity is not justified.

---

## Appendix A: Diagnostic Summary (from backtest output)

```
Data Ingestion:
  HG: 3,995 bars  GC: 3,982 bars  CL: 3,998 bars
  SI: 3,964 bars  ZN: 4,003 bars  UB: 4,002 bars
  6J: 3,999 bars  MES: 1,696 bars  MNQ: 1,696 bars
  DXY: 5,240  VIX: 9,415  HY: 7,689  FedBS: 1,205

Cu/Gold Ratio:
  Valid days: 4,011  Range: [0.284, 0.854]
  First: 0.557  Last: 0.303

Signal Distribution:
  RISK_ON: 1,712  RISK_OFF: 2,070  NEUTRAL: 229

Regime Distribution:
  GROWTH+: 2,853  GROWTH-: 648  INFL: 100  LIQ: 199  NEUT: 211

Liquidity Score:
  Min: -3.251  Max: 4.586  Mean: 0.486

Position Activity:
  Days with positions: 3,534 / 4,011 (88.1%)
  Max GC contracts: 1.0  Max HG contracts: 3.0

Final Positions:
  6J: 4  UB: 7  SI: 1  GC: 1  CL: -3  ZN: 8  HG: -2  MNQ: -7  MES: -12
```

## Appendix B: Kill Criteria Status

| Criterion | Threshold | Actual | Status |
|---|---|---|---|
| Sharpe Ratio | >= 0.80 | 0.34 | FAIL |
| Sortino Ratio | >= 1.00 | 0.33 | FAIL |
| Max Drawdown | < 20% | 25.6% | FAIL |
| Win Rate | >= 45% | 45.6% | PASS (marginal) |
| Profit Factor | >= 1.30 | 1.08 | FAIL |
| Annual Turnover | < 15x | 46.7x | FAIL |
| SPX Correlation | < 0.50 | -0.17 | PASS |
| Signal Flips/Year | <= 12 | 6.0 | PASS |

**Passing**: 3 of 8 criteria. **Failing**: 5 of 8 criteria.

The three passing criteria (win rate, correlation, flips) measure structural properties of the signal rather than economic performance. All four economic performance criteria (Sharpe, Sortino, profit factor, turnover) fail. This pattern is consistent with a strategy that has a theoretically sound structure but insufficient signal strength to generate returns after real-world frictions.
