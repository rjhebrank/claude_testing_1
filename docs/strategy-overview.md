# Copper-Gold Ratio Economic Regime Strategy: Portfolio Manager Review

> **Date:** 2026-02-24 | **Version:** v2.1 | **Classification:** Internal -- Proprietary

---

## 1. Executive Summary

This strategy uses the copper-to-gold futures price ratio as a macro regime indicator to express directional views across equities (MES, MNQ), commodities (CL, HG, GC, SI), fixed income (ZN, UB), and FX (6J). The core thesis is sound and well-established in macro research: copper is a cyclical industrial metal driven by global growth, while gold is a defensive store-of-value asset. Their ratio serves as a real-time barometer of risk appetite. When the ratio rises, the strategy goes risk-on (long equities, long industrial commodities, short bonds, short yen); when it falls, the strategy reverses to risk-off positioning.

The implementation is considerably more sophisticated than a naive ratio-following strategy. Five filtering layers -- a macro regime classifier (growth/inflation/liquidity shock detection), a USD/DXY filter, a commodity term structure filter, a China demand filter, and a safe-haven override -- attempt to distinguish genuine regime shifts from noise, USD-driven distortions, and liquidity events. Position sizing is volatility-aware, margin-constrained (50% max utilization), and subject to portfolio-level drawdown stops (10% warning, 15% hard stop) and per-position ATR stops. The strategy targets 2x leverage across a 9-instrument universe with weekly rebalancing and event-driven triggers.

The backtest covers approximately 15.4 years (June 2010 to November 2025) using Bloomberg-sourced data including front-month and second-month futures, macro indicators, and China-specific demand proxies. The implementation is in C++ (~1,870 lines), handles transaction costs explicitly (spread + slippage + commission), and includes built-in diagnostic reporting with performance acceptance criteria (minimum Sharpe 0.8, max drawdown 20%, win rate above 45%). While the framework is intellectually rigorous and the implementation is disciplined, several concerns around overfitting, regime classification calibration, and the lack of reported out-of-sample results require attention before any capital allocation decision.

---

## 2. Trading Thesis

### Fundamental Economic Reasoning

The copper-gold ratio exploits one of the most robust relationships in macro-commodity markets. Copper -- often called "Dr. Copper" -- is overwhelmingly an industrial input. Its price is driven by construction, infrastructure, manufacturing, and electrification demand, making it a leading indicator of global economic activity. Gold, by contrast, is primarily a monetary metal and safe-haven asset whose price rises with fear, uncertainty, falling real rates, and central bank demand.

When copper outperforms gold (rising ratio), it signals that the market is pricing in stronger global growth, rising industrial demand, and a willingness to take risk. When gold outperforms copper (falling ratio), it signals risk aversion, slowing growth, or flight to safety. This is not a new insight -- it is a well-documented macro relationship used by institutional investors and central bank watchers. The strategy's edge, if it exists, comes not from the signal itself but from the filtering and trade expression layers that attempt to avoid the known failure modes.

### Key Macro Dynamics Exploited

1. **Growth cycle rotation**: The ratio tends to trend during sustained economic expansions and contractions, creating multi-week to multi-month tradeable regimes.
2. **Risk appetite contagion**: Changes in the ratio propagate to equities, credit, and FX with a lag, allowing the ratio to serve as a leading indicator for cross-asset positioning.
3. **China demand amplification**: China consumes roughly 50% of global copper, so Chinese policy cycles (credit impulse, infrastructure spending) amplify the signal.
4. **Real rate linkage**: Gold is heavily influenced by real interest rates (nominal minus breakeven inflation), giving the ratio an embedded rates signal.

### Concern: Signal Crowding

The copper-gold ratio is widely monitored. Goldman Sachs, JPMorgan, and multiple macro hedge funds have published research on this relationship. The risk that the signal is "crowded" -- that enough capital follows it to arbitrage away the edge -- is real and should be monitored via signal decay analysis across sub-periods.

