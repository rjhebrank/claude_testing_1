# Turnover Reduction Proposals -- Copper-Gold Macro Strategy v2

**Author**: Quantitative Strategy Research
**Date**: 2026-02-24
**Status**: Research / Pre-implementation
**Target**: Reduce annual turnover from 46.7x to <15x without degrading signal capture

---

## 1. Problem Diagnosis

### 1.1 The Numbers

| Metric | Current | Target |
|--------|---------|--------|
| Annual Turnover | 46.7x | <15x |
| Signal Flips/Year | 6.0 | -- |
| Rebalance Events | 1,679 over 15.9 years (106/year) | -- |
| Rebalances with `stop=1` | 1,030 / 1,679 (61.3%) | -- |
| Friday-triggered rebalances | 788 | -- |
| Tilt-triggered rebalances | ~96 (6/year * 15.9 years) | -- |

If the signal only flips 6 times per year, each flip should generate at most 2x turnover (unwind + rebuild). That yields ~12x theoretical minimum. The actual 46.7x is **3.9 times the theoretical minimum**, implying massive churning between flips.

### 1.2 Root Cause Analysis

I identified **four distinct turnover drivers**, ordered by estimated contribution:

#### Driver A: The `size_mult` Oscillator (Primary -- estimated 55-65% of excess turnover)

The `size_mult` cascade is the dominant source of churning. From the backtest log, `size_mult` takes the following values across 3,506 logged SIZING events:

| `size_mult` Value | Count | Percentage |
|-------------------|-------|------------|
| 0.50 | 1,686 | 48.1% |
| 1.00 | 1,194 | 34.1% |
| 0.00 | 444 | 12.7% |
| 0.25 | 182 | 5.2% |

Only 34% of rebalance days run at full size. The strategy oscillates between 1.00x and 0.50x almost every week because the drawdown warning threshold (10%) sits exactly at the strategy's normal operating drawdown range. The October 2015 log illustrates this perfectly:

```
2015-10-02  size_mult=1.00  GC_final=5   (Friday, dd=0.09)
2015-10-08  size_mult=0.50  GC_final=2   (stop=1, dd=0.11)
2015-10-09  size_mult=0.50  GC_final=2   (Friday + stop=1, dd=0.11)
2015-10-12  size_mult=0.50  GC_final=2   (stop=1, dd=0.10)
2015-10-16  size_mult=1.00  GC_final=5   (Friday, dd=0.10)
2015-10-20  size_mult=0.50  GC_final=2   (stop=1, dd=0.10)
2015-10-23  size_mult=0.50  GC_final=2   (Friday + stop=1, dd=0.10)
2015-10-28  size_mult=0.25  GC_final=1   (stop=1 + corr_spike, dd=0.10)
```

The strategy is thrashing between 5 GC contracts and 2 GC contracts **every few days** while the signal direction does not change at all. Each swing generates 3 round-trip contracts of turnover. Across 9 instruments, this pattern generates enormous portfolio-level turnover with zero directional information.

**The `size_mult` is changing because drawdown hovers around 10%.** On a 10.7% annualized volatility strategy, a 10% drawdown threshold triggers approximately 61% of the time (as confirmed by the log data). Every time drawdown crosses 10%, `size_mult` halves (0.50). When equity recovers slightly, `size_mult` restores to 1.0. This creates a sawtooth pattern in position size.

#### Driver B: Full Mark-to-Target Rebalancing (Secondary -- estimated 20-25% of excess turnover)

On every rebalance day, the strategy computes target positions from scratch based on current equity and `size_mult`, then adjusts to that exact target. Because equity fluctuates daily (~0.5% daily vol) and `size_mult` cascades through multiple discrete filters, the raw contract count `floor(raw * direction + 0.5)` frequently rounds to a different integer than the prior day.

For example, with equity at $1.30M and `size_mult=1.0`, GC_raw = 4.55 which rounds to 5. At equity $1.28M the next week, GC_raw = 4.48 which still rounds to 4. This one-contract difference is a round-trip trade that serves no directional purpose.

The `contracts_for()` lambda (line 1514) recalculates from scratch every rebalance:
```cpp
double raw = (notional_alloc / spec.notional) * size_mult * vol_adj;
return std::floor(raw * direction + 0.5);
```

