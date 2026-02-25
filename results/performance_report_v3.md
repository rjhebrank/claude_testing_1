# Copper-Gold Macro Strategy -- V3 Backtest Performance Report

**Report Date**: 2026-02-24
**Analyst**: Quantitative Strategy Review
**Backtest Period**: 2010-06-07 to 2025-11-12 (15.9 years, 4,011 trading days)
**Initial Capital**: $1,000,000
**Final Equity**: $1,258,266
**Data Source**: `results/backtest_output_v3.txt`
**Comparison Baseline**: `results/performance_report_v2.md`

---

## 1. Executive Summary

V3 represents a meaningful step forward in infrastructure -- transaction costs are now explicitly modeled, turnover has been halved, and max drawdown has been pulled below the 20% threshold for the first time. These are real improvements to the risk and cost framework that were identified as critical gaps in the V2 report. The drawdown stop, which triggered on 61% of V2 rebalances, now fires only 3 times in the entire 15.9-year backtest. The rebalance band and volatility filter mechanics are working as designed.

However, the signal-level changes introduced in V3 -- Cu/Au detrending, the volatility filter, rebalance bands, and a real rate signal overlay -- appear to have overcorrected. Sharpe dropped from 0.34 to 0.19, CAGR from 3.62% to 1.45%, and win rate from 45.65% to 43.48%. The strategy now returns roughly half of what V2 delivered on a gross basis, and the cost-adjusted economics are marginal at best. Five of the seven performance metrics still fail their kill criteria thresholds.

Compounding this, a position implementation bug prevents GC (gold) and SI (silver) from ever trading -- despite the sizing engine computing non-zero positions for GC on 698 separate days. The per-instrument P&L confirms 0 trades and $0 P&L for both. This is not a minor issue: GC and SI are core components of the commodity basket, and their absence removes two potential alpha sources from the portfolio while leaving the strategy under-diversified. Fixing this bug and re-running is the single highest-priority action item.

---

## 2. V3 Performance Summary Table

| Metric | Value | Target / Threshold | Status |
|---|---|---|---|
| **Total Return** | 25.83% | -- | -- |
| **CAGR** | 1.45% | -- | Very Weak |
| **Annualized Volatility** | 7.51% | -- | Low |
| **Sharpe Ratio** | 0.194 | >= 0.80 | **FAIL** |
| **Sortino Ratio** | 0.184 | >= 1.00 | **FAIL** |
| **Max Drawdown** | 18.42% | < 20% | **PASS** |
| **Win Rate** | 43.48% | >= 45% | **FAIL** |
| **Profit Factor** | 1.045 | >= 1.30 | **FAIL** |
| **Annual Turnover** | 23.24x | < 15x | **FAIL** |
| **Correlation to SPX** | -0.053 | < 0.50 | **PASS** |
| **Signal Flips/Year** | 8.0 | <= 12 | **PASS** |
| **Transaction Costs** | $142,722 (14.27%) | -- | High |
| **Kill Criteria Passed** | 3 of 8 | -- | **FAIL overall** |

**Kill Criteria Summary**: Max drawdown, SPX correlation, and signal flip frequency pass. All five economic performance criteria (Sharpe, Sortino, win rate, profit factor, turnover) fail. The same 3-of-8 pass rate as V2, but with different composition: max drawdown flipped from FAIL to PASS, while win rate flipped from marginal PASS to FAIL.

---

## 3. V2 vs V3 Comparison Table