---

## 3. Universe & Instruments

### Traded Instruments

| Instrument | Symbol | Asset Class | Notional (~) | Margin (~) | Role |
|---|---|---|---|---|---|
| Micro E-mini S&P 500 | MES | Equity Index | $25,000 | $1,500 | Risk-on/off equity expression |
| Micro E-mini Nasdaq 100 | MNQ | Equity Index | $40,000 | $2,000 | Risk-on/off equity expression |
| Copper | HG | Commodities | $110,000 | $6,000 | Primary signal component + trade expression |
| Gold | GC | Commodities | $200,000 | $11,000 | Primary signal component + trade expression |
| Crude Oil | CL | Commodities | $75,000 | $7,000 | Cyclical commodity expression |
| Silver | SI | Commodities | $150,000 | $10,000 | Hybrid industrial/precious expression |
| 10-Year T-Note | ZN | Fixed Income | $110,000 | $2,500 | Duration expression |
| Ultra T-Bond | UB | Fixed Income | $130,000 | $9,000 | Long-end duration expression |
| Japanese Yen | 6J | FX | $80,000 | $4,000 | Safe-haven/carry trade expression |

### Allocation Weights by Asset Class

- Equity Index: 30% of leveraged notional (MES + MNQ)
- Commodities: 35% (CL + HG + GC + SI)
- Fixed Income: 25% (ZN + UB)
- FX: 10% (6J)

### Concern: Concentration Risk

The commodity sleeve (35% weight) is dominated by gold and copper -- the same instruments that generate the signal. This creates a feedback loop: the signal determines whether to go long or short the instruments it is derived from. The strategy is, in part, a copper-gold momentum/mean-reversion strategy dressed up as a macro regime system. This should be acknowledged explicitly.

### Data History

Full-stack history (all 5 layers) spans June 2010 to November 2025 (~15.4 years, ~4,780 trading days). MES and MNQ only launched in May 2019; the code uses SPX and NQ full-size futures as backfill for the pre-2019 period, which is acceptable but introduces minor tracking error due to different contract multipliers and liquidity profiles.

---

## 4. Signal Framework

### Layer 1: Composite Ratio Signal

The Cu/Gold ratio is computed using **notional normalization**: `(HG_price * 25,000) / (GC_price * 100)`. Three sub-signals are generated from this ratio:

1. **Rate of Change (ROC)** at 10, 20, and 60-day windows -- captures momentum at multiple frequencies.
2. **Moving Average Crossover** (10-day vs 50-day SMA) -- a trend-following filter.
3. **Z-Score Regime** (120-day lookback, +/-0.5 threshold) -- identifies statistical extremes relative to recent history.

These are combined into a composite score using equal weights (0.33/0.33/0.34). The composite is compared against a threshold of 0.0 (simple majority vote). A **minimum holding period of 5 days** is enforced before signal flips are confirmed, preventing whipsaws.

### Layer 2: Regime Classifier

The classifier categorizes the macro environment into one of five states: Growth Positive, Growth Negative, Inflation Shock, Liquidity Shock, or Neutral. Detection uses:

- **Growth proxy**: 60-day SPX momentum
- **Inflation proxy**: 20-day change in 10-year breakeven inflation
- **Liquidity proxy**: Composite of VIX percentile (60-day), high-yield spread z-score (60-day), and Fed balance sheet YoY growth (z-scored)

Regime determines trade expression (which instruments get traded and in which direction) and sizing (Liquidity Shock = flatten all, Neutral = half size, Inflation Shock = half size with commodity-only longs).

### Layer 3: USD/DXY Filter

Flags when a strong USD move (+/-3% over 20 days) may be distorting the copper-gold ratio. If the DXY move is in the same direction as the macro tilt, it confirms the signal (full size). If it contradicts, the signal is marked "Suspect" and size is halved.

### Layer 4: Term Structure Filter

