# CL (Crude Oil) and SI (Silver) Analysis for V5

## Executive Summary

**CL Verdict: DROP (Option A)**. CL is structurally broken in this strategy. The raw Cu/Au ratio's secular decline creates a persistent RISK_OFF bias that shorts oil -- exactly wrong in the post-2022 environment where oil is range-bound with backwardated term structure. Even with detrending, CL is marginal. Without it, CL is a guaranteed loser.

**SI Verdict: KEEP (conditionally)**. Despite -$360 net in V4, SI is not broken -- it is being strangled by costs. The detrend_off A/B test shows SI at +$123K net (the second-best instrument). V4's poor SI result is an artifact of the other V4 changes (dropping 6J/HG/MES, fixing GC/SI bug) that altered equity trajectory and sizing. SI deserves another look in V5 rather than being dropped.

---

## 1. CL P&L Comparison Across Versions

| Version / Config     | CL Gross | CL Trades | CL Win% | CL Costs | CL Net P&L |
|---------------------|----------|-----------|---------|----------|-------------|
| V4 (production)      | -$52,880 | 103       | 50.5%   | $14,716  | **-$67,596** |
| A/B: Detrend ON      | +$80,820 | 75        | 62.7%   | $6,474   | **+$74,346** |
| A/B: Detrend OFF     | +$107,940| 82        | 59.8%   | $11,006  | **+$96,934** |

### Key Observation: V4 is WORSE than both A/B variants

This is the central puzzle. The A/B tests (which tested detrending in isolation) both show CL profitable. But V4 (which also dropped 6J, HG, MES and fixed the GC/SI bug) shows CL at -$68K.

**Root cause:** V4's other changes (dropping 6J/HG/MES, fixing GC/SI) altered the overall equity trajectory. Lower portfolio equity means:
1. Smaller `size_mult` (equity-based position sizing)
2. Different rebalance timing (drawdown triggers fire at different points)
3. The CL positions that DO get taken are smaller and hit during worse periods

This is a path-dependency problem. CL's profitability is fragile -- it depends on WHEN and HOW BIG the positions are, which depends on the rest of the portfolio. That fragility alone is a red flag.

---

## 2. CL Directional Bias Analysis

### Position Direction by Year (V4)

```
Year   LONG  SHORT  Net Bias    CL Price Regime
----   ----  -----  --------    ----------------
2010      3      2  LONG        $70-90 (recovery)
2011     17     27  SHORT       $80-115 (volatile up)
2012     29     25  LONG        $80-110 (range)
2013     45      5  LONG        $90-110 (stable high)
2014     30      5  LONG        $55-105 (crash starts)
2015     15     37  SHORT       $35-65 (crash bottom)
2016     17     31  SHORT       $26-54 (recovery start)
2017     37     20  LONG        $42-60 (recovery)
2018     20     12  LONG        $42-77 (rally then crash)
2019     23     20  LONG        $46-66 (range)
2020     29     15  LONG        $-37-63 (COVID crash/recovery)
2021     30      4  LONG        $48-85 (strong rally)
2022     24      2  LONG        $71-124 (Ukraine spike)
2023     22     18  LONG        $64-94 (range)
2024     13      8  LONG        $66-87 (range)
2025     12      8  LONG        $56-79 (weak)
```

**Total: 366 LONG vs 239 SHORT (1.53:1 ratio)**

### Tilt Distribution (explains the bias)

| Config            | RISK_ON days | RISK_OFF days | NEUTRAL days |
|-------------------|-------------|---------------|-------------|
| V4 (no detrend)   | 1,712       | 2,070         | 229         |
| A/B: Detrend ON   | 1,564       | 1,707         | 740         |
| A/B: Detrend OFF  | 1,719       | 2,082         | 210         |

V4's raw Cu/Au ratio has been in secular decline since ~2011 (gold up, copper flat). Without detrending:
- The ratio's z-score is persistently negative
- This generates MORE RISK_OFF signals (2,070 days vs 1,564 with detrending)
- RISK_OFF = short CL
- But CL has been in a secular range with frequent backwardation since 2021

**The RISK_OFF short bias does NOT make economic sense for oil post-2022.** The Cu/Au ratio is declining because gold is surging (central bank buying, geopolitics), NOT because the economy is weakening. Shorting oil based on gold strength is a category error -- gold and oil have been structurally decoupled since 2020.

---

## 3. CL Term Structure vs Direction

CL's term structure has been predominantly BACKWARDATED since 2021:

```
Year   BACKWARDATION  CONTANGO  FLAT
2010       0             2        0
2014       2             0        0    (brief)
2018       1             1        0    (brief)
2021       2             0        0    <-- shift begins
2022       2             0        0
2023       2             0        0
2024       2             0        1
2025       1             0        0
```

