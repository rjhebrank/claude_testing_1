# V5 Research: Turnover Decomposition and Reduction Proposals

**Date**: 2026-02-24
**Scope**: Decompose V4's 32.1x annual turnover, identify root causes, propose testable fixes
**Target**: Reduce annual turnover from 32.1x to <25x while preserving Sharpe >= 0.40

---

## 1. Per-Instrument Trade Frequency

### Summary Table

| Instrument | Round-Trips | RT/Year | Position Changes | Changes/Year | Avg Hold (cal days) | Avg Size (contracts) | Max Size | Active % |
|---|---|---|---|---|---|---|---|---|
| **UB** | 107 | 6.7 | 178 | 11.2 | 33.2 | 4.7 | 8 | 97.8% |
| **ZN** | 108 | 6.8 | 199 | 12.5 | 30.1 | 5.0 | 9 | 97.2% |
| GC | 100 | 6.3 | 124 | 7.8 | 53.7 | 1.0 | 1 | 96.6% |
| CL | 103 | 6.5 | 191 | 12.0 | 32.5 | 2.1 | 4 | 74.2% |
| SI | 62 | 3.9 | 98 | 6.2 | 89.6 | 1.0 | 1 | 79.8% |
| MNQ | 46 | 2.9 | 86 | 5.4 | 55.2 | 5.2 | 7 | 44.9% |
| **TOTAL** | **526** | **33.1** | **876** | **55.1** | -- | -- | -- | -- |

### Key Observations

1. **UB and ZN dominate position changes**: 377 of 876 total position changes (43%) come from just two instruments. They also account for 83% of all transaction costs ($192K of $230K).

2. **The cost asymmetry is extreme**: UB costs $1,364 per round-trip vs GC at $70/RT -- a 19x difference. This is because:
   - UB tick value is $31.25 (vs GC $10.00), making spread/slippage much more expensive
   - UB trades in larger contract sizes (avg 4.7 vs GC 1.0)
   - UB commission is comparable ($4.70 RT) but spread+slippage dominate ($93.75 per RT)

3. **GC is the most efficient alpha generator**: 100 round-trips, $105K net P&L, only $7K in costs. Cost ratio: 6.2% of gross. This is because GC trades exactly 1 contract always (position limit clamps it).

4. **CL has high churn but negative alpha**: 191 position changes, 103 round-trips, -$68K net. CL should be the first removal candidate regardless of turnover analysis.

5. **Position changes exceed round-trips by 1.7x on average**: The 526 RTs correspond to 876 position changes, meaning many trades are same-direction resizes rather than clean entry/exit pairs.

---

## 2. Trade Trigger Classification (UB and ZN)

### Rebalance Event Counts (Backtest-Wide)

The backtest contains **882 rebalance events** over 15.9 years. They decompose as:

| Trigger Type | Count | % of All |
|---|---|---|
| Friday (calendar) | 788 | 89.3% |
| Tilt change (signal flip) | 96 | 10.9% |
| Filter trigger (DXY) | 13 | 1.5% |
| Drawdown stop | 1 | 0.1% |

Note: These overlap. 14 tilt changes landed on Fridays (counted in both). Non-Friday, non-tilt pure Friday rebalances that changed nothing are the majority of the 788 -- most Fridays the band check suppresses changes and positions carry forward.

### UB Position Change Triggers (175 total changes)

| Trigger | Count | % | Description |
|---|---|---|---|
| **Tilt flip** | 63 | 36.0% | Signal flips RISK_ON/RISK_OFF, UB reverses direction |
| **Friday-only resize** | 49 | 28.0% | Same direction, equity/size_mult change causes different contract count |
| **Friday-only entry** | 16 | 9.1% | From flat to positioned (after dd stop release, etc.) |
| **Friday-only exit** | 14 | 8.0% | From positioned to flat (dd stop, NEUTRAL tilt, etc.) |
| **Friday+tilt combo** | 13 | 7.4% | Signal flip that happened to land on a Friday |
| **Friday-only flip** | 10 | 5.7% | Direction change driven by Friday rebalance (not tilt -- likely regime or size_mult change) |
| Filter trigger | 5 | 2.9% | DXY filter engagement |
| Tilt resize | 3 | 1.7% | Tilt change but same direction (rare edge case) |
| Tilt entry | 1 | 0.6% | |
| Stop trigger | 1 | 0.6% | |

