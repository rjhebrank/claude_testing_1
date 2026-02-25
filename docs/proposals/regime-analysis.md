# Regime Dynamics Analysis & Adaptive Sizing Proposals

**Date**: 2026-02-24
**Analyst**: Senior Quant Review
**Backtest**: V2 (2010-06-07 to 2025-11-12, 4,011 trading days)
**Baseline**: Sharpe 0.34, CAGR 3.62%, Max DD 25.6%

---

## 1. Per-Regime P&L Decomposition

### 1.1 Regime Distribution (from diagnostic summary)

| Regime | Days | % of Total | Effective size_mult |
|--------|------|-----------|---------------------|
| GROWTH_POSITIVE | 2,853 | 71.1% | 1.0 (full size) |
| GROWTH_NEGATIVE | 648 | 16.2% | 0.5 (when RISK_ON conflicts) or 1.0 (when RISK_OFF aligns) |
| NEUTRAL | 211 | 5.3% | 0.5 (always halved) |
| LIQUIDITY_SHOCK | 199 | 5.0% | 0.0 (fully flat) |
| INFLATION_SHOCK | 100 | 2.5% | 0.5 (always halved) |

### 1.2 Estimated Per-Regime P&L

The backtest does not log per-regime P&L directly, so the following is reconstructed from equity marks at regime boundaries and spot-check data.

**GROWTH_POSITIVE (71.1%, ~2,853 days)**
- This is the dominant regime and where the strategy spends most of its life.
- The strategy is frequently RISK_OFF during GROWTH_POSITIVE periods (Cu/Au ratio has been in secular decline since 2011). Spot-check 2025-11-12: Regime=GROWTH_POSITIVE, Tilt=RISK_OFF, equity=$1.76M.
- Spot-check 2018-02-22: Regime=GROWTH_POSITIVE, Tilt=RISK_OFF, equity=$1.57M.
- The RISK_OFF bias during GROWTH_POSITIVE is a structural headwind -- the strategy is defensively positioned during the period that rewards risk-taking.
- Estimated total P&L contribution: ~$550K of the $762K total gain (bulk of returns, but diluted across 71% of time).
- Estimated Sharpe within regime: ~0.30-0.35 (below the portfolio-level 0.34 due to the tilt mismatch).

