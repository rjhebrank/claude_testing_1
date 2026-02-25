# Per-Instrument P&L Decomposition and Universe Optimization

**Date**: 2026-02-24
**Analyst**: Quantitative Strategy Review
**Strategy**: Copper-Gold Macro Regime v2.0
**Backtest Period**: 2010-06-07 to 2025-11-12 (15.9 years)
**Gross CAGR**: 3.62% | **Sharpe**: 0.34 | **Total Return**: 76.2%

---

## 0. Critical Finding: Per-Instrument P&L Is Not Tracked

**This is the single most important finding of this analysis.**

The backtest engine (`copper_gold_strategy.cpp`, lines 1222-1231) calculates daily P&L as a single aggregate number:

```cpp
double daily_pnl = 0.0;
for (const auto& [sym, qty] : positions) {
    if (qty == 0.0) continue;
    double pv = POINT_VALUE.at(sym);
    double price_change = (*px)[i] - (*px)[i-1];
    daily_pnl += qty * price_change * pv;
}
equity += daily_pnl;
```

There is no `instrument_pnl` map, no per-symbol accumulator, no attribution log. The backtest output (`backtest_output_v2.txt`, 7,095 lines) contains:
- Position snapshots (1,399 `Positions:` lines with instrument:quantity pairs)
- Aggregate equity marks (`Post-equity:` lines triggered by |daily_pnl| > $10,000)
- Sizing diagnostics (`[SIZING]` lines with GC_raw/GC_final only)

But **zero per-instrument P&L data**. The performance report (`performance_report_v2.md`) explicitly acknowledges this at Section 7: "The backtest does not log per-instrument P&L, so exact attribution is not available."

**Implication**: Everything below is estimated from position frequency, direction, contract sizes, and known price histories. These are directionally informative but not precise P&L attribution.

---

## 1. Instrument Position Summary

Extracted from 1,399 position log lines in the backtest output. "Appearances" means the number of position snapshots where that instrument appeared with a non-zero position.

| Instrument | Long Appearances | Short Appearances | Total | Direction Bias | Typical Size | Notional per Contract |
|---|---|---|---|---|---|---|
| **6J** (Yen) | 769 | 574 | 1,343 | 57% long | 2-5 contracts | ~$80,000 |
| **UB** (Ultra Bond) | 772 | 584 | 1,356 | 57% long | 3-7 contracts | ~$130,000 |
| **SI** (Silver) | 1,148 | 0 | 1,148 | 100% long | 1 contract | ~$150,000 |
| **GC** (Gold) | 632 | 439 | 1,071 | 59% long | 1 contract | ~$200,000 |
| **CL** (Crude) | 567 | 388 | 955 | 59% long | 1-3 contracts | ~$75,000 |
| **ZN** (10Y Note) | 585 | 251 | 836 | 70% long | 4-9 contracts | ~$110,000 |
| **HG** (Copper) | 63 | 111 | 174 | 64% short | 1-2 contracts | ~$110,000 |
| **MNQ** (Micro NQ) | 9 | 62 | 71 | 87% short | 4-7 contracts | ~$40,000 |
| **MES** (Micro ES) | 5 | 22 | 27 | 81% short | 6-12 contracts | ~$25,000 |

### Key Observations

1. **Silver is ALWAYS long** (1,148 appearances, zero short). Across all 6 trade expression tables, SI is long in RISK_ON, long in RISK_OFF, and long in both inflation variants. This is by design -- the strategy treats silver as a hybrid commodity/precious-metal that benefits in both regimes. This is the only instrument that never flips direction.

2. **6J, UB, ZN are the workhorses** with the highest appearance counts and multi-contract positions. These dominate the portfolio's notional exposure.

3. **MES/MNQ are extremely sparse** -- 27 and 71 appearances respectively out of 1,399 position snapshots. They show up in less than 5% of active position sets.

4. **HG (Copper) is infrequent** (174 appearances) despite being the namesake of the strategy. The combination of L4 term structure filtering (ts_mult frequently 0.00-0.75 for HG) and the commodity notional cap severely limits copper's actual portfolio participation.

---

## 2. Per-Instrument Analysis

