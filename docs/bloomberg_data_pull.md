# Bloomberg Data Pull Guide — V6 Signal Research

**Purpose**: Pull new macro data series for testing as independent signal sources alongside the Cu/Au ratio strategy.
**Backtest period**: 2010-06-07 to 2025-11-12 (use 2010-01-01 start for buffer)
**Output format**: CSV with columns `date,value` — date format `YYYY-MM-DD`, daily frequency

---

## 1. MOVE Index (ICE BofA Rates Volatility)

The VIX equivalent for bonds. Since 73% of our alpha is in UB/ZN, this is the right vol gauge.

**Bloomberg formulas** (A1 = start date `2010-01-01`, B1 = end date `2025-11-12`):

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `MOVE Index` | `=BDH("MOVE Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 1 | `.MOVE` | `=BDH(".MOVE","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 2 | `BOFA MOVE` | `=BDH("MOVE Index","LAST_PRICE",A1,B1,"Dir=V","Dts=S","Fill=P")` |

**Notes**: MOVE = Merrill Lynch Option Volatility Estimate. Measures implied vol across the Treasury curve. Spikes during rate shocks (2013 taper tantrum, 2022 hiking cycle). Daily close values, no unit conversion needed.

---

## 2. CDX Investment Grade Spread (NA IG CDS Index)

Cleaner credit risk signal than the HY ETF spread we currently use. More liquid, higher frequency, directly tradeable.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `CDX IG CDSI GEN 5Y Corp` | `=BDH("CDX IG CDSI GEN 5Y Corp","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 1 | `CDX.NA.IG` | `=BDH("CDX.NA.IG","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 2 | `IBOXIG Index` | `=BDH("IBOXIG Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |

**Notes**: Quoted in bps. Higher = wider spreads = more risk aversion. The 5Y on-the-run rolls every 6 months (March/September). Bloomberg should handle the roll automatically with the generic ticker.

---

## 3. CDX High Yield Spread (NA HY CDS Index)

Pair with CDX IG for the IG-HY basis (credit curve steepness). Also useful standalone — HY CDS is the purest "risk appetite" gauge.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `CDX HY CDSI GEN 5Y Corp` | `=BDH("CDX HY CDSI GEN 5Y Corp","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 1 | `CDX.NA.HY` | `=BDH("CDX.NA.HY","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 2 | `IBOXHY Index` | `=BDH("IBOXHY Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |

**Notes**: Quoted in bps. Typically 300-600 bps range. Correlation with Cu/Au ratio is moderate (~0.4-0.5) — more independent than HY ETF spread which is ~0.6 correlated.

---

## 4. CFTC Commitments of Traders — Copper Net Speculative Position

Know when the market is crowded. Extreme spec positioning in copper often precedes Cu/Au ratio reversals.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `CFTCNET COPPER` | `=BDH("CFTCNET COPPER Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |
| Backup 1 | `CFNCHG1P Index` | `=BDH("CFNCHG1P Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |
| Backup 2 | `CLNTHGP Index` | `=BDH("CLNTHGP Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |

**Notes**: Weekly data (released Fridays, as-of-Tuesday). Use `Days=A` to get all calendar days with forward-fill. Values are net contracts (long - short) held by managed money / speculators. Can be positive or negative.

---

## 5. CFTC Commitments of Traders — Gold Net Speculative Position

Same rationale as copper COT. Extreme gold positioning signals regime exhaustion.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `CFTCNET GOLD` | `=BDH("CFTCNET GOLD Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |
| Backup 1 | `CFNAGCP Index` | `=BDH("CFNAGCP Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |
| Backup 2 | `CLNTGCP Index` | `=BDH("CLNTGCP Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P","Days=A")` |

**Notes**: Same weekly frequency as copper COT. Net contracts held by speculators. The Cu COT / Au COT ratio could itself be a signal — when specs are long copper and short gold, that's peak risk-on consensus.

---

## 6. Citi Economic Surprise Index (US)

Captures macro turning points before Cu/Au ratio does. When economic data beats/misses consensus, this moves first.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `CESIUSD Index` | `=BDH("CESIUSD Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 1 | `CESIU Index` | `=BDH("CESIU Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 2 | `CESI USD Index` | `=BDH("CESI USD Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |

**Notes**: Ranges roughly -100 to +100. Mean-reverting by construction (old surprises roll off). Positive = data beating expectations. Daily. Low correlation with Cu/Au ratio — measures data flow, not price levels.

---

## 7. 2s10s Treasury Spread (Yield Curve Slope)

Classic recession indicator. Inversion predicts RISK_OFF regimes 6-18 months ahead — potentially leads the Cu/Au ratio.

| Priority | Ticker | Formula |
|----------|--------|---------|
| **Primary** | `USYC2Y10 Index` | `=BDH("USYC2Y10 Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 1 | `US2Y10Y` | `=BDH("US2Y10Y Index","PX_LAST",A1,B1,"Dir=V","Dts=S","Fill=P")` |
| Backup 2 | Compute manually | `=BDH("USGG10YR Index","PX_LAST",A1,B1) - BDH("USGG2YR Index","PX_LAST",A1,B1)` |

**Notes**: Quoted in bps. Positive = normal curve, negative = inverted. We already have 10Y treasury data; if Bloomberg tickers don't work, pulling just the 2Y yield and computing 10Y-2Y ourselves works fine.

---

## BDH Formula Reference

```
=BDH(security, field, start_date, end_date, [optional args])
```

| Argument | Meaning | Our Setting |
|----------|---------|-------------|
| `Dir=V` | Vertical output (dates down rows) | Always use |
| `Dts=S` | Show dates in first column | Always use |
| `Fill=P` | Forward-fill missing values with previous | Always use |
| `Days=A` | All calendar days (not just business days) | Use for weekly data (COT) |

**Date cells**: Set A1 = `2010-01-01`, B1 = `2025-11-12`. Format as dates, not text.

---

## After Pulling — Export Steps

1. Each series goes in its own sheet or section
2. Copy the date + value columns
3. Save as CSV: `data/cleaned/macro/<name>.csv`
4. File naming convention (match existing files):
   - `move_index.csv`
   - `cdx_ig.csv`
   - `cdx_hy.csv`
   - `cot_copper.csv`
   - `cot_gold.csv`
   - `citi_esi.csv`
   - `treasury_2s10s.csv`
5. Column headers: `date,close` (match existing macro CSV format — actually use descriptive names like `date,move` or `date,cdx_ig_spread`)
6. Date format: `YYYY-MM-DD` (match existing files)
7. Verify row count: ~3,900-4,100 rows for daily data (2010-2025), ~780 rows for weekly COT data

---

## Priority Ranking for V6 Research

| Priority | Series | Why | Independence from Cu/Au |
|----------|--------|-----|------------------------|
| **1** | MOVE Index | We're a bond strategy — rates vol is our core risk | High |
| **2** | CDX IG + HY | Cleaner credit signal than HY ETF spread | Medium-High |
| **3** | 2s10s Spread | Leads regime changes by months | Medium |
| **4** | Citi ESI | Catches turning points early | High |
| **5** | COT Copper + Gold | Positioning extremes = reversal signal | Medium |

Start with #1-3. If those don't move the needle, #4-5 won't either and we should consider the multi-strategy sleeve approach instead.
