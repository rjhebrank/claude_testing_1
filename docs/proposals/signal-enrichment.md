# Signal Enrichment Proposals: Copper-Gold Macro Strategy v2.0

**Author**: Quantitative Strategy Research
**Date**: 2026-02-24
**Status**: PROPOSAL -- Research Only, No Code Changes
**Target**: Improve Sharpe from 0.34 toward 0.80+ threshold; reduce turnover from 46.7x

---

## Diagnosis: Why Is the Sharpe 0.34?

Before proposing fixes, it is worth understanding the decomposition of the problem. The strategy has three compounding weaknesses:

1. **Signal is too binary and too noisy.** The composite signal is a vote of three {-1, 0, +1} sub-signals, producing a coarse output in [-1, +1] that collapses to a ternary tilt (RISK_ON / RISK_OFF / NEUTRAL). No conviction gradient means the strategy runs full size on weak signals and strong signals alike.

2. **Structural RISK_OFF bias destroys returns during the longest equity bull market in history.** The Cu/Au ratio declined secularly from 0.56 to 0.30 over the backtest, putting the strategy in RISK_OFF 51.6% of the time. This is the single largest source of drag -- the strategy was short equities and long bonds during years when risk-on was the dominant trade.

3. **Computed signals are wasted.** Real rates, real rate z-scores, DXY trend, ROC_10, ROC_60 are all computed and thrown away. The infrastructure already pays the cost of these calculations with zero return.

The five proposals below attack these three problems with data that is already on disk.

---

## Proposal 1: Cu/Au Ratio Realized Volatility Regime Filter (Conviction-Weighted Sizing)

### Signal Name
**CuAu_RealizedVol_Sizing** -- Use realized volatility of the Cu/Au ratio as a dynamic position sizing scalar, replacing the current binary full-size / half-size approach.

### Data Source
- `data/cleaned/futures/HG.csv` (close)
- `data/cleaned/futures/GC.csv` (close)
- No additional data required -- derived from the ratio already computed.

### Computation

```
ratio[i] = (HG[i] * 25000) / (GC[i] * 100)      // already computed
ratio_ret[i] = ln(ratio[i] / ratio[i-1])          // daily log return of ratio
rvol_20[i]  = std(ratio_ret[i-19..i]) * sqrt(252)  // 20-day annualized realized vol
rvol_60[i]  = std(ratio_ret[i-59..i]) * sqrt(252)  // 60-day annualized realized vol

// Volatility regime: compare short to long
vol_ratio = rvol_20[i] / rvol_60[i]

// Sizing scalar: inverse-vol with floor and cap
// When vol is expanding (vol_ratio > 1.5), cut size aggressively
// When vol is contracting (vol_ratio < 0.7), allow full/enlarged size
if (vol_ratio > 2.0):
    vol_sizing = 0.25          // crisis-level vol expansion
elif (vol_ratio > 1.5):
    vol_sizing = 0.50          // moderate vol expansion
elif (vol_ratio < 0.7):
    vol_sizing = 1.25          // compressed vol, higher conviction
else:
    vol_sizing = 1.0           // normal

// Additionally: size_mult *= min(1.0, target_vol / rvol_20)
// where target_vol = 10% (matching the strategy's realized 10.67% annual vol)
vol_target_scalar = min(1.0, 0.10 / rvol_20[i])
final_vol_sizing = vol_sizing * vol_target_scalar
```

Apply `final_vol_sizing` as a multiplier on `size_mult` in the sizing cascade (after regime/filter effects, before position limit checks).

### Expected Effect

| Metric | Direction | Magnitude | Reasoning |
|--------|-----------|-----------|-----------|
| Sharpe | UP | +0.10 to +0.20 | Reduces exposure during high-vol whipsaws that dominate losses |
| Turnover | DOWN | -10% to -20% | Smaller positions in volatile regimes = smaller rebalance deltas |
| Max DD | DOWN | -2% to -5% | Vol expansion precedes most drawdowns by 1-5 days |
| Profit Factor | UP | +0.05 to +0.10 | Removes worst-case days from loss distribution |

### Implementation Complexity
- **Estimated lines**: 25-35 C++ lines
- **Location**: After line 661 (ratio construction), add `ratio_ret` and `rvol_20/rvol_60` computations. Apply the scalar inside the size_mult cascade block (around lines 1058-1078).
- **Difficulty**: Low. Uses `rolling_std` already implemented. No new data loading.

### C++ Pseudocode