There is **no comparison to the current position**. The strategy never asks "am I already close to where I should be?" -- it simply overwrites.

#### Driver C: Drawdown Stop Triggering Rebalances (Tertiary -- estimated 10-15% of excess turnover)

The `stop_triggered` flag (lines 1431-1436) is true whenever `dd_stop || dd_warn`. Since `dd_warn` fires at 10% drawdown and `stop=1` appeared on 1,030 out of 1,679 rebalance days, the drawdown system is generating extra non-Friday rebalance events. Each of these events recomputes full positions at the new (halved) `size_mult`, forcing the strategy to sell down to half-size even when the underlying signal has not changed.

This means a single week can see: Friday rebalance (full size) -> Monday stop trigger (half size) -> Wednesday equity recovers -> Friday rebalance (full size again). Three full portfolio rebalances in 5 days, none of which reflect signal information.

#### Driver D: Position Direction Flips on Tilt Changes (Minor -- estimated 5-10% of excess turnover)

When the tilt flips from RISK_ON to RISK_OFF, the strategy reverses every position (e.g., UB goes from -4 to +7 in a single bar). These are genuine signal events and should contribute to turnover. At 6 flips/year with ~12 instruments, this contributes approximately 6-8x annual turnover. This is the **unavoidable baseline** and should not be reduced.

---

## 2. Proposals

### Proposal 1: Rebalance Bands (Minimum Trade Threshold)

**Mechanism**: Only execute a position change if the target differs from the current position by more than a threshold. Two variants:

- **Absolute band**: Only trade if `|target - current| >= N contracts` (suggest N=2 for large positions, N=1 for single-contract instruments).
- **Relative band**: Only trade if `|target - current| / max(|current|, 1) >= Y%` (suggest Y=30%).

**Root cause addressed**: Driver B (mark-to-target rounding noise). Eliminates the one-contract adjustments that contribute nothing directionally.

**Implementation**: Insert immediately before the transaction cost deduction block at line 1740 of `copper_gold_strategy.cpp`:

```cpp
// REBALANCE BANDS: suppress noise trades
for (auto& [sym, new_qty] : new_positions) {
    double old_qty = positions.count(sym) ? positions.at(sym) : 0.0;
    double delta = std::abs(new_qty - old_qty);
    double current_abs = std::max(std::abs(old_qty), 1.0);

    // Allow direction flips (sign change) unconditionally
    bool direction_flip = (old_qty * new_qty < 0.0);
    // Allow entry from flat or exit to flat unconditionally
    bool entry_or_exit = (old_qty == 0.0 || new_qty == 0.0);

    if (!direction_flip && !entry_or_exit) {
        // Suppress same-direction resizing below threshold
        double relative_change = delta / current_abs;
        if (delta < 2.0 && relative_change < 0.30) {
            new_qty = old_qty;  // keep current position
        }
    }
}
```

**Expected turnover reduction**: 10-15x reduction (from 46.7x to approximately 32-37x). This addresses the rounding noise but does not fix the `size_mult` oscillator, which causes large-magnitude changes (e.g., 5->2 contracts, a 3-contract delta that exceeds the 2-contract band).

**Impact on signal capture**: Minimal. The suppressed trades are 1-contract same-direction adjustments that have zero directional information. Direction flips and entries/exits are exempted and execute normally. Slight tracking error between target and actual notional, bounded by the band width (~15% of target at worst).

**Risks**:
- Positions drift from target during sustained equity growth/decline, accumulating a larger rebalance when the band is finally breached.
- May interact poorly with margin utilization cap (actual leverage slightly deviates from target).

**Rank**: 3rd (necessary but insufficient alone -- does not address the primary driver).

---

### Proposal 2: `size_mult` Hysteresis / Drawdown Threshold Recalibration

**Mechanism**: Two-part fix:

**(A) Raise the drawdown warning threshold from 10% to 15%.** The 10% threshold fires 61% of the time on a strategy with 10.7% annualized vol. At 15%, it would fire approximately 15-25% of the time (based on the empirical drawdown distribution), dramatically reducing the on/off oscillation.

**(B) Add hysteresis to the `size_mult` transitions.** Once `size_mult` drops due to a drawdown warning, it should not restore to full size until drawdown recovers to below a lower threshold (e.g., 8%). This prevents the sawtooth pattern where drawdown oscillates around 10% and `size_mult` toggles every few days.

