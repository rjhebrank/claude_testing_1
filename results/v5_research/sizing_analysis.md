# V5 Research: Position Sizing and Concentration Risk Analysis

**Date**: 2026-02-24
**Analyst**: Quantitative Strategy Review
**Subject**: UB dominance root cause, concentration risk, and three sizing proposals for V5

---

## 1. Why UB Dominates: Tracing the Math

### 1.1 The `contracts_for` Lambda

The position sizing engine lives at line 1613 of `copper_gold_strategy.cpp`:

```cpp
auto contracts_for = [&](const std::string& sym,
                         double direction,
                         double vol_adj = 1.0) -> double {
    if (std::abs(direction) < 1e-9 || std::abs(size_mult) < 1e-9)
        return 0.0;

    const auto cls = asset_class(sym);
    double w = ASSET_WEIGHTS.count(cls) ? ASSET_WEIGHTS.at(cls) : 0.1;
    double notional_alloc = std::max(0.0, equity * leverage_target * w);
    const auto spec = ContractSpec::get(sym);
    double raw = (notional_alloc / spec.notional) * size_mult * vol_adj;
    return std::floor(raw * direction + 0.5);
};
```

The formula is:

```
contracts = floor( (equity * leverage * asset_class_weight / contract_notional) * size_mult * vol_adj )
```

### 1.2 Asset Class Weights (line 329)

| Asset Class     | Weight | Instruments          |
|-----------------|--------|----------------------|
| equity_index    | 0.30   | MES, MNQ             |
| commodities     | 0.35   | CL, HG, GC, SI      |
| fixed_income    | 0.25   | ZN, UB               |
| fx              | 0.10   | 6J                   |

**Critical observation**: ZN and UB share the **same** 0.25 weight as a class. The weight is not split between them -- each instrument individually receives the full `equity * 2.0 * 0.25` allocation. This is the first amplifier.

### 1.3 Contract Notionals (line 299)

| Instrument | Notional/contract | Tick Value | Asset Class   |
|------------|-------------------|------------|---------------|
| UB         | $122,000          | $31.25     | fixed_income  |
| ZN         | $113,000          | $15.625    | fixed_income  |
| GC         | $420,000          | $10.00     | commodities   |
| CL         | $60,000           | $10.00     | commodities   |
| SI         | $265,000          | $25.00     | commodities   |
| MNQ        | $51,000           | $0.50      | equity_index  |

### 1.4 Worked Example: $1.5M Equity, size_mult = 0.80

**UB calculation:**
```
notional_alloc = $1,500,000 * 2.0 * 0.25 = $750,000
raw = ($750,000 / $122,000) * 0.80 = 4.92
contracts = floor(4.92 + 0.5) = 5
UB notional exposure = 5 * $122,000 = $610,000  (40.7% of equity)
```

**ZN calculation:**
```
notional_alloc = $1,500,000 * 2.0 * 0.25 = $750,000
raw = ($750,000 / $113,000) * 0.80 = 5.31
contracts = floor(5.31 + 0.5) = 5
ZN notional exposure = 5 * $113,000 = $565,000  (37.7% of equity)
```

**GC calculation:**
```
notional_alloc = $1,500,000 * 2.0 * 0.35 = $1,050,000
raw = ($1,050,000 / $420,000) * 0.80 = 2.00
contracts = floor(2.00 + 0.5) = 2
BUT: per-instrument cap = 15% * $1,500,000 / $420,000 = 0.54 -> floored to 1
GC notional exposure = 1 * $420,000 = $420,000  (28.0% of equity)
```

**CL calculation:**
```
notional_alloc = $1,500,000 * 2.0 * 0.35 = $1,050,000
raw = ($1,050,000 / $60,000) * 0.80 = 14.0
BUT: per-instrument cap = 15% * $1,500,000 / $60,000 = 3.75 -> floor = 3
AND: total commodity cap = 40% * equity clips this further
CL notional exposure = ~2-3 * $60,000 = $120K-$180K  (8-12% of equity)
```

### 1.5 Why UB Gets So Many Contracts: The Three Amplifiers

**Amplifier 1: No per-instrument notional cap on fixed income.**

