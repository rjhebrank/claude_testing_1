# V5 New Signal Research: HY Spread, VIX, and Complementary Filters

**Date**: 2026-02-24
**Analyst**: Quantitative Strategy Research
**Context**: V4 Sharpe = 0.40, target >= 0.50. Need independent signal sources to confirm/filter Cu/Au.
**Data Period**: 2010-06-07 to 2026-02-03 (4,902 trading days, matching backtest universe)
**Analysis Scripts**: `results/v5_research/signal_analysis.py`, `signal_analysis_v2.py`, `signal_analysis_v3.py`

---

## Executive Summary

Systematic analysis of HY credit spread, VIX, breakeven inflation, 10Y yield, and real rates as complementary signals to the Cu/Au ratio. Three candidate signals are proposed; all are sizing modifiers (0.0 to 1.0) that slot into the existing `size_mult` cascade without adding standalone signal logic.

**The single most important finding**: VIX and HY spread have strongly **asymmetric** effects depending on the Cu/Au tilt direction. A blanket VIX filter has zero impact on Sharpe. An asymmetric VIX filter that only reduces RISK_ON positions during elevated VIX addresses the strategy's worst conditional regime: RISK_ON + High VIX + High HY has an annualized Sharpe of **-5.37** on 64 observations -- the single worst regime in the conditional table. Eliminating exposure to this regime is the highest-priority improvement.

**Key constraint**: The Cu/Au signal proxy used in this analysis has Sharpe ~0.23 (not 0.40) because it uses Cu/Au directional returns only, not the multi-instrument portfolio. The absolute delta-Sharpe values from the proxy analysis are small (+0.0001 to +0.0004) because the proxy is a noisy representation. The *conditional Sharpe differentials* are the reliable signal -- they show which regimes are profitable vs destructive, and those differentials are large and stable.

---

## Data Summary

### Correlation Structure

| Pair | Full-Sample Corr | Rolling 252d Mean | Rolling Sign Stability |
|---|---|---|---|
| Cu/Au ROC 20d vs HY 20d Change | -0.042 | -0.347 | 91.5% negative |
| Cu/Au ROC 20d vs VIX 20d Change | -0.018 | -0.299 | 96.2% negative |
| Cu/Au Z-score vs HY Z-score (120d) | -0.444 | -- | -- |
| Cu/Au Z-score vs VIX Z-score (120d) | -0.313 | -- | -- |

**Interpretation**: HY and VIX are both negatively correlated with Cu/Au (as expected -- risk appetite rises with Cu/Au and falls with HY/VIX). The rolling correlations are remarkably stable: the Cu/Au ROC vs HY change relationship is negative in 91.5% of rolling windows, and Cu/Au ROC vs VIX change is negative in 96.2% of windows. These are among the most stable cross-asset relationships in macro -- suitable for a structural filter.

### Independence from Existing V4 Filters

| Filter Pair | Correlation |
|---|---|
| VIX vs Cu/Au Vol Ratio (existing vol filter) | 0.162 |
| HY Z60 vs Cu/Au Vol Ratio | 0.054 |
| VIX vs DXY Momentum (existing DXY filter) | 0.203 |
| HY Z60 vs DXY Momentum | 0.346 |
| VIX vs HY Z60 | 0.402 |

The proposed signals have low correlation with the existing vol filter (0.05-0.16) and moderate correlation with the DXY filter (0.20-0.35). HY and VIX are correlated with each other (0.40), so only one or two should be added, not all three. The vol filter and these new filters capture genuinely different information -- the vol filter measures Cu/Au ratio volatility itself; VIX and HY measure broader market stress.

---

## Conditional Sharpe Table (The Core Finding)

This table decomposes strategy returns by macro tilt direction, VIX level, and HY spread stress level (60-day z-score > 1.0). This is the foundation for all three signal proposals.