### ZN Position Change Triggers (196 total changes)

| Trigger | Count | % | Description |
|---|---|---|---|
| **Friday-only resize** | 63 | 32.1% | Same direction, magnitude changed by equity/sizing |
| **Tilt flip** | 62 | 31.6% | Signal reversal |
| **Friday-only entry** | 18 | 9.2% | |
| **Friday-only exit** | 17 | 8.7% | |
| **Friday+tilt combo** | 13 | 6.6% | |
| **Friday-only flip** | 10 | 5.1% | |
| Filter trigger | 6 | 3.1% | |
| Tilt resize | 4 | 2.0% | |
| Tilt entry | 2 | 1.0% | |
| Stop trigger | 1 | 0.5% | |

### Same-Direction Resize Magnitude Distribution

The resize magnitudes represent the actual contract-count delta after all position limits and margin constraints are applied:

| Delta (contracts) | UB Count | ZN Count |
|---|---|---|
| 1 | 20 | 23 |
| 2 | 7 | 8 |
| 3 | 25 | 34 |
| 4 | 5 | 8 |

**Important**: The current band check (3 contracts / 40%) happens BEFORE position limits and margin caps. A trade that passes the band check with a raw delta of 3+ can get clipped to a 1-contract change after margin utilization scaling. This means the band check is less effective than it appears -- it filters on the raw target, but the actual executed trade may be smaller, creating noise turnover.

### Root Cause Analysis

**The #1 driver of UB/ZN turnover is Friday resize churn (28-32% of changes).** This happens because:

1. **Equity fluctuations change target sizes**: The formula `notional_alloc = equity * leverage_target * weight` means a 5% equity change shifts the target by 5%. For UB at 4.7 avg contracts, a 5% equity change = 0.24 contracts. After rounding, this rarely triggers a 3-contract band. But a 10% equity swing (common over a multi-week drawdown/recovery) can produce a 3-contract delta.

2. **`size_mult` volatility**: The vol-adjusted sizing multiplier (`size_mult`) varies between 0.0 and 1.0. When it transitions (e.g., 0.53 to 0.94 over a few weeks), UB target jumps from 4 to 7 contracts, easily passing the 3-contract band.

3. **Position limits create cascading adjustments**: ZN and UB share the fixed_income asset class at 25% weight. They don't have per-instrument caps (unlike commodities at 15%). So the full 25% allocation flows through to both, creating large notional positions that are sensitive to equity changes.

**The #2 driver is tilt flips (36% for UB, 32% for ZN).** These are the genuine signal -- 6 flips/year is reasonable and necessary for the strategy. These should NOT be reduced.

### Illustrative High-Churn Sequences

**Example 1** (2011-03-03 to 2011-03-11): Tilt flip + immediate Friday resize
```
2011-02-25  UB=-4  ZN=-4  FRI         sm=1.00  dd=0.02
2011-03-03  UB=+4  ZN=+4  TILT        sm=1.00  dd=0.00   <- flip (8 contracts traded)
2011-03-04  UB= 0  ZN=+4  FRI         sm=1.00  dd=0.00   <- next day exit (4 traded)
2011-03-11  UB=+4  ZN=+5  FRI         sm=1.00  dd=0.00   <- re-entry (4 traded)
```
Three UB position changes in 8 calendar days: 16 contracts traded. The exit on 3/4 and re-entry on 3/11 are pure churn -- the tilt did not change.

**Example 2** (2012-07-13 to 2012-07-31): Size_mult oscillation + tilt whipsaw
```
2012-07-13  UB=+5  ZN=+5  FRI         sm=1.00  dd=0.02
2012-07-17  UB=-2  ZN=-2  TILT        sm=0.50  dd=0.03   <- tilt flip + size_mult halved
2012-07-20  UB=-2  ZN=-2  FRI         sm=0.50  dd=0.03
2012-07-27  UB=-5  ZN=-5  FRI         sm=1.00  dd=0.03   <- size_mult restored
2012-07-31  UB=+5  ZN=+5  TILT        sm=1.00  dd=0.04   <- tilt flips back
```
Four UB changes in 18 days: 5+7+3+10 = 25 contracts traded. The UB 5 -> -2 -> -5 -> +5 sequence incurs enormous cost. The -2 -> -5 resize on 7/27 is pure `size_mult` driven.

---

## 3. Turnover Reduction Proposals