**Root cause addressed**: Driver A (the `size_mult` oscillator). This is the **single highest-impact change** because it addresses the dominant turnover source.

**Implementation**: Modify the drawdown check at line 1365 and add a hysteresis state variable before the main loop:

```cpp
// Before loop -- add state variables:
bool dd_warn_engaged = false;  // sticky drawdown warning state

// Replace lines 1365-1368:
// OLD:
//   } else if (drawdown > p_.drawdown_warn) {
//       size_mult *= 0.5;
//       dd_warn = true;
//   }

// NEW:
} else if (!dd_warn_engaged && drawdown > 0.15) {
    // Engage at 15% drawdown (raised from 10%)
    dd_warn_engaged = true;
    size_mult *= 0.5;
    dd_warn = true;
} else if (dd_warn_engaged && drawdown > 0.08) {
    // Stay engaged until drawdown recovers below 8% (hysteresis)
    size_mult *= 0.5;
    dd_warn = true;
} else if (dd_warn_engaged && drawdown <= 0.08) {
    // Release -- drawdown recovered sufficiently
    dd_warn_engaged = false;
}
```

Additionally, the `stop_triggered` flag should only be true on the **transition** into dd_warn, not on every bar while it remains engaged. This prevents daily re-triggering of rebalance events:

```cpp
// Replace line 1431:
bool stop_triggered = dd_stop || (dd_warn && !dd_warn_prev_day);
```

**Expected turnover reduction**: 15-20x reduction (from 46.7x to approximately 27-32x). The 10%->15% threshold change alone reduces the number of drawdown-triggered rebalances from ~1,030 to an estimated ~300-400. The hysteresis prevents the remaining events from oscillating.

**Impact on signal capture**: Moderate positive impact. The current 10% threshold is causing the strategy to defensively halve positions during normal market volatility, then re-enter at worse prices. Allowing the strategy to trade through normal drawdowns should improve returns, not hurt them. The performance report explicitly calls this out: "A 10% threshold that fires 61% of the time is not a stop -- it is a permanent position limiter."

**Risks**:
- Larger drawdowns become possible (the strategy runs full-size through 10-15% drawdowns that were previously halved). Peak drawdown could increase from 25.6% to ~28-30%.
- Must test sensitivity: if the strategy's edge is marginal, running full-size through drawdowns may not improve net returns.

**Rank**: 1st (highest impact, addresses the dominant turnover source, likely improves returns).

---

### Proposal 3: Position Smoothing (Exponential Blend Toward Target)

**Mechanism**: Instead of immediately jumping to the target position, move a fraction (alpha) per rebalance day:

```
new_position = current_position + alpha * (target_position - current_position)
```

With alpha=0.25, the position moves 25% of the remaining gap each rebalance. After 4 rebalances at the same target, the position reaches ~68% of target; after 8 rebalances, ~90%.

**Exception**: Direction flips (sign change in target vs current) execute immediately at full target. Smoothing only applies to same-direction magnitude adjustments.

**Root cause addressed**: Drivers A and B simultaneously. The exponential blend absorbs both `size_mult` oscillation and equity-driven rounding noise because transient changes in target are automatically dampened. If `size_mult` flips from 1.0 to 0.5 for one week then back, the position only adjusts by ~25% of the difference rather than the full amount.

**Implementation**: Replace the position update block at line 1740:

```cpp
// POSITION SMOOTHING: blend toward target
const double SMOOTH_ALPHA = 0.25;  // 25% per rebalance step

for (auto& [sym, target_qty] : new_positions) {
    double old_qty = positions.count(sym) ? positions.at(sym) : 0.0;
    bool direction_flip = (old_qty * target_qty < -1e-9);
    bool from_flat = (std::abs(old_qty) < 1e-9);
    bool to_flat = (std::abs(target_qty) < 1e-9);

    double actual_new;
    if (direction_flip || from_flat || to_flat) {
        // Immediate execution for direction changes, entries, exits
        actual_new = target_qty;
    } else {
        // Smooth same-direction adjustments
        double blended = old_qty + SMOOTH_ALPHA * (target_qty - old_qty);
        actual_new = std::floor(blended + 0.5);
        // If rounding cancels the move entirely, keep current
        if (std::abs(actual_new - old_qty) < 0.5)
            actual_new = old_qty;
    }

    // Deduct transaction costs on delta
    double qty_change = std::abs(actual_new - old_qty);
    if (qty_change > 0.0) {
        double total_cost = ContractSpec::total_cost_rt(sym) * qty_change;
        equity -= total_cost;
    }
    // ... entry price logic ...
}
```