```cpp
// After ratio[] computation (line 655)
std::vector<double> ratio_ret(n, NaN);
for (int i = 1; i < n; ++i) {
    if (!isnan(ratio[i]) && !isnan(ratio[i-1]) && ratio[i-1] > 0.0)
        ratio_ret[i] = std::log(ratio[i] / ratio[i-1]);
}
auto rvol_20 = rolling_std(ratio_ret, 20);
auto rvol_60 = rolling_std(ratio_ret, 60);

// Inside main loop, after size_mult cascade:
if (!isnan(rvol_20[i]) && !isnan(rvol_60[i]) && rvol_60[i] > 0.0) {
    double vol_ratio = rvol_20[i] / rvol_60[i];
    double vol_sizing = 1.0;
    if (vol_ratio > 2.0)      vol_sizing = 0.25;
    else if (vol_ratio > 1.5) vol_sizing = 0.50;
    else if (vol_ratio < 0.7) vol_sizing = 1.25;

    double rvol_ann = rvol_20[i] * std::sqrt(252.0);
    double vol_target_scalar = std::min(1.0, 0.10 / std::max(rvol_ann, 0.01));
    size_mult *= vol_sizing * vol_target_scalar;
}
```

### Risks and Pitfalls
- **Overfitting thresholds**: The 0.7 / 1.5 / 2.0 breakpoints are empirical. Sensitivity test with +/-20% perturbation. If Sharpe swings more than 0.05, the thresholds are fragile.
- **Lagging indicator**: Realized vol trails actual vol by definition. A sudden regime break (e.g., COVID March 2020) will hit full-sized before the vol filter kicks in. Mitigation: the 20-day window is responsive enough for most regime shifts (catches within 3-5 days).
- **Stacking with existing filters**: This multiplies onto an already-complex size_mult cascade. The worst-case stacking (from the audit) already reduces to 1.1% of full size. Adding another 0.25x on top could make the strategy nearly inert. Guard: floor size_mult at 0.05 after all adjustments.

---

## Proposal 2: Activate the Real Rate Signal (Currently Dead Code)

### Signal Name
**RealRate_Trend_Overlay** -- Use the already-computed real rate z-score and real rate change as a confirmation/discount layer for the regime classifier, replacing the current dead-code status.

### Data Source
- `data/cleaned/macro/treasury_10y.csv` (column: `treasury_10y`, daily, 4.06 to 4.29 range recent)
- `data/cleaned/macro/breakeven_10y.csv` (column: `breakeven_10y`, daily, 2.35 recent)
- Both already loaded. Real rate = treasury_10y - breakeven_10y. Already computed at lines 678-690.

### Computation

The code already computes these three signals (lines 678-690) but stores them without using them:

```
real_rate     = treasury_10y - breakeven_10y       // already computed
rr_chg_20    = real_rate[i] - real_rate[i-20]      // already computed
rr_zscore    = rolling_zscore(real_rate, 120)       // already computed
```

Proposed integration into the composite signal and regime classifier:

**A. Real Rate Confirmation of Regime (modifies Layer 2 output)**

```
// After regime classification, before size_mult cascade:
if (regime == GROWTH_POSITIVE && rr_chg_20 > +0.30):
    // Rising real rates + positive growth = hawkish tightening
    // Risk assets face headwind from rates
    regime_confidence = 0.75    // discount growth-positive conviction
elif (regime == GROWTH_POSITIVE && rr_chg_20 < -0.20):
    // Falling real rates + positive growth = goldilocks
    regime_confidence = 1.25    // boost growth-positive conviction
elif (regime == GROWTH_NEGATIVE && rr_zscore > 1.5):
    // Very high real rates + negative growth = restrictive policy
    regime_confidence = 1.25    // boost growth-negative conviction (bearish)
else:
    regime_confidence = 1.0
```

**B. Real Rate as Composite Signal Component (modifies Layer 1 output)**

```
// Real rate direction as a 4th sub-signal in the composite
signal_rr = 0.0
if (rr_chg_20 < -0.15):  signal_rr = +1.0   // falling real rates = risk-on
elif (rr_chg_20 > +0.15): signal_rr = -1.0   // rising real rates = risk-off

// Revised composite: reweight to include real rates
// Old: composite = 0.33*ROC + 0.33*MA + 0.34*Z
// New: composite = 0.25*ROC + 0.25*MA + 0.25*Z + 0.25*RR
composite = 0.25 * sign(roc20) + 0.25 * signal_ma + 0.25 * signal_z + 0.25 * signal_rr
```

### Expected Effect