Uses front-month vs. second-month futures prices to compute annualized roll yield. Commodities in backwardation (+2% annualized) get favored for longs; commodities in contango get favored for shorts. Misaligned term structure (e.g., risk-off signal but copper in backwardation) results in skipping that instrument.

**Implementation note**: The term structure filter is specified in the design document but I did not find it fully implemented in the C++ code. The code loads second-month futures data but the per-commodity term structure decision matrix (backwardation/contango gating per instrument) does not appear to be wired into the position sizing logic. This is a gap.

### Layer 5: China Demand Filter

A composite score derived from China's OECD Leading Indicator, PMI, credit growth, SHFE copper inventory, and CNY/USD. When China demand weakens significantly (score below -1.0), copper-related conviction is reduced by 30-50%. The implementation uses the CLI 3-month moving average deviation as a simplified proxy rather than the full composite formula from the design document.

### Safe-Haven Override

When VIX exceeds its 90th percentile, gold rallies > 1.5%, and equities drop > 1.5% in a single day, the system flags a crisis event and suppresses gold shorts regardless of the macro signal.

---

## 5. Risk Framework

### Portfolio-Level Controls

| Control | Threshold | Action |
|---|---|---|
| Drawdown Warning | 10% from peak | Halve all position sizes |
| Drawdown Hard Stop | 15% from peak | Flatten all positions to zero |
| Max Margin Utilization | 50% of equity | Scale all positions proportionally to fit |
| Correlation Spike | >0.7 avg pairwise (20-day) | Reduce all positions by 50% |
| Signal Stability | >12 flips/year | Warning; >20 = kill criterion |
| Leverage Target | 2.0x equity | Applied to base notional allocation |

### Position-Level Controls

| Control | Threshold | Action |
|---|---|---|
| Single Equity Instrument | 20% of equity notional | Hard cap per MES/MNQ |
| Single Commodity Instrument | 15% of equity notional | Hard cap per HG/GC/CL/SI |
| Total Directional Equity | 35% of equity | Aggregate cap on MES + MNQ |
| Total Directional Commodity | 40% of equity | Aggregate cap on HG + GC + CL + SI |
| ATR Stop | 2x ATR(20) unrealized loss | Exit individual position |
| BOJ Intervention Filter | >2% daily yen move | Reduce 6J position by 50% |

### Rebalance Triggers

Positions are updated on: (1) weekly Friday rebalance, (2) macro tilt signal flip, (3) regime classifier state change, (4) DXY filter trigger, (5) drawdown stop/warning. The code also force-rebalances if all positions are flat but the size multiplier says the strategy should be trading -- a practical safeguard against getting "stuck" flat after a drawdown reset.

### Concern: Drawdown Reset Mechanism

The code resets `peak_equity` when `dd_stop` is triggered AND all positions are zero: `if (dd_stop && all_positions_zero(positions)) { peak_equity = equity; }`. This is a form of drawdown reset that effectively gives the strategy a fresh start after every 15% drawdown. While pragmatically useful, it means the "max drawdown" metric reported by the backtest understates the true peak-to-trough experience an investor would face across the full period. Over 15 years, a strategy that hits the 15% stop multiple times could have a cumulative drawdown experience far worse than 15%.

### Concern: Transaction Cost Model

Transaction costs are applied when positions change: round-trip cost = commission + spread (tick value) + 2x slippage (entry + exit). For example, HG costs $2.50 commission + $6.25 spread + $12.50 slippage = $21.25 per round trip. This is reasonable but may underestimate costs during volatile regimes when spreads widen -- precisely when the strategy is most likely to be rebalancing. No market impact model is included, which matters for full-size futures like HG and GC.

---

## 6. Backtesting Results

### What the Code Reports

The implementation computes and reports the following metrics against the design document's acceptance criteria:

| Metric | Minimum Threshold | Target | Reported by Code? |
|---|---|---|---|
| Sharpe Ratio (net of costs) | >= 0.8 | >= 1.2 | Yes |
| Sortino Ratio | >= 1.0 | >= 1.5 | Yes |
| Max Drawdown | < 20% | < 15% | Yes |
| Win Rate (daily) | > 45% | > 50% | Yes |
| Profit Factor | > 1.3 | > 1.5 | Yes |
| Annual Turnover | < 15x | < 10x | Yes |
| Correlation to SPX | < 0.5 | < 0.3 | Yes |
| Signal Flips/Year | <= 12 | -- | Yes |

### What Is NOT Available

**No actual backtest output numbers are included in either the design document or the source code.** The code computes these metrics, but without running the binary against the data, we have no reported Sharpe, drawdown, or return figures to evaluate. The diagnostic section prints results to stdout, but no CSV or database output captures them for review.

This is a critical gap. We are being asked to evaluate a strategy framework without seeing its actual performance numbers. The code structure suggests the developer was actively debugging (multiple `[DEBUG]` print statements, inline regime change tracking, breakeven unit checks, inflation shock day counts), which implies the backtest results may not yet be satisfactory.

### Kill Criteria

The code implements one explicit kill criterion: if signal flips exceed 20 per year, development should stop. This is a sensible overfitting guard.

### Concern: Win Rate Calculation

The "win rate" is computed on daily returns, not on trade-level P&L. A daily win rate above 50% is typical for any strategy with positive drift and is not a meaningful measure of edge. Trade-level win rate (entry to exit, per position) would be far more informative but is not computed.

---

## 7. Known Limitations

### 7.1 Regime Classification Calibration

The inflation shock threshold (`inflation > 0.10 && growth < 0.5`) appears to use breakeven inflation changes in percentage-point units. A 10bp change over 20 days is extremely common -- breakeven inflation moves by this amount routinely. The diagnostic section itself warns about this: *"threshold 0.10 = 10bp change over 20d (fires easily)"*. If the INFLATION_SHOCK regime is triggering on 20-40% of days, the strategy is spending a disproportionate amount of time in a cautious, half-sized mode, potentially destroying returns. The developer acknowledged this concern in the diagnostics but the threshold has not been corrected in the code.

### 7.2 Term Structure Filter Incomplete

The design document specifies detailed per-commodity trade expression matrices based on backwardation/contango (e.g., "don't short copper in backwardation," "skip outright CL long in contango"). The C++ implementation loads second-month futures data but does not appear to wire the term structure decision logic into the position sizing block. This means one of the five core filtering layers is not operational, and the backtest does not reflect the intended strategy.

### 7.3 Regime Dependence

This is fundamentally a regime-following strategy. It performs well when regimes are persistent and transitions are clean. It will underperform -- potentially significantly -- during choppy, regime-ambiguous environments (2021-2023 is noted as "difficult" and "mixed" in the historical reference table). The strategy has no mechanism for estimating regime clarity or confidence; it always picks one of five states.

### 7.4 Data Snooping / Overfitting Risk

Multiple concerns:

- **Five filtering layers with numerous thresholds** (z-score window 120d, z-score threshold 0.5, DXY momentum threshold 3%, liquidity threshold -1.5, correlation threshold 0.7, BOJ move threshold 2%, ATR stop 2x, etc.) create a large parameter space. Even with "initial values" from domain knowledge, the risk that these thresholds were implicitly optimized by running the backtest and observing results is high.
- **Equal signal weights** (0.33/0.33/0.34) are a good default, but if other weight combinations were tested and rejected, that constitutes implicit curve-fitting.
- **No out-of-sample or walk-forward results** are presented. A 15-year in-sample backtest with this many degrees of freedom is not compelling without a hold-out period.
- **Diagnostic debugging residue**: The code contains extensive debug output for specific date ranges (Nov 2014, liquidity checks) suggesting the developer was iterating on the calibration to fix specific historical episodes. This is a textbook path to overfitting.

### 7.5 Static Variables / Reentrance Bug