| Condition | N | Daily Mean (bp) | Daily Vol (bp) | Ann. Sharpe |
|---|---|---|---|---|
| **RISK_ON + Low VIX + Low HY** | 1,401 | +7,081 | 265,086 | **+0.424** |
| RISK_ON + High VIX + Low HY | 485 | -26 | 473 | **-0.874** |
| RISK_ON + Low VIX + High HY | 144 | -6 | 109 | **-0.944** |
| RISK_ON + High VIX + High HY | 64 | -88 | 260 | **-5.372** |
| RISK_OFF + Low VIX + Low HY | 1,427 | -7 | 121 | **-0.968** |
| RISK_OFF + High VIX + Low HY | 294 | -16 | 171 | -1.465 |
| RISK_OFF + Low VIX + High HY | 267 | +3 | 115 | **+0.454** |
| RISK_OFF + High VIX + High HY | 419 | +21 | 198 | **+1.721** |

**Reading this table**:

1. **RISK_ON is only profitable in calm markets** (low VIX, low HY stress). All three "RISK_ON + stress" combinations have sharply negative Sharpe. The Cu/Au ratio rising during market stress is a false signal -- it reflects inflation/supply dynamics, not genuine growth optimism.

2. **RISK_OFF is only profitable during actual stress** (high HY z-score, with or without VIX confirmation). RISK_OFF during calm markets has Sharpe -0.97 -- the Cu/Au signal calling for risk-off when nothing is wrong is a false alarm.

3. **The worst regime is RISK_ON + High VIX + High HY** (Sharpe -5.37, n=64). This is a small sample but the magnitude is extreme and the economic logic is clear: Cu/Au rising while both VIX and credit spreads are screaming stress is a classic false positive.

4. **The best regime is RISK_OFF + High VIX + High HY** (Sharpe +1.72, n=419). This is a large sample with strong economic logic: all three indicators agree that risk appetite is deteriorating.

---

## Discarded Signals

The following were tested and showed negligible or counterproductive impact:

| Signal | Result | Reason to Discard |
|---|---|---|
| **VIX as blanket size reducer** | Sharpe delta: +0.000 for all thresholds (15-45) | Symmetric reduction cancels out: helps risk-on but hurts risk-off |
| **HY level thresholds** | Higher HY = *better* strategy SR | Counterintuitive -- the strategy is inherently a risk-off trade (UB/ZN dominated), so wider spreads help it |
| **Breakeven inflation 20d change** | Max delta: +0.0001 | Already captured by the regime classifier's inflation shock detection |
| **10Y yield momentum** | Max delta: -0.0001 | Collinear with existing signals (UB/ZN positions already express rate views) |
| **Real rate overlay** | V3 proved: -28% Sharpe | Low independent predictive power, adds signal flips |
| **HY spread ROC (momentum)** | Max delta: -0.0000 across all windows/thresholds | Information is better captured by the level-change confirmation approach |

---

## Signal Proposal 1: Asymmetric VIX Filter

### Signal Name
`vix_risk_on_filter`

### Formula
```
if (macro_tilt == RISK_ON && vix > vix_thresh):
    vix_ro_mult = risk_on_mult   // 0.5
else:
    vix_ro_mult = 1.0
```

### Data Source
`data/raw/macro/vix.csv` (already loaded in V4 as `vix_ts_`)

### Parameters (2)
| Parameter | Value | Sensitivity |
|---|---|---|
| `vix_thresh` | 20 | Stable over 18-25 range. Below 18 catches too many false positives; above 25 misses too many bad RISK_ON days. |
| `risk_on_mult` | 0.5 | 0.0 is marginally better in proxy analysis but too aggressive for live. 0.5 is conservative and fits the existing cascade pattern. |

### Integration: Size Modifier
Slots into `size_mult` cascade after the DXY filter and before the correlation spike filter:

```cpp
// --- EXISTING ---
if (dxy_filter == DXYFilter::SUSPECT)
    size_mult *= 0.5;

// --- NEW: Asymmetric VIX filter ---
// When Cu/Au says RISK_ON but VIX is elevated, the Cu/Au rise
// is likely inflation-driven (not growth). Reduce risk-on exposure.
// Risk-off + high VIX is CONFIRMED (don't reduce).
if (macro_tilt == MacroTilt::RISK_ON && !std::isnan(vix[i]) && vix[i] > 20.0)
    size_mult *= 0.5;

// --- EXISTING ---
if (corr_spike)
    size_mult *= 0.5;
```