| Metric | Direction | Magnitude | Reasoning |
|--------|-----------|-----------|-----------|
| Sharpe | UP | +0.08 to +0.15 | Real rates are the dominant cross-asset driver (2022-2025 demonstrated this conclusively). Adding them breaks the Cu/Au ratio's blind spot during rate-hiking cycles. |
| Turnover | NEUTRAL | +/-5% | Fourth signal component adds some vote diversity but also smooths transitions |
| RISK_OFF bias | DOWN | -5% to -10% of RISK_OFF days | Falling real rates during 2019-2021 would have pushed the composite toward RISK_ON, partially offsetting the secular Cu/Au decline |
| Profit Factor | UP | +0.03 to +0.08 | Avoids the worst trades where Cu/Au said RISK_OFF but rates said goldilocks |

### Implementation Complexity
- **Estimated lines**: 15-20 C++ lines (the heavy lifting is already done)
- **Location**: Part A integrates at line ~968 (after regime classification, before size_mult). Part B modifies lines 839-842 (composite calculation) and requires weight changes.
- **Difficulty**: Very low. All inputs are already computed and stored in variables.

### C++ Pseudocode

```cpp
// Part B: In composite calculation (modify lines 839-842)
double signal_rr = 0.0;
if (!isnan(rr_chg[i])) {
    if (rr_chg[i] < -0.15) signal_rr = 1.0;       // falling real rates = risk-on
    else if (rr_chg[i] > 0.15) signal_rr = -1.0;   // rising real rates = risk-off
}

if (!isnan(roc20) && !isnan(zscore)) {
    double sign_roc20 = (roc20 > 0.0) ? 1.0 : -1.0;
    composite = 0.25 * sign_roc20 + 0.25 * signal_ma
              + 0.25 * signal_z   + 0.25 * signal_rr;
}

// Part A: After regime classification (after line 957)
double regime_confidence = 1.0;
if (regime == Regime::GROWTH_POSITIVE && rr_chg_val > 0.30)
    regime_confidence = 0.75;
else if (regime == Regime::GROWTH_POSITIVE && rr_chg_val < -0.20)
    regime_confidence = 1.25;
else if (regime == Regime::GROWTH_NEGATIVE && rr_z_val > 1.5)
    regime_confidence = 1.25;

size_mult *= regime_confidence;
```

### Risks and Pitfalls
- **Regime dependence**: Real rates were a dominant driver in 2022-2025 but were largely irrelevant in 2010-2018 (rates were pinned near zero). The signal may show strong in-sample fit for the recent period but add noise for the earlier decade. Mitigation: test on 2010-2019 subsample separately; if signal_rr is net-zero in that period, it is at least not harmful.
- **Correlation with existing signals**: Rising real rates often coincide with falling Cu/Au (both reflect risk-off). Adding a correlated signal may not improve the information ratio. Check the rank correlation between signal_rr and sign(ROC_20) -- if > 0.6, the diversification benefit is minimal.
- **Threshold sensitivity**: The +/-0.15 (15bp) threshold for rr_chg_20 and the +/-0.30 threshold for regime confirmation are initial estimates. The breakeven_10y data shows typical 20-day changes in the range of +/-0.10 to +/-0.30, so 0.15 should fire roughly 30-40% of the time.
- **Units verified**: Real rates are computed as `treasury_10y - breakeven_10y`, both in percentage points (e.g., 4.26 - 2.35 = 1.91%). A 20-day change of 0.15 means 15 basis points, which is a moderate move. This is correctly calibrated.

---

## Proposal 3: HY Spread Momentum as Independent Risk Appetite Signal

### Signal Name
**HY_Spread_Momentum** -- Use the rate of change and z-score of high-yield credit spreads as an independent risk appetite signal that cross-validates the Cu/Au ratio.

### Data Source
- `data/cleaned/macro/high_yield_spread.csv` (column: `high_yield_spread`, daily, in percentage points, e.g., 2.81 = 281bps)
- Already loaded and used only for the liquidity score (as a z-score component). The raw level and its momentum are unused.

### Computation

```
hy = high_yield_spread[i]                          // already loaded
hy_sma_20  = SMA(hy, 20)
hy_sma_60  = SMA(hy, 60)

// Momentum: rate of change over 20 days
hy_roc_20 = (hy[i] / hy[i-20]) - 1.0

// Trend: MA crossover (fast vs slow)
hy_trend = (hy_sma_20 < hy_sma_60) ? +1.0 : -1.0
// Tightening spreads (fast < slow, falling) = risk-on = +1
// Widening spreads (fast > slow, rising) = risk-off = -1

// Z-score of absolute level
hy_z120 = rolling_zscore(hy, 120)

// Composite HY signal
hy_signal = 0.0
if (hy_roc_20 < -0.05 && hy_trend > 0):   hy_signal = +1.0  // spreads compressing, confirmed
elif (hy_roc_20 > +0.10 && hy_trend < 0):  hy_signal = -1.0  // spreads blowing out, confirmed
elif (hy_z120 > 2.0):                       hy_signal = -1.0  // extreme wide spreads
elif (hy_z120 < -1.0):                      hy_signal = +1.0  // extremely tight spreads

// Use as confirmation filter on the Cu/Au composite:
// When hy_signal agrees with composite sign -> full conviction
// When hy_signal disagrees -> reduce by 50%
// When hy_signal is neutral -> no change
if (hy_signal != 0.0 && sign(composite) != sign(hy_signal)):
    size_mult *= 0.50   // disagreement discount
```