The code uses `static` local variables inside the main loop (lines 1106-1107: `static Regime pending_regime`, `static int pending_regime_count`; line 877: `static Regime last_debug_regime`). While these work in a single-run context, they would cause incorrect behavior if the `run()` method were ever called more than once (e.g., in a parameter sweep or Monte Carlo). This is a code quality concern, not a strategy concern, but it limits the utility of the code for systematic validation.

### 7.6 Look-Ahead Bias Risk

The code claims "no lookahead bias" in its header comment and uses `data[0..i]` consistently. The rolling statistics use only past data through index `i`. The forward-fill functions (`ffill`, `ffill_fut_close`) return the most recent value at or before the query date. This appears correct, but the signal evaluation timing (the design document specifies 4:00 PM ET after cash close) is not enforced in the daily-bar backtest. If the "close" price includes information that would not be available at signal generation time, there is a subtle timing bias.

### 7.7 Survivorship Bias in Universe

All nine instruments traded existed throughout the backtest period (or have backfill). There is no consideration of instruments that might have been added to or removed from the universe over time (e.g., UB contract spec changes, micro contract launches). The universe is small enough that this is a minor concern, but worth noting.

### 7.8 Drawdown Peak Reset Understates True Risk

As noted in Section 5, the equity peak resets after a 15% drawdown stop + full flatten. This means the reported max drawdown will never exceed 15% in the metrics output, even if the strategy experiences multiple sequential 15% drawdowns. The true capital loss from peak could be 25-30% or more across a multi-drawdown sequence. This is misleading for risk budgeting.

---

## 8. Potential Improvements & Research Directions

### 8.1 Out-of-Sample Validation (Critical)

Split the 15.4-year dataset into in-sample (2010-2020) and out-of-sample (2020-2025). Alternatively, implement expanding-window walk-forward optimization. No allocation decision should be made without this.

### 8.2 Parameter Sensitivity Analysis

Systematically vary each threshold (+/-25%, +/-50%) and measure the impact on Sharpe and max drawdown. If performance degrades sharply with small parameter changes, the strategy is overfit. Produce a sensitivity table for the top 5 parameters (z-score window, composite threshold, DXY momentum threshold, liquidity threshold, min holding period).

### 8.3 Complete the Term Structure Filter

Wire the per-commodity backwardation/contango logic into the position sizing code as designed. This is the most impactful missing feature -- it should improve risk-adjusted returns by avoiding counter-carry trades.

### 8.4 Fix the Inflation Shock Threshold

Investigate the actual distribution of 20-day breakeven inflation changes and set the threshold at an appropriate percentile (e.g., 90th percentile of absolute changes). The current 0.10 threshold appears too sensitive.

### 8.5 Trade-Level Analytics

Implement per-trade tracking (entry date, exit date, entry price, exit price, hold duration, P&L) rather than relying solely on daily equity marks. Compute trade-level win rate, average win/loss ratio, and average hold duration. This is essential for understanding the strategy's character.

### 8.6 Regime Confidence Scoring

Instead of a hard classification into one of five regimes, produce a probability distribution or confidence score across regimes. Use the confidence score to scale positions continuously rather than in discrete steps (0x, 0.5x, 1.0x). This would reduce the impact of misclassification at regime boundaries.

### 8.7 Alternative Signal Enrichment

- **Credit spreads as a direct signal**: IG and HY credit spread changes are another growth/risk-appetite indicator that could complement or replace the copper-gold ratio.
- **Yield curve slope**: 2s10s or 3m10y spread as an additional growth proxy.
- **Commodity volatility skew**: Options-derived skew on HG and GC as a forward-looking sentiment indicator.
- **Cross-asset momentum composite**: Combine the copper-gold ratio with equity-bond and equity-commodity momentum for a more robust macro signal.

### 8.8 Dynamic Sizing via Realized Volatility