| Metric | V2 | V3 | Delta | Direction |
|---|---|---|---|---|
| **Total Return** | 76.19% | 25.83% | -50.36 pp | Degraded |
| **CAGR** | 3.62% | 1.45% | -2.17 pp | Degraded |
| **Annualized Volatility** | 10.67% | 7.51% | -3.16 pp | Improved (lower risk) |
| **Sharpe Ratio** | 0.34 | 0.194 | -0.146 | Degraded |
| **Sortino Ratio** | 0.33 | 0.184 | -0.146 | Degraded |
| **Max Drawdown** | 25.63% | 18.42% | -7.21 pp | **Improved (now passes)** |
| **Win Rate** | 45.65% | 43.48% | -2.17 pp | Degraded (now fails) |
| **Profit Factor** | 1.075 | 1.045 | -0.030 | Degraded |
| **Annual Turnover** | 46.66x | 23.24x | -23.42x | **Improved (50% reduction)** |
| **SPX Correlation** | -0.166 | -0.053 | +0.113 | Neutral (both pass) |
| **Signal Flips/Year** | 6.0 | 8.0 | +2.0 | Neutral (both pass) |
| **Transaction Costs** | Not modeled | $142,722 | -- | Now tracked |
| **Drawdown Stops Triggered** | 3 episodes | 3 instances | -- | Improved (far less frequent) |
| **Final Equity** | $1,761,940 | $1,258,266 | -$503,674 | Degraded |
| **Position Activity Days** | 88.1% | 86.6% | -1.5 pp | Comparable |
| **Kill Criteria Passed** | 3 / 8 | 3 / 8 | 0 | No net change |

**Summary**: V3 improved the risk profile (lower vol, lower drawdown, lower turnover) but at the cost of substantially degraded returns. The Sharpe ratio -- which adjusts for lower vol -- still dropped by 43%, confirming that the return reduction was disproportionate to the risk reduction. The strategy is now less volatile but also less profitable, and the net result is a worse risk-adjusted outcome.

---

## 4. Per-Instrument P&L Table

Copied verbatim from the V3 backtest output:

```
Instr     Gross P&L Trades   Win%    Avg Win   Avg Loss      Costs      Net P&L
--------------------------------------------------------------------------------
HG            38.13    101  44.6%      46.31      36.53    7504.86     -7466.74
GC             0.00      0   0.0%       0.00       0.00       0.00         0.00
CL        163070.00     77  64.9%    9748.60   12013.33   10582.50    152487.50
SI             0.00      0   0.0%       0.00       0.00       0.00         0.00
ZN         24921.88     84  52.4%    6208.45    6206.25   25395.19      -473.31
UB        170750.00     86  54.7%   17873.67   17613.49   79547.60     91202.40
6J             0.04     85  50.6%       0.01       0.00   14387.80    -14387.76
MES         4690.00     83  14.5%    7216.56    5119.30    4609.40        80.60
MNQ        37518.00     41  14.6%   10404.33    2490.80     694.60     36823.40
--------------------------------------------------------------------------------
TOTAL     400988.04    557  44.3%    7092.20    5898.62  142721.95    258266.10
```

P&L attribution cross-check: passed (diff = $0.00).

### Instrument-Level Analysis

**Winners (net positive, meaningful contribution):**

| Instrument | Net P&L | Trades | Win% | Assessment |
|---|---|---|---|---|
| **CL (Crude Oil)** | +$152,488 | 77 | 64.9% | Dominant alpha source. High win rate, favorable avg win/loss ratio. 59% of total net P&L. |
| **UB (Ultra Bond)** | +$91,202 | 86 | 54.7% | Second alpha source, but $79,548 in costs eats 47% of gross. Net contribution still meaningful. |
| **MNQ (Micro Nasdaq)** | +$36,823 | 41 | 14.6% | Low win rate but massive win/loss asymmetry ($10,404 avg win vs $2,491 avg loss). Genuine tail-capture profile. |

**Marginal (near-zero or noise):**

| Instrument | Net P&L | Trades | Win% | Assessment |
|---|---|---|---|---|
| **MES (E-mini S&P)** | +$81 | 83 | 14.5% | Effectively breakeven. Same tail-capture profile as MNQ but weaker. |
| **ZN (10Y Note)** | -$473 | 84 | 52.4% | $24,922 gross profit destroyed by $25,395 in transaction costs. Alpha exists but costs consume it entirely. |