### Expected Effect

| Metric | Direction | Magnitude | Reasoning |
|--------|-----------|-----------|-----------|
| Sharpe | UP | +0.05 to +0.12 | Credit spreads are a direct measure of risk appetite from the fixed income market, orthogonal to the Cu/Au commodity signal. Disagreement between the two is a strong whipsaw indicator. |
| Max DD | DOWN | -3% to -6% | HY spreads tend to widen 2-4 weeks before equity corrections. The spread momentum signal would have flagged the 2014 and 2022 drawdown episodes earlier than Cu/Au alone. |
| Turnover | UP | +5% to +10% | The disagreement discount adds a new position-reduction trigger. Acceptable if the avoided losses exceed the additional friction. |
| Win Rate | UP | +1% to +2% | Filtering out contradicted trades removes the lowest-quality entries. |

### Implementation Complexity
- **Estimated lines**: 30-40 C++ lines
- **Location**: New `hy_sma_20` and `hy_sma_60` computation after line 694 (where `hy_z60` is computed). HY signal logic inside the main loop before the size_mult cascade.
- **Difficulty**: Low-moderate. Requires new rolling_mean calls and new signal logic, but follows the exact pattern of existing code.

### C++ Pseudocode

```cpp
// Pre-loop: compute HY rolling statistics (after line 694)
auto hy_sma_20 = rolling_mean(hy, 20);
auto hy_sma_60 = rolling_mean(hy, 60);
auto hy_z120   = rolling_zscore(hy, 120);

// Inside main loop (after composite calculation, before size_mult):
double hy_roc_20 = NaN;
if (i >= 20 && !isnan(hy[i]) && !isnan(hy[i-20]) && hy[i-20] > 0.0)
    hy_roc_20 = (hy[i] / hy[i-20]) - 1.0;

double hy_trend = 0.0;
if (!isnan(hy_sma_20[i]) && !isnan(hy_sma_60[i]))
    hy_trend = (hy_sma_20[i] < hy_sma_60[i]) ? 1.0 : -1.0;

double hy_signal = 0.0;
if (!isnan(hy_roc_20) && hy_roc_20 < -0.05 && hy_trend > 0.0)
    hy_signal = 1.0;
else if (!isnan(hy_roc_20) && hy_roc_20 > 0.10 && hy_trend < 0.0)
    hy_signal = -1.0;
else if (!isnan(hy_z120[i]) && hy_z120[i] > 2.0)
    hy_signal = -1.0;
else if (!isnan(hy_z120[i]) && hy_z120[i] < -1.0)
    hy_signal = 1.0;

// Disagreement discount
if (hy_signal != 0.0 && !isnan(composite)) {
    double comp_sign = (composite > 0.0) ? 1.0 : -1.0;
    if (comp_sign != hy_signal)
        size_mult *= 0.50;
}
```

### Risks and Pitfalls
- **HY spread data quality**: The file has occasional empty values on holidays (noted in data inventory). The forward-fill handles this, but stale data around year-end holidays could produce spurious signals. Mitigation: require at least 15 valid observations in the 20-day momentum window.
- **Regime sensitivity**: HY spreads are heavily influenced by monetary policy. During QE periods (2010-2013, 2020-2021), spreads were artificially compressed. The z-score and momentum signals may give false risk-on reads during policy-distorted periods.
- **Asymmetric thresholds are deliberate**: The -0.05 (5% tightening) vs. +0.10 (10% widening) asymmetry reflects the empirical observation that credit spreads tighten slowly and widen fast. Requiring a larger move for risk-off catches real stress, not noise.
- **Double-counting with liquidity score**: HY spread z-score already enters the liquidity composite at line 930 (`hy_component = -1.0 * hy_zscore`). This proposal uses the same data differently (trend + momentum vs. z-score), but there is information overlap. The incremental signal content is primarily from the momentum/trend component, not the level.

---

## Proposal 4: Enriched Carry Signal from 2nd-Month Futures (Continuous Roll Yield)

### Signal Name
**Carry_RollYield_Continuous** -- Replace the current L4 term structure filter (which updates every ~125 trading days) with a continuous daily roll yield signal, and extend it to a portfolio-level carry composite.