Replace the static 2x leverage target with a volatility-targeted approach (e.g., target 10% annualized portfolio volatility, dynamically adjust leverage). This would reduce exposure during high-vol regimes and increase it during low-vol regimes, likely improving Sharpe.

### 8.9 Expand the Universe

Consider adding: (a) agricultural commodities (ZW, ZS, ZC) for a broader commodity basket, (b) European equity futures for geographic diversification, (c) additional FX pairs (AUD, CAD, NOK) that have strong commodity linkages.

### 8.10 Stress Testing

Run the strategy through synthetic stress scenarios: (a) 2008-style liquidity crisis (backfill earlier data if possible), (b) rapid rate hiking cycles, (c) China hard landing, (d) prolonged stagflation. Evaluate whether the risk controls (drawdown stops, correlation spike detection) actually protect capital under extreme conditions.

---

## 9. Allocation Recommendation

### Verdict: NOT READY FOR CAPITAL ALLOCATION

This is a well-designed strategy framework with a sound economic thesis, but it is not yet at the stage where capital should be committed. The following must be addressed first:

### Must-Haves Before Allocation

1. **Actual backtest results**: Run the code, produce the performance metrics, and present Sharpe, drawdown, return stream, and trade statistics. Without numbers, there is nothing to evaluate.

2. **Out-of-sample validation**: At minimum, a 2020-2025 out-of-sample period. If the in-sample Sharpe is 1.2 but out-of-sample is 0.3, the strategy is overfit and should not be traded.

3. **Fix the inflation shock calibration**: Verify that the regime classifier spends a reasonable fraction of time in each state (Growth+: ~30-40%, Growth-: ~20-30%, Inflation: ~5-10%, Liquidity: ~2-5%, Neutral: ~20-30%). If INFLATION_SHOCK dominates, the strategy's return profile is being distorted.

4. **Complete the term structure filter implementation**: One of five core layers is not wired up. The backtest does not represent the intended strategy.

5. **Parameter sensitivity report**: Demonstrate that the strategy is robust to reasonable parameter perturbations.

### Would Like to See

- Walk-forward optimization results across rolling 5-year windows
- Trade-level analytics (not just daily equity marks)
- Comparison to a naive copper-gold momentum strategy (no filters) to quantify the value added by each layer
- Monte Carlo bootstrap of the equity curve to estimate confidence intervals on Sharpe and drawdown
- Live paper trading for 3-6 months to verify execution assumptions

### Conditional Allocation Scenario

If the above must-haves are satisfied and the strategy demonstrates:
- Out-of-sample Sharpe >= 0.7 (lower bar than in-sample to account for degradation)
- Max drawdown < 20% out-of-sample
- Signal flips < 12/year
- Parameter stability (Sharpe above 0.5 across +/-25% parameter perturbations)

Then a **small pilot allocation** of $500K-$1M (vs. the $1M default capital in the code) would be appropriate, with a 6-month live performance evaluation period before scaling. The 2x leverage target should be reduced to 1.5x for the pilot to provide additional margin of safety.

### What Could Go Wrong

- **Regime misclassification during transitions**: The strategy could be fully risk-on at the exact moment a growth shock turns into a liquidity crisis (2020 Q1 scenario). The 5-day minimum holding period means it cannot react quickly.
- **Correlated drawdowns**: During a true liquidity crisis, all nine instruments may move against the portfolio simultaneously despite the diversification. The 0.7 correlation threshold may trigger too late.
- **The signal stops working**: If the copper-gold ratio relationship breaks down (e.g., due to green energy copper demand decoupling from traditional growth, or central bank gold buying decoupling from risk sentiment), the entire strategy premise fails. This is a secular risk that no amount of filtering can address.
- **Execution slippage**: Full-size HG and GC futures have adequate liquidity, but rebalancing multiple instruments simultaneously during a regime change at Friday close could face meaningful market impact that the backtest does not capture.

---

*Reviewed by: Portfolio Management | Date: 2026-02-24*