Line 347 of the code:
```cpp
static const std::unordered_map<std::string, double> SINGLE_NOTIONAL_LIMIT = {
    {"MES", 0.20}, {"MNQ", 0.20},
    {"HG",  0.15}, {"GC",  0.15}, {"CL",  0.15}, {"SI",  0.15}
    // ZN, UB, 6J intentionally omitted - no per-instrument limits in doc
};
```

GC is capped at 15% of equity per instrument (typically 1 contract). CL is capped at 15% (2-3 contracts). But ZN and UB have **no individual cap at all**. There is no `MAX_TOTAL_FIXED_INCOME_NOTIONAL` cap either -- the 35% equity cap and 40% commodity cap exist, but no equivalent for bonds.

**Amplifier 2: UB's low notional ($122K) relative to its dollar risk per tick ($31.25).**

UB has the highest tick value of any instrument in the portfolio. At $31.25/tick with tick_size 1/32, a 1-point move in UB = $1,000 per contract. Compare to ZN where a 1-point move = $1,000 but the contract trades in 1/64ths ($15.625/tick). UB's dollar P&L per contract per unit price move is comparable to ZN, but the Ultra Bond is **far more volatile** than the 10-year note. UB has roughly 2x the duration of ZN (25-30yr vs 6.5-10yr effective duration), meaning UB generates roughly 2x the dollar P&L per interest rate move.

**Amplifier 3: Both ZN and UB get the full 25% weight, not 12.5% each.**

The asset class weight of 0.25 is applied to BOTH ZN and UB individually, not divided between them. This means the combined fixed income allocation is actually 50% of `equity * leverage` (= 100% of equity), not the intended 25%. With $1.5M equity at 2x leverage:
- ZN allocation: $750K notional
- UB allocation: $750K notional
- **Combined FI notional: $1.5M = 100% of equity**

By comparison, commodities get 35% weight but it is shared across 4 instruments, each capped at 15%. The effective commodity allocation is ~40% of equity (the sector cap). Equities get 30% weight but capped at 35% total and 20% per instrument.

### 1.6 Observed Position Sizes from Backtest

From `backtest_output_v4.txt`, UB contract counts by period:

| Period      | Equity      | size_mult | UB Contracts | UB Notional | UB % of Equity |
|-------------|-------------|-----------|-------------|-------------|----------------|
| 2010-2011   | ~$1.0M      | 0.50      | 2-4         | $244-488K   | 24-49%         |
| 2013-2014   | ~$1.2M      | 0.40-0.85 | 1-4         | $122-488K   | 10-41%         |
| 2015-2016   | ~$1.3M      | 0.70-0.85 | 4-5         | $488-610K   | 38-47%         |
| 2017-2018   | ~$1.5M      | 0.80-0.90 | 4-5         | $488-610K   | 33-41%         |
| 2019-2020   | ~$1.5-1.9M  | 0.80-0.85 | 5-6         | $610-732K   | 32-49%         |
| 2021-2022   | ~$1.7-2.0M  | 0.60-0.85 | 5-7         | $610-854K   | 31-50%         |
| 2023-2025   | ~$1.8-1.9M  | 0.60-0.95 | 7-8         | $854-976K   | 45-54%         |

**Final position (2025-11-10)**: UB:7, ZN:8, GC:1, CL:-3, SI:1

At final equity of $1.87M:
- UB: 7 * $122K = **$854K = 45.7% of equity**
- ZN: 8 * $113K = **$904K = 48.3% of equity**
- Combined FI: **$1.758M = 94.0% of equity** in directional rate exposure
- GC: 1 * $420K = $420K = 22.5%
- CL: 3 * $60K = $180K = 9.6%

### 1.7 Why UB P&L Dominates Despite Similar Sizing to ZN

UB and ZN hold comparable numbers of contracts (7-8 each at end of backtest). But UB generates $633K net P&L vs ZN's $163K. The reason:

**Duration leverage.** UB (Ultra Bonds, 25-30yr maturity) has roughly 2.5x the modified duration of ZN (10-year notes). For a given interest rate move:
- UB price change per 100bp rate move: ~25 points = ~$25,000/contract
- ZN price change per 100bp rate move: ~8 points = ~$8,000/contract