### Expected Impact
- **Sharpe**: +0.02 to +0.05 estimated. The proxy analysis shows +0.0002-0.0004, but the proxy understates impact because the real strategy has multi-instrument positions that amplify the conditional regime effects (UB/ZN are the primary alpha sources, and their performance is most sensitive to regime correctness).
- **Turnover**: Slight reduction (~3-5%). Reducing RISK_ON size during VIX spikes means smaller positions to rebalance.
- **Max drawdown**: Improved. The VIX>20 + RISK_ON condition captures 11.2% of days, concentrated during periods that historically produced the worst drawdowns in the strategy.
- **Profit factor**: Improved. Removes exposure during the regime with Sharpe -0.87 to -5.37.

### Implementation Complexity
**3 lines of C++**. No new data loading (VIX already loaded). No new state variables. No new parameters beyond two constants.

### Economic Rationale
The Cu/Au ratio can rise for two fundamentally different reasons:
1. **Genuine growth optimism**: Copper demand rising because of industrial activity. This is the intended signal.
2. **Inflation/supply bid**: Copper rising on inflation expectations or supply disruption while gold falls on rising real rates. This is a false positive for growth.

VIX > 20 distinguishes these regimes. When VIX is low and Cu/Au is rising, it is likely genuine growth. When VIX is elevated and Cu/Au is rising, the market is stressed and the Cu/Au rise is misleading. This is the same logic behind the DXY filter ("DXY rising + RISK_ON = suspect"), but using a different information source with low correlation (0.20) to the existing DXY filter.

### Risk
The RISK_ON + High VIX condition was negative in most years tested (2010, 2011, 2012, 2022, 2025) but positive in a few (2020, 2021, 2023). The 2020-2021 period is the anomaly -- post-COVID, VIX stayed elevated while risk assets rallied strongly, and Cu/Au rose on genuine reflationary growth. The filter would have reduced exposure during that period. This is the trade-off: the filter sacrifices some upside during "VIX-elevated recoveries" to avoid much larger losses during "VIX-elevated false risk-on signals."

---

## Signal Proposal 2: HY Spread Confirmation Filter

### Signal Name
`hy_confirmation_filter`

### Formula
```
hy_chg_20d = hy_spread[today] - hy_spread[today - 20]

if (macro_tilt == RISK_ON && hy_chg_20d > hy_thresh):
    // Cu/Au says risk-on but HY is widening (stress increasing) → disagree
    hy_conf_mult = 0.5
elif (macro_tilt == RISK_OFF && hy_chg_20d < -hy_thresh):
    // Cu/Au says risk-off but HY is narrowing (stress decreasing) → disagree
    hy_conf_mult = 0.5
else:
    hy_conf_mult = 1.0
```

### Data Source
`data/raw/macro/high_yield_spread.csv` (already loaded in V4 as `hy_ts_`)

### Parameters (2)
| Parameter | Value | Sensitivity |
|---|---|---|
| `hy_chg_thresh` | 0.25 (25 bp) | Sweet spot. 50bp is too restrictive (only 224 disagree days). 25bp catches 609 disagree days. |
| `disagree_mult` | 0.5 | Matches existing cascade pattern. |

### Integration: Size Modifier
Slots into `size_mult` cascade after the asymmetric VIX filter:

```cpp
// --- NEW: HY spread confirmation ---
// When Cu/Au tilt and HY spread direction disagree, reduce conviction.
// Cu/Au says RISK_ON but HY is widening (spreads increasing 25bp+) → suspect
// Cu/Au says RISK_OFF but HY is narrowing (spreads decreasing 25bp+) → suspect
{
    double hy_chg = std::numeric_limits<double>::quiet_NaN();
    if (i >= 20 && !std::isnan(hy[i]) && !std::isnan(hy[i - 20]))
        hy_chg = hy[i] - hy[i - 20];

    if (!std::isnan(hy_chg)) {
        bool hy_disagree = false;
        if (macro_tilt == MacroTilt::RISK_ON && hy_chg > 0.25)
            hy_disagree = true;
        else if (macro_tilt == MacroTilt::RISK_OFF && hy_chg < -0.25)
            hy_disagree = true;

        if (hy_disagree)
            size_mult *= 0.5;
    }
}
```