**Losers (net negative, pure drag):**

| Instrument | Net P&L | Trades | Win% | Assessment |
|---|---|---|---|---|
| **6J (Yen)** | -$14,388 | 85 | 50.6% | $0.04 gross profit, $14,388 in costs. Pure friction drag. 85 round-trips generating zero alpha. |
| **HG (Copper)** | -$7,467 | 101 | 44.6% | $38 gross profit, $7,505 in costs. Same story as 6J -- trading activity with no signal. |

**Bugs (never traded):**

| Instrument | Net P&L | Trades | Assessment |
|---|---|---|---|
| **GC (Gold)** | $0.00 | 0 | **BUG**: Sizing engine computes GC_final != 0 on 698 days, but positions never placed. Max GC contracts held = 0.0. |
| **SI (Silver)** | $0.00 | 0 | **BUG**: Same issue. Never appears in any position log. |

### Concentration Risk

CL and UB account for $243,690 of $258,266 total net P&L -- that is 94.4% of all profits from 2 of 9 instruments. The strategy is effectively a CL + UB trade with noise from everything else. This is not diversified alpha.

---

## 5. What Improved (V2 to V3)

### Max Drawdown: 25.63% to 18.42% (now passes the 20% threshold)

This is the headline improvement. The drawdown management system has been meaningfully tightened. In V2, the drawdown stop triggered on 61% of rebalance days, functioning as a permanent position limiter rather than a true circuit breaker. In V3, `stop=1` appears only 3 times in 904 rebalances. The combination of reduced base sizing, volatility filtering, and rebalance bands has lowered the strategy's risk profile enough to bring drawdowns within target. The 18.42% max DD is the first time this metric has passed its threshold in any version of the backtest.

### Turnover: 46.66x to 23.24x (50% reduction)

Turnover was cut in half, which is a substantial improvement from the V2 level that was described as "wildly excessive." The rebalance bands are doing their job -- preventing unnecessary position adjustments when the target has not moved materially. However, 23.24x is still above the 15x target. For a macro signal that flips 8 times per year, even 23x implies roughly 3 full portfolio turns per signal flip, suggesting intra-flip rebalancing is still too frequent.

### Drawdown Stop Behavior: From Constant to Rare

In V2, `stop=1` was active on 1,030 of 1,679 rebalances (61.3%). In V3, it appears exactly 3 times. This is a dramatic improvement in drawdown stop calibration. The strategy now runs at its intended position sizing the vast majority of the time, rather than being perpetually throttled.

### Transaction Cost Transparency

V2 assumed zero transaction costs, and the V2 report estimated that the 3.62% CAGR would likely drop to 0-2% after costs. V3 now explicitly models $142,722 in total costs (14.27% of initial capital over 15.9 years), producing a net CAGR of 1.45%. This is consistent with the V2 report's estimate and confirms that realistic cost modeling was essential.

### No Liquidity Shock Crashes

Seven LIQUIDITY_SHOCK events were detected and handled cleanly via transition cancellation (2015, 2019, 2023, 2024 x3, 2025). The system correctly aborted in-progress tilt transitions during stress events rather than forcing position changes into illiquid markets.

---

## 6. What Degraded (V2 to V3)

### Sharpe Ratio: 0.34 to 0.194

The most important number got worse. A 43% decline in Sharpe means V3 delivers proportionally less return per unit of risk than V2. The t-statistic is now: t = 0.194 * sqrt(15.9) = 0.77, compared to V2's 1.36. Both are below the 1.96 threshold for statistical significance, but V3 is now so far below that the alpha signal is indistinguishable from a random walk at any conventional confidence level.

### CAGR: 3.62% to 1.45%

A 60% reduction in annualized return. At 1.45%, the strategy underperforms Treasury bills (which yielded 0-5% over the period, averaging roughly 1.5-2%). The strategy now delivers cash-equivalent returns with equity-like complexity and operational burden.

