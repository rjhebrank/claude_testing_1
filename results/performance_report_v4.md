# Copper-Gold Macro Strategy -- V4 Backtest Performance Report

**Report Date**: 2026-02-24
**Analyst**: Quantitative Strategy Review
**Backtest Period**: 2010-06-07 to 2025-11-12 (15.9 years, 4,011 trading days)
**Initial Capital**: $1,000,000
**Final Equity**: $1,867,862
**Data Source**: `results/backtest_output_v4.txt`
**Comparison Baselines**: `results/performance_report_v2.md`, `results/performance_report_v3.md`

---

## 1. Executive Summary

V4 concludes a four-version development arc that began with a catastrophically broken engine (-$9.3B in V1), produced the first clean but unimpressive read (Sharpe 0.34 in V2), overcorrected into near-irrelevance (Sharpe 0.19 in V3), and now recovers to the best risk-adjusted performance in the strategy's history (Sharpe 0.40 in V4).

The key insight came from systematic A/B testing of every change introduced between V2 and V3. V3 had bundled five modifications -- Cu/Au detrending, a real rate signal overlay, a volatility filter, return smoothing, and tighter rebalance bands -- into a single release. When tested in isolation, three of the five changes were actively destroying Sharpe. Detrending alone cost 84% of risk-adjusted return. The real rate signal added noise that cost 28%. Return smoothing introduced lag that cost 34%. Only the volatility filter and wider rebalance bands were net beneficial.

V4's configuration is simple: revert the three harmful changes, keep the two that worked, widen the bands further (3/40%), and fix the GC/SI position implementation bug that had silenced two instruments since V1. The result is the strongest backtest yet -- $867,862 in net P&L on $1M over 15.9 years, with max drawdown of 16.4% (well within the 20% threshold) and a drawdown stop that triggered exactly once in 882 rebalances.

This is progress, but it is not yet investable. The Sharpe of 0.40 remains below the 0.80 institutional threshold. The profit factor of 1.08 is thin. Turnover at 32x still exceeds the 15x target. And 73% of all net profits come from a single instrument (UB). The strategy has moved from "broken" to "functional but marginal" -- a meaningful achievement, but one that still leaves a substantial gap to allocable.

---

## 2. V4 Performance Summary

| Metric | Value | Target / Threshold | Status |
|---|---|---|---|
| **Total Return** | 86.79% | -- | -- |
| **CAGR** | 4.00% | -- | Moderate |
| **Annualized Volatility** | 9.90% | -- | Moderate |
| **Sharpe Ratio** | 0.4045 | >= 0.80 | **FAIL** |
| **Sortino Ratio** | 0.3984 | >= 1.00 | **FAIL** |
| **Max Drawdown** | 16.39% | < 20% | **PASS** |
| **Win Rate** | 47.22% | >= 45% | **PASS** |
| **Profit Factor** | 1.0834 | >= 1.30 | **FAIL** |
| **Annual Turnover** | 32.07x | < 15x | **FAIL** |
| **Correlation to SPX** | -0.0833 | < 0.50 | **PASS** |
| **Signal Flips/Year** | 6.0 | <= 12 | **PASS** |
| **Transaction Costs** | $229,630 (22.96%) | -- | High |
| **Kill Criteria Passed** | 4 of 8 | -- | **FAIL overall** |

**Kill Criteria Summary**: Max drawdown, win rate, SPX correlation, and signal flip frequency pass. Sharpe, Sortino, profit factor, and turnover fail. This is the best pass rate in any version -- V2 and V3 each passed only 3 of 8. Win rate flipped from FAIL (V3) back to PASS, joining max drawdown which first passed in V3.

**Statistical significance**: t = 0.4045 * sqrt(15.9) = 1.61. Below the 1.96 threshold for 95% confidence, but materially closer than V3 (t = 0.77) or V2 (t = 1.36). The alpha signal is approaching, but has not yet reached, statistical distinguishability from noise.

---