### Data Source
- `data/cleaned/futures/HG_2nd.csv` (copper 2nd month, **NOTE**: in cents/lb, code already converts at line 574-575)
- `data/cleaned/futures/GC_2nd.csv` (gold 2nd month)
- `data/cleaned/futures/CL_2nd.csv` (crude oil 2nd month)
- `data/cleaned/futures/SI_2nd.csv` (silver 2nd month)
- `data/cleaned/futures/ZN_2nd.csv` (10Y T-Note 2nd month)
- `data/cleaned/futures/ZB_2nd.csv` (30Y T-Bond 2nd month)
- All 6 files already loaded at lines 582-587. The data is already extracted daily. The current L4 code computes roll yield daily but only logs diagnostically every 126 bars.

### Computation

The current code already computes daily roll_yield per commodity but then classifies into {BACKWARDATION, CONTANGO, FLAT} and applies static multipliers. The proposal is threefold:

**A. Daily Rolling 20-Day Average Roll Yield (Smoothed Carry)**

```
// For each commodity sym in {HG, GC, CL, SI, ZN}:
roll_yield[sym][i] = (front[i] / back[i] - 1.0) * (365.0 / 30.0)  // annualized
carry_20[sym]      = SMA(roll_yield[sym], 20)                       // smoothed

// Positive carry_20 = backwardation = favorable for longs
// Negative carry_20 = contango = favorable for shorts
```

**B. Carry Momentum (Change in Roll Yield)**

```
carry_delta[sym] = carry_20[sym][i] - carry_20[sym][i-20]

// Rising carry (toward backwardation) = tightening physical market = bullish
// Falling carry (toward contango) = loosening supply = bearish
```

**C. Portfolio Carry Composite**

```
// Aggregate across commodities for a single carry indicator
carry_composite = mean(carry_20["HG"], carry_20["CL"], carry_20["SI"])
// Exclude GC (carry behavior is special for gold) and ZN (bond carry is different)

// Use as a sizing scalar:
// Positive carry_composite (backwardation) + RISK_ON -> boost commodities to 1.25x
// Negative carry_composite (contango) + RISK_ON -> reduce commodities to 0.50x
// Carry direction agreeing with tilt -> full size
// Carry direction opposing tilt -> reduce
```

**D. Replace L4 Static Multipliers with Continuous Scalar**

```
// Instead of ts_mult[sym] in {0.0, 0.25, 0.5, 0.75, 1.0}:
// Use a continuous function of carry_20:
ts_mult[sym] = clip(0.5 + carry_20[sym] * 5.0, 0.1, 1.5)
// carry_20 = +0.10 (10% annualized backwardation) -> ts_mult = 1.0
// carry_20 = -0.10 (10% annualized contango) -> ts_mult = 0.0
// carry_20 = 0.0 (flat) -> ts_mult = 0.5
```

### Expected Effect

| Metric | Direction | Magnitude | Reasoning |
|--------|-----------|-----------|-----------|
| Sharpe | UP | +0.05 to +0.10 | Carry is a well-documented factor premium in commodities. The current L4 implementation captures the concept but the 126-bar update cadence is far too slow. Daily updates should capture carry regime transitions 3-4 months earlier. |
| Turnover | UP | +5% to +15% | Daily carry changes will create more frequent position adjustments. Partially mitigated by the 20-day smoothing. |
| Profit Factor | UP | +0.02 to +0.05 | Avoiding contango longs and backwardation shorts eliminates negative-carry drag |
| CL allocation | UP | More active CL trading | The current L4 has CL zeroed since 2022 (persistent backwardation). Continuous scoring would allow partial CL allocation even in backwardation. |

### Implementation Complexity
- **Estimated lines**: 40-60 C++ lines
- **Location**: Replace lines 1090-1215 (current L4 block) with new continuous carry calculation. Add pre-loop `rolling_mean` calls for each commodity's roll yield.
- **Difficulty**: Moderate. The structural change to L4 is significant but the math is simple. The risk is in the interaction with the existing trade expression matrix.

### C++ Pseudocode

```cpp
// Pre-loop: compute daily roll yield vectors (after 2nd-month extraction)
auto compute_roll_yield = [&](const std::vector<double>& front,
                              const std::vector<double>& back) {
    std::vector<double> ry(n, NaN);
    for (int i = 0; i < n; ++i) {
        if (!isnan(front[i]) && !isnan(back[i]) && back[i] > 0.0)
            ry[i] = (front[i] / back[i] - 1.0) * (365.0 / 30.0);
    }
    return ry;
};

auto ry_hg = compute_roll_yield(hg, hg_2nd);
auto ry_gc = compute_roll_yield(gc, gc_2nd);
auto ry_cl = compute_roll_yield(cl, cl_2nd);
auto ry_si = compute_roll_yield(si, si_2nd);
auto ry_zn = compute_roll_yield(zn, zn_2nd);

auto carry_hg = rolling_mean(ry_hg, 20);
auto carry_cl = rolling_mean(ry_cl, 20);
auto carry_si = rolling_mean(ry_si, 20);
auto carry_zn = rolling_mean(ry_zn, 20);

// Inside main loop, replacing the L4 block:
for (const auto& [sym, carry_ptr] : carry_map) {
    double c = (*carry_ptr)[i];
    if (isnan(c)) { ts_mult[sym] = 0.75; continue; }
    ts_mult[sym] = std::clamp(0.5 + c * 5.0, 0.1, 1.5);
}
```