### Cost Context

| Instrument | Total Costs | Cost/RT | Cost % of Gross |
|---|---|---|---|
| UB | $145,903 | $1,364 | 18.7% |
| ZN | $46,628 | $432 | 22.2% |
| CL | $14,716 | $143 | N/A (net negative) |
| SI | $14,185 | $229 | 102.6% |
| GC | $6,989 | $70 | 6.2% |
| MNQ | $1,210 | $26 | 3.5% |

UB+ZN = $192,531 = **83.8% of all costs**. Any turnover reduction strategy must target these two instruments.

---

### Proposal A: Instrument-Specific Rebalance Bands

**Current**: Uniform 3 contracts / 40% relative for all instruments.

**Proposed**:

| Instrument(s) | Absolute Band | Relative Band | Rationale |
|---|---|---|---|
| UB | 4 contracts | 50% | $122K notional per contract. A 1-contract change = $122K notional churn. Needs wider band. |
| ZN | 4 contracts | 50% | $113K notional per contract. Same logic as UB. |
| GC | 1 contract | 30% | Max position is 1 contract. Any band > 1 would prevent all resizes (effectively, GC already cannot resize). |
| SI | 1 contract | 30% | Max position is 1 contract. Same as GC. |
| CL | 2 contracts | 30% | Avg position 2.1 contracts. Tighter band OK since CL cost/RT is low. |
| MNQ | 5 contracts | 40% | Avg position 5.2 contracts. Micro contract so cost is minimal anyway. |

**Mechanism**: Replace the uniform band check at line 1884 of `copper_gold_strategy.cpp` with a per-instrument lookup.

**Estimated Impact**:
- UB: ~35% of the 52 same-direction resizes blocked. Saves ~$14,900 in costs.
- ZN: ~35% of the 73 same-direction resizes blocked. Saves ~$6,100 in costs.
- **Total savings: ~$21,000** (~9.1% of total costs)
- **New estimated turnover: ~29.1x** (down from 32.1x)

**Risk**: Wider bands mean the portfolio deviates further from target before correcting. For UB at 4 contracts, the portfolio could be over/under-allocated by up to 3 contracts = $366K notional before rebalancing. This is acceptable given the $1.87M equity (19.6% of equity) and the existing 50% margin utilization cap.

**Confidence**: Medium-high. The savings are mechanically deterministic -- fewer resizes means fewer costs. The risk is that suppressed resizes would have been profitable (e.g., sizing up before a big move). Given that resizes are equity-driven, not signal-driven, this risk is low.

---

### Proposal B: Biweekly Rebalancing for Bonds

**Current**: All instruments rebalance every Friday (52x/year) plus event-driven triggers.

**Proposed**: UB and ZN rebalance only on even-numbered Fridays (26x/year). All other instruments keep weekly Friday rebalancing. Event-driven triggers (tilt change, regime change, drawdown stop) still override on any day.

**Mechanism**: Add a counter or modular check to the `is_friday` condition for UB/ZN. When the skipped Friday falls on a tilt change, the tilt change still triggers -- this proposal only affects pure Friday calendar rebalances.

**Estimated Impact**:
- UB has 89 Friday-only position changes. Biweekly blocks ~50% = 44 changes. Saves ~$37,100.
- ZN has 108 Friday-only position changes. Biweekly blocks ~50% = 54 changes. Saves ~$12,800.
- **Total savings: ~$49,900** (~21.7% of total costs)
- **New estimated turnover: ~25.1x** (down from 32.1x)

**Risk**: Higher. Missing a weekly rebalance means:
1. Position sizing is stale for an extra week. If equity drops 5% between rebalances, positions are oversized relative to target. This increases drawdown risk.
2. If `size_mult` changes sharply (from 0.5 to 1.0), the portfolio doesn't resize for up to 2 weeks. This could miss a sizing-up opportunity during a favorable regime.

**Mitigation**: Add a "safety valve" -- if the raw target deviates from current position by more than 50%, force a rebalance even on the off-week. This captures extreme sizing changes while still eliminating the minor weekly adjustments.

**Confidence**: Medium. The savings are larger than Proposal A, but the risk of stale sizing is real. This is the strongest single-lever turnover reduction available.

---

### Proposal C: Minimum Holding Period (10 Trading Days)

**Current**: `min_hold_days = 5` applies to **tilt changes only** (the signal must persist for 5 days before a tilt flip is confirmed). There is no minimum holding period for positions.