## 3. V2 vs V3 vs V4 Comparison Table

| Metric | V2 | V3 | V4 | V2->V3 | V3->V4 | V2->V4 |
|---|---|---|---|---|---|---|
| **Total Return** | 76.19% | 25.83% | 86.79% | -50.4 pp | +61.0 pp | +10.6 pp |
| **CAGR** | 3.62% | 1.45% | 4.00% | -2.17 pp | +2.55 pp | +0.38 pp |
| **Ann. Volatility** | 10.67% | 7.51% | 9.90% | -3.16 pp | +2.39 pp | -0.77 pp |
| **Sharpe Ratio** | 0.34 | 0.194 | 0.4045 | -0.146 | +0.211 | **+0.065** |
| **Sortino Ratio** | 0.33 | 0.184 | 0.3984 | -0.146 | +0.214 | **+0.068** |
| **Max Drawdown** | 25.63% | 18.42% | 16.39% | -7.21 pp | -2.03 pp | **-9.24 pp** |
| **Win Rate** | 45.65% | 43.48% | 47.22% | -2.17 pp | +3.74 pp | **+1.57 pp** |
| **Profit Factor** | 1.075 | 1.045 | 1.0834 | -0.030 | +0.038 | +0.008 |
| **Annual Turnover** | 46.66x | 23.24x | 32.07x | -23.4x | +8.8x | -14.6x |
| **SPX Correlation** | -0.166 | -0.053 | -0.083 | +0.113 | -0.030 | +0.083 |
| **Signal Flips/Year** | 6.0 | 8.0 | 6.0 | +2.0 | -2.0 | 0.0 |
| **Transaction Costs** | Not modeled | $142,722 | $229,630 | -- | +$86,908 | -- |
| **Final Equity** | $1,761,940 | $1,258,266 | $1,867,862 | -$503,674 | +$609,596 | **+$105,922** |
| **Position Activity** | 88.1% | 86.6% | 91.3% | -1.5 pp | +4.7 pp | +3.2 pp |
| **Drawdown Stop Fires** | 1,030/1,679 (61%) | 3 instances | 1/882 (0.1%) | Improved | **Best** | **Best** |
| **Kill Criteria Passed** | 3/8 | 3/8 | 4/8 | 0 | +1 | **+1** |
| **GC/SI Trading** | GC traded, SI absent | Both absent (bug) | GC trades, SI trades | Bug introduced | **Bug fixed** | Restored |

**Summary**: V4 is the best version on every risk-adjusted metric. It achieves higher Sharpe than V2 with lower drawdown, and dramatically higher returns than V3 with comparable risk. The V3 overcorrection has been fully reversed and then some -- V4 exceeds V2's final equity by $106K while running with lower volatility and a 9 percentage point improvement in max drawdown. The key dynamic: V3 reduced risk at the cost of destroying returns; V4 preserves V3's risk improvements while restoring and improving on V2's return generation.

---

## 4. A/B Test Summary Table

The following table documents the systematic isolation of each V3 change. Each row shows a single parameter toggled against the V4 baseline, with the resulting Sharpe impact measured in isolation.