### 2.1 6J -- Japanese Yen Futures

**Position profile**: 1,343 appearances (96% of all position snapshots). 2-5 contracts. 57% long.
**Asset class weight**: 10% (FX). No per-instrument notional cap. No term structure filter.
**Point value**: $12.50/pip. Contract notional ~$80,000.

**Regime mapping**:
- RISK_OFF (default): Long 6J (yen strengthens in risk aversion)
- RISK_ON (default): Short 6J (yen weakens in growth)
- RISK_OFF + INFLATION: Flat (yen ambiguous in stagflation)
- RISK_ON + INFLATION: Short 6J

**Assessment**: 6J is the strategy's most consistently traded instrument. Over 2010-2025, 6J (USDJPY inverse) went from 0.0109 to 0.0065 -- a ~40% decline in yen value. The strategy was long 6J 57% of the time (corresponding to the 52% RISK_OFF regime), which means it was holding a structurally losing position (long a depreciating asset) the majority of the time. However, the BOJ intervention filter (halves position on >2% daily JPY moves) provides some tail protection.

**Estimated P&L direction**: Likely negative contributor. The yen weakened persistently from 2012-2024. With 57% long bias at 2-5 contracts * $12.50/pip, the cumulative yen depreciation from ~0.0109 to ~0.0065 over the long-biased periods would have generated substantial losses. The short periods during RISK_ON may have partially offset this, but the timing would need to be precise.

**Diversification value**: Moderate. JPY has genuine crisis-alpha properties (strengthens during equity selloffs), providing portfolio-level hedging during drawdowns. But the secular yen weakness over this period makes it an expensive hedge.

---

### 2.2 UB -- Ultra Bond Futures

**Position profile**: 1,356 appearances (97% of all snapshots). 3-7 contracts. 57% long.
**Asset class weight**: 25% (Fixed Income, shared with ZN). No per-instrument notional cap.
**Point value**: $1,000/point. Contract notional ~$130,000.
**Transaction costs**: $2.50 RT (spread/slippage = $0 -- unrealistic, see note below).

**Regime mapping**:
- RISK_OFF (default): Long UB (flight to quality)
- RISK_ON (default): Short UB (rates rise in growth)
- RISK_OFF + INFLATION: Short UB (rates rise despite risk-off)
- RISK_ON + INFLATION: Short UB

**Assessment**: UB is the portfolio's largest notional exposure (7 contracts * $130K = $910K at peak). Over 2010-2025, UB went from ~132 to ~121.5 -- a 7.9% price decline. However, the path was highly non-linear: UB peaked around ~180 in 2020 during COVID zero-rate policy, then crashed to ~105 range during the 2022-2023 rate hiking cycle.

**CRITICAL COST ISSUE**: UB transaction costs are modeled at $2.50 round-trip (zero spread, zero slippage). This is unrealistic. Ultra Bond futures have meaningful bid-ask spreads, especially for 7-contract orders. Real RT costs are likely $15-30 per contract. With 46.7x annual turnover and 7 contracts, this understatement could represent $5,000-15,000/year in hidden costs.

**Estimated P&L direction**: Mixed. The strategy was long UB 57% of the time. During 2010-2020 (rates declining), long UB positions likely generated positive returns. During 2020-2025 (rates rising), the strategy would have alternated between long and short, with the long-biased periods taking losses. The peak equity of $2.28M in mid-2021 correlates with UB's high-water mark, suggesting UB was a major contributor to the 2020-2021 rally.

**Diversification value**: High. Treasuries are the canonical portfolio diversifier. But the strategy's 57% long bias during a period of rising rates (2022-2025) turned this diversifier into a drag.

---

### 2.3 ZN -- 10-Year Treasury Note

**Position profile**: 836 appearances. 4-9 contracts. 70% long.
**Asset class weight**: 25% (Fixed Income, shared with UB). No per-instrument notional cap.
**Point value**: $1,000/point. Contract notional ~$110,000.

**Regime mapping**: Identical to UB.