### Win Rate: 45.65% to 43.48%

Dropped below the 45% threshold, moving from marginal PASS to FAIL. The strategy now loses more often than it wins, and the profit factor of 1.045 means winning trades are only marginally larger than losing trades.

### Profit Factor: 1.075 to 1.045

Already razor-thin in V2, now even thinner. For every dollar lost, the strategy earns $1.045. This leaves zero margin for model degradation, execution slippage beyond what is modeled, or any other real-world friction.

### Likely Causes of Degradation

**1. Cu/Au Detrending May Have Removed Signal Along with Noise**

The V2 report recommended detrending the Cu/Au ratio to address its secular decline (from 0.56 to 0.30 over the period). While this addresses the RISK_OFF structural bias, detrending can also remove genuine level information. If the raw ratio level contained predictive power (e.g., "ratio below 0.4 = definitively risk-off"), detrending against a rolling window may have diluted that signal. The signal distribution shifted: RISK_ON went from 1,712 to 1,564 days and RISK_OFF from 2,070 to 1,707 days, with NEUTRAL expanding from 229 to 740 days. The tripling of NEUTRAL days means the strategy is spending far more time with no directional conviction, which mechanically reduces both return and risk.

**2. Volatility Filter Reduces Sizing During High-Vol Periods**

The `size_mult` values in the V3 logs are notably lower than V2 across comparable periods. The volatility filter scales down position size during high-volatility regimes. But volatile periods are often when the signal is most informative -- macro regime shifts produce both higher vol and stronger directional moves. By reducing size precisely when the signal may be strongest, the vol filter could be systematically cutting the strategy's best trades.

**3. Rebalance Bands Introduce Lag**

Rebalance bands prevent position adjustments unless the target deviates materially from the current position. This reduces turnover (good) but also introduces implementation lag -- the portfolio drifts from the intended allocation. For a signal that changes direction 8 times per year, even a few days of lag per flip compounds into meaningful tracking error.

**4. Real Rate Signal May Be Adding Noise**

The additional signal overlay adds another dimension of model complexity. If the real rate signal has low predictive power, blending it with the Cu/Au signal dilutes the primary signal's effectiveness. The signal flips increased from 6.0/year (V2) to 8.0/year (V3), suggesting the composite signal is more active, which is consistent with additive noise.

**5. GC/SI Bug Removes Two Instruments**

Gold and silver are absent from the portfolio. In V2, GC appeared frequently (max 1 contract) and SI traded intermittently. Their removal -- even if unintentional -- eliminates two potential diversification sources and may remove genuine alpha. GC in particular should have a strong relationship with the Cu/Au ratio signal by construction.

---

## 7. Critical Bugs & Issues

### 7.1 GC/SI Position Implementation Bug (Severity: HIGH)

**Symptom**: The sizing engine computes `GC_final` values of -2, -1, +1, or +2 on 698 separate trading days. However, GC never appears in any `Positions:` log line. The diagnostic summary confirms: "Max GC contracts ever held: 0.0". The per-instrument P&L shows 0 trades and $0 P&L for both GC and SI.

**Impact**: Two of nine tradeable instruments are completely excluded. GC is the denominator of the primary signal (Cu/Au ratio) -- its absence from the portfolio is particularly concerning. If the bug were fixed and GC contributed even a fraction of what CL does, it could meaningfully improve both returns and diversification.

**Recommended action**: Trace the code path from `GC_final` computation to position placement. The value is computed correctly but never translated into an actual position. This is likely an indexing error, a mapping bug, or a conditional that inadvertently filters GC/SI positions.

### 7.2 Turnover Still Above Target (Severity: MEDIUM)

At 23.24x, turnover has been halved from V2's 46.66x but remains 55% above the 15x target. The rebalance bands reduced the problem but did not solve it. Further widening, or switching to monthly rebalancing cadence, may be needed.