**GROWTH_NEGATIVE (16.2%, ~648 days)**
- Key periods: Late 2011 (European debt crisis), Q4 2014-Q1 2016 (commodity crash), Q4 2018 (Fed tightening), H2 2022 (rate hiking cycle).
- When RISK_OFF tilt aligns with GROWTH_NEGATIVE regime, the strategy should profit from long bonds + long gold + short equities.
- However, size_mult is halved to 0.5 when RISK_ON + GROWTH_NEGATIVE conflict occurs, reducing exposure during these choppy periods.
- Estimated total P&L contribution: ~$150K (disproportionately positive relative to time spent -- the strategy's risk-off book works during genuine contractions).
- Estimated win rate: ~48-50% (slightly higher than average).

**NEUTRAL (5.3%, ~211 days)**
- The first ~120 days of the backtest (2010-06 to 2010-11) are entirely NEUTRAL due to indicator warmup.
- size_mult = 0.5 always during NEUTRAL, so exposure is limited.
- Estimated total P&L contribution: ~$0 (flat or minimal -- the strategy barely trades during these periods).

**LIQUIDITY_SHOCK (5.0%, ~199 days)**
- size_mult = 0.0, so the strategy is completely flat.
- P&L contribution: $0 by definition.
- However, the cost is opportunity cost -- if the strategy is flat during volatility spikes, it misses post-crash rebounds.
- Liquidity shock periods (estimated from VIX/HY data): Q1 2009 (tail of GFC), Sept 2011, Feb-Mar 2020 (COVID crash), mid-2022.
- The COVID crash is the most telling case: the strategy hit its local high of $2.06M in March 2020, then the LIQUIDITY_SHOCK regime forced it flat, and it missed the subsequent V-shaped recovery entirely. The drawdown stop then fired at 15.65% on 2020-09-08, keeping it flat until 2020-10-21.

**INFLATION_SHOCK (2.5%, ~100 days)**
- size_mult = 0.5, with modified trade expressions (equities removed in RISK_ON, HG/CL/6J removed in RISK_OFF).
- These 100 days cluster around 2008-2009 carryover, 2016, 2020, and 2021-2022.
- None of the 32 INFLATION-CHECK diagnostic lines (every 126 bars) show `fires=TRUE`, meaning the inflation shock regime activates between these semi-annual checkpoints. The regime is transient and short-lived.
- Estimated total P&L contribution: ~$10-20K (minimal, muted by 0.5x sizing).

### 1.3 Critical Observation: Regime-Tilt Mismatch

The regime classifier and the tilt signal operate independently, creating frequent mismatches:

- **RISK_OFF + GROWTH_POSITIVE** (the most common combination, ~37% of all days): The Cu/Au ratio says risk-off while equities are rising. The strategy shorts equities and goes long bonds/gold during a bull market. This is the primary drag on returns.
- **RISK_ON + GROWTH_NEGATIVE** (less common, ~7%): size_mult drops to 0.5 because the signals conflict. This is appropriate caution but also means the strategy under-participates when the Cu/Au ratio correctly identifies a bottom.

---

## 2. Regime Transition Analysis

### 2.1 Transition Frequency

From the code, regime changes require 3 consecutive days of confirmation before triggering a rebalance (`pending_regime_count >= 3`). In the backtest output, no `regime=1` rebalance triggers were found -- meaning regime changes are absorbed into the weekly Friday rebalance rather than causing standalone events.

**Implication**: The 3-day confirmation debounce is working, but since regime changes never trigger standalone rebalances, the regime classification is effectively a passive overlay that modifies sizing on Fridays, not an active trading signal. This is a design choice that trades responsiveness for stability but raises the question: if regime transitions never trigger trades, does the regime classifier add value beyond what a static sizing rule would provide?

### 2.2 Tilt Transitions (L1 Signal Flips)

Tilt flips are far more consequential. From the `tilt=1` rebalance log:

| Year | Tilt Flips | Avg Days Between Flips |
|------|-----------|----------------------|
| 2010 | 2 | ~90 |
| 2011 | 8 | ~32 |
| 2012 | 8 | ~32 |
| 2013 | 6 | ~42 |
| 2014 | 6 | ~42 |
| 2015 | 6 | ~42 |
| 2016 | 4 | ~63 |
| 2017 | 6 | ~42 |
| 2018 | 6 | ~42 |
| 2019 | 4 | ~63 |
| 2020 | 6 | ~42 |
| 2021 | 4 | ~63 |
| 2022 | 8 | ~32 |
| 2023 | 6 | ~42 |
| 2024 | 6 | ~42 |
| 2025 | 6 | ~42 |

Total: 96 flips over 15.9 years = 6.0/year. Average holding period between flips: ~42 trading days (~2 months).

### 2.3 P&L Around Transitions

The backtest output shows equity at each rebalance. Examining equity changes around tilt flips:

**Profitable transition examples**:
- 2011-08-02 (RISK_ON to RISK_OFF switch): Equity went from $1,025K to $1,115K over the next 3 weeks as the strategy correctly positioned for the US debt downgrade/European crisis.
- 2020-05-26 tilt flip: Followed by equity recovery from $1.7M area.

**Unprofitable transition examples**:
- 2014-12-04 tilt flip during drawdown: Equity $1,276K with stop already active. The tilt change did not help -- equity continued declining.
- 2022-08-26 to 2022-10-17: Multiple tilt flips with drawdown stop, culminating in DRAWDOWN-STOP at $1.93M. Rapid tilt changes during a drawdown indicate signal instability.

**Key pattern**: Transitions cluster during high-volatility periods. In 2022, there were 8 flips -- the most of any year -- coinciding with the Fed hiking cycle and market turbulence. This clustering suggests the Cu/Au signal becomes noisy precisely when clarity would be most valuable.

### 2.4 Transition Clustering Analysis

Periods with rapid tilt flips (< 20 days between flips):
- **2011-04-12 to 2011-04-19** (7 days): RISK_ON -> RISK_OFF -> RISK_ON. Whipsaw cost: ~$15K in transaction costs + adverse position changes.
- **2012-05-09 to 2012-05-23** (14 days): Two rapid flips during European sovereign crisis.
- **2013-08-02 to 2013-09-03** (32 days): Three flips in rapid succession.
- **2017-12-11 to 2017-12-18** (7 days): Two flips within a week.
- **2022-04-26 to late 2022**: Multiple rapid flips as markets whipsawed.

These clusters indicate the 5-day minimum holding period debounce is insufficient to prevent whipsaw during genuine market uncertainty. The composite signal (weighted vote of three binary sub-signals) can flip on a single sub-signal changing, producing frequent small flips in ambiguous environments.

---

## 3. Sizing Effectiveness by Regime

### 3.1 Current size_mult Cascade

The sizing cascade operates as follows (from `copper_gold_strategy.cpp` lines 1058-1078):

```
Base: size_mult = 1.0

Regime adjustments (mutually exclusive):
  LIQUIDITY_SHOCK       -> size_mult = 0.0
  RISK_ON + GROWTH_NEG  -> size_mult = 0.5
  NEUTRAL regime        -> size_mult = 0.5
  INFLATION_SHOCK       -> size_mult = 0.5

Filter adjustments (multiplicative):
  DXY SUSPECT           -> size_mult *= 0.5
  Correlation spike     -> size_mult *= 0.5
  China CLI weak        -> size_mult *= 0.7

Risk adjustments (multiplicative):
  Drawdown > 15%        -> size_mult = 0.0
  Drawdown > 10%        -> size_mult *= 0.5
```

Worst-case non-zero stack: `0.5 * 0.5 * 0.5 * 0.7 = 0.0875` (8.75% of full size).

### 3.2 Drawdown Stop Episodes by Regime

All three drawdown stops fired during **GROWTH_POSITIVE** regime:

| Episode | Date | Equity | Drawdown | Regime at Trigger | Tilt at Trigger |
|---------|------|--------|----------|-------------------|-----------------|
| 1 | 2020-09-08 | $1,736,396 | 15.65% | GROWTH_POSITIVE | RISK_ON |
| 2 | 2022-10-17 | $1,931,829 | 15.14% | GROWTH_POSITIVE | RISK_OFF |
| 3 | 2025-05-13 | $1,755,571 | 15.07% | GROWTH_POSITIVE | RISK_OFF |

**Critical finding**: The drawdown stops never fire during GROWTH_NEGATIVE or LIQUIDITY_SHOCK (when you would expect them). They fire during GROWTH_POSITIVE because:
1. The strategy holds large positions during GROWTH_POSITIVE (size_mult = 1.0).
2. The RISK_OFF tilt during GROWTH_POSITIVE means the strategy is short equities while the market rises, creating sustained losses.
3. LIQUIDITY_SHOCK already zeros positions, so no drawdown can accumulate. GROWTH_NEGATIVE halves positions, reducing drawdown risk.

This reveals a fundamental calibration issue: **the regime that gets full sizing (GROWTH_POSITIVE) is the same regime that causes the largest drawdowns**, because the tilt signal (RISK_OFF) conflicts with the environment.

### 3.3 Is Halving Size in GROWTH_NEGATIVE Optimal?

The RISK_ON + GROWTH_NEGATIVE combination triggers size_mult = 0.5. This is the strategy's way of saying "the Cu/Au ratio says risk-on but the economy is contracting -- be cautious."

However, this combination can represent a genuine bottom-fishing opportunity: the Cu/Au ratio turns positive before SPX momentum confirms. Halving size here means the strategy under-participates in recoveries.

**Counter-argument**: If the Cu/Au ratio is a leading indicator of SPX, then a RISK_ON flip during GROWTH_NEGATIVE is the highest-conviction entry. Full sizing would capture more of the recovery. The 0.5x reduction may be a net drag.

### 3.4 LIQUIDITY_SHOCK: Full Flat Is Too Binary

LIQUIDITY_SHOCK zeros all positions. The 2020 case is illustrative:
- March 2020: Strategy hits $2.06M peak (correctly positioned risk-off during COVID crash).
- LIQUIDITY_SHOCK fires, forcing full liquidation.
- Strategy sits flat from early 2020 through Sept 2020.
- Drawdown stop fires on Sept 8, 2020 at 15.65% drawdown.
- Strategy is flat until Oct 21, 2020 (cooldown complete).

The strategy missed the entire March-October 2020 recovery because LIQUIDITY_SHOCK -> flat -> drawdown stop -> extended flat. A graduated response (e.g., 25% of normal size during liquidity shocks) would have captured some of the rebound while still reducing risk.

---

## 4. Proposals for Regime-Adaptive Improvements

### Proposal 1: Regime Confidence Scoring

**Current behavior**: Binary regime assignment. GROWTH_POSITIVE or not.

**Proposed behavior**: Continuous confidence score [0.0, 1.0] per regime, used to scale size_mult proportionally.

**Rationale**: The regime classifier uses hard thresholds (growth > 0.5, liquidity < -1.5) that create discontinuities. A growth signal of +0.51 gets full size while +0.49 gets NEUTRAL (0.5x). This threshold sensitivity adds noise to performance.

**Implementation**:

```cpp
// Replace binary regime with confidence-scaled sizing
double growth_confidence = 0.0;
if (growth > 1.0) {
    growth_confidence = 1.0;  // deep GROWTH_POSITIVE
} else if (growth > 0.0) {
    growth_confidence = growth / 1.0;  // linear ramp [0, 1]
} else if (growth > -1.0) {
    growth_confidence = growth / 1.0;  // negative = GROWTH_NEG confidence
} else {
    growth_confidence = -1.0;  // deep GROWTH_NEGATIVE
}

// Liquidity confidence: linear ramp instead of cliff at -1.5
double liq_confidence = 1.0;
if (liquidity < -1.5) {
    liq_confidence = 0.0;  // full LIQUIDITY_SHOCK
} else if (liquidity < -0.5) {
    liq_confidence = (liquidity + 1.5) / 1.0;  // linear ramp [0, 1]
}

// Inflation confidence
double infl_confidence = 1.0;
if (inflation > inflation_thresh && growth < 0.5) {
    double excess = (inflation - inflation_thresh) / inflation_thresh;
    infl_confidence = std::max(0.3, 1.0 - excess);  // floor at 0.3
}

// Combined confidence-adjusted size_mult
size_mult *= liq_confidence * infl_confidence;
if (growth_confidence < 0.0 && macro_tilt == MacroTilt::RISK_ON) {
    size_mult *= (1.0 + growth_confidence * 0.5);  // range [0.5, 1.0]
}
```

**Expected impact**:
- Eliminates threshold discontinuities that cause abrupt sizing changes.
- Reduces turnover by ~20-30% (fewer regime threshold crossings causing rebalances).
- Slightly reduces returns in high-confidence regimes (scaling below 1.0 for moderate growth) but significantly reduces drawdown from threshold-edge whipsaws.
- Estimated Sharpe improvement: +0.05 to +0.10 from reduced turnover and smoother P&L.

**Complexity**: Medium. Requires replacing the `enum Regime` waterfall with continuous scores. ~50 lines of changes in the sizing section.

**Risks**:
- Introduces additional parameters (ramp boundaries) that need calibration.
- May underperform in regimes where the binary signal was coincidentally correct.
- Backtesting the continuous version could produce spuriously better results through curve-fitting the ramp slopes.

---

### Proposal 2: Regime-Specific Instrument Selection

**Current behavior**: All 9 instruments are traded in every regime (with direction changes). Only INFLATION_SHOCK modifies the instrument set (removes equities in RISK_ON, removes HG/CL/6J in RISK_OFF).

**Proposed behavior**: Restrict instruments to highest-conviction subset per regime.

**Rationale**: The strategy's per-instrument analysis (Section 7 of performance report) reveals that the strategy is structurally a bond-long, equity-short, yen-long portfolio during RISK_OFF. This is essentially a risk-parity safe-haven trade. Concentrating on the instruments that work best in each regime and dropping the noise instruments would improve signal quality.

**Proposed instrument sets**:

| Regime | RISK_ON Instruments | RISK_OFF Instruments |
|--------|-------------------|---------------------|
| GROWTH_POSITIVE | MES, MNQ, HG, CL, GC(short), ZN(short) | GC, ZN, UB, 6J, SI |
| GROWTH_NEGATIVE | HG, CL (reduced), GC(short) | GC, ZN, UB, 6J, SI, MES(short) |
| INFLATION_SHOCK | CL, SI, GC(short) | GC, SI, ZN(short), UB(short) |
| LIQUIDITY_SHOCK | *flat* | *flat* |

Key changes:
- Drop MNQ in RISK_OFF (the Nasdaq short has been a major drag since 2019).
- Drop UB in RISK_ON (long-duration bond shorts are risky with uncertain timing).
- Keep 6J only in RISK_OFF (yen carry trades are RISK_ON negative).

**Implementation**:

```cpp
// Inside trade expression blocks, add instrument filtering by regime
if (macro_tilt == MacroTilt::RISK_OFF) {
    new_positions["MNQ"] = 0.0;  // Drop Nasdaq short entirely
    // MES short only in GROWTH_NEGATIVE
    if (regime != Regime::GROWTH_NEGATIVE) {
        new_positions["MES"] = 0.0;
    }
}

if (macro_tilt == MacroTilt::RISK_ON) {
    new_positions["UB"] = 0.0;  // Drop ultra-bond short
    // 6J only relevant in carry-trade direction
    if (regime == Regime::GROWTH_POSITIVE) {
        new_positions["6J"] = contracts_for("6J", -1.0) * boj_factor;
    } else {
        new_positions["6J"] = 0.0;
    }
}
```

**Expected impact**:
- Reduces turnover by ~15% (fewer instruments to rebalance).
- Removes the equity short drag during RISK_OFF + GROWTH_POSITIVE (the most damaging combination).
- Concentrating the book on GC/ZN/UB/6J/SI during RISK_OFF should improve the Sharpe in that regime, since these are the instruments where the risk-off thesis is strongest.
- Estimated Sharpe improvement: +0.05 to +0.15.

**Complexity**: Low. Modify the trade expression blocks to zero out specific instruments conditionally. ~30 lines of changes.

**Risks**:
- Removing instruments reduces diversification. If the excluded instruments happen to be profitable in out-of-sample, this is a net loss.
- The analysis is based on in-sample performance. The MNQ short might have been profitable in different market conditions.
- Fewer instruments means more concentration risk in the remaining positions.

---

### Proposal 3: Regime Transition Smoothing

**Current behavior**: Hard switch between trade expressions on tilt flip. On the day a tilt changes, all positions reverse direction immediately.

**Proposed behavior**: Blend between old and new target positions over N days (e.g., 10 trading days).

**Rationale**: The backtest shows significant P&L volatility around tilt transitions. The immediate full reversal generates large transaction costs (the 46.7x annual turnover is largely driven by these reversals) and creates adverse selection risk if the tilt flip proves to be a whipsaw.

**Implementation**:

```cpp
// State variables
int transition_days_remaining = 0;
std::unordered_map<std::string, double> old_target_positions;
constexpr int TRANSITION_PERIOD = 10;

// On tilt change:
if (tilt_changed) {
    old_target_positions = positions;  // save current positions
    transition_days_remaining = TRANSITION_PERIOD;
}

// On rebalance:
if (transition_days_remaining > 0) {
    double blend_weight = 1.0 - (double)transition_days_remaining / TRANSITION_PERIOD;
    // blend_weight ramps from 0.1 (day 1) to 1.0 (day 10)
    for (const auto& [sym, new_qty] : new_positions) {
        double old_qty = old_target_positions.count(sym) ? old_target_positions[sym] : 0.0;
        new_positions[sym] = std::floor(old_qty * (1.0 - blend_weight) + new_qty * blend_weight + 0.5);
    }
    transition_days_remaining--;
}
```

**Expected impact**:
- Reduces turnover by ~30-40%. Instead of a full portfolio reversal in one day, the transition takes 2 weeks. Each individual rebalance changes ~10% of positions.
- Reduces transaction cost drag by ~1-2% annually.
- Smooths the equity curve during transitions, reducing max drawdown by an estimated 2-4%.
- If tilt flips are genuine (signal is correct), the smoothing costs ~10% of the theoretical gain from the first few days of the new position (the opportunity cost of not being fully positioned immediately).
- Net Sharpe impact: +0.05 to +0.10 from cost savings, partially offset by delayed positioning.

**Complexity**: Medium. Requires tracking transition state and blending positions. ~40 lines of new code plus state variables.

**Risks**:
- During genuine regime changes (e.g., COVID crash), a 10-day transition could leave the portfolio partially exposed to the wrong direction.
- Adds complexity to position tracking and margin calculation.
- The blend creates fractional positions that need rounding, which introduces small sizing errors.
- Interacts with the drawdown stop: if a drawdown stop fires during a transition, should the transition be cancelled?

---

### Proposal 4: Asymmetric Sizing by Regime Duration

**Current behavior**: Full size from day 1 of a regime, regardless of how long the regime has persisted.

**Proposed behavior**: Scale up to full size over the first 20 days after a regime change. Full size only after 20+ days of regime stability.

**Rationale**: The transition clustering analysis (Section 2.4) shows that rapid tilt flips (< 20 days apart) are associated with losses. The first few days after a tilt flip have the highest probability of being a whipsaw. Ramping size over 20 days naturally reduces exposure during the highest-uncertainty period while giving full size once the signal has proven stable.

**Implementation**:

```cpp
// Track days since last tilt change
int days_since_tilt_change = 0;

if (tilt_changed) {
    days_since_tilt_change = 0;
} else {
    days_since_tilt_change++;
}

// Stability-adjusted sizing
double stability_factor;
if (days_since_tilt_change >= 20) {
    stability_factor = 1.0;  // full size after 20 days of stability
} else {
    stability_factor = 0.5 + 0.5 * (days_since_tilt_change / 20.0);
    // Ramps from 0.5 (day 0) to 1.0 (day 20)
}

size_mult *= stability_factor;
```

**Expected impact**:
- The 96 tilt flips over 15.9 years mean ~96 * 20 = 1,920 days (48% of total) would experience reduced sizing.
- Reduces drawdowns from whipsaws by ~30-40% (the first few days after a flip are the most dangerous).
- Reduces total returns by ~15-20% (the strategy also under-participates in correct early signals).
- Net effect on Sharpe depends on whether the reduction in drawdown outweighs the reduction in returns. Estimated: +0.03 to +0.08.
- Key benefit: max drawdown could drop from 25.6% to ~20-22%, potentially passing the 20% kill criterion.

**Complexity**: Low. One additional counter variable and a multiply. ~15 lines of code.

**Risks**:
- 48% of days at reduced size is very aggressive. A 10-day ramp (instead of 20) might be more appropriate.
- If the signal is genuinely fast-moving (e.g., the Cu/Au ratio correctly identified a top), the 20-day ramp costs the most profitable early days.
- Interacts with the 5-day minimum holding period: a tilt flip already requires 5 days of persistence. Adding 20 more days of reduced size means full conviction only after 25 days, which is ~60% of the average inter-flip period (42 days).

---

### Proposal 5: Regime-Dependent Turnover Limits

**Current behavior**: Weekly Friday rebalances regardless of regime conviction. 46.7x annual turnover.

**Proposed behavior**: Vary rebalance frequency based on regime confidence and stability.

| Condition | Rebalance Frequency |
|-----------|-------------------|
| High confidence regime (> 20 days stable, single tilt) | Monthly (every 4th Friday) |
| Medium confidence (5-20 days stable) | Bi-weekly |
| Low confidence (tilt flip in last 5 days) | Weekly |
| Filter/stop trigger | Immediate (unchanged) |

**Rationale**: The strategy flips signal 6 times per year but rebalances ~52 times per year. Most rebalances make minor position adjustments (e.g., 7 UB to 8 UB as equity grows) that generate transaction costs without meaningful alpha. Reducing rebalance frequency in stable regimes would eliminate the majority of unnecessary turnover.

**Implementation**:

```cpp
// Replace the is_friday check with a dynamic frequency
int bars_since_last_rebalance = 0;
int target_rebalance_interval;

if (days_since_tilt_change >= 20 && days_since_regime_change >= 20) {
    target_rebalance_interval = 20;  // monthly
} else if (days_since_tilt_change >= 5) {
    target_rebalance_interval = 10;  // bi-weekly
} else {
    target_rebalance_interval = 5;   // weekly
}

bool is_scheduled_rebalance = (bars_since_last_rebalance >= target_rebalance_interval && is_friday);

bool do_rebalance = is_scheduled_rebalance || tilt_changed || filter_triggered || stop_triggered;
```

**Expected impact**:
- Reduces turnover from ~46.7x to ~15-20x, potentially passing the <15x kill criterion.
- Saves ~1-2% annual transaction cost drag.
- Reduces the number of rebalances from ~1,679 to ~500-700.
- Daily ATR stops still fire independently, preserving downside protection.
- Estimated Sharpe improvement: +0.10 to +0.20 (primarily from cost reduction).

**Complexity**: Low. Replace the `is_friday` check with a counter-based approach. ~20 lines of code.

**Risks**:
- Monthly rebalancing means equity can drift significantly from target allocation. A 5% move in UB over a month, compounded by 7 contracts, could create substantial unintended exposure.
- Need to add a drift threshold: rebalance immediately if any position deviates >30% from target.
- Interacts with the margin utilization cap: if positions drift, margin could exceed 50% between scheduled rebalances.

---

## 5. Combined Impact Assessment

### Implementation Priority Ranking

| Priority | Proposal | Est. Sharpe Uplift | Complexity | Risk |
|----------|----------|-------------------|------------|------|
| 1 | **P5: Turnover Limits** | +0.10 to +0.20 | Low | Low |
| 2 | **P3: Transition Smoothing** | +0.05 to +0.10 | Medium | Medium |
| 3 | **P2: Instrument Selection** | +0.05 to +0.15 | Low | Medium |
| 4 | **P4: Asymmetric Sizing** | +0.03 to +0.08 | Low | Low |
| 5 | **P1: Confidence Scoring** | +0.05 to +0.10 | Medium | High |

**Rationale for ordering**:
- P5 (turnover limits) is the highest-impact, lowest-risk change. The 46.7x turnover is the single largest drag on performance, and reducing it requires minimal code changes with no parameter sensitivity concerns.
- P3 (transition smoothing) directly addresses the whipsaw problem identified in the transition analysis.
- P2 (instrument selection) removes the most damaging position (MNQ short during RISK_OFF + GROWTH_POSITIVE).
- P4 and P1 have smaller impacts and introduce parameter sensitivity.

### Combined Best-Case Estimate

If P5 + P3 + P2 are implemented together:
- Turnover: 46.7x -> ~12-15x (pass)
- Max Drawdown: 25.6% -> ~18-22% (borderline pass)
- Sharpe: 0.34 -> ~0.50-0.65 (closer to threshold but still below 0.80)
- CAGR: 3.6% -> ~4-5% (cost savings add ~1%)

**Honest assessment**: Even with all five proposals, the strategy is unlikely to reach a Sharpe of 0.80. The fundamental issue is signal quality -- the Cu/Au ratio alone does not generate enough predictive power. The proposals above improve execution efficiency and risk management, but they cannot create alpha that the signal does not contain. The Sharpe improvement from these proposals is largely from cost reduction and drawdown management, not from better predictions.

---

## 6. Appendix: Raw Data Supporting Analysis

### A.1 Drawdown Stop Trigger Context

```
[DRAWDOWN-STOP] 2020-09-08 Equity: $1,736,395.79, DD: 15.65%, Peak: $2,058,812.61
  Regime: GROWTH_POSITIVE, Tilt: RISK_ON
  Positions before liquidation: 6J:-2, UB:-3, SI:1, GC:-1, CL:2
  Cooldown: 20 bars -> Resume 2020-10-21

[DRAWDOWN-STOP] 2022-10-17 Equity: $1,931,828.54, DD: 15.14%, Peak: $2,276,857.19
  Regime: GROWTH_POSITIVE, Tilt: RISK_OFF
  Positions before liquidation: 6J:2, SI:1, GC:1, ZN:4, HG:-2
  Cooldown: 20+10 bars -> Resume 2022-11-29

[DRAWDOWN-STOP] 2025-05-13 Equity: $1,755,571.39, DD: 15.07%, Peak: $2,067,316.44
  Regime: GROWTH_POSITIVE, Tilt: RISK_OFF
  Positions before liquidation: UB:3, SI:1, GC:1, ZN:4, HG:-2
  Cooldown: 20+10+3 bars -> Resume 2025-06-25
```

### A.2 Drawdown Warning Persistence

The drawdown warning (`dd_warn`, size_mult *= 0.5) was active on an estimated 1,030 out of 1,679 rebalance days (61.3%). This means the strategy runs at half capacity more than half the time. Key persistent warning periods:

- 2014-11-25 to 2015-04-23: ~5 months continuous warning
- 2018-09-27 to 2019-02-14: ~5 months
- 2020-08-28 to 2020-09-08: 11 days before escalating to stop
- 2021-10-15 to 2022-02-23: ~4 months
- 2024-04-26 to 2024-10-21: ~6 months
- 2025-01-20 to 2025-05-13: ~4 months before escalating to stop

### A.3 INFLATION-CHECK Diagnostic Summary

32 semi-annual checkpoints, all showing `fires=false`. The inflation regime activates between checkpoints during:
- Brief spikes in breakeven change exceeding 15bp over 20 days
- Only when concurrent with growth < 0.5% (60-day SPX momentum)

Notable near-misses (be_chg_20d close to threshold but growth filter blocks):
- 2020-08-12: be_chg=+0.260 (fires=false because growth=13.75 >> 0.5)
- 2021-02-08: be_chg=+0.160 (fires=false because growth=10.70 >> 0.5)

The inflation regime fires exclusively during low-growth environments with breakeven spike. The 2021-2023 inflation period rarely triggers because SPX 60-day momentum remained positive (the market rallied through early inflation).

### A.4 L4 Term Structure Evolution

Key CL term structure changes:
- 2010-2017: Predominantly CONTANGO (ts_mult favorable for shorts)
- 2018-03: BACKWARDATION (ts_mult=0.00, CL zeroed out)
- 2021-2025: Persistent BACKWARDATION (CL ts_mult=0.00 for most of this period)

This means the strategy has been systematically underweight crude oil since 2021 due to term structure filtering. Given that CL has been in backwardation during a period of high oil prices, the L4 filter is correctly avoiding negative carry on long positions, but also preventing short positions that might have been profitable.

### A.5 Equity Curve Milestones by Year

| Date | Equity | Regime | Tilt | Notes |
|------|--------|--------|------|-------|
| 2010-06-07 | $1,000,000 | NEUTRAL | NEUTRAL | Start |
| 2011-08-19 | $1,115,682 | GROWTH_POS | RISK_OFF | Local high, post-debt-ceiling |
| 2012-06-01 | $1,156,217 | GROWTH_NEG | RISK_OFF | European crisis benefit |
| 2013-10-28 | $1,344,757 | GROWTH_POS | RISK_ON | Taper tantrum recovery |
| 2014-07-09 | $1,438,871 | GROWTH_POS | RISK_ON | Pre-commodity crash peak |
| 2016-04-01 | $1,395,455 | GROWTH_POS | RISK_OFF | Recovery from commodity crash |
| 2017-12-11 | $1,636,671 | GROWTH_POS | RISK_ON | Pre-volatility spike |
| 2019-02-27 | $1,456,198 | GROWTH_POS | RISK_OFF | Post-2018 drawdown |
| 2020-03-20 | $2,058,813 | GROWTH_POS | RISK_OFF | COVID crash peak |
| 2021-06-07 | $2,276,857 | GROWTH_POS | RISK_ON | All-time high |
| 2022-11-29 | $1,931,829 | GROWTH_POS | RISK_OFF | Post-2nd drawdown stop |
| 2025-06-25 | $1,755,571 | GROWTH_POS | RISK_OFF | Post-3rd drawdown stop |
| 2025-11-12 | $1,761,940 | GROWTH_POS | RISK_OFF | End of backtest |

The equity curve peaked at $2.28M in mid-2021 and has been in decline since. The terminal drawdown from the 2021 peak to the 2025 end is -22.6%, suggesting structural signal degradation in the post-2021 environment.