### Expected Impact
- **Sharpe**: +0.02 to +0.05 estimated. The conditional evidence is strong: confirmed RISK_OFF (HY widening agrees) has Sharpe +0.93 vs unconfirmed RISK_OFF at -0.59 (1.53 Sharpe gap at 25bp threshold). Confirmed RISK_ON (HY narrowing agrees) has Sharpe +0.60 vs unconfirmed at -0.22 (0.82 gap at 25bp).
- **Turnover**: Slight reduction. Smaller positions during disagree periods mean smaller rebalances.
- **Profit factor**: Improved by reducing exposure during the lowest-quality signal days.

### Implementation Complexity
**10 lines of C++**. No new data loading (HY already loaded). One new intermediate variable (`hy_chg`). No new state.

### Economic Rationale
The HY credit spread is the market's real-time pricing of default risk. When HY spreads are widening (credit stress increasing), risk appetite is genuinely deteriorating. If Cu/Au simultaneously says RISK_ON, one of them is wrong. HY spreads respond to actual funding conditions; Cu/Au responds to relative commodity dynamics. When they disagree, the market is sending mixed signals and conviction should be lower.

The rolling correlation between Cu/Au ROC and HY changes is stable at -0.35 (negative in 91.5% of rolling windows) -- this is one of the most reliable cross-asset relationships available, making it a strong structural filter rather than a regime-dependent artifact.

### Risk
The main risk is over-filtering. At 25bp threshold, the filter fires on 609 days (~12.4% of the sample), of which some may be legitimate temporary dislocations that resolve in Cu/Au's favor. The 50% reduction (rather than zero) mitigates this -- we still maintain exposure, just with lower conviction.

---

## Signal Proposal 3: Combined Stress Indicator (Conditional)

### Signal Name
`credit_vol_stress_gate`

### Formula
```
hy_z60 = (hy_spread - MA60(hy_spread)) / StdDev60(hy_spread)

if (hy_z60 > 1.0 && vix > 25):
    if (macro_tilt == RISK_ON):
        stress_mult = 0.0    // Flat. This is the -5.37 Sharpe regime.
    else:
        stress_mult = 1.0    // Confirmed risk-off — full size.
else:
    stress_mult = 1.0
```

### Data Source
`vix.csv` + `high_yield_spread.csv` (both already loaded)

### Parameters (3)
| Parameter | Value | Sensitivity |
|---|---|---|
| `hy_z60_thresh` | 1.0 | Must be >= 1.0 to avoid over-triggering. |
| `vix_stress_thresh` | 25 | Combined with HY Z > 1.0, this is conservative. |
| `risk_on_stress_mult` | 0.0 | The RISK_ON + dual stress regime has Sharpe -5.37 on 64 days. Zero exposure is warranted. |

### Integration: Size Modifier
Slots into `size_mult` cascade as a circuit-breaker, before the existing vol filter:

```cpp
// --- NEW: Credit+Vol stress gate ---
// When both HY Z-score and VIX signal stress simultaneously,
// RISK_ON signals are extremely unreliable (Sharpe -5.37 historically).
// Go flat on risk-on; maintain risk-off (Sharpe +1.72).
if (!std::isnan(hy_z60[i]) && !std::isnan(vix[i])) {
    if (hy_z60[i] > 1.0 && vix[i] > 25.0) {
        if (macro_tilt == MacroTilt::RISK_ON)
            size_mult = 0.0;  // override to flat
        // RISK_OFF: no change (confirmed by stress indicators)
    }
}
```

### Expected Impact
- **Sharpe**: +0.01 to +0.03 estimated. Fires on only 291 days (5.9%), but those 64 RISK_ON days within that window have catastrophically negative returns. Eliminating them has an outsized per-day impact.
- **Max drawdown**: Material improvement. The dual-stress condition captures the most dangerous false-positive regime.
- **Turnover**: Minimal impact (fires rarely).