Same number of contracts, but UB carries 3x the dollar sensitivity. The average winning UB trade ($33,107) dwarfs the average winning ZN trade ($9,411) by 3.5x. This is pure duration exposure -- UB is a leveraged bet on rates.

---

## 2. Concentration Risk Assessment

### 2.1 P&L Concentration Summary

```
UB:   $633,253   73.0% of net P&L
ZN:   $163,294   18.8%
GC:   $105,501   12.2%
MNQ:   $33,769    3.9%
CL:   -$67,596   -7.8%
SI:      -$360   -0.0%
                 ------
Total: $867,862  100.0%
```

Rate products (UB + ZN): **$796,547 = 91.8% of total net P&L**

### 2.2 If UB Has One Bad Year

UB's average annual contribution: $633K / 15.9 years = ~$40K/year.

But UB P&L is not evenly distributed. In a year where rates rise sharply (like 2022), UB can lose substantially. Consider:
- The 2022 rate shock: Fed funds went from 0% to 4.5%. UB (long duration) would have been hit hard.
- A single UB contract loses ~$25K per 100bp rate rise.
- At 5-7 contracts, a 200bp adverse rate move = $250K-$350K loss.
- That is 29-40% of starting equity and would likely trigger the drawdown stop.

**If UB contributes zero P&L for one year** (neither gains nor loses), total strategy CAGR drops from 4.0% to approximately 1.4% -- essentially the V3 performance that was deemed unacceptable.

**If UB has a -$200K year** (plausible in a 2013-style taper tantrum or 2022-style rate shock), total strategy P&L goes deeply negative for that year and potentially triggers cascading drawdown stops.

### 2.3 Is the UB Edge Real or an Artifact?

**The case for "real edge":**
- The Cu/Au ratio is a genuine risk-appetite indicator that predicts rate direction.
- UB's 51.4% win rate with 1.65x avg win/loss ratio across 107 trades over 16 years is not trivially explained by luck (though the t-stat is marginal).
- The signal correctly positioned long UB during flights to quality (2011, 2015-2016, 2019, 2020) and short during reflation (2012-2013, 2017-2018).

**The case for "artifact":**
- The 2010-2020 period was a historically unprecedented bond bull market (10Y yield: 3.2% -> 0.5%). Any strategy with structural long bond exposure would have profited.
- The Cu/Au ratio's secular decline from 0.85 to 0.30 produced a persistent RISK_OFF bias (2,070 RISK_OFF days vs 1,712 RISK_ON). RISK_OFF = long UB. In a bond bull market, being structurally long bonds prints money.
- The strategy's RISK_OFF bias + long UB is partially a levered version of "buy bonds for 15 years" -- and the 2010-2020 period was the best 10 years for long bonds in a century.
- Post-2020 performance has been weaker (the equity peaked ~$2.03M in 2021 and is still below that 4 years later), which coincides with the end of the bond bull market.

**Verdict**: The UB edge is likely 60% structural signal + 40% bond bull market tailwind. The signal has some genuine predictive power for rate direction, but the magnitude of UB P&L is inflated by a favorable secular environment. This is the most dangerous kind of edge -- partially real, partially environmental -- because it is hard to distinguish ex ante and tends to degrade exactly when you need it most (rising rate environments).

### 2.4 Would Risk-Parity Sizing Reduce UB Dominance?

Yes, substantially. UB's annualized volatility is roughly 2-3x that of ZN. Under risk-parity:
- UB contracts would be cut by ~50-60% (from 7 to 3)
- ZN contracts would stay approximately the same or increase slightly
- GC (high vol) would also be reduced
- CL (moderate vol) might increase
- The net effect: UB P&L contribution would drop from 73% to approximately 30-40%

This directly addresses the PM's concern ("no single instrument above 50% of P&L").

---

## 3. Sizing Proposals

### Proposal A: Inverse-Volatility (Risk-Parity) Sizing

**Thesis**: Size each instrument so it contributes approximately equal dollar volatility to the portfolio. High-vol instruments (UB, GC) get fewer contracts; low-vol instruments (ZN, CL) get more. This mechanically deconcentrates the P&L.

**Formula**:

```
vol_i         = 63-day realized volatility of instrument i (annualized, dollar terms)
target_vol    = portfolio_equity * leverage * asset_class_weight / N_instruments_in_class
inv_vol_i     = 1.0 / vol_i
sum_inv_vol   = sum(inv_vol_j) for all j in same asset class
rp_weight_i   = inv_vol_i / sum_inv_vol
contracts_i   = floor(target_vol * rp_weight_i / notional_i * size_mult)
```

For UB vs ZN specifically:
```
UB_dollar_vol = UB_price * UB_63d_rvol * 1000  (point value $1000/pt)
ZN_dollar_vol = ZN_price * ZN_63d_rvol * 1000

UB_rp_weight = (1/UB_dollar_vol) / (1/UB_dollar_vol + 1/ZN_dollar_vol)
ZN_rp_weight = (1/ZN_dollar_vol) / (1/UB_dollar_vol + 1/ZN_dollar_vol)
```

Since UB has ~2.5x the dollar vol of ZN, UB_rp_weight ~ 0.29, ZN_rp_weight ~ 0.71. The combined FI allocation is then split ~29/71 instead of 50/50.

**Implementation location**: Inside the `contracts_for` lambda (line 1613). Replace:
```cpp
double w = ASSET_WEIGHTS.count(cls) ? ASSET_WEIGHTS.at(cls) : 0.1;
```
with a per-instrument risk-parity weight that considers dollar vol.

**C++ pseudocode**:

```cpp
// Pre-compute once per rebalance day (before contracts_for calls):
// 63-day realized dollar vol for each instrument
std::unordered_map<std::string, double> dollar_vol_63;
for (const auto& sym : {"ZN", "UB", "GC", "CL", "SI", "HG", "MES", "MNQ"}) {
    if (i < 63) continue;
    double sum_sq = 0.0;
    int count = 0;
    for (int k = i - 62; k <= i; ++k) {
        auto it = fut_.find(sym);
        if (it == fut_.end()) continue;
        auto bar_it = it->second.find(dates[k]);
        auto bar_prev = it->second.find(dates[k-1]);
        if (bar_it == it->second.end() || bar_prev == it->second.end()) continue;
        double ret = (bar_it->second.close - bar_prev->second.close)
                   * ContractSpec::get(sym).notional / bar_prev->second.close;
        sum_sq += ret * ret;
        count++;
    }
    if (count > 10)
        dollar_vol_63[sym] = std::sqrt(sum_sq / count) * std::sqrt(252.0);
}

// Inside contracts_for, replace flat weight with risk-parity weight:
auto contracts_for_rp = [&](const std::string& sym,
                            double direction,
                            double vol_adj = 1.0) -> double {
    if (std::abs(direction) < 1e-9 || std::abs(size_mult) < 1e-9)
        return 0.0;

    const auto cls = asset_class(sym);
    double class_weight = ASSET_WEIGHTS.count(cls) ? ASSET_WEIGHTS.at(cls) : 0.1;

    // Collect instruments in same class that are active this rebalance
    double sum_inv_vol = 0.0;
    double my_inv_vol = 0.0;
    for (const auto& [s, dv] : dollar_vol_63) {
        if (asset_class(s) == cls && dv > 0.0) {
            double iv = 1.0 / dv;
            sum_inv_vol += iv;
            if (s == sym) my_inv_vol = iv;
        }
    }

    double rp_frac = (sum_inv_vol > 0.0 && my_inv_vol > 0.0)
                   ? my_inv_vol / sum_inv_vol
                   : 0.5;  // fallback: equal weight

    double notional_alloc = std::max(0.0, equity * p_.leverage_target
                                         * class_weight * rp_frac);
    // Note: multiply by number of instruments in class to maintain
    // total class allocation (since rp_frac sums to 1.0 within class)
    // Actually: class_weight already represents total class budget.
    // rp_frac splits it. No N multiplier needed.

    // But we need to scale up because the original code gives each
    // instrument the FULL class weight. To maintain total exposure
    // parity with the old system, multiply by N_active_in_class.
    // OR to actually reduce total FI exposure (the goal), don't.
    // DECISION: Do NOT scale up. This naturally halves FI exposure
    // since the budget is now split between ZN and UB.

    const auto spec = ContractSpec::get(sym);
    double raw = (notional_alloc / spec.notional) * size_mult * vol_adj;
    return std::floor(raw * direction + 0.5);
};
```