**Expected turnover reduction**: 12-18x reduction (from 46.7x to approximately 29-35x). The smoothing absorbs both `size_mult` transients and equity rounding noise. However, persistent target changes (sustained drawdown) still propagate through after 4-8 rebalances.

**Impact on signal capture**: Minor negative for fast-moving signals, neutral for the macro regime being traded. A signal that flips 6 times per year has average holding periods of ~40 trading days. With weekly rebalancing and alpha=0.25, full convergence takes ~8 rebalances (~40 trading days) -- which means the position is close to target for most of the holding period. However, the initial ramp-in takes 2-3 weeks, which delays full exposure to a new regime by approximately 10-15 trading days.

**Risks**:
- Delayed entry reduces capture of the initial regime-change move, which may be the most profitable part of the signal.
- Creates a gap between target and actual that complicates risk reporting and margin calculations.
- The alpha parameter requires tuning. Too low (0.10) = position never reaches target. Too high (0.50) = insufficient dampening.
- Smoothing interacts with the rebalance trigger logic: if stop_triggered causes daily rebalances, each day moves 25% closer -- at daily frequency, convergence is 4-8 trading days, which is faster than weekly.

**Rank**: 4th (effective but complex, introduces lag, better suited as a complement to Proposal 2 than as a standalone fix).

---

### Proposal 4: Reduce Rebalance Frequency (Weekly -> Biweekly + Event-Only)

**Mechanism**: Change the scheduled rebalance from every Friday to every-other-Friday (biweekly). Event-driven rebalances (tilt flip, drawdown stop, regime change) remain unchanged but with the additional constraint that drawdown warnings (`dd_warn`) no longer trigger rebalances -- only drawdown stops (`dd_stop`) and tilt changes do.

**Root cause addressed**: Driver C (excess rebalance events). The strategy currently fires 1,679 rebalances over 15.9 years (106/year). With biweekly scheduling and removing `dd_warn` as a rebalance trigger, this drops to approximately 26 scheduled + ~10 event-driven = ~36 rebalances per year.

**Implementation**: Modify the rebalance trigger logic at lines 1407-1436:

```cpp
// Replace is_friday check:
// Track biweekly calendar
static int friday_count = 0;
bool is_friday = false;
{
    time_t ts = static_cast<time_t>(dates[i]) * 86400;
    std::tm* t = std::gmtime(&ts);
    if (t->tm_wday == 5) {
        friday_count++;
        is_friday = (friday_count % 2 == 0);  // every other Friday
    }
}

// Modify stop_triggered to only fire on hard stop, not warning:
bool stop_triggered = dd_stop;  // removed: || dd_warn

// Keep all other triggers unchanged
bool do_rebalance = is_friday || regime_changed || filter_triggered ||
                    stop_triggered || tilt_changed;
```

The `dd_warn` still reduces `size_mult` (affecting the size of positions computed at the next scheduled rebalance), but it no longer forces an immediate rebalance. The position adjustment to half-size only happens at the next biweekly rebalance, which is at most 10 trading days away.

**Expected turnover reduction**: 10-12x reduction (from 46.7x to approximately 35-37x). The halving of scheduled rebalances cuts ~50% of the Friday-driven turnover. Removing `dd_warn` as a trigger eliminates ~400 of the 1,030 stop-triggered rebalances (the remaining ~630 are `dd_stop` which correctly zeroes positions entirely and should remain). Net effect: total rebalances drop from ~106/year to ~36/year.

**Impact on signal capture**: Minor negative. Biweekly rebalancing means tilt changes that happen to coincide with a non-rebalance Friday take up to 10 additional trading days to express (since tilt_changed still triggers immediately, this only matters for Friday-aligned adjustments). For a 40-day average holding period, a 5-day average delay is modest (~12% of hold time).