### Risks and Pitfalls
- **HG_2nd unit mismatch**: The code already handles this (line 574: `val /= 100.0`), but any modification to the 2nd-month loading must preserve this conversion. Failure to do so will produce roll yields that are 100x wrong.
- **Roll date artifacts**: Continuous front-month to 2nd-month spreads can spike around roll dates as the front-month contract converges to spot. The 20-day SMA smooths this but does not eliminate it. Consider excluding the 3 days around each contract roll.
- **Business-day vs. calendar-day mismatch**: Front-month files include weekends (noted in data inventory) while 2nd-month files do not. The forward-fill mechanism handles this, but weekend bars will show stale 2nd-month prices against fresher front-month prices, potentially distorting the carry signal.
- **Gold carry is special**: Gold's cost of carry is dominated by interest rates, not supply/demand. Including GC in the carry composite would add rate-driven noise. The proposal deliberately excludes GC from the commodity carry composite.
- **Overfitting the `* 5.0` scaling factor**: The scalar that maps carry to ts_mult is arbitrary. The choice of 5.0 means +/-20% annualized carry maps to the full [0, 1] range. This needs calibration against historical carry distributions. If the typical carry is only +/-3% annualized, the scalar should be larger.

---

## Proposal 5: Detrended Cu/Au Ratio (Fix the Structural RISK_OFF Bias)

### Signal Name
**CuAu_Detrended_Ratio** -- Replace the raw Cu/Au ratio with a ratio detrended against its own 2-year rolling median, eliminating the secular decline that causes a permanent RISK_OFF lean.

### Data Source
- `data/cleaned/futures/HG.csv` (close)
- `data/cleaned/futures/GC.csv` (close)
- No additional data. This modifies the primary ratio calculation.

### Computation

```
ratio[i] = (HG[i] * 25000) / (GC[i] * 100)      // existing
ratio_median_504 = rolling_median(ratio, 504)       // 504 trading days ~ 2 years

// Detrended ratio: express current ratio as deviation from its 2-year median
detrended[i] = ratio[i] / ratio_median_504[i]

// detrended > 1.0 -> ratio is above its recent trend = cyclical risk-on
// detrended < 1.0 -> ratio is below its recent trend = cyclical risk-off
// detrended = 1.0 -> ratio is at trend = neutral

// Apply all existing sub-signals to detrended instead of raw ratio:
// ROC_20 of detrended, SMA(10)/SMA(50) of detrended, Z-score of detrended
roc20_dt = (detrended[i] / detrended[i-20]) - 1.0
sma10_dt = SMA(detrended, 10)
sma50_dt = SMA(detrended, 50)
signal_ma_dt = (sma10_dt > sma50_dt) ? +1 : -1

zscore_dt = (detrended[i] - SMA(detrended, 120)) / StdDev(detrended, 120)
signal_z_dt = +1 if zscore_dt > 0.5, -1 if zscore_dt < -0.5, else 0

composite_dt = 0.33 * sign(roc20_dt) + 0.33 * signal_ma_dt + 0.34 * signal_z_dt
```

### Expected Effect

| Metric | Direction | Magnitude | Reasoning |
|--------|-----------|-----------|-----------|
| Sharpe | UP | +0.10 to +0.25 | This is the single highest-impact change. The secular Cu/Au decline from 0.56 to 0.30 over 15 years is a structural bias, not a trading signal. Detrending isolates the cyclical component that actually predicts risk-on/risk-off periods. |
| RISK_OFF days | DOWN | From 51.6% to ~45-48% | The persistent RISK_OFF lean disappears once the secular trend is removed. The strategy should be approximately balanced between RISK_ON and RISK_OFF. |
| CAGR | UP | +1% to +3% annualized | More time in RISK_ON during 2013-2019 (when equities rallied) should add significant return |
| Max DD | MIXED | +/- 2% | Detrending may increase exposure during some drawdown episodes where the raw signal correctly went defensive. The 2014 commodity crush and 2022 rate hike cycle need careful examination. |
| Signal Flips | UP | From 6/yr to 8-10/yr | The detrended ratio will be more mean-reverting and may generate more frequent tilt changes. Still within the 12/yr threshold but should be monitored. |