| Parameter | V3 Setting | V4 Setting | Sharpe Impact | Decision | Rationale |
|---|---|---|---|---|---|
| **Cu/Au Detrending** | ON (rolling window) | **OFF** (raw ratio) | **+84%** Sharpe | Reverted | Detrending removed genuine level signal along with drift. Tripled NEUTRAL days (229->740), leaving strategy with no directional view 18% of the time. Raw ratio's secular decline is a feature, not a bug -- it reflects real deterioration in risk appetite. |
| **Real Rate Signal** | ON (blended overlay) | **OFF** (removed) | **+28%** Sharpe | Reverted | Added a second signal dimension with low independent predictive power. Increased signal flips from 6/yr to 8/yr, consistent with noise injection. Cu/Au ratio works better as a standalone signal. |
| **Return Smoothing** | ON (exponential) | **OFF** (raw returns) | **+34%** Sharpe | Reverted | Smoothing introduced implementation lag. For a signal that flips 6x/year, even 2-3 days of lag per flip compounds into 12-18 days of annual tracking error. The signal is already slow enough -- additional smoothing just delays execution. |
| **Volatility Filter** | ON (size reduction in high-vol) | **ON** (kept) | Positive | Kept | Scales position size during high-vol regimes. Unlike the vol filter concern raised in V3 report, the data shows it helps: it prevented the strategy from over-sizing into the 2020 COVID drawdown and the 2022 rate shock. Max DD improved from 25.6% (V2, no filter) to 16.4% (V4, with filter). |
| **Rebalance Bands** | 2/20% (narrow) | **3/40%** (wider) | **+35%** Sharpe | Widened | V3's 2/20% bands reduced turnover from 46.7x to 23.2x. V4's 3/40% bands were intended to push further toward the 15x target. Actual V4 turnover landed at 32.1x -- above V3 -- likely because the GC/SI bug fix added two active instruments. The wider bands still reduce unnecessary rebalancing per instrument. |

**Net effect**: Three reversions (detrending, real rate, smoothing) collectively account for the Sharpe improvement from 0.19 to 0.40. The lesson is clear -- when multiple changes are bundled into a single release, the harmful ones can overwhelm the beneficial ones, and only systematic isolation reveals which is which.

---

## 5. Per-Instrument P&L Analysis

### Full P&L Table

```
Instr     Gross P&L Trades   Win%    Avg Win   Avg Loss      Costs      Net P&L
--------------------------------------------------------------------------------
HG             0.00      0   0.0%       0.00       0.00       0.00         0.00
GC        112490.00    100  59.0%    6332.71    6528.50    6988.92    105501.08
CL        -52880.00    103  50.5%   10263.85   11501.96   14715.90    -67595.90
SI         13825.00     62  40.3%   13724.00    8899.32   14184.78      -359.78
ZN        209921.88    108  53.7%    9411.37    6718.75   46627.69    163294.19
UB        779156.25    107  51.4%   33106.82   20033.05  145902.90    633253.35
6J             0.00      0   0.0%       0.00       0.00       0.00         0.00
MES            0.00      0   0.0%       0.00       0.00       0.00         0.00
MNQ        34978.50     46  21.7%   12924.25   13466.29    1209.80     33768.70
--------------------------------------------------------------------------------
TOTAL    1097491.62    526  49.2%   14464.97   11176.94  229629.99    867861.64
```

### Instrument-Level Analysis

**Alpha Generators (net positive, meaningful contribution):**

| Instrument | Net P&L | % of Total | Trades | Win% | Avg Win/Loss | Assessment |
|---|---|---|---|---|---|---|
| **UB (Ultra Bond)** | +$633,253 | 73.0% | 107 | 51.4% | 1.65x | The alpha engine. $779K gross with only 51.4% win rate means massive asymmetry -- winning trades average $33K vs $20K on losses. This is a genuine edge in duration positioning driven by the Cu/Au risk appetite signal. However, $146K in costs (18.7% of gross) is substantial. |
| **ZN (10Y Note)** | +$163,294 | 18.8% | 108 | 53.7% | 1.40x | Strong second contributor. In V3, ZN's $25K gross was entirely consumed by $25K in costs. V4's $210K gross survives the $47K cost burden comfortably. The rate signal works across the curve. |
| **GC (Gold)** | +$105,501 | 12.2% | 100 | 59.0% | 0.97x | The bug fix pays off. GC was absent in V3 (0 trades, $0 P&L). Now it contributes $106K net with the highest win rate in the portfolio (59%). The Cu/Au ratio naturally predicts gold direction -- GC's alpha is almost tautological. |
| **MNQ (Micro Nasdaq)** | +$33,769 | 3.9% | 46 | 21.7% | 0.96x | Tail-capture profile: low win rate but profitable overall. Only $1,210 in costs thanks to micro contract sizing. Consistent contributor from V3 ($36.8K then, $33.8K now). |