**Assessment**: ZN mirrors UB but with lower duration (10Y vs 30Y+), meaning less sensitivity to rate moves. The 70% long bias is even more pronounced than UB's 57%, suggesting ZN appears more consistently in RISK_OFF positions. ZN went from 121 to 113 over the full period -- an ~6.6% decline, but with significant path dependence (peaked around 140 in 2020).

**Estimated P&L direction**: Similar profile to UB but with lower magnitude per contract due to lower duration. The strong long bias during the rising-rate environment (2022-2025) would have been a headwind.

**Diversification value**: Partially redundant with UB. Both are long-duration treasuries that move in the same direction. Running both at full weight doubles the fixed income exposure without proportional diversification benefit.

---

### 2.4 GC -- Gold

**Position profile**: 1,071 appearances. 1 contract max. 59% long.
**Asset class weight**: 35% (Commodities, shared with CL, HG, SI). 15% per-instrument notional cap.
**Point value**: $100/point. Contract notional ~$200,000.

**Regime mapping**:
- RISK_OFF (default): Long GC (safe haven)
- RISK_ON (default): Short GC (risk-on reduces gold bid)
- Both INFLATION variants: Long GC (inflation hedge)
- Safe-haven gold override prevents shorting when VIX > 90th pctile + gold up >1.5% + SPX down >1.5%

**Assessment**: GC went from $1,241 to $4,196 over the backtest period -- a 238% gain. The strategy was long GC 59% of the time. Even at just 1 contract, the $295,400 price appreciation * $100 point value = ~$295,400 in potential long-side P&L. But the 41% of time spent short GC during gold's massive bull run would have generated significant losses.

**Estimated P&L direction**: Likely net positive but far less than buy-and-hold. A single long GC contract held for the full period would have gained ~$295K. The strategy's 59/41 long/short split with intermittent flat periods means it captured perhaps 20-40% of that move at best. The short periods during RISK_ON coincided with some of gold's strongest rallies (2019-2020 from $1,300 to $2,000), which would have been painful.

**Diversification value**: High. Gold is the portfolio's only pure safe-haven commodity and provides genuine decorrelation.

---

### 2.5 SI -- Silver

**Position profile**: 1,148 appearances. 1 contract. 100% long (never short).
**Asset class weight**: 35% (Commodities). 15% per-instrument notional cap.
**Point value**: $5,000/point. Contract notional ~$150,000.
**Transaction cost**: $77.50 RT (most expensive instrument).

**Regime mapping**: Long in ALL regime/tilt combinations. Vol-adjusted using GC/SI ATR ratio.

**Assessment**: Silver went from $18.14 to $53.17 -- a 193% gain. At 1 contract with $5,000/point, the full move = ~$175,150. Since SI is always long, the strategy captured essentially the full buy-and-hold move minus flat periods (SI appeared in 82% of position snapshots).

**Estimated P&L direction**: Almost certainly a positive contributor. The always-long positioning means silver's 193% rally directly contributed to portfolio equity. Rough estimate: 82% time-in-market * $175K total move = ~$143K contribution. This may be one of the strategy's largest single-instrument P&L contributors.

**CONCERN**: If SI contributes meaningfully to total returns while requiring zero signal (it is always long regardless of regime), this raises a fundamental question: is the Cu/Au signal adding value, or is the strategy just a leveraged long silver position with noisy overlays?

**Diversification value**: Low as a diversifier (it never goes short, so it adds directional exposure, not hedging). High as a return generator during this specific backtest period.

---

### 2.6 CL -- Crude Oil

**Position profile**: 955 appearances. 1-3 contracts. 59% long.
**Asset class weight**: 35% (Commodities). 15% per-instrument notional cap.
**Point value**: $1,000/point. Contract notional ~$75,000.

**Regime mapping**:
- RISK_OFF (default): Short CL
- RISK_ON (default): Long CL
- Both INFLATION variants: see note below
- **Heavily filtered by L4 term structure**: CL ts_mult was 0.00 (fully zeroed) during multiple periods: 2014 (backwardation), 2018-03 to 2018-09, 2022-07 to 2023-01, 2024-07 to 2025-end.