### Implementation Complexity
- **Estimated lines**: 25-35 C++ lines
- **Location**: After ratio computation (line 655), add rolling_median and detrended calculation. Replace `ratio` with `detrended` in all downstream signal calculations (lines 658-661, 819-824, 832-836).
- **Difficulty**: Moderate. Requires implementing `rolling_median` (not currently in the codebase). The median is O(n*window*log(window)) with a naive sort approach, or O(n*log(window)) with a two-heap structure. For window=504 and n=4011, the naive approach takes ~2M comparisons -- acceptable for a single backtest.

### C++ Pseudocode

```cpp
// New utility function (after rolling_zscore, line 189)
static std::vector<double> rolling_median(const std::vector<double>& v, int window) {
    std::vector<double> out(v.size(), NaN);
    for (int i = window - 1; i < (int)v.size(); ++i) {
        std::vector<double> win;
        win.reserve(window);
        for (int j = i - window + 1; j <= i; ++j) {
            if (!isnan(v[j])) win.push_back(v[j]);
        }
        if (win.empty()) continue;
        std::sort(win.begin(), win.end());
        int m = win.size();
        out[i] = (m % 2 == 0) ? (win[m/2-1] + win[m/2]) / 2.0 : win[m/2];
    }
    return out;
}

// After ratio computation (line 655)
auto ratio_median_504 = rolling_median(ratio, 504);

std::vector<double> detrended(n, NaN);
for (int i = 0; i < n; ++i) {
    if (!isnan(ratio[i]) && !isnan(ratio_median_504[i]) && ratio_median_504[i] > 0.0)
        detrended[i] = ratio[i] / ratio_median_504[i];
}

// Replace all downstream references to ratio with detrended:
auto ratio_sma10  = rolling_mean(detrended, p_.ma_fast);   // was ratio
auto ratio_sma50  = rolling_mean(detrended, p_.ma_slow);   // was ratio
auto ratio_sma120 = rolling_mean(detrended, p_.zscore_window);  // was ratio
auto ratio_std120 = rolling_std(detrended, p_.zscore_window);   // was ratio

// ROC calculations also use detrended:
roc20 = (detrended[i] / detrended[i - 20]) - 1.0;   // was ratio
```