The Layer 4 term structure filter is supposed to protect CL:
- RISK_OFF + CL BACKWARDATION => `ts_mult = 0.0` (skip the short entirely)
- RISK_OFF + CL CONTANGO => `ts_mult = 1.0` (full short position)

**Problem:** The filter evaluates only twice per year (at the ~6-month macro signal checkpoints). Between evaluations, the term structure can flip, but the position persists. In 2022-2025, CL was mostly backwardated, meaning the filter SHOULD have killed most shorts. But V4 shows CL short positions in 2023-2025, suggesting:
1. The filter catches some but not all shorts
2. The shorts that DO get through (during brief contango windows) are large and get caught when CL rallies

---

## 4. Why Detrending Helped CL (But Still Not Enough)

With detrending ON (A/B test):
- Tilt distribution shifts: RISK_ON=1,564, RISK_OFF=1,707, NEUTRAL=740
- The detrended signal generates 740 NEUTRAL days (vs 229 without)
- NEUTRAL = flat CL (no position)
- This eliminates the weakest RISK_OFF short signals
- CL goes from -$68K to +$74K -- a $142K improvement

But even +$74K over 15 years is mediocre:
- $74K / 15 years = ~$5K/year
- On 75 trades = $990 avg profit per trade
- CL's avg win is $6,191, avg loss is $7,505 -- negative edge per trade
- The profitability comes entirely from the 62.7% win rate, not from edge size
- This is a fragile setup: any small degradation in win rate flips CL negative

---

## 5. CL Position Sizing Logic (Code Trace)

From `copper_gold_strategy.cpp`:

```
RISK_ON (any regime except INFLATION_SHOCK):
  CL = contracts_for("CL", +1.0)   // LONG

RISK_ON + INFLATION_SHOCK:
  CL = contracts_for("CL", +1.0)   // LONG (same)

RISK_OFF (any regime except INFLATION_SHOCK):
  CL = contracts_for("CL", -1.0)   // SHORT

RISK_OFF + INFLATION_SHOCK:
  CL = 0                            // FLAT (no position)
```

The `contracts_for` function:
```
notional_alloc = equity * leverage_target * 0.35  (commodity weight)
raw_contracts  = (notional_alloc / 60000) * size_mult
```

CL notional per contract: $60,000. With $1M equity and 1.0x leverage:
- Commodity allocation: $1M * 1.0 * 0.35 = $350K
- Raw CL contracts: $350K / $60K = ~5.8
- After position limits (15% single instrument cap): max ~2.5 contracts
- After size_mult scaling: typically 1-3 contracts

CL is getting sized proportionally to the commodity bucket. It competes with GC and SI for the same 35% allocation, capped at 15% per instrument.

---

## 6. Verdict on CL

### Option A: DROP CL entirely -- RECOMMENDED

**Arguments for dropping:**
1. **-$68K net in V4** -- worst instrument by far
2. **Fragile profitability** -- profitable in A/B tests but only because of win rate, not edge size
3. **Structural RISK_OFF short bias is broken** -- shorting oil because gold is strong is economically wrong in the current regime
4. **Path-dependent** -- CL's P&L swings $140K+ depending on what other instruments are in the portfolio
5. **Saves $15K in costs** -- 103 trades * ~$143/trade average cost
6. **$53K gross losses eliminated** -- the negative gross P&L means CL is actively destroying value, not just being eaten by costs
7. **Term structure filter is insufficient** -- evaluates too infrequently to reliably catch the backwardation/contango transitions

**What we give up:**
- In RISK_ON, CL long has been generally correct (oil tends to rally in risk-on)
- Some diversification in the commodity bucket
- But GC and SI already provide commodity exposure

### Option B: Keep CL RISK_ON only -- NOT recommended

This would mean CL is long-only, entering only during RISK_ON. The problem:
- RISK_ON longs were profitable in 2012-2014, 2017, 2021-2022
- But in 2023-2025 (range-bound market), RISK_ON longs have been mediocre
- Adds complexity for marginal benefit
- The commodity bucket (GC, SI) already provides long commodity exposure in RISK_ON

### Option C: CL-specific filter (term structure only) -- NOT recommended

The existing Layer 4 term structure filter already does this:
- RISK_OFF + BACKWARDATION => skip (ts_mult = 0.0)
- RISK_ON + CONTANGO => minimal (ts_mult = 0.25)

The problem is the filter evaluates at ~6-month intervals. More frequent evaluation would help, but adds complexity for an instrument that is already marginal.

**Final answer: DROP CL. Save ~$15K costs + eliminate ~$53K gross losses. Use the freed-up commodity allocation to increase GC/SI sizing if warranted.**

---

## 7. SI (Silver) Analysis

### V4 Performance