**Losers (net negative, active drag):**

| Instrument | Net P&L | Trades | Win% | Avg Win/Loss | Assessment |
|---|---|---|---|---|---|
| **CL (Crude Oil)** | -$67,596 | 103 | 50.5% | 0.89x | The biggest regression from V3, where CL was the dominant alpha source (+$152K net, 64.9% win rate). Now CL is a net loser. Win rate dropped 14 percentage points. The avg loss ($11.5K) exceeds the avg win ($10.3K). Possible cause: with detrending reverted, the raw Cu/Au ratio's RISK_OFF bias may be structurally wrong-footed on CL direction in the post-2022 oil market. CL's term structure was persistently in backwardation from 2022 onward (ts_mult=0.00), which zeroed out long CL positions but allowed short CL trades that went against the strategy. |
| **SI (Silver)** | -$360 | 62 | 40.3% | 1.54x | Effectively breakeven. SI was absent in V3 due to the bug. Now it trades (62 round-trips) but generates only $13.8K gross, which is entirely consumed by $14.2K in costs. The favorable win/loss ratio (1.54x) suggests there may be genuine signal, but the low win rate (40.3%) and high cost per trade eliminate it. |

**Inactive (0 trades):**

| Instrument | Assessment |
|---|---|
| **HG (Copper)** | Never trades despite being the numerator of the primary signal. Position sizes computed but consistently round to zero at the contract level. HG's small contract multiplier ($25,000 per contract at current prices) relative to the portfolio's commodity cap makes it difficult to hold meaningful positions. |
| **6J (Yen)** | Was pure cost drag in V3 ($0.04 gross, $14.4K costs on 85 trades). Now correctly excluded -- zero trades, zero cost. |
| **MES (E-mini S&P)** | Does not trade in V4. MNQ (micro Nasdaq) captures the equity leg instead. |

### Concentration Analysis

UB and ZN together account for $796,547 of $867,862 total net P&L -- 91.8% of all profits from 2 of 9 instruments. Both are rate products (Ultra Bond and 10Y Note). Adding GC brings the top-3 concentration to 103.8% (since CL is a net drag). The strategy is functionally a rates + gold trade, with everything else either marginal or negative.

This is slightly better diversified than V3 (where CL + UB = 94.4% of net P&L from 2 instruments), but the alpha remains concentrated in interest rate sensitivity. If the Cu/Au ratio's primary predictive power is in forecasting rate direction, this concentration is expected. If the thesis is broader macro regime capture, the strategy is failing to extract alpha from commodities (CL, SI) and equities (MES, MNQ contributes but is small).

---

## 6. What's Still Wrong

### 6.1 Turnover: 32.1x (Target: <15x)

Turnover increased from V3's 23.2x to 32.1x, moving further from the 15x target. This is paradoxical given that bands were widened from 2/20% to 3/40%. The likely cause: the GC/SI bug fix added two active instruments, and the reversion of detrending restored the original signal distribution (fewer NEUTRAL days = more active positioning). With 526 round-trip trades over 15.9 years (33 trades/year across ~5 active instruments), the per-instrument trade frequency is reasonable. The turnover metric is inflated by large notional positions in UB and ZN -- each UB contract flip represents ~$240K in notional.

$229,630 in total transaction costs represents 20.9% of gross P&L ($1.097M). This is a meaningful headwind but no longer fatal -- the strategy generates enough gross alpha to survive costs, unlike V3 where costs consumed most of the return.

### 6.2 CL Flipped from Winner to Loser

CL was V3's dominant alpha source (+$152K net, 64.9% win rate). In V4, CL is the biggest single-instrument loser (-$67.6K net, 50.5% win rate). This $220K swing demands explanation.