### Risks and Pitfalls
- **504-day lookback burns 2 years of data**: The detrended signal will not be available until mid-2012. This reduces the effective backtest by 2 years. Given the MES/MNQ constraint (starts 2019), this is less of a concern -- the equity sleeve was already missing for the first 9 years.
- **Median choice vs. mean**: The median is preferred over SMA because it is more robust to outlier spikes in the ratio (e.g., a single-day copper spike). However, the 504-day median is computationally heavier. If performance is a concern, use rolling_mean(504) instead -- the bias-correction effect is similar though less robust.
- **Window length is critical**: Too short (e.g., 126 days) and the detrending removes cyclical signal along with the trend. Too long (e.g., 1260 days / 5 years) and the detrending fails to capture multi-year structural shifts. 504 days (2 years) is a standard academic choice for detrending macro ratios (Asness, Moskowitz, Pedersen 2013).
- **Z-score threshold may need recalibration**: The detrended ratio will have a mean of ~1.0 and much lower volatility than the raw ratio. The z-score window (120 days) and threshold (0.5) may need adjustment. Test the distribution of detrended values before committing to 0.5.
- **Removes a genuine signal**: If the secular Cu/Au decline reflects a real, persistent shift in the global economy (e.g., gold's permanent repricing as a monetary asset), then detrending throws away valid information. The strategy would have been correctly RISK_OFF during a period where the macro environment genuinely deteriorated for industrial commodities relative to safe havens. Counter-argument: even if the long-term trend is informative, a daily trading strategy cannot profit from a 15-year secular trend -- it needs cyclical variation.

---

## Ranking: Expected Sharpe Improvement per Unit of Implementation Effort

| Rank | Proposal | Expected Sharpe Lift | Implementation Lines | Effort-Adjusted Score | Rationale |
|------|----------|---------------------|----------------------|-----------------------|-----------|
| **1** | **P2: Activate Real Rate Signal** | +0.08 to +0.15 | 15-20 | **Highest** | Zero new data loading. All inputs already computed. Literally activating dead code with 15 lines of signal logic. The risk/reward of this change is asymmetric: the computation already runs, we just wire it in. |
| **2** | **P5: Detrended Cu/Au Ratio** | +0.10 to +0.25 | 25-35 | **High** | Addresses the largest single source of strategy drag (structural RISK_OFF bias). Requires a new `rolling_median` function but the math is simple. The impact is broad -- it changes the primary signal for all downstream decisions. |
| **3** | **P1: Cu/Au Realized Vol Sizing** | +0.10 to +0.20 | 25-35 | **High** | Pure risk management improvement with no signal changes. Protects against drawdowns (which is what is killing the Sharpe -- the 25.6% max DD and 61% stop engagement rate are the binding constraints). Easy to implement and easy to validate. |
| **4** | **P3: HY Spread Momentum** | +0.05 to +0.12 | 30-40 | **Medium** | Genuine information diversification (credit vs. commodity signal). Moderate implementation but requires care around the double-counting with the existing liquidity score. |
| **5** | **P4: Enriched Carry Signal** | +0.05 to +0.10 | 40-60 | **Lower** | The data is already loaded and the concept is sound (carry is a documented factor). But replacing the L4 block is the most invasive change, the interaction effects are complex, and the marginal Sharpe lift is lower than the signal-level improvements. |

### Recommended Implementation Sequence

**Phase 1 (1 day)**: Implement P2 (Real Rate Signal) and P1 (Vol Sizing). These are additive changes that do not alter existing signal generation. Both are sizing/confirmation overlays -- low risk of breaking existing behavior.

**Phase 2 (1 day)**: Implement P5 (Detrended Ratio). This is a fundamental change to the primary signal. Run it as an A/B test: compute both raw and detrended composites, log both, and compare signal-level statistics before switching.

**Phase 3 (1-2 days)**: Implement P3 (HY Spread Momentum) and P4 (Enriched Carry). These are incremental improvements that should be tested after the core signal is fixed by P2+P5.

### Combined Estimate

If proposals P1+P2+P5 are implemented together, the expected combined Sharpe improvement is approximately +0.25 to +0.50 (from 0.34 to 0.59-0.84), with the largest single contribution from P5 (fixing the structural bias). This estimate assumes the effects are partially additive -- there will be interaction effects that reduce the combined impact below the sum of individual estimates.

At a Sharpe of 0.60+, the strategy crosses from "statistically indistinguishable from zero" to "marginally significant" (t-stat = 0.60 * sqrt(15.9) = 2.39 > 1.96). This is the minimum bar for continued development.

---

## Appendix: Signals Considered and Rejected

### A. VIX Term Structure (VIX vs. VIX Futures 2nd Month)
**Rejected**: No VIX futures data on disk. The strategy only has spot VIX (`vix.csv`). Without VIX futures (VX1, VX2), term structure (contango/backwardation) cannot be computed. This would be the single most valuable addition if the data were available -- VIX term structure is arguably the best short-term risk appetite indicator in existence.

### B. Platinum/Gold Ratio as Industrial Metal Proxy
**Rejected**: PL.csv (Platinum) is on disk and unused. The Pt/Au ratio is a well-known alternative to Cu/Au for measuring industrial vs. safe-haven demand. However, adding a second ratio signal would be highly correlated with the primary Cu/Au signal (rank correlation typically >0.7). The marginal information content does not justify the additional complexity and parameter risk.

### C. AUD/USD (6A.csv) as Risk Sentiment Proxy
**Rejected**: 6A.csv is on disk. AUD/USD is a well-known "risk currency" -- it rises in risk-on and falls in risk-off, heavily influenced by commodity demand and China growth. However, it would largely duplicate the Cu/Au signal (Australia is a major copper exporter). Additionally, it would add correlation with the 6J (Yen) position, reducing portfolio diversification.

### D. Agricultural Commodity Momentum
**Rejected**: 10 agricultural futures on disk (ZC, ZW, ZS, etc.). Agricultural commodity momentum has been shown to contain macro information (food price inflation, Chinese demand). However, these are distinct economic cycles from the metals/energy complex, and integrating them would require expanding the strategy's thesis beyond its current scope. Possible future work, not a quick fix.

### E. Yield Curve Slope (2Y-10Y) from ZT.csv + ZN.csv
**Rejected**: ZT.csv (2Y T-Note) is on disk. The 2Y-10Y spread is a classic recession predictor. However, the yield curve information is partially captured by the existing ZN/ZB 2nd-month spread (yield curve state in L4). Adding a separate yield curve signal would double-count this information. If the L4 enrichment (Proposal 4) is implemented, revisit this.

### F. Fed Balance Sheet Acceleration
**Rejected**: The Fed BS YoY growth is already in the liquidity score. An acceleration signal (second derivative: change in YoY growth) could flag turning points in liquidity policy. However, the weekly granularity of `fed_balance_sheet.csv` means the acceleration signal would be extremely noisy and update too slowly to be useful for a daily strategy.