**Risks**:
- During drawdown warnings, the strategy continues running at full size for up to 10 trading days before the biweekly rebalance halves positions. This increases drawdown risk.
- A 2-week rebalance cadence may feel "slow" for a multi-asset futures portfolio where notional exposures can drift significantly with price moves. Consider adding a notional drift check: force rebalance if total notional deviates by >25% from target.
- The `force_rebalance` logic (line 1453) for flat portfolios still runs daily, which is correct -- a portfolio that should be invested but is flat should not wait 2 weeks.

**Rank**: 2nd (simple to implement, meaningful turnover reduction, minimal signal degradation when combined with Proposal 2).

---

### Proposal 5: Composite Signal Averaging (5-Day EMA)

**Mechanism**: Replace the point-in-time composite score with a 5-day exponential moving average before applying the tilt threshold:

```
smoothed_composite[t] = alpha * composite[t] + (1 - alpha) * smoothed_composite[t-1]
```

With alpha = 2/(5+1) = 0.333. The MacroTilt determination then uses `smoothed_composite` instead of raw `composite`.

**Root cause addressed**: An indirect contributor to turnover that is not captured in the four drivers above. The composite score is a weighted vote of three binary-ish sub-signals. When one sub-signal is near its threshold, the composite can oscillate between +0.33 and -0.33 on consecutive days, causing rapid tilt flips even after the 5-day debounce. Signal averaging dampens these oscillations at the source.

**Implementation**: Add EMA state before the loop and modify the tilt determination at line 748:

```cpp
// Before loop:
double smoothed_composite = 0.0;
bool smoothed_initialized = false;
const double EMA_ALPHA = 2.0 / (5.0 + 1.0);  // 5-day EMA

// Inside loop, after computing composite (line 746):
if (!smoothed_initialized && !std::isnan(composite)) {
    smoothed_composite = composite;
    smoothed_initialized = true;
} else if (!std::isnan(composite)) {
    smoothed_composite = EMA_ALPHA * composite + (1.0 - EMA_ALPHA) * smoothed_composite;
}

// Replace tilt determination:
MacroTilt raw_tilt = MacroTilt::NEUTRAL;
if (smoothed_composite > composite_thresh)
    raw_tilt = MacroTilt::RISK_ON;
else if (smoothed_composite < -composite_thresh)
    raw_tilt = MacroTilt::RISK_OFF;
```

**Expected turnover reduction**: 3-5x reduction (from 46.7x to approximately 42-44x). This addresses a minor contributor -- signal flips are already debounced by a 5-day holding period, and only 6 flips/year reach through. The EMA would reduce borderline flips from ~6 to perhaps ~4-5 per year, each saving ~2x turnover.

**Impact on signal capture**: Small negative. The 5-day EMA introduces 2-3 days of lag to genuine regime changes. For a signal that changes every 2 months, this is a ~5% delay. However, the lag also means the strategy misses the immediate price move on regime changes, which can be the most informative period.

**Risks**:
- The 5-day debounce already provides similar functionality. Stacking EMA + debounce may over-smooth the signal, converting genuine regime changes into NEUTRAL periods.
- If the composite oscillates between +0.33 and -0.33 with a 5-day EMA, the smoothed value will hover near zero -- potentially keeping the strategy in NEUTRAL (flat) for extended periods, which is itself a form of turnover (entry -> flat -> re-entry).

**Rank**: 5th (least impactful, addresses a minor contributor, risks over-smoothing when combined with existing debounce).

---

## 3. Ranked Recommendations

| Rank | Proposal | Expected Turnover After | Complexity | Signal Impact |
|------|----------|------------------------|------------|---------------|
| 1 | **Drawdown Threshold Recalibration + Hysteresis** | 27-32x standalone | Low | Positive (improves returns) |
| 2 | **Biweekly Rebalancing + Event-Only dd_warn** | 35-37x standalone | Low | Minor negative |
| 3 | **Rebalance Bands** | 32-37x standalone | Low | Negligible |
| 4 | **Position Smoothing** | 29-35x standalone | Medium | Minor negative (entry lag) |
| 5 | **Signal Averaging (5-Day EMA)** | 42-44x standalone | Low | Minor negative |

### Recommended Implementation Order

**Phase 1** (implement together, expected combined effect: **12-18x turnover**):
1. Proposal 2: Raise drawdown warning to 15%, add 8% recovery hysteresis
2. Proposal 4: Biweekly rebalancing, remove dd_warn as rebalance trigger
3. Proposal 1: Rebalance bands (2-contract / 30% threshold)