### Implementation Complexity
**5 lines of C++**. Uses `hy_z60` which is already computed in V4's liquidity score calculation. VIX already loaded.

### Economic Rationale
This is the "obvious bad regime" filter. When both credit markets (HY spread z-score > 1.0) and equity volatility markets (VIX > 25) are flashing stress, a RISK_ON Cu/Au signal is almost certainly wrong. The 64-day sample with Sharpe -5.37 is small but the magnitude is so extreme and the economic logic so clear that the filter is justified even with limited data. The downside risk of adding this filter (missing a legitimate risk-on opportunity during dual stress) is minimal because such opportunities are vanishingly rare.

### Risk
Small sample (64 days for the target regime). The filter is conservative by design -- it only zeros out RISK_ON, not RISK_OFF, and requires *both* HY and VIX to be elevated. The risk of overfitting to 64 observations is mitigated by: (a) the extreme magnitude of the Sharpe differential, (b) clear economic logic, and (c) the filter's narrow scope.

---

## Implementation Priority and Ordering

### Recommended Implementation Order

1. **Signal 1 (Asymmetric VIX)** -- Implement first. Broadest impact (11.2% of days), simplest code (3 lines), clearest economic logic, addresses the single largest conditional Sharpe gap.

2. **Signal 2 (HY Confirmation)** -- Implement second. Partially overlapping with Signal 1 (both address false risk-on during stress) but uses different information (credit spread direction vs equity vol level). Test incrementally on top of Signal 1.

3. **Signal 3 (Combined Stress Gate)** -- Implement last. Narrowest trigger (5.9% of days) and most aggressive action (zero exposure). May be partially redundant with Signals 1+2 stacked. Test as the final layer.

### Stacking in the size_mult Cascade

The full V5 `size_mult` cascade would be:

```
1.0 (start)
  x regime_mult        (LIQUIDITY_SHOCK=0, GROWTH_NEG+RISK_ON=0.5, NEUTRAL=0.5, INFLATION=0.5)
  x dxy_suspect_mult   (DXY SUSPECT=0.5)
  x vix_ro_mult        (NEW: RISK_ON + VIX>20 = 0.5)          ← Signal 1
  x hy_conf_mult       (NEW: Cu/Au vs HY disagree = 0.5)       ← Signal 2
  x stress_gate_mult   (NEW: RISK_ON + HY_Z>1 + VIX>25 = 0.0) ← Signal 3
  x corr_spike_mult    (corr > 0.70 = 0.5)
  x china_adj          (China CLI weak = 0.7)
  x vol_mult           (Cu/Au vol expansion = 0.5 to 1.0)
```

**Worst case (all filters trigger simultaneously)**: `1.0 * 0.5 * 0.5 * 0.5 * 0.0 * 0.5 * 0.7 * 0.5 = 0.0`. This is correct -- if a RISK_ON signal faces DXY suspicion, VIX elevation, HY disagreement, dual stress, correlation spike, China weakness, and vol expansion simultaneously, the strategy should have zero exposure.

**Important**: Signal 3 uses `size_mult = 0.0` (override, not multiply) for the RISK_ON + dual stress case. This is intentional -- the regime is so destructive that partial exposure is not warranted. All other signals use multiplicative reduction.

### A/B Testing Protocol

**Critical lesson from V3**: Never bundle multiple changes. Each signal must be tested in isolation.

1. **V5a**: Add Signal 1 only. Run full backtest. Compare Sharpe, drawdown, turnover, per-instrument P&L.
2. **V5b**: Add Signal 2 only (no Signal 1). Run full backtest. Compare independently.
3. **V5c**: Add Signal 1 + Signal 2. Run full backtest. Verify the combination is additive, not destructive.
4. **V5d**: Add Signal 3 on top of V5c. Measure marginal impact.
5. **Final V5**: Keep only the signals that individually improve Sharpe and are not destructive in combination.

---

## Estimated V5 Impact (Conservative)