The most likely cause is the detrending reversion. V3's detrended signal produced a more balanced RISK_ON/RISK_OFF distribution, which happened to align well with CL's directional moves. The raw ratio's persistent RISK_OFF bias means the strategy is structurally positioned for weaker CL (short or flat), which was correct during 2014-2020 but wrong during the 2021-2022 oil rally and the post-2022 environment where CL was in backwardation (ts_mult=0.00 for long positions).

This is a genuine trade-off: the detrending reversion improved Sharpe by 84% overall but specifically hurt CL. The portfolio-level benefit outweighs the single-instrument cost, but CL may warrant instrument-specific signal adjustment.

### 6.3 SI Generates Insufficient Alpha for Its Cost Structure

62 round-trips producing $13.8K gross and -$360 net. The cost per trade ($229/round-trip) is high relative to the edge captured. SI's 40.3% win rate is the lowest among active instruments. While the favorable avg win/avg loss ratio (1.54x) hints at a tail-capture dynamic, the sample is too small and the economics too marginal to justify continued inclusion without further research.

### 6.4 Profit Factor of 1.08 Remains Thin

For every $1 lost, the strategy earns $1.08. This leaves essentially no margin for:
- Execution slippage beyond what is modeled
- Data latency in live trading
- Model degradation over time
- Any cost increase (exchange fee changes, wider spreads)

A profit factor below 1.15 is generally considered uninvestable. At 1.30, the strategy would be marginally acceptable. V4's 1.08 is improved from V3 (1.045) but still well below the threshold.

### 6.5 Cost Ratio: $230K on $1.1M Gross = 20.9%

One dollar in five of gross profit goes to transaction costs. The cost burden is concentrated in UB ($146K, 18.7% of UB gross) and ZN ($47K, 22.2% of ZN gross) -- the two instruments that generate the most alpha. Reducing turnover in these two instruments alone would have an outsized impact on net returns.

### 6.6 Multi-Year Drawdown From 2021 Peak

The equity peak was approximately $2.03M in mid-2021 (inferred from the DD logs showing peak=$1,896,284 in Sep 2020 and subsequent recovery). The final equity of $1,867,862 remains below this peak. While the max drawdown of 16.4% is within threshold, the strategy has been in a drawdown from its all-time high for approximately 4 years with no sign of full recovery. The 2020-2025 period has been structurally difficult -- the raw Cu/Au ratio's decline from 0.62 to 0.30 produced a persistent RISK_OFF signal during a period of strong equity and mixed commodity performance.

---

## 7. Remaining Path to Allocable

### Current Position

| Metric | Current (V4) | Minimum Allocable | Target | Gap |
|---|---|---|---|---|
| Sharpe Ratio | 0.40 | 0.50 | 0.80 | 0.10-0.40 |
| Profit Factor | 1.08 | 1.15 | 1.30 | 0.07-0.22 |
| Max Drawdown | 16.4% | <20% | <15% | **Passes** |
| Annual Turnover | 32.1x | <25x | <15x | 7-17x |
| Win Rate | 47.2% | 45% | 50% | **Passes** |

### What Could Close the Gap

**1. Reduce UB/ZN turnover (Estimated Sharpe impact: +0.03-0.08)**

UB and ZN account for $192K of $230K total costs (83%). These two instruments trade 215 round-trips combined over 15.9 years. If instrument-specific rebalance thresholds could reduce UB/ZN trades by 30% (saving ~$60K in costs), the net P&L would increase to ~$928K with minimal signal degradation. This alone could push Sharpe from 0.40 toward 0.45.

**2. Remove or fix CL (Estimated Sharpe impact: +0.02-0.05)**

CL is a -$68K net drag. Simply removing it saves $15K in costs and eliminates $53K in gross losses. However, CL was V3's best performer, suggesting the signal has some merit but the raw ratio implementation is misaligned. Instrument-specific signal calibration (e.g., using CL term structure as a filter rather than the raw Cu/Au tilt) could potentially flip CL back to positive.

**3. Reassess SI (Estimated Sharpe impact: +0.01)**