**Expected impact**:
- UB contracts: 7 -> 2-3 (at $1.87M equity, size_mult=0.95)
- ZN contracts: 8 -> 4-5
- UB P&L contribution: 73% -> estimated 25-35%
- ZN P&L contribution: 19% -> estimated 15-20%
- Sharpe impact: **Uncertain, likely -0.05 to +0.05.** Reduces UB alpha capture but also reduces UB drawdown episodes. Net effect depends on whether UB's edge persists post-2020.
- Concentration: **Significantly improved.** No single instrument above 40% of P&L.
- Turnover: Likely reduced (smaller positions = smaller rebalance notional).
- Risk: If UB's edge IS real and structural, this proposal leaves alpha on the table. If UB's edge is environmental, this proposal protects capital.

**Key consideration**: The current code gives BOTH ZN and UB the full 25% class weight independently. This is a bug or design oversight -- the document says 25% for "fixed income" as a class, not 25% per instrument. Risk-parity sizing naturally fixes this by splitting the 25% budget proportional to inverse vol.

---

### Proposal B: Max Instrument P&L Concentration Cap (40% Notional Cap)

**Thesis**: Hard-cap any single instrument's gross notional exposure at 40% of portfolio equity. When an instrument would exceed the cap, scale it down. This is a blunt instrument but directly addresses the PM's "no single instrument above 50% of P&L" requirement.

**Formula**:

```
max_notional_per_instrument = 0.40 * equity
max_contracts_i = floor(max_notional_per_instrument / notional_i)
if abs(contracts_i) > max_contracts_i:
    contracts_i = copysign(max_contracts_i, contracts_i)
```

For UB at $1.87M equity:
```
max_notional = 0.40 * $1,870,000 = $748,000
max_UB = floor($748,000 / $122,000) = 6
```

This caps UB at 6 contracts (vs current 7-8) at peak equity. At $1.5M equity:
```
max_UB = floor($600,000 / $122,000) = 4
```

This caps at 4 (vs current 5-6). Modest reduction.

**Implementation location**: In the position limits section (line 1698-1731). Add UB and ZN to the `SINGLE_NOTIONAL_LIMIT` map.

**C++ pseudocode**:

```cpp
// Option 1: Add FI instruments to existing per-instrument cap map
static const std::unordered_map<std::string, double> SINGLE_NOTIONAL_LIMIT = {
    {"MES", 0.20}, {"MNQ", 0.20},
    {"HG",  0.15}, {"GC",  0.15}, {"CL",  0.15}, {"SI",  0.15},
    {"ZN",  0.40}, {"UB",  0.40},  // NEW: 40% per-instrument cap for FI
    {"6J",  0.15},
};

// Option 2: Add a total fixed income cap (parallel to equity and commodity caps)
static constexpr double MAX_TOTAL_FI_NOTIONAL = 0.60;  // 60% combined ZN+UB

// After existing position limit code, add:
{
    double fi_not = 0.0;
    for (const auto& s : {"ZN", "UB"}) {
        auto it = new_positions.find(s);
        if (it != new_positions.end())
            fi_not += std::abs(it->second) * ContractSpec::get(s).notional;
    }
    double max_fi = std::max(0.0, equity * MAX_TOTAL_FI_NOTIONAL);
    if (fi_not > max_fi && fi_not > 0.0) {
        double scale = max_fi / fi_not;
        for (const auto& s : {"ZN", "UB"}) {
            auto it = new_positions.find(s);
            if (it != new_positions.end()) {
                double old_val = it->second;
                double scaled = std::floor(std::abs(old_val) * scale + 0.5);
                if (scaled < 1.0 && std::abs(old_val) > 1e-9)
                    scaled = 1.0;
                it->second = std::copysign(scaled, old_val);
            }
        }
    }
}
```

**Expected impact**:
- UB contracts: 7-8 -> 5-6 (at peak equity); 4-5 -> 4 (at $1.3M equity)
- UB P&L contribution: 73% -> estimated 50-60% (modest reduction)
- Sharpe impact: **-0.02 to +0.02.** Minimal -- this only clips the largest positions.
- Concentration: **Modestly improved.** Still likely above 50% UB contribution.
- Turnover: Negligible change.
- Risk: Low risk. This is a guardrail, not a redesign. Easy to A/B test.