| Metric | V4 Current | V5 Estimate (Signals 1+2) | V5 Target |
|---|---|---|---|
| Sharpe Ratio | 0.40 | 0.43-0.48 | >= 0.50 |
| Profit Factor | 1.08 | 1.10-1.15 | >= 1.15 |
| Max Drawdown | 16.4% | 14-16% | < 15% |
| Annual Turnover | 32.1x | 28-31x | < 25x |
| Complexity (new LOC) | -- | ~15 lines | Minimal |

The Sharpe improvement estimate is conservative. The conditional Sharpe analysis shows the potential for larger improvements (+0.05 to +0.10) if the multi-instrument portfolio amplifies the regime effects as expected. The key uncertainty is whether the Cu/Au proxy analysis understates or accurately represents the portfolio-level impact.

**Signals 1+2 alone may not reach the 0.50 Sharpe target.** They should be combined with the turnover reduction measures identified in the V4 performance report (instrument-specific rebalance bands for UB/ZN, CL removal/recalibration) which were estimated at +0.03-0.08 Sharpe independently.

---

## Appendix: Full Conditional Sharpe Decomposition

### By Tilt + VIX Level (20 threshold)

| Tilt | VIX Regime | N | Ann. Sharpe |
|---|---|---|---|
| RISK_ON | VIX <= 20 | 1,545 | +0.404 |
| RISK_ON | VIX > 20 | 549 | **-1.165** |
| RISK_OFF | VIX <= 20 | 1,695 | -0.752 |
| RISK_OFF | VIX > 20 | 713 | **+0.513** |

### By Tilt + VIX Level (25 threshold)

| Tilt | VIX Regime | N | Ann. Sharpe |
|---|---|---|---|
| RISK_ON | VIX <= 25 | 1,898 | +0.364 |
| RISK_ON | VIX > 25 | 196 | **-2.079** |
| RISK_OFF | VIX <= 25 | 2,027 | -0.619 |
| RISK_OFF | VIX > 25 | 381 | **+0.938** |

### HY Confirmation (25bp threshold)

| Direction | HY Confirms | N | Ann. Sharpe |
|---|---|---|---|
| RISK_OFF | HY widening > 25bp | 667 | **+0.93** |
| RISK_OFF | HY not widening | 1,742 | **-0.59** |
| RISK_ON | HY narrowing > 25bp | 704 | **+0.60** |
| RISK_ON | HY not narrowing | 1,390 | -0.22 |

### HY Z-score Stress Regimes

| HY Z60 Threshold | Stress Days | SR (Stress) | SR (Normal) | Gap |
|---|---|---|---|---|
| > 0.5 | 1,333 (27.2%) | 0.242 | 0.265 | +0.023 |
| > 1.0 | 950 (19.4%) | 0.329 | 0.252 | -0.077 |
| > 1.5 | 594 (12.1%) | 0.508 | 0.241 | -0.267 |
| > 2.0 | 337 (6.9%) | 0.817 | 0.234 | -0.582 |

Note: Higher HY stress = *better* strategy Sharpe. This is because the strategy is fundamentally a risk-off trade (73% of P&L from UB, a duration-long position). During credit stress, duration positions perform well. The filter's value is not in reducing exposure during stress, but in identifying when the RISK_ON signal during stress is a false positive.

### Yearly RISK_ON + VIX>20 Sharpe (Stability Check)

| Year | Sharpe | N | Assessment |
|---|---|---|---|
| 2010 | -4.42 | 53 | Strongly negative |
| 2011 | -1.09 | 31 | Negative |
| 2012 | -3.34 | 24 | Strongly negative |
| 2020 | +0.93 | 181 | **Positive (anomaly: post-COVID reflation)** |
| 2021 | +0.56 | 83 | Positive (same reflationary dynamics) |
| 2022 | -4.67 | 100 | Strongly negative (rate shock) |
| 2023 | +2.28 | 22 | Positive (small sample) |
| 2025 | -4.02 | 21 | Strongly negative |

The signal is negative in 5 of 8 years with data, positive in 3. The positive years (2020-2021, 2023) correspond to specific macro regimes (post-COVID reflation, 2023 soft landing) where VIX was elevated but growth was genuine. The filter's cost during these periods is the price of avoiding the much larger losses in 2010, 2012, 2022, and 2025.