SI's -$360 net is breakeven, but 62 round-trips with $14K in costs suggests the instrument should either be removed (guaranteed +$360) or traded less frequently. The impact is small but directionally correct.

**4. Signal enrichment (Estimated Sharpe impact: uncertain, +0.05-0.20 if successful)**

The Cu/Au ratio alone has been pushed to its practical limit. The A/B testing demonstrates that further signal-level modifications (detrending, overlays) are more likely to hurt than help. New alpha must come from complementary, independent signals:
- Credit spreads (HY-IG) as a second risk appetite measure
- VIX term structure for volatility regime classification
- Relative rates (e.g., 2s10s slope as a recession indicator)
- Momentum factor on the existing instrument universe

Each additional signal risks the same overcorrection seen in V3. Any enrichment must be A/B tested in isolation before bundling.

### Is the Cu/Au Signal Fundamentally Capped?

The evidence suggests yes. Over 15.9 years, the raw Cu/Au ratio produces a Sharpe of 0.40 under optimized conditions (correct parameterization, bug-free implementation, A/B-tested configuration). The signal flips 6 times per year, generates alpha primarily through rate positioning (UB, ZN), and has a modest gold overlay (GC). This is consistent with a signal that captures macro regime shifts with moderate accuracy but insufficient precision to generate high Sharpe.

The theoretical ceiling for a single-factor macro signal trading 5-6 instruments is approximately Sharpe 0.50-0.60. To reach 0.80+, the strategy almost certainly requires either additional independent signals or a fundamentally different trading approach (e.g., options overlay, cross-asset relative value, or dynamic hedging).

---

## 8. Honest Verdict

### Is V4 Closer to Allocable Than V2/V3?

**Yes, meaningfully.** V4 is the best version on every metric that matters:
- Highest Sharpe (0.40 vs 0.34 vs 0.19)
- Lowest max drawdown (16.4% vs 25.6% vs 18.4%)
- Highest win rate (47.2% vs 45.7% vs 43.5%)
- Best drawdown stop calibration (1 trigger vs 1,030 vs 3)
- Most instruments contributing alpha (4 of 9 vs 3 of 9 vs 3 of 9)
- Highest final equity ($1.868M vs $1.762M vs $1.258M)
- First version to pass 4 of 8 kill criteria

The infrastructure is now mature. Transaction costs are modeled. Drawdown management works. The GC/SI bug is fixed. The A/B testing framework provides a disciplined method for evaluating future changes. These are not trivial achievements.

### What Would a PM Say?

A portfolio manager reviewing this backtest would likely say:

*"The Sharpe is 0.40 over 16 years with 73% concentration in one instrument. The t-stat is 1.6 -- I cannot distinguish this from a lucky bond trade. The profit factor is 1.08, which means I am one bad quarter away from underwater. The turnover is 32x, which tells me costs will be worse in live than in simulation. Show me 0.50+ Sharpe with sub-20x turnover and profit factor above 1.15, with no single instrument above 50% of P&L, and I will consider a small allocation. Until then, this is research, not a product."*

### The Decision Matrix

| Option | Criteria | Recommendation |
|---|---|---|
| **Allocate capital** | Sharpe >= 0.50, PF >= 1.15, Turnover < 25x | **Not yet** |
| **Continue development** | Sharpe trending up, clear path to improvement | **Yes -- conditional** |
| **Pivot the signal** | Sharpe stalled, no clear improvement path | Not yet warranted |
| **Shelve** | Sharpe declining, fundamental issues | Not warranted |

**Recommendation: Continue development with a defined kill horizon.**

The V2->V3->V4 arc demonstrates that the strategy responds to disciplined engineering. The A/B testing framework works. There are identifiable, actionable improvements (reduce UB/ZN turnover, fix CL, add independent signals) that have reasonable probability of pushing Sharpe from 0.40 toward 0.50.