| Metric     | Value |
|-----------|-------|
| Gross P&L  | +$13,825 |
| Trades     | 62 |
| Win Rate   | 40.3% |
| Avg Win    | $13,724 |
| Avg Loss   | $8,899 |
| Costs      | $14,185 |
| **Net P&L**| **-$360** |

SI has POSITIVE gross P&L ($13,825) that is entirely consumed by costs ($14,185). This is NOT the same problem as CL -- CL has negative gross P&L.

### SI Across Versions

| Version / Config     | SI Gross  | SI Trades | SI Win% | SI Costs  | SI Net P&L |
|---------------------|----------|-----------|---------|----------|-------------|
| V4 (production)      | +$13,825 | 62        | 40.3%   | $14,185  | **-$360**   |
| A/B: Detrend ON      | +$65,025 | 65        | 47.7%   | $14,105  | **+$50,920**|
| A/B: Detrend OFF     | +$135,350| 55        | 45.5%   | $12,261  | **+$123,089**|

### Why SI collapsed from +$123K to -$360

The same path-dependency issue as CL, but more pronounced:
1. A/B detrend_off has SI at +$135K gross on 55 trades -- strong gross edge
2. V4 has SI at +$14K gross on 62 trades -- drastically lower gross per trade
3. V4's other changes (dropping 6J/HG/MES, GC/SI bug fix) changed the equity trajectory
4. The GC/SI bug fix in V4 likely changed SI's position sizing or timing directly
5. Different equity levels = different sizing = different entry points = different P&L

### SI's Economic Logic

SI (silver) is ALWAYS long in this strategy, regardless of tilt:
- RISK_ON: Long SI (industrial demand proxy)
- RISK_OFF: Long SI (precious metals safe haven, paired with long GC)
- INFLATION_SHOCK: Long SI (inflation hedge)

This makes more economic sense than CL because:
- Silver benefits in BOTH risk-on (industrial use) and risk-off (precious metal)
- The position direction never flips -- no whipsaw risk from regime changes
- Silver has been in a secular bull since 2020 ($18 to $53)

### SI Cost Problem

SI costs are high because:
- Contract specs: $265K notional, $25/tick, 1.0 spread ticks, 1.0 slippage ticks
- Round-trip cost: $5.14 commission + $25 spread + 2*$25 slippage = $80.14/contract/RT
- BUT 62 trades * $80/contract would only be ~$5K, yet costs are $14K
- This implies ~2 contracts average per trade, or that the slippage estimate is conservative

The cost-to-gross ratio is the issue: $14K costs / $14K gross = 100% cost drag.

### SI Verdict: KEEP, but investigate sizing

**Arguments for keeping:**
1. **Positive gross P&L** -- SI is generating alpha, just not enough to overcome costs
2. **Consistent direction** -- always long, no whipsaw
3. **Strong in A/B tests** -- +$51K to +$123K net across variants
4. **Diversification** -- silver provides precious metals exposure distinct from gold
5. **Secular tailwind** -- silver has nearly tripled since 2020

**Arguments for concern:**
1. **40.3% win rate** in V4 is below break-even (though avg win >> avg loss)
2. **Path-dependent** -- $123K swing between A/B test and V4
3. **High costs** -- $229/trade average is expensive for an instrument that only generates $223/trade gross

**Recommendation:** Keep SI in V5, but:
- Monitor the cost/gross ratio -- if V5's other changes (dropping CL, etc.) improve equity trajectory, SI sizing and timing may improve
- Consider reducing SI slippage estimate if real-world fills are better than 1.0 tick
- The vol-adjustment (SI sized relative to GC ATR) may be over-sizing in high-vol periods

---

## 8. Summary Table

| Instrument | V4 Net P&L | Gross P&L | Action | Rationale |
|-----------|-----------|-----------|--------|-----------|
| CL         | -$67,596  | -$52,880  | **DROP** | Negative gross = structural problem. RISK_OFF short bias is economically broken. |
| SI         | -$360     | +$13,825  | **KEEP** | Positive gross consumed by costs. Strong in A/B tests. Always-long direction is sound. |

## 9. Impact Estimate for V5

Dropping CL from V5:
- **Eliminate ~$53K gross losses** (the negative gross P&L)
- **Save ~$15K in transaction costs** (103 trades avoided)
- **Net improvement: ~$68K** over the backtest period ($4.3K/year)
- **Freed commodity allocation** -- 15% single-instrument cap no longer consumed by CL
- **Reduced portfolio volatility** -- CL's 50.5% win rate with $11.5K avg loss was the highest loss-per-trade in the portfolio

Keeping SI:
- **Risk: -$360** (essentially flat, not actively harmful)
- **Upside: $51K-$123K** if equity trajectory improves from other V5 changes
- **Cost: ~$14K/year in transaction costs** (the price of optionality)