**Key consideration**: A 40% notional cap is relatively generous. At current UB sizing (7 contracts * $122K = $854K on $1.87M = 45.7%), UB only barely exceeds 40%. The cap would clip 1-2 contracts in the late backtest period. A stricter 30% cap would be more impactful but also more costly to Sharpe.

**Recommended**: Implement BOTH the per-instrument 40% cap AND a combined FI notional cap of 60%. The combination is more effective than either alone.

---

### Proposal C: Signal-Strength (Composite-Scaled) Sizing

**Thesis**: The current sizing is binary -- the `contracts_for` function sizes to full allocation whenever the signal is non-NEUTRAL, regardless of signal conviction. A composite score of +0.01 gets the same position size as +1.00. This wastes capital on low-conviction trades and under-sizes high-conviction trades.

**Current signal logic** (line 886-895):

```cpp
composite = w1 * sign_roc20 + w2 * signal_ma + w3 * signal_z;
// composite ranges from approximately -1.0 to +1.0
// but threshold is 0.0: anything positive = RISK_ON, anything negative = RISK_OFF
```

The composite score is a weighted average of three components (each weighted ~0.33), producing values in [-1.0, +1.0]. Currently, ANY positive value triggers full RISK_ON sizing. The proposal: scale position size by the absolute magnitude of the composite.

**Formula**:

```
signal_scale = max(0.3, min(1.0, abs(composite) / composite_full_size))
contracts_i = floor(base_contracts_i * signal_scale)
```

Where `composite_full_size` is the composite value at which you want full sizing (e.g., 0.67 = two of three sub-signals agreeing).

| |composite| | signal_scale | Interpretation                    |
|-------------|--------------|-----------------------------------|
| 0.00 - 0.20 | 0.30         | Minimum position (marginal signal)|
| 0.33        | 0.50         | One sub-signal agrees             |
| 0.67        | 1.00         | Two sub-signals agree (full size) |
| 1.00        | 1.00         | All three agree (full size, capped)|

**Implementation location**: Inside the `contracts_for` lambda or as a multiplier applied to `size_mult` before the lambda is called. The cleanest approach is to multiply `size_mult` by the signal_scale at line 1106.

**C++ pseudocode**:

```cpp
// After computing composite (line 889) and size_mult (line 1106-1141):

// Signal-strength scaling
double composite_full_size = 0.67;  // full size when 2/3 sub-signals agree
double signal_scale = 1.0;
if (!std::isnan(composite) && macro_tilt != MacroTilt::NEUTRAL) {
    double abs_comp = std::abs(composite);
    signal_scale = std::max(0.30, std::min(1.0, abs_comp / composite_full_size));
}
size_mult *= signal_scale;

// Everything downstream (contracts_for, position limits) is unchanged.
// The effect is purely to modulate position size by conviction.
```