### 7.3 6J Is Pure Cost Drag (Severity: LOW)

85 round-trip trades generating $0.04 in gross profit and $14,388 in costs. The Yen futures position is being rebalanced frequently with no directional edge. Either the signal has no predictive power for 6J, or the cost of expressing the view via 6J futures is too high relative to the position size.

### 7.4 Multi-Year Drawdown Since 2022 Peak (Severity: HIGH)

The equity peak of $1,528,752 was reached in approximately Q3-Q4 2021. By the end of the backtest (November 2025), equity is $1,258,266 -- a drawdown of 17.7% from peak that has persisted for over 4 years with no sign of recovery. The strategy spent the last 100+ trading days with `size_mult` between 0.0 and 0.5, and the final position set is empty. This is not a temporary drawdown; the strategy appears to have stopped working after 2021.

### 7.5 ZN Alpha Destroyed by Costs (Severity: MEDIUM)

ZN generates $24,922 in gross profit with 52.4% win rate -- genuine alpha. But $25,395 in transaction costs turns it into a -$473 net loss. The 84 trades over 15.9 years (5.3 per year) should not generate this level of cost. Investigate whether ZN position sizes are being churned (frequently adjusted by 1-2 contracts around a stable target).

---

## 8. Recommendations

### Priority 1: Fix GC/SI Bug and Re-Run (Estimated Impact: +2-5% total return)

This is the single highest-value action. The bug is clearly identifiable (GC_final is non-zero, but no positions are placed), and fixing it adds two instruments to the portfolio. GC alone could be a meaningful alpha contributor given its direct relationship to the primary signal. Re-run the backtest with the fix before making any signal-level changes, to isolate the impact.

### Priority 2: Consider Reverting Cu/Au Detrending (Estimated Impact: Unknown)

The detrending tripled NEUTRAL days (229 to 740), meaning the strategy spends 18.4% of the time with no directional view, up from 5.7%. Run an A/B comparison: V3 with detrending vs V3 without detrending (but keeping all other V3 improvements). If the raw ratio restores the Sharpe without blowing up drawdowns, the detrending is net harmful.

### Priority 3: Remove 6J from the Tradeable Universe (Estimated Impact: +$14K / +1.1% total return)

6J contributes zero alpha and $14,388 in pure cost drag. Removing it is a guaranteed improvement. No further analysis needed.

### Priority 4: Widen Rebalance Bands or Move to Monthly Rebalancing (Estimated Impact: Reduced turnover toward 15x target)

The current bands reduced turnover from 46.7x to 23.2x. To reach 15x, either widen bands further (e.g., require 30-40% deviation from target before rebalancing) or switch from weekly to monthly rebalancing. The signal flips 8 times per year -- monthly rebalancing would still capture every flip while eliminating intra-month noise trading.

### Priority 5: Investigate Volatility Filter Calibration

The vol filter may be cutting position size during the strategy's most informative periods. Test a variant where the vol filter is inverted (increase size during high-vol regimes, within drawdown limits) or removed entirely. Compare the Sharpe with and without the filter.

### Priority 6: Evaluate Real Rate Signal Independence

Test whether the real rate signal adds value by running V3 with and without it. If removing it reduces signal flips from 8/year back toward 6/year without degrading Sharpe, the real rate signal is adding noise.

### Priority 7: Address ZN Cost Drag

ZN has genuine alpha ($24,922 gross, 52.4% win rate) but costs consume it all. Reduce ZN rebalancing frequency or add wider bands specific to ZN. The alpha is there; the implementation is destroying it.

---

## 9. Honest Assessment

### Is V3 Closer to or Further from Allocable?

**Further from allocable on an absolute basis.** The metrics that matter for allocation decisions -- Sharpe, CAGR, profit factor -- all degraded. A Sharpe of 0.19 is not a credible basis for capital allocation at any institutional threshold. The 1.45% CAGR does not compensate for the complexity, operational cost, and model risk of running a multi-instrument futures strategy.