**Assessment**: CL went from $70.99 to $58.20 -- a 18% decline. But the path was extreme: it crashed to negative prices in April 2020, rallied to $120+ in 2022, then declined. The L4 term structure filter aggressively zeroed CL in backwardation periods (2014, 2018, 2022 onward), which coincidentally removed CL during some of its strongest price moves.

From the L4-TS logs:
- 2014-04-23: CL=BACKWARDATION, ts_mult=0.00 (removed during oil crash)
- 2018-03-09: CL=BACKWARDATION, ts_mult=0.00 (removed during rally)
- 2022-07-25: CL=BACKWARDATION, ts_mult=0.00 (removed during $100+ oil)
- 2024-07-01: CL=BACKWARDATION, ts_mult=0.00 (removed through end of backtest)

**Estimated P&L direction**: Uncertain. The heavy filtering means CL was absent from the portfolio during the most volatile oil periods. When present (59% long bias), the ~18% decline over the full period would suggest slight negative contribution on the long side, partially offset by short-side gains during selloffs.

**Diversification value**: Moderate in theory (oil is uncorrelated with bonds/yen), but the L4 filter removes CL precisely when it would provide the most diversification benefit (during high-volatility backwardation periods).

---

### 2.7 HG -- Copper

**Position profile**: 174 appearances (12% of snapshots). 1-2 contracts. 64% short.
**Asset class weight**: 35% (Commodities). 15% per-instrument notional cap.
**Point value**: $250/cent. Contract notional ~$110,000.

**Regime mapping**:
- RISK_OFF (default): Short HG
- RISK_ON (default): Long HG (with china_adj)
- RISK_OFF + INFLATION: Flat (ambiguous in stagflation)
- RISK_ON + INFLATION: Long HG

**Assessment**: HG went from $2.76 to $5.09 -- an 84% gain. At $250/cent, that is $250 * (509 - 276) = $58,250 per contract for buy-and-hold. But the strategy was short HG 64% of the time it held a position, meaning it was systematically betting against copper's rally. Furthermore, HG only appeared in 12% of position snapshots -- the combination of L4 term structure filtering (HG frequently at 0.00-0.75 ts_mult), the China CLI filter, and commodity notional caps severely limited copper exposure.

**Irony**: This is the Copper-Gold strategy, yet copper is the least-traded commodity in the portfolio. The copper position appears in fewer snapshots than gold, silver, crude, or even the micro equity futures.

**Estimated P&L direction**: Likely small net negative. Short bias during an 84% copper rally, but very low frequency and small position sizes limit the damage. The L4 filter protected the strategy from holding large short copper positions during the strongest rallies.

**Diversification value**: Low. Too infrequent to contribute meaningful diversification.

---

### 2.8 MES -- Micro E-mini S&P 500

**Position profile**: 27 appearances. 4-12 contracts. 81% short (22 short vs 5 long).
**Asset class weight**: 30% (Equity Index, shared with MNQ). 20% per-instrument notional cap.
**Point value**: $5/point. Contract notional ~$25,000.
**Data availability**: 1,696 bars (~2019-06 to 2025-11). NOT available 2010-2019.

**CRITICAL DATA GAP**: MES launched on the CME in May 2019. The backtest loads 1,696 bars vs ~4,000 for other instruments. However, position logs show MES appearing as early as 2013 (line 761: "Positions: 6J:-3 SI:1 MNQ:5 MES:9") and 2015 (line 1292: "Positions: 6J:-2 ZN:-3 HG:1 MNQ:6 MES:9").

**This is a bug or a data artifact**: The code uses `ffill` for missing data and checks `std::isnan()` before calculating P&L, but the sizing logic appears to allocate positions to MES/MNQ even when no price data exists. If the prices are NaN, the P&L contribution would be zero (the NaN check on line 1227 skips the instrument), but the notional allocation still consumes portfolio capacity. This means the strategy is allocating to phantom MES/MNQ positions that generate no P&L but consume the 30% equity index weight allocation, potentially crowding out other instruments.

**Assessment (2019-2025 only)**: MES went from ~2,918 to ~6,858 -- a 135% gain. The strategy was short 81% of the time. At 12 contracts * $5/point, the full short-side exposure on a 135% rally would be devastating: 12 * 5 * (6858 - 2918) = ~$236,400 in losses on the short side. Even at the lower 4-6 contract range with intermittent flat periods, the short bias during one of history's strongest equity bull runs was a major P&L headwind.