**Proposed**: Once a position is entered or changed, suppress further changes to that instrument for 10 trading days (~2 weeks). Exceptions:
- Signal flip (tilt change) overrides the hold
- Drawdown stop overrides the hold
- ATR stop overrides the hold

**Mechanism**: Add a `last_change_date[sym]` tracker. In the band check section, if `current_date - last_change_date[sym] < 10`, suppress the change (carry forward existing position).

**Estimated Impact**:
- Targets the "churn pattern" where a tilt flip on day N is followed by a Friday resize on day N+1 or N+7 (as in Example 1 above).
- Conservatively blocks ~15% of UB/ZN trades. Saves ~$28,900.
- **Total savings: ~$28,900** (~12.6% of total costs)
- **New estimated turnover: ~28.0x** (down from 32.1x)

**Risk**: Low to medium. The 10-day hold prevents the "entry then immediate resize" pattern, which is the most clearly wasteful trade pattern identified in Section 2. The override exceptions ensure the strategy can still respond to genuine signal changes.

**Confidence**: Medium. The 15% estimate is conservative. The actual savings depend on how many of the short-duration positions are noise (cost-destroying) vs alpha-generating. The high-churn examples above suggest most are noise.

---

### Combined Proposal: A + B

Applying both Proposal A (wider bands) and Proposal B (biweekly bonds) together with a 20% overlap adjustment (some trades blocked by both mechanisms simultaneously):

- **Combined savings: ~$56,800**
- **New estimated turnover: ~24.1x** -- **below the 25x target**
- **Cost reduction: 24.7% of total costs**
- **New total costs: ~$172,800**
- **New net P&L: ~$924,700** (up from $867,900)
- **Estimated new Sharpe: ~0.43** (rough estimate, assuming signal quality unchanged)

---

## 4. Supplementary Finding: The `size_mult` Oscillation Problem

Beyond the three proposals above, the analysis reveals a structural issue: **the volatility-adjusted `size_mult` creates a feedback loop with equity fluctuations that amplifies turnover**.

The sequence is:
1. Drawdown increases -> `size_mult` decreases -> target positions shrink
2. Positions are cut (incurring transaction costs)
3. Recovery begins -> `size_mult` increases -> target positions grow
4. Positions are added back (incurring more transaction costs)

This "size oscillation" accounts for a significant fraction of the Friday resize churn. The vol filter is net beneficial for drawdown control (as documented in the V4 A/B tests), but its interaction with weekly rebalancing creates unnecessary turnover.

**Future investigation**: Consider applying `size_mult` changes with hysteresis (e.g., only resize when `size_mult` changes by more than 0.15 from its value at last rebalance) or using a slower-moving `size_mult` (e.g., 20-day exponential smoothing of the current instantaneous value).

---

## 5. Implementation Priority

| Priority | Proposal | Savings | Turnover | Risk | Complexity |
|---|---|---|---|---|---|
| **1** | **A: Wider bands for UB/ZN** | $21K | 29.1x | Low | Low (5 lines of code) |
| **2** | **B: Biweekly bonds** | $50K | 25.1x | Medium | Low (10 lines of code) |
| **3** | **C: Min hold period** | $29K | 28.0x | Low-Med | Medium (20 lines of code) |
| **Combo** | **A+B** | $57K | **24.1x** | Medium | Low |

**Recommendation**: Implement A first (minimal risk, simple to test), then A+B together as the V5 candidate. Run the backtest and verify turnover < 25x with Sharpe >= 0.40. If A+B achieves the target, C is unnecessary. If A+B falls short, add C.

---

## 6. Appendix: Data Sources

- Backtest output: `results/backtest_output_v4.txt` (4,005 lines, 882 rebalances, 815 position snapshots)
- Strategy source: `copper_gold_strategy.cpp` (rebalance bands at line 1869-1888, sizing at line 1609-1802)
- Performance report: `results/performance_report_v4.md` (Sections 6-7)
- Rebalance band logic: line 1882-1884, uniform `delta < 3.0 || relative_change < 0.40`
- Position sizing formula: `raw = (equity * leverage_target * asset_weight / notional) * size_mult * vol_adj`
- Contract specs: lines 286-326, UB notional $122K, ZN notional $113K, UB RT cost $98.45/contract, ZN RT cost $35.63/contract