These three are complementary and address orthogonal drivers. Their effects multiply rather than overlap:
- Proposal 2 reduces `size_mult` oscillation by ~70% (eliminating the sawtooth)
- Proposal 4 halves the number of scheduled rebalances
- Proposal 1 suppresses rounding noise on the remaining rebalances

Combined estimate: 46.7x * 0.35 (Proposal 2) * 0.65 (Proposal 4) * 0.75 (Proposal 1) = **~8.0x**

Even with conservative overlap assumptions (effects are not fully independent), the combined result should be in the **10-15x range**, which meets the <15x target.

**Phase 2** (implement only if Phase 1 is insufficient):
4. Proposal 3: Position smoothing with alpha=0.25

**Do not implement**:
5. Proposal 5: Signal averaging -- the 5-day debounce already covers this, and over-smoothing risks are real.

---

## 4. Verification Plan

After implementing the Phase 1 changes, re-run the v2 backtest and verify:

1. **Turnover < 15x** (primary objective)
2. **Sharpe ratio does not decrease** (should increase due to reduced transaction costs)
3. **Signal flip count remains ~6/year** (ensures signal is not over-dampened)
4. **Max drawdown does not exceed 30%** (relaxed threshold trade-off for less whipsawing)
5. **Profit factor increases** (fewer transaction costs = better net economics)
6. **Inspect [REB] log lines**: confirm rebalance count drops from ~106/year to ~36/year
7. **Inspect [SIZING] log lines**: confirm `size_mult` is stable within regimes (no sawtooth pattern)

### Key Diagnostic Queries

```bash
# Count rebalance events per year (target: ~36)
grep '\[REB\]' backtest_output_v3.txt | wc -l

# Count size_mult transitions (should see fewer 1.00->0.50 oscillations)
grep '\[SIZING\]' backtest_output_v3.txt | awk -F'size_mult=' '{print $2}' | \
    awk -F' ' '{print $1}' | uniq -c | sort -rn

# Verify turnover metric directly
grep 'Annual Turnover' backtest_output_v3.txt
```

---

## 5. Appendix: Detailed Turnover Arithmetic

### Current Turnover Decomposition (Estimated)

The backtest reports 46.7x annual turnover. Using average equity of ~$1.4M and average gross notional of ~$2.8M (2x leverage):

- **Total notional traded per year**: 46.7 * $1.4M = **$65.4M** in notional changes
- **Gross notional at any point**: ~$2.8M
- **Full portfolio turns per year**: $65.4M / $2.8M = **~23.4 full turns**

### Decomposition by Driver

| Driver | Estimated Annual Notional Traded | Percentage |
|--------|----------------------------------|------------|
| A: `size_mult` oscillation | $36-42M | 55-65% |
| B: Equity rounding noise | $13-16M | 20-25% |
| C: Excess rebalance events | $7-10M | 10-15% |
| D: Signal flips (unavoidable) | $3-7M | 5-10% |
| **Total** | **$65.4M** | **100%** |

### Post-Phase-1 Projection

| Driver | Current | After Phase 1 | Reduction |
|--------|---------|---------------|-----------|
| A: `size_mult` oscillation | $39M | $8M | -80% |
| B: Equity rounding noise | $14.5M | $4M | -72% |
| C: Excess rebalance events | $8.5M | $2M | -76% |
| D: Signal flips (unavoidable) | $3.4M | $3.4M | 0% |
| **Total** | **$65.4M** | **$17.4M** | **-73%** |
| **Implied turnover** | **46.7x** | **~12.4x** | -- |

### Transaction Cost Savings

At an average of ~$20 round-trip per contract and an average contract notional of ~$100K:

- **Current annual trading costs**: $65.4M / $100K * $20 = **~$13,080/year** (1.3% of $1M initial, 0.9% of average equity)
- **Projected Phase 1 costs**: $17.4M / $100K * $20 = **~$3,480/year** (0.35% of $1M initial)
- **Annual savings**: ~$9,600 or **~0.6% of average equity per year**

This savings flows directly to the bottom line. The current 3.6% CAGR could improve to approximately 4.1-4.3% CAGR just from reduced friction, a meaningful improvement for a strategy with a 1.075 profit factor.