**Estimated P&L direction**: Strongly negative. Persistent short bias in a multi-year bull market. The 5 long appearances (likely during brief RISK_ON windows in 2021) cannot offset the systematic short exposure.

**Diversification value**: High in theory (equity shorts hedge portfolio during crashes), but the persistent loss generation makes it an expensive hedge that rarely pays off.

---

### 2.9 MNQ -- Micro E-mini Nasdaq-100

**Position profile**: 71 appearances. 2-7 contracts. 87% short (62 short vs 9 long).
**Asset class weight**: 30% (Equity Index, shared with MES). 20% per-instrument notional cap.
**Point value**: $2/point. Contract notional ~$40,000.
**Data availability**: 1,696 bars (~2019-06 to 2025-11). Same data gap as MES.

**Same data gap concern as MES** -- MNQ appears in position logs as early as 2010-12 (line 202) and 2011-03 (line 249). Same phantom-position issue applies.

**Assessment (2019-2025 only)**: MNQ went from ~7,764 to ~25,540 -- a 229% gain. At 87% short bias, 7 contracts * $2/point, the short-side loss potential is: 7 * 2 * (25540 - 7764) = ~$248,864. Even with smaller sizes and intermittent periods, this is a substantial P&L headwind.

**Estimated P&L direction**: Strongly negative. Worse than MES due to stronger short bias (87% vs 81%) and the Nasdaq's outperformance vs S&P.

**Diversification value**: Same as MES -- theoretically valuable as a crash hedge, practically expensive.

---

## 3. Trade Expression Matrix Assessment

### Current Mapping

| Instrument | RISK_ON | RISK_OFF | RISK_ON+INFL | RISK_OFF+INFL |
|---|---|---|---|---|
| MES | Long | Short | Flat | Short (0.5x) |
| MNQ | Long | Short | Flat | Short (0.5x) |
| HG | Long | Short | Long | Flat |
| CL | Long | Short | Long | Flat |
| SI | Long | Long | Long | Long |
| GC | Short | Long | Short | Long |
| ZN | Short | Long | Short | Short |
| UB | Short | Long | Short | Short |
| 6J | Short | Long | Short | Flat |

### Is This Mapping Sensible?

**Broadly yes, with caveats**:

1. **RISK_ON mapping is textbook**: Long cyclicals (HG, CL, MES, MNQ), short safe havens (GC, ZN, UB, 6J). This is a standard risk-parity-like trade expression.

2. **RISK_OFF mapping is textbook**: The mirror image. Long safe havens, short cyclicals.

3. **INFLATION variants are thoughtful**: Removing equities in RISK_ON+INFLATION (inflation hurts P/E multiples) and flipping bonds short in RISK_OFF+INFLATION (rates rise in inflation) show genuine macro reasoning.

4. **SI always long is debatable**: Silver has both industrial (cyclical) and precious metal (safe haven) properties. The strategy bets silver always has a bid regardless of regime. This worked spectacularly in 2010-2025 due to silver's secular bull run, but it is a directional bet, not a diversified expression.

### Instruments That Consistently Lose Regardless of Regime

Based on the directional analysis:

1. **MES/MNQ**: 81-87% short bias during a 135-229% equity rally. The strategy's RISK_OFF tilt (52% of days) means equities are shorted the majority of the time. Even the RISK_ON long exposure (5-9 long appearances) is too infrequent to offset.

2. **6J**: 57% long bias during a 40% yen depreciation. The yen's secular weakness (BOJ monetary policy divergence) means the RISK_OFF long-yen trade has been a persistent loser.

3. **HG**: 64% short bias during an 84% copper rally, but low frequency limits damage.

### The Structural Problem

The strategy is in RISK_OFF mode 52% of the time. RISK_OFF means: long bonds, long gold, long yen, long silver, short equities, short crude, short copper. Over 2010-2025, this portfolio was systematically:
- Long assets that declined or went sideways (yen, early-period bonds)
- Short assets that rallied massively (equities)
- Benefiting primarily from gold and silver's secular bull runs