**Expected impact**:
- High-conviction periods (|composite| > 0.67): No change. Full size.
- Low-conviction periods (|composite| ~ 0.10-0.33): Positions reduced 50-70%.
- Average position size: Reduced by approximately 20-30% across the backtest.
- UB P&L contribution: Depends on whether UB's wins come from high or low conviction. If UB's edge is concentrated in high-conviction periods, concentration may actually INCREASE (other instruments' low-conviction trades get cut more). If UB's edge is spread evenly, concentration decreases modestly.
- Sharpe impact: **Potentially +0.05 to +0.15.** This is the most Sharpe-positive proposal because it reduces exposure during low-conviction periods (which are statistically more likely to be losing trades) while preserving full exposure during high-conviction periods.
- Turnover: Likely reduced (smaller positions on marginal signals = less notional traded).
- Profit factor: Should improve (fewer marginal trades = less cost leakage).
- Risk: **This does not directly address concentration.** If UB's best trades happen to have high composite scores, UB concentration may stay at 70%+. This proposal improves efficiency but not diversification.

**Key consideration**: Signal-strength sizing is orthogonal to the concentration problem. It improves the strategy's risk-adjusted returns but does not necessarily fix the "73% in UB" issue. It should be combined with Proposal A or B for maximum effect.

---

## 4. Comparison Matrix

| Dimension               | A: Risk-Parity        | B: Notional Cap       | C: Signal-Strength    |
|-------------------------|-----------------------|-----------------------|-----------------------|
| **UB concentration**    | Strong reduction      | Modest reduction      | Uncertain/minimal     |
| **Expected Sharpe**     | Neutral (-0.05/+0.05) | Neutral (-0.02/+0.02) | Positive (+0.05/+0.15)|
| **Implementation risk** | Medium (new vol calc)  | Low (add 2 lines)     | Low (1 multiplier)    |
| **Addresses PM concern**| Yes (sub-40% conc.)   | Partially (sub-60%)   | No (not directly)     |
| **Turnover impact**     | Reduced               | Negligible            | Reduced               |
| **Profit factor**       | Uncertain              | Slight improvement    | Improvement expected  |
| **Testability**         | Single A/B test        | Single A/B test       | Single A/B test       |
| **Reversibility**       | Easy (revert lambda)   | Easy (remove cap)     | Easy (set scale=1.0)  |

---

## 5. Recommended Testing Order

**Phase 1**: Test Proposal C (signal-strength sizing) first. It is the most likely to improve Sharpe and profit factor, has the lowest implementation risk, and is independent of the concentration fix. This establishes a better baseline.

**Phase 2**: Test Proposal A (risk-parity) on top of Phase 1 results. This directly addresses concentration. The combination of A+C is the most likely to satisfy the PM's requirements: better Sharpe AND better diversification.

**Phase 3**: If A+C fails to push UB below 50% of P&L, add Proposal B (notional cap) as a hard guardrail. B is a safety net, not a primary fix.

**V5 target (from performance_report_v4.md)**: Sharpe >= 0.50, Profit Factor >= 1.15, Turnover < 25x, no single instrument above 50% of P&L.

---

## 6. The Core Structural Issue

The deepest problem is not in the sizing formula. It is in the portfolio construction.

The strategy has 9 instruments but only 2 of them (UB and ZN) have:
1. Uncapped position limits
2. Asset class weight applied per-instrument (not split)
3. High dollar sensitivity per contract (duration * notional)
4. A signal (Cu/Au ratio) whose primary predictive power is for interest rate direction

The Cu/Au ratio predicts rates. The portfolio is overweight rates. The result is mechanically inevitable: UB dominates.

To truly solve concentration, the strategy either needs:
1. **A signal that predicts more than rates** -- i.e., a signal that predicts CL, GC, or equity direction with comparable accuracy to its rate predictions. (This is the "signal enrichment" path from the V4 report.)
2. **Instruments whose notional risk is commensurate with rate instruments** -- i.e., trade ES instead of MES, trade more GC/SI contracts. (Currently blocked by per-instrument caps on commodities.)
3. **Mechanically de-lever the rate leg** -- i.e., Proposals A/B above.

Option 3 is the only one implementable in V5 without new signals. Options 1 and 2 are V6+ territory.

---

## Appendix: Key Source Locations

| Component                    | File                           | Line(s)     |
|------------------------------|--------------------------------|-------------|
| Contract specs (notionals)   | `copper_gold_strategy.cpp`     | 286-310     |
| Asset class weights          | `copper_gold_strategy.cpp`     | 328-334     |
| Per-instrument caps          | `copper_gold_strategy.cpp`     | 347-353     |
| `contracts_for` lambda       | `copper_gold_strategy.cpp`     | 1613-1625   |
| Size multiplier calculation  | `copper_gold_strategy.cpp`     | 1106-1141   |
| Position limits enforcement  | `copper_gold_strategy.cpp`     | 1698-1789   |
| Composite signal calculation | `copper_gold_strategy.cpp`     | 886-895     |
| Trade expressions            | `copper_gold_strategy.cpp`     | 1639-1688   |
| Per-instrument P&L table     | `performance_report_v4.md`     | 96-109      |
| Concentration analysis       | `performance_report_v4.md`     | 137-141     |
| Final positions              | `backtest_output_v4.txt`       | 3902        |