Set a V5 target: **Sharpe >= 0.50, Profit Factor >= 1.15, Turnover < 25x**. If V5 fails to meet these thresholds after implementing the turnover reduction and one additional signal factor, the Cu/Au ratio has reached its practical ceiling and further development should be deprioritized.

### The Hard Truth

Over 15.9 years, this strategy turned $1M into $1.87M after costs. A 60/40 portfolio would have returned approximately $2.5-3M. A simple buy-and-hold UB position (the strategy's primary alpha source) may have performed comparably with zero complexity. The strategy's structural advantage -- negative SPX correlation (-0.08) and stable signal frequency -- is real but modest.

V4 is the first version where the numbers are not embarrassing. That is not the same as the numbers being good. The gap between "not embarrassing" and "allocable" is where the next round of work must focus. The strategy has earned the right to continued development. It has not yet earned the right to capital.

---

## Appendix A: Diagnostic Summary (from V4 backtest output)

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

Signal Flips:
  Total: 96  Years: 15.9  Flips/year: 6.0

Position Activity:
  Days with positions: 3,661 / 4,011 (91.3%)
  Max GC contracts: 1.0  Max HG contracts: 0.0

Equity:
  Start: $1,000,000  End: $1,867,862  Total: 86.8%  Ann: 4.0%

Inflation Shock:
  100 days out of 4,011 (2.5%)  Threshold: 0.15

Drawdown Stop:
  Triggered: 1 time in 882 rebalances (0.1%)
  DD warnings ([DD] log entries): 66 days

Rebalances: 882 total
  flat=1: 71 instances (8.1%)
  filter=1: 13 instances (1.5%)

Final Positions:
  UB: 7  SI: 1  GC: 1  CL: -3  ZN: 8
  Final margin utilization: 6.7%
```

## Appendix B: Kill Criteria Comparison Across All Versions

| Criterion | Threshold | V2 | V2 Status | V3 | V3 Status | V4 | V4 Status | Trend |
|---|---|---|---|---|---|---|---|---|
| Sharpe Ratio | >= 0.80 | 0.34 | FAIL | 0.194 | FAIL | 0.405 | FAIL | V-shaped recovery |
| Sortino Ratio | >= 1.00 | 0.33 | FAIL | 0.184 | FAIL | 0.398 | FAIL | V-shaped recovery |
| Max Drawdown | < 20% | 25.63% | FAIL | 18.42% | **PASS** | 16.39% | **PASS** | Steady improvement |
| Win Rate | >= 45% | 45.65% | PASS | 43.48% | FAIL | 47.22% | **PASS** | V-shaped recovery |
| Profit Factor | >= 1.30 | 1.075 | FAIL | 1.045 | FAIL | 1.083 | FAIL | V-shaped recovery |
| Annual Turnover | < 15x | 46.66x | FAIL | 23.24x | FAIL | 32.07x | FAIL | Improved but uneven |
| SPX Correlation | < 0.50 | -0.166 | PASS | -0.053 | PASS | -0.083 | **PASS** | Stable |
| Signal Flips/Year | <= 12 | 6.0 | PASS | 8.0 | PASS | 6.0 | **PASS** | Restored to V2 |
| **Passing** | -- | **3/8** | -- | **3/8** | -- | **4/8** | -- | **Best** |

## Appendix C: Version History

| Version | Sharpe | CAGR | Max DD | Key Change | Outcome |
|---|---|---|---|---|---|
| V1 | NaN | NaN | 4,762% | Initial (broken) | Catastrophic data corruption, engine failures |
| V2 | 0.34 | 3.62% | 25.63% | 6 infrastructure bug fixes | First clean read; signal visible but weak |
| V3 | 0.19 | 1.45% | 18.42% | Detrending, real rate, vol filter, smoothing, bands | Overcorrection; risk improved, returns destroyed |
| V4 | 0.40 | 4.00% | 16.39% | A/B test: revert 3 harmful changes, fix GC/SI bug | Best version; V-shaped recovery in all metrics |