The alpha, such as it is, appears to come from precious metals (GC, SI) and early-period bond rallies (2010-2020), offset by persistent losses on equity shorts and yen longs.

---

## 4. Estimated P&L Attribution (Directional, Not Precise)

| Instrument | Estimated Direction | Confidence | Key Drivers |
|---|---|---|---|
| **SI** | Strong positive | High | Always long during 193% rally. ~$143K est. |
| **GC** | Moderate positive | Medium | 59% long during 238% rally. Offset by short periods. ~$50-100K est. |
| **UB** | Mixed (positive early, negative late) | Medium | Long bias helped 2010-2020. Hurt 2020-2025. |
| **ZN** | Mixed (positive early, negative late) | Medium | Same as UB but lower magnitude. |
| **CL** | Slightly negative to flat | Low | Heavy L4 filtering reduces impact. |
| **6J** | Moderate negative | Medium | Long bias during yen depreciation. |
| **HG** | Slightly negative | Medium | Short bias during rally, but very low frequency. |
| **MES** | Strongly negative | High | 81% short during 135% rally. |
| **MNQ** | Strongly negative | High | 87% short during 229% rally. |

**Rough decomposition of the $762K total return**:
- SI: +$100-150K (the bedrock of returns)
- GC: +$50-100K (significant positive contributor)
- UB/ZN: +$50-100K net (positive early period, negative late)
- CL/HG: -$20K to +$20K (approximately flat, heavily filtered)
- 6J: -$30-60K (yen depreciation drag)
- MES/MNQ: -$30-80K (equity short losses, partially limited by late data start and low appearance frequency)
- Transaction costs: embedded in equity (estimated -$50-100K over full period)

**This decomposition suggests 60-80% of gross returns came from being long silver and gold** -- positions that required zero signal sophistication. The Cu/Au ratio, macro regime classifier, and DXY filter add complexity without demonstrably adding return.

---

## 5. MES/MNQ Data Gap Analysis

### The Problem

MES and MNQ launched on CME in May 2019. The backtest has 1,696 bars for each (~6.7 years), vs ~4,000 bars for other instruments (~15.9 years). This creates three issues:

1. **Phantom positions pre-2019**: Position logs show MES/MNQ allocated as early as 2010-2013. The code allocates 30% of portfolio notional to the equity index asset class on every rebalance. Before MES/MNQ data exists, these positions generate zero P&L (NaN price checks skip them in P&L calculation) but still consume the allocation budget. This means the strategy was effectively running at 70% capacity for the first 9 years -- the equity index weight was "burned" on phantom positions that never generated returns.

2. **Survivorship period bias**: The 2019-2025 period includes one of history's strongest equity bull runs (COVID stimulus, AI rally). MES/MNQ short bias during this specific period looks terrible. A longer history including 2000-2002 and 2007-2009 bear markets would likely show equity shorts as significant positive contributors. The short sample biases against equity instruments.

3. **No pre-2019 equity exposure at all**: Without MES/MNQ data, the strategy had zero equity index exposure from 2010-2019. This means the portfolio was commodities + bonds + FX only for 60% of its history. Any portfolio-level statistics (Sharpe, correlation to SPX, etc.) are contaminated by this structural break.

### Should We Use ES/NQ Proxies?

**Yes, strongly recommended.** Here is the proposal:

- Use ES (E-mini S&P 500) data from 2010-2019, scaled to MES notional ($5/point vs $50/point for ES -- multiply contract count by 10 to get equivalent MES contracts, or divide ES position by 10).
- Use NQ (E-mini Nasdaq-100) data from 2010-2019, scaled to MNQ notional ($2/point vs $20/point for NQ).
- This is a standard practice in futures backtesting. Micro contracts are economically identical to their full-size counterparts, just smaller.

**Impact estimate**: Adding 2010-2019 equity data would:
- Capture the 2010-2019 bull market (SPX from ~1,000 to ~3,200, +220%). With the strategy's RISK_OFF bias, this would show equity shorts losing money during 2012-2019.
- Capture the 2011 European debt crisis and 2015-2016 selloff, where equity shorts would have generated positive returns.
- Eliminate the phantom-position bug where 30% of portfolio capacity was wasted.
- Likely worsen the Sharpe ratio (more equity short losses during the bull run) but provide a more honest assessment.