**Closer to allocable on a structural basis.** The infrastructure improvements are real: transaction costs are modeled, drawdowns are better controlled, turnover is lower, and the drawdown stop no longer dominates the strategy's behavior. These are prerequisites for an allocable strategy, and V3 has them where V2 did not.

### What Is the Minimum Viable Path from Here?

The most capital-efficient path to an allocable backtest:

1. **Fix GC/SI bug** -- this is free alpha left on the table.
2. **Remove 6J** -- guaranteed cost savings.
3. **A/B test detrending** -- if reverting recovers Sharpe to 0.30+ while keeping DD < 20%, that is the better configuration.
4. **A/B test vol filter** -- may be suppressing the strategy's best opportunities.

If these four changes can push the Sharpe from 0.19 back above 0.35 while keeping max DD below 20%, the strategy reaches a point where further signal research (additional factors, better regime classification) has a credible foundation. If these changes do NOT move the Sharpe above 0.35, the Cu/Au ratio signal itself may have insufficient predictive power, and continued development should be deprioritized in favor of alternative signal research.

### The Hard Truth

Over 15.9 years, this strategy turned $1M into $1.26M after costs. A 0% money market account would have returned $1M. A simple 60/40 portfolio would have returned approximately $2.5-3M. The strategy's only structural advantages -- negative SPX correlation and stable signal frequency -- are not sufficient to justify the performance shortfall. The improvements from V2 to V3 were real, but they were improvements to the cost of being wrong, not improvements to being right. Until the signal quality itself improves, the infrastructure improvements are polishing a strategy that does not generate enough edge to cover its costs.

---

## Appendix A: Diagnostic Summary (from V3 backtest output)

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
  RISK_ON: 1,564  RISK_OFF: 1,707  NEUTRAL: 740

Regime Distribution:
  GROWTH+: 2,853  GROWTH-: 648  INFL: 100  LIQ: 199  NEUT: 211

Liquidity Score:
  Min: -3.251  Max: 4.586  Mean: 0.486

Signal Flips:
  Total: 128  Years: 15.9  Flips/year: 8.0

Position Activity:
  Days with positions: 3,472 / 4,011 (86.6%)
  Max GC contracts: 0.0  Max HG contracts: 1.0

Equity:
  Start: $1,000,000  End: $1,258,266  Total: 25.8%  Ann: 1.5%

Inflation Shock:
  100 days out of 4,011 (2.5%)  Threshold: 0.15
```

## Appendix B: Kill Criteria Comparison

| Criterion | Threshold | V2 | V2 Status | V3 | V3 Status | Delta |
|---|---|---|---|---|---|---|
| Sharpe Ratio | >= 0.80 | 0.34 | FAIL | 0.194 | FAIL | Worse |
| Sortino Ratio | >= 1.00 | 0.33 | FAIL | 0.184 | FAIL | Worse |
| Max Drawdown | < 20% | 25.63% | FAIL | 18.42% | **PASS** | **Improved** |
| Win Rate | >= 45% | 45.65% | PASS | 43.48% | FAIL | Worse |
| Profit Factor | >= 1.30 | 1.075 | FAIL | 1.045 | FAIL | Worse |
| Annual Turnover | < 15x | 46.66x | FAIL | 23.24x | FAIL | Improved |
| SPX Correlation | < 0.50 | -0.166 | PASS | -0.053 | PASS | Comparable |
| Signal Flips/Year | <= 12 | 6.0 | PASS | 8.0 | PASS | Comparable |

**V2 passing**: 3 of 8 (win rate, SPX corr, signal flips).
**V3 passing**: 3 of 8 (max DD, SPX corr, signal flips).

Net result: same pass count, different composition. The one economic metric that improved (max DD) was offset by an economic metric that degraded (win rate).