---

## 6. Proposed Optimized Universe

### Option A: Concentrated Core (4 instruments)

**Keep**: GC, SI, UB, ZN
**Remove**: 6J, HG, CL, MES, MNQ

**Rationale**: The strategy's returns appear to come almost entirely from precious metals and bonds. Removing the consistently losing instruments (equity shorts, yen longs) and the heavily-filtered instruments (CL, HG) would:
- Eliminate the equity short drag (estimated -$30-80K)
- Eliminate the yen depreciation drag (estimated -$30-60K)
- Reduce turnover (fewer instruments to rebalance)
- Simplify position management

**Risk**: This becomes a pure precious-metals + bonds portfolio. It works when gold/silver rally and rates decline. It fails in rising-rate environments (2022-2023) with no equity or commodity diversification.

**Estimated impact**: CAGR would likely increase to 4-5% with lower volatility, improving Sharpe to ~0.5. But this is entirely a function of the specific backtest period (gold up 238%, silver up 193%). Out-of-sample, this concentration could be catastrophic.

### Option B: Refined Full Universe (7 instruments)

**Keep at current weight**: GC, SI, ZN
**Increase weight**: UB (but fix transaction cost model first)
**Decrease weight or conditional inclusion**: CL (only when L4 ts_mult > 0; do not allocate when zeroed)
**Remove**: HG, MES, MNQ, 6J

**Rationale**:
- HG is too infrequent (12% of snapshots) to matter. Its removal frees commodity notional for GC/SI/CL.
- MES/MNQ are persistent losers in the current signal regime. Unless the RISK_OFF bias is fixed, they will continue to generate losses.
- 6J is a persistent loser during yen secular weakness. Its crisis-alpha value does not compensate.
- CL is worth keeping conditionally because it provides genuine commodity cycle exposure when not zeroed by L4.

**Risk**: Losing equity and FX diversification reduces the portfolio's cross-asset properties. SPX correlation (currently -0.17) would likely shift closer to zero or slightly positive.

**Estimated impact**: Moderate CAGR improvement (4-5%), Sharpe improvement to ~0.4-0.5.

### Option C: Fix the Signal, Keep the Universe

**Keep all 9 instruments** but address the root cause: the signal's RISK_OFF bias.

**Rationale**: The instruments themselves are not the problem. The Cu/Au ratio's secular decline since 2011 has kept the strategy in RISK_OFF mode 52% of the time during the longest equity bull market in history. If the signal were detrended or complemented with additional indicators, the RISK_ON/RISK_OFF balance could shift, making equity longs and yen shorts more prevalent, which would have been profitable.

**Required changes**:
1. Detrend the Cu/Au ratio (use 2-year rolling median relative measure instead of absolute level)
2. Add composite signal inputs (credit spreads, VIX term structure, ISM)
3. Fix MES/MNQ data gap with ES/NQ proxies
4. Fix UB transaction costs
5. Implement per-instrument P&L tracking to validate

**Risk**: More complexity, more parameters, more overfitting risk. The fundamental question remains: does the Cu/Au ratio have predictive power, or is it noise?

### Recommendation

**Option C first, then evaluate**: The most valuable next step is implementing per-instrument P&L tracking in the C++ engine. Until we have actual attribution data, any universe optimization is guesswork. The estimated attribution above could be significantly wrong -- perhaps 6J is actually net positive because its crisis-alpha moments (COVID crash, Aug 2024 yen squeeze) more than offset the secular depreciation. We cannot know without data.

**If forced to act immediately**: Option B (remove HG, MES/MNQ, 6J) is the safest short-term improvement. It eliminates known losers without requiring signal changes.

---

## 7. Implementation Proposal: Per-Instrument P&L Tracking

Add the following to `copper_gold_strategy.cpp`:

### Data Structure (before main loop)
```cpp
std::unordered_map<std::string, double> cumulative_pnl;  // running total per instrument
std::unordered_map<std::string, double> daily_inst_pnl;   // daily breakdown
for (const auto& sym : {"HG","GC","CL","SI","ZN","UB","6J","MES","MNQ"})
    cumulative_pnl[sym] = 0.0;
```

### Modification to P&L Calculation (lines 1222-1231)
```cpp
double daily_pnl = 0.0;
daily_inst_pnl.clear();
for (const auto& [sym, qty] : positions) {
    if (qty == 0.0) continue;
    const auto* px = px_map[sym];
    if (!px || std::isnan((*px)[i]) || std::isnan((*px)[i-1])) continue;
    double pv = POINT_VALUE.count(sym) ? POINT_VALUE.at(sym) : 0.0;
    double price_change = (*px)[i] - (*px)[i-1];
    double inst_pnl = qty * price_change * pv;
    daily_pnl += inst_pnl;
    daily_inst_pnl[sym] = inst_pnl;
    cumulative_pnl[sym] += inst_pnl;
}
```

### Output in Diagnostic Summary
```cpp
std::cout << "── PER-INSTRUMENT P&L ──\n";
for (const auto& [sym, pnl] : cumulative_pnl) {
    std::cout << "  " << sym << ": $" << std::fixed << std::setprecision(2) << pnl
              << " (" << (pnl / (equity - p_.initial_capital) * 100.0) << "% of total)\n";
}
```

This is approximately 15 lines of code. It should be the highest priority change before any universe optimization.

---

## 8. Diversification Cost of Removing Instruments

Removing instruments reduces portfolio diversification, which can be measured by the expected increase in portfolio volatility. A rough framework:

| Removal | Diversification Cost | Return Cost | Net Impact |
|---|---|---|---|
| Remove MES/MNQ | Low (only 27+71 appearances) | Positive (removes persistent short losses) | Likely positive |
| Remove 6J | Moderate (1,343 appearances, crisis-alpha) | Positive (removes yen depreciation drag) | Likely positive short-term, risky long-term |
| Remove HG | Very low (174 appearances, 12% of snapshots) | Slightly positive (removes small short-bias losses) | Positive |
| Remove CL | Moderate (955 appearances, unique commodity exposure) | Uncertain (heavy L4 filtering already minimizes) | Neutral |
| Remove all 5 above | High (40%+ of instruments gone) | Positive in-sample | Dangerous -- concentration risk |

**Key insight**: The instruments that contribute the most diversification (6J, CL) are not the same ones that contribute the most return (SI, GC). This creates a classic diversification-vs-return tradeoff.

---

## 9. Summary of Key Findings

1. **Per-instrument P&L is not tracked.** This is the most critical gap. All attribution analysis is estimated, not measured. Fix this first.

2. **Silver (SI) and Gold (GC) appear to drive 60-80% of returns.** SI is always long and captured a 193% rally. GC is long 59% of the time during a 238% rally. The strategy may be a disguised precious metals momentum fund.

3. **Equity shorts (MES/MNQ) are persistent losers.** 81-87% short bias during a 135-229% equity rally. Data starts only in 2019, missing the full 2010-2019 bull run as well.

4. **Yen longs (6J) are a persistent drag.** 57% long bias during a 40% yen depreciation.

5. **Copper (HG) is barely traded** despite being the strategy's namesake signal. 12% appearance rate, heavily filtered by L4 term structure and commodity notional caps.

6. **CL is heavily filtered by L4**, zeroed out during precisely the most volatile and informative periods (backwardation in 2014, 2018, 2022-2025).

7. **MES/MNQ data gap (pre-2019) causes phantom positions** that consume 30% of portfolio capacity with zero P&L contribution.

8. **UB transaction costs are modeled at $2.50 RT (zero spread/slippage)**, which is unrealistic and flatters UB's apparent contribution.

9. **The Cu/Au ratio's secular decline drives a structural RISK_OFF bias** (52% of days), which is the root cause of equity short losses and yen long losses. Fixing the signal is more impactful than removing instruments.

10. **Before optimizing the universe, implement per-instrument P&L tracking.** This is ~15 lines of C++ and transforms all future analysis from guesswork to data-driven.
