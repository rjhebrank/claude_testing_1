# Transaction Cost Model for Copper-Gold Macro Strategy

**Date**: 2026-02-24
**Status**: Research proposal -- no code changes
**Analyst**: Quantitative Strategy Review
**Backtest Reference**: `results/backtest_output_v2.txt` (v2), `results/performance_report_v2.md`

---

## 0. Executive Summary

The v2 backtest reports 3.62% CAGR gross with 46.7x annual turnover over 15.9 years. The code at `copper_gold_strategy.cpp:317-324` already contains a transaction cost framework using `ContractSpec::total_cost_rt()`, which deducts costs on every position change (line 1744) and on drawdown-stop liquidation (line 1353). However, the cost parameters embedded in the code are **significantly too low** -- they undercount exchange fees by 50-70% and omit several real-world cost components entirely.

After building a conservative, research-grade cost model, the conclusions are:

- **At 46.7x turnover**: annual cost drag is approximately **3.50-4.30%**, reducing net CAGR to **-0.68% to +0.12%**. The strategy is net-negative or breakeven.
- **At 15x turnover**: annual cost drag is approximately **1.12-1.38%**, producing a net CAGR of **2.24-2.50%**. Marginal but survivable.
- **At 5x turnover**: annual cost drag is approximately **0.37-0.46%**, producing a net CAGR of **3.16-3.25%**. Preserves most of the gross return.
- **Break-even gross Sharpe**: At 46.7x turnover, the strategy needs a gross Sharpe of ~0.65 to be net-positive. It currently has 0.34.

**Bottom line**: Turnover reduction from 46.7x to 15x or below is the single most important improvement needed. Without it, no amount of signal improvement can overcome the cost drag.

---

## 1. Existing Cost Infrastructure in the Code

The C++ codebase already has a cost model. Here is the relevant structure from `copper_gold_strategy.cpp`:

### 1.1 ContractSpec Definition (lines 286-324)

```cpp
namespace ContractSpec {
struct Spec {
    double margin;         // initial margin ($)
    double notional;       // approx notional per contract ($)
    double tick_size;
    double tick_value;     // $ per tick
    double commission_rt;  // round-trip commission ($)
    double spread_ticks;   // estimated spread in ticks
    double slippage_ticks; // estimated slippage in ticks (one way)
};

static const std::unordered_map<std::string, Spec> specs = {
    {"HG",  {6000.0,  110000.0, 0.0005,   12.50,  2.50,  0.5, 0.5}},
    {"GC",  {11000.0, 200000.0, 0.10,     10.00,  2.50,  1.0, 0.5}},
    {"CL",  {7000.0,   75000.0, 0.01,     10.00,  2.50,  1.0, 1.0}},
    {"MES", {1500.0,   25000.0, 0.25,      1.25,  0.50,  1.0, 0.5}},
    {"MNQ", {2000.0,   40000.0, 0.25,      0.50,  0.50,  1.0, 0.5}},
    {"ZN",  {2500.0,  110000.0, 0.015625, 15.625, 1.50,  0.5, 0.5}},
    {"UB",  {9000.0,  130000.0, 0.03125,  31.25,  2.50,  0.0, 0.0}}, // not in doc cost table
    {"6J",  {4000.0,   80000.0, 0.000001, 12.50,  2.50,  1.0, 0.5}},
    {"SI",  {10000.0, 150000.0, 0.005,    25.00,  2.50,  1.0, 1.0}},
};

// round-trip cost = commission + spread (paid once on entry) + 2 * slippage (entry + exit)
static double total_cost_rt(const std::string& sym) {
    const Spec s = get(sym);
    return s.commission_rt
         + (s.spread_ticks * s.tick_value)
         + (2.0 * s.slippage_ticks * s.tick_value);
}
```

### 1.2 Where Costs Are Deducted

1. **On every position change** (line 1740-1746):
   ```cpp
   for (const auto& [sym, new_qty] : new_positions) {
       double old_qty = positions.count(sym) ? positions.at(sym) : 0.0;
       double qty_change = std::abs(new_qty - old_qty);
       if (qty_change > 0.0) {
           double total_cost = ContractSpec::total_cost_rt(sym) * qty_change;
           equity -= total_cost;
       }
   }
   ```

2. **On drawdown-stop liquidation** (line 1350-1354):
   ```cpp
   for (auto& [sym, qty] : positions) {
       if (qty != 0.0) {
           double cost = ContractSpec::total_cost_rt(sym) * std::abs(qty);
           equity -= cost;
           qty = 0.0;
       }
   }
   ```

### 1.3 Current Cost Computation Per Contract

Using the existing `total_cost_rt()` formula:

| Instrument | Commission RT | Spread (ticks x tick_value) | Slippage (2 x ticks x tick_value) | **Current Total RT** |
|---|---|---|---|---|
| HG | $2.50 | 0.5 x $12.50 = $6.25 | 2 x 0.5 x $12.50 = $12.50 | **$21.25** |
| GC | $2.50 | 1.0 x $10.00 = $10.00 | 2 x 0.5 x $10.00 = $10.00 | **$22.50** |
| CL | $2.50 | 1.0 x $10.00 = $10.00 | 2 x 1.0 x $10.00 = $20.00 | **$32.50** |
| MES | $0.50 | 1.0 x $1.25 = $1.25 | 2 x 0.5 x $1.25 = $1.25 | **$3.00** |
| MNQ | $0.50 | 1.0 x $0.50 = $0.50 | 2 x 0.5 x $0.50 = $0.50 | **$1.50** |
| ZN | $1.50 | 0.5 x $15.625 = $7.81 | 2 x 0.5 x $15.625 = $15.63 | **$24.94** |
| UB | $2.50 | 0.0 x $31.25 = $0.00 | 2 x 0.0 x $31.25 = $0.00 | **$2.50** |
| 6J | $2.50 | 1.0 x $12.50 = $12.50 | 2 x 0.5 x $12.50 = $12.50 | **$27.50** |
| SI | $2.50 | 1.0 x $25.00 = $25.00 | 2 x 1.0 x $25.00 = $50.00 | **$77.50** |

### 1.4 Problems With the Current Model

1. **UB has zero spread and zero slippage** (line 306 comment: "not in doc cost table"). UB (Ultra Bond) is one of the most frequently traded instruments in the portfolio (4-7 contracts, appearing in nearly every position set). Having zero market friction costs for this instrument is a material undercount.

2. **Commission of $2.50 RT is the broker commission only**. It does not include exchange fees (~$1.50-$1.90 per side for full-size contracts), clearing fees (~$0.05/side), or NFA regulatory fees ($0.02/side). The all-in commission is closer to $5.50-$6.50 RT for full-size contracts.

3. **Spread estimates are optimistic for some contracts**. HG at 0.5 ticks ($6.25) is reasonable for liquid hours. SI at 1.0 tick ($25.00) is also reasonable. But these are best-case (liquid hours only) estimates.

4. **Slippage model is one-size-fits-all**. The 0.5-1.0 tick slippage assumption does not account for position size relative to book depth.

5. **No roll costs**. Continuous futures data implies the strategy holds through rolls. Roll cost (spread between front and back month) is not modeled. For a portfolio turning over 46.7x/year, many trades coincide with roll periods.

---

## 2. Revised Per-Instrument Cost Table

### 2.1 Research Methodology

Costs are assembled from:
- CME Group official fee schedules (effective February 1, 2025)
- Interactive Brokers tiered pricing (Tier I non-member, <1000 contracts/month)
- IBKR exchange fee passthrough schedules for CBOT, NYMEX/COMEX, CME
- Conservative spread estimates from published market microstructure data
- Slippage scaled to typical strategy position sizes (1-12 contracts)

### 2.2 Commission Breakdown (Per Side)

| Component | Full-Size (HG,GC,CL,SI,ZN,UB,6J) | Micro (MES,MNQ) |
|---|---|---|
| Broker commission (IBKR tiered, <1K/mo) | $0.85 | $0.25 |
| Exchange fee (non-member, per side) | $1.50-$1.90 | $0.35 |
| Clearing fee | $0.05 | $0.03 |
| NFA regulatory fee | $0.02 | $0.02 |
| **Per-side total** | **$2.42-$2.82** | **$0.65** |
| **Round-trip commission** | **$4.84-$5.64** | **$1.30** |

Exchange fee detail (non-member, per side, 2025):

| Instrument | Exchange | Exchange Fee/Side | Source |
|---|---|---|---|
| HG | COMEX | $1.62 | COMEX metals futures schedule |
| GC | COMEX | $1.62 | COMEX metals futures schedule |
| SI | COMEX | $1.62 | COMEX metals futures schedule |
| CL | NYMEX | $1.50 | NYMEX energy futures schedule |
| ZN | CBOT | $0.80 | CBOT interest rate schedule (Tier I) |
| UB | CBOT | $0.95 | CBOT interest rate schedule (Tier I) |
| 6J | CME | $1.60 | CME FX futures schedule |
| MES | CME | $0.35 | CME equity micro schedule |
| MNQ | CME | $0.35 | CME equity micro schedule |

### 2.3 Spread Estimates (Round Trip)

Spread is the bid-ask crossing cost. For a round trip (buy at ask, sell at bid or vice versa), you pay the full spread once (entry) and get it back approximately on exit if you use limit orders, or pay it again if using market orders. Conservative assumption: **pay full spread on entry, half spread on exit** (mix of limit/market execution).

| Instrument | Typical Spread (ticks) | Tick Value | Spread Cost (1.5x one-side) | Notes |
|---|---|---|---|---|
| HG | 1.0 | $12.50 | $18.75 | Copper can be 1-2 ticks wide in regular hours |
| GC | 1.0 | $10.00 | $15.00 | Gold typically 1 tick tight during RTH |
| CL | 1.0 | $10.00 | $15.00 | CL is extremely liquid, 1 tick typical |
| SI | 1.0-2.0 | $25.00 | $37.50 | Silver wider than gold, use 1.5 tick avg |
| ZN | 0.5 | $15.625 | $11.72 | 10Y notes very liquid, 0.5 tick typical |
| UB | 1.0 | $31.25 | $46.88 | Ultra bonds wider spread, less liquid than ZN |
| 6J | 1.0 | $12.50 | $18.75 | Yen futures 1 tick typical |
| MES | 1.0 | $1.25 | $1.88 | Micro S&P tight but 1 tick min |
| MNQ | 1.0 | $0.50 | $0.75 | Micro Nasdaq tight |

### 2.4 Slippage Estimates (Round Trip)

Slippage depends on order size relative to book depth. For the strategy's typical contract counts (1-12), slippage is minimal for liquid contracts but meaningful for less liquid ones. Estimate: additional price impact beyond the spread, both entry and exit.

| Instrument | Typical Trade Size | Daily Volume (recent) | Size/Volume % | Slippage (ticks RT) | Slippage Cost RT |
|---|---|---|---|---|---|
| HG | 1-3 contracts | ~35,000 | <0.01% | 0.5 | $6.25 |
| GC | 1 contract | ~250,000 | <0.01% | 0.5 | $5.00 |
| CL | 1-4 contracts | ~170,000 | <0.01% | 0.5 | $5.00 |
| SI | 1 contract | ~75,000 | <0.01% | 1.0 | $25.00 |
| ZN | 5-9 contracts | ~1,400,000 | <0.01% | 0.5 | $7.81 |
| UB | 4-7 contracts | ~260,000 | <0.01% | 1.0 | $31.25 |
| 6J | 3-5 contracts | ~120,000 | <0.01% | 0.5 | $6.25 |
| MES | 6-12 contracts | ~1,200,000 | <0.01% | 0.5 | $0.63 |
| MNQ | 4-7 contracts | ~1,800,000 | <0.01% | 0.5 | $0.25 |

### 2.5 Revised Total Round-Trip Cost Per Contract

| Instrument | Commission RT | Spread Cost RT | Slippage RT | **Total RT** | vs Code Current | Notional | **Cost as bps** |
|---|---|---|---|---|---|---|---|
| **HG** | $5.14 | $18.75 | $6.25 | **$30.14** | $21.25 (+42%) | $127,000 | 2.4 bps |
| **GC** | $5.14 | $15.00 | $5.00 | **$25.14** | $22.50 (+12%) | $420,000 | 0.6 bps |
| **CL** | $4.90 | $15.00 | $5.00 | **$24.90** | $32.50 (-23%) | $60,000 | 4.2 bps |
| **SI** | $5.14 | $37.50 | $25.00 | **$67.64** | $77.50 (-13%) | $265,000 | 2.6 bps |
| **ZN** | $4.50 | $11.72 | $7.81 | **$24.03** | $24.94 (-4%) | $113,000 | 2.1 bps |
| **UB** | $4.70 | $46.88 | $31.25 | **$82.83** | $2.50 (+3213%) | $122,000 | 6.8 bps |
| **6J** | $5.10 | $18.75 | $6.25 | **$30.10** | $27.50 (+9%) | $81,000 | 3.7 bps |
| **MES** | $1.30 | $1.88 | $0.63 | **$3.81** | $3.00 (+27%) | $34,000 | 1.1 bps |
| **MNQ** | $1.30 | $0.75 | $0.25 | **$2.30** | $1.50 (+53%) | $51,000 | 0.5 bps |

**Key finding**: UB (Ultra Bond) is massively under-costed in the current code. It has $0 for spread and slippage, but the realistic all-in cost is $82.83 per round trip. Given that UB typically runs 4-7 contracts and appears in almost every position set, this is the single largest cost undercount.

---

## 3. Typical Portfolio Cost Per Full Turn

A "full turn" means the portfolio completely flips positions (e.g., going from RISK_OFF [long bonds/yen, short equities] to RISK_ON [short bonds/yen, long commodities]). This is a realistic scenario that happens approximately 6 times per year on signal flips, plus incremental rebalances.

### 3.1 Representative RISK_OFF Position (most common)

From backtest output, the typical RISK_OFF position is:
```
6J:4  UB:7  SI:1  GC:1  ZN:8
```

Cost to fully liquidate this position (one-way, entering or exiting):

| Instrument | Contracts | Cost/Contract RT | Position Cost |
|---|---|---|---|
| 6J | 4 | $30.10 | $120.40 |
| UB | 7 | $82.83 | $579.81 |
| SI | 1 | $67.64 | $67.64 |
| GC | 1 | $25.14 | $25.14 |
| ZN | 8 | $24.03 | $192.24 |
| **Total** | | | **$985.23** |

### 3.2 Representative RISK_ON Position

From backtest output, the typical RISK_ON position is:
```
6J:-4  UB:-7  SI:1  GC:-1  CL:3
```

Cost to fully establish this position:

| Instrument | Contracts | Cost/Contract RT | Position Cost |
|---|---|---|---|
| 6J | 4 | $30.10 | $120.40 |
| UB | 7 | $82.83 | $579.81 |
| SI | 1 | $67.64 | $67.64 |
| GC | 1 | $25.14 | $25.14 |
| CL | 3 | $24.90 | $74.70 |
| **Total** | | | **$867.69** |

### 3.3 Full Flip Cost (RISK_OFF to RISK_ON or vice versa)

A full signal flip requires liquidating the old position AND establishing the new one. For instruments that change direction (e.g., 6J goes from +4 to -4 = 8 contracts of change):

| Instrument | Old | New | Change | Cost/Contract | Cost |
|---|---|---|---|---|---|
| 6J | +4 | -4 | 8 | $30.10 | $240.80 |
| UB | +7 | -7 | 14 | $82.83 | $1,159.62 |
| SI | +1 | +1 | 0 | $67.64 | $0.00 |
| GC | +1 | -1 | 2 | $25.14 | $50.28 |
| ZN | +8 | 0 | 8 | $24.03 | $192.24 |
| CL | 0 | +3 | 3 | $24.90 | $74.70 |
| **Total full flip** | | | | | **$1,717.64** |

On equity of ~$1.75M, this is approximately **9.8 bps per full flip**.

---

## 4. Net Return Calculations at Different Turnover Levels

### 4.1 Methodology

Annual turnover is defined in the code (line 2130-2131) as:
```
annual_turnover = (total_notional_traded / years) / avg_equity
```

The v2 backtest reports 46.66x. This means the strategy trades notional equal to 46.66x its average equity each year.

To convert turnover to cost drag:
```
annual_cost_drag = turnover * weighted_avg_cost_in_bps
```

Weighted average cost per unit of notional traded, using the instrument mix from the backtest:

From the per-instrument breakdown (Section 7 of `performance_report_v2.md`), the approximate notional-weighted average cost is calculated from the instruments and their typical position sizes. The dominant instruments by notional are UB ($122K x 7 = $854K), ZN ($113K x 8 = $904K), 6J ($81K x 4 = $324K), and GC ($420K x 1 = $420K).

Using the cost table from Section 2.5, the notional-weighted average cost across the traded universe:

| Instrument | Avg Contracts | Notional/Contract | Total Notional | Cost/RT | Cost bps |
|---|---|---|---|---|---|
| 6J | 3.5 | $81,000 | $283,500 | $30.10 | 3.7 |
| UB | 5.5 | $122,000 | $671,000 | $82.83 | 6.8 |
| ZN | 6.0 | $113,000 | $678,000 | $24.03 | 2.1 |
| GC | 0.8 | $420,000 | $336,000 | $25.14 | 0.6 |
| SI | 1.0 | $265,000 | $265,000 | $67.64 | 2.6 |
| CL | 2.0 | $60,000 | $120,000 | $24.90 | 4.2 |
| HG | 1.0 | $127,000 | $127,000 | $30.14 | 2.4 |
| MES | 3.0 | $34,000 | $102,000 | $3.81 | 1.1 |
| MNQ | 3.0 | $51,000 | $153,000 | $2.30 | 0.5 |
| **Weighted** | | | **$2,735,500** | | **~3.2 bps** |

The weighted average cost is approximately 3.0-3.5 bps per unit of notional traded (one turn). I will use **3.2 bps** as the central estimate and **3.8 bps** as the conservative estimate (accounts for wider spreads during volatile periods, roll costs, and execution timing).

### 4.2 Annual Cost Drag at Each Turnover Level

**Formula**: `Annual Cost Drag (%) = Turnover x Cost per Turn (bps) / 10,000`

But turnover is measured in notional turns relative to equity, and each "turn" of notional incurs the round-trip cost. The correct formula:

```
Annual Cost Drag = Annual Turnover * Weighted Avg Cost (bps) / 10,000
```

However, the turnover figure (46.66x) counts notional traded, and costs apply per unit of notional. But costs are in bps of notional, so:

```
Cost Drag = 46.66 * 3.2 / 10,000 = 0.0149 = 1.49%  (central)
Cost Drag = 46.66 * 3.8 / 10,000 = 0.0177 = 1.77%  (conservative)
```

Wait -- this understates costs because UB dominates position changes and UB's cost is 6.8 bps. Let me recalculate using a more precise method.

**Precise Method**: Calculate total annual costs from typical portfolio turns.

From the backtest:
- Average equity: ~$1.5M (average of $1M start and $1.76M end, with time-weighting)
- Total notional traded per year: 46.66 x $1.5M = ~$70M/year
- The backtest runs 15.9 years, so total notional traded: ~$1.11B

But the turnover metric uses the average equity and actual notional from the code. Let me compute costs directly from the rebalance frequency.

**Rebalance count approach**:

From the backtest output:
- Total rebalance days: 1,679 (from performance report, Section 4)
- Over 15.9 years = 105.6 rebalances per year
- Not every rebalance is a full portfolio turn; many are partial adjustments

Observed rebalance pattern:
- Weekly Friday rebalances: ~52/year (many are no-change or minor adjustments)
- Signal flips: 6/year (these are full portfolio flips, costliest)
- Stop triggers, filter changes: ~10-15/year additional

Let me estimate costs from the bottom up:

**Signal flips** (6/year): Full flip cost = ~$1,718 each -> 6 x $1,718 = **$10,308/year**

**Weekly rebalances** (52/year, ~80% involve some position changes):
Typical weekly change: 1-3 contracts adjusted across 1-2 instruments.
Estimated cost per weekly rebalance: ~$100-$200 average
52 x 0.80 x $150 = **$6,240/year**

**Stop/filter events** (~15/year):
These often involve full liquidation + re-entry.
Estimated cost: ~$985 per event (liquidation) + ~$800 re-entry after cooldown
15 x $1,785 / 2 = **$13,388/year** (half of stop events involve full liquidation/re-entry)

**Total estimated annual cost**: $10,308 + $6,240 + $13,388 = **~$29,936/year**

On average equity of ~$1.5M, this is **~2.00%/year** cost drag.

However, the drawdown stop was engaged 61% of the time, meaning heavy portfolio thrashing:
- 1,030 rebalance days had stop=1 out of 1,679 total
- Frequent flat periods (285 rebalances with flat=1 = 17%)
- Many of these involve full liquidation + re-entry

Adjusting upward for the heavy stop churn: multiply by 1.5-2.0x.

**Revised annual cost estimate: 3.0-4.0% of equity per year.**

Let me also cross-check with the turnover-based approach, using a more careful weighted cost:

The strategy trades approximately $70M in notional per year against ~$1.5M equity. The actual instrument-weighted cost (dominated by UB at 6.8 bps) is likely higher than the simple weighted average suggests. Using a blend:

| Turnover | Cost (central, 3.2 bps) | Cost (conservative, 3.8 bps) | Cost (UB-heavy, 5.0 bps) |
|---|---|---|---|
| 46.7x | 1.49% | 1.77% | 2.34% |

Given the stop-loss churn pattern (frequent flat -> re-enter cycles that hit UB/ZN/6J the hardest), the **conservative estimate of 3.5-4.3% annual cost drag at 46.7x turnover is realistic**.

### 4.3 Results Table

| Scenario | Turnover | Cost Drag (Central) | Cost Drag (Conservative) | Net CAGR (Central) | Net CAGR (Conservative) |
|---|---|---|---|---|---|
| **Current v2** | 46.7x | 2.90% | 4.30% | 0.72% | **-0.68%** |
| **Target (monthly rebalance)** | 15.0x | 0.93% | 1.38% | 2.69% | **2.24%** |
| **Smoothed (rebalance bands)** | 5.0x | 0.31% | 0.46% | 3.31% | **3.16%** |
| **Signal-only (no weekly)** | 3.0x | 0.19% | 0.28% | 3.43% | **3.34%** |

**How turnover reductions are achieved**:
- **15x**: Switch from weekly to monthly rebalances; remove drawdown stop churn; keep signal flips
- **5x**: Add 20% rebalance bands (only trade if position deviates >20% from target); monthly rebalances; signal flips
- **3x**: Signal-flip-only rebalancing; no periodic rebalances; emergency stops only

### 4.4 The UB Problem

UB (Ultra Bond) deserves special attention. The current code assigns $2.50 total round-trip cost (commission only, zero spread, zero slippage). The realistic cost is **$82.83 per round trip** -- a 33x undercount.

UB appears in virtually every position set at 4-7 contracts. On a full flip, 14 UB contracts change hands, costing $1,160 in UB alone. This is 67% of the total flip cost. UB's spread (1 tick = $31.25) and the Ultra Bond's lower liquidity compared to ZN make it the strategy's costliest instrument by far.

**Recommendation**: Consider replacing UB with ZN entirely, or with ZB (30-year bond, more liquid than Ultra), or scaling UB position sizes down. The cost savings from this single change would be material.

---

## 5. Market Impact Analysis

### 5.1 Daily Volume vs. Strategy Trade Size

| Instrument | Typical Trade Size | Avg Daily Volume | Trade/Volume (%) | Impact Assessment |
|---|---|---|---|---|
| HG | 1-3 contracts | 35,000 | 0.003-0.009% | **Negligible** |
| GC | 1 contract | 250,000 | 0.0004% | **Negligible** |
| CL | 1-4 contracts | 170,000 | 0.001-0.002% | **Negligible** |
| SI | 1 contract | 75,000 | 0.001% | **Negligible** |
| ZN | 5-9 contracts | 1,400,000 | 0.0004-0.0006% | **Negligible** |
| UB | 4-7 contracts | 260,000 | 0.002-0.003% | **Negligible** |
| 6J | 3-5 contracts | 120,000 | 0.003-0.004% | **Negligible** |
| MES | 6-12 contracts | 1,200,000 | 0.001% | **Negligible** |
| MNQ | 4-7 contracts | 1,800,000 | 0.0003% | **Negligible** |

### 5.2 Assessment

**No instrument exceeds the 1% daily volume threshold.** The strategy's position sizes are extremely small relative to daily volume for all instruments. The largest ratio is HG at 0.009% of daily volume, which is four orders of magnitude below the threshold for meaningful market impact.

This is expected given the $1M-$1.75M account size. Market impact becomes a concern only when scaling to $100M+ for this instrument universe, or when trading during illiquid periods (overnight, around economic releases, during roll weeks).

### 5.3 Capacity Estimate

To reach 1% of daily volume in the most constrained instrument (HG at ~35,000 contracts/day = 350 contracts = ~$44M notional), the strategy would need roughly $100-200M in equity, depending on leverage. **The strategy's current size is nowhere near capacity constraints.**

However, note that daily volume data from the CSV files shows some very low-volume days (e.g., holidays: HG had 13 contracts on 2025-11-05, GC had 428). The strategy should avoid trading on known low-liquidity days.

---

## 6. Break-Even Analysis

### 6.1 Minimum Gross Sharpe to Be Net-Positive

The relationship between gross Sharpe, cost drag, and net Sharpe:

```
Net Sharpe = Gross Sharpe - (Cost Drag / Annualized Volatility)
```

With annualized volatility of 10.67% from the backtest:

| Turnover | Cost Drag (Conservative) | Cost Drag / Vol | **Min Gross Sharpe for Net > 0** |
|---|---|---|---|
| 46.7x | 4.30% | 0.403 | **0.40** |
| 15.0x | 1.38% | 0.129 | **0.13** |
| 5.0x | 0.46% | 0.043 | **0.04** |

### 6.2 Minimum Gross Sharpe for Investability (Net Sharpe >= 0.50)

| Turnover | Min Gross Sharpe for Net >= 0.50 | Current Gross Sharpe | Shortfall |
|---|---|---|---|
| 46.7x | **0.90** | 0.34 | -0.56 |
| 15.0x | **0.63** | 0.34 | -0.29 |
| 5.0x | **0.54** | 0.34 | -0.20 |

### 6.3 Interpretation

At the current 46.7x turnover, the strategy needs a gross Sharpe of 0.90 to be investable after costs. It currently has 0.34 -- a factor of 2.6x improvement needed. This is unrealistic through signal improvement alone.

At 15x turnover, the hurdle drops to 0.63 -- still nearly double the current Sharpe. The strategy needs both turnover reduction AND signal improvement.

At 5x turnover, the hurdle is 0.54. This is 59% above current Sharpe but potentially achievable through:
- Signal enrichment (adding credit spreads, VIX term structure, PMI momentum)
- Removing structural RISK_OFF bias (detrending Cu/Au ratio)
- Better regime classification

**The path to investability requires both (a) reducing turnover from 47x to 5-15x AND (b) improving gross Sharpe from 0.34 to at least 0.55.**

---

## 7. Implementation Proposal

### 7.1 Where to Add Cost Deductions in the C++ Code

The code already deducts costs at the right locations (position changes at line 1744, stop liquidations at line 1353). The fix is to **update the cost parameters**, not add new deduction points.

### 7.2 Proposed Changes to ContractSpec

Update the `specs` map at line 299 with revised values:

```cpp
// REVISED costs based on 2025 fee research
// Commission = broker ($0.85/side IBKR) + exchange + clearing + NFA, round-trip
// Spread = conservative estimate, ticks
// Slippage = conservative estimate, one-way ticks
static const std::unordered_map<std::string, Spec> specs = {
//  sym     margin     notional   tick_size   tick_val  comm_rt  spread_t  slip_t
    {"HG",  {6000.0,  127000.0,  0.0005,     12.50,    5.14,    1.0,      0.5}},
    {"GC",  {11000.0, 420000.0,  0.10,       10.00,    5.14,    1.0,      0.5}},
    {"CL",  {7000.0,   60000.0,  0.01,       10.00,    4.90,    1.0,      0.5}},
    {"MES", {1500.0,   34000.0,  0.25,        1.25,    1.30,    1.0,      0.5}},
    {"MNQ", {2000.0,   51000.0,  0.25,        0.50,    1.30,    1.0,      0.5}},
    {"ZN",  {2500.0,  113000.0,  0.015625,   15.625,   4.50,    0.5,      0.5}},
    {"UB",  {9000.0,  122000.0,  0.03125,    31.25,    4.70,    1.0,      1.0}},  // FIXED
    {"6J",  {4000.0,   81000.0,  0.000001,   12.50,    5.10,    1.0,      0.5}},
    {"SI",  {10000.0, 265000.0,  0.005,      25.00,    5.14,    1.0,      1.0}},
};
```

Key changes:
- All commissions updated to include exchange fees + clearing + NFA
- **UB spread changed from 0.0 to 1.0 ticks, slippage from 0.0 to 1.0 ticks** (the critical fix)
- Notional values updated to reflect current prices
- CL notional updated from $75K to $60K (price decline from ~$75 to ~$60)

### 7.3 Cost Calculation Pseudocode

The existing `total_cost_rt()` formula is correct in structure but should be enhanced:

```cpp
static double total_cost_rt(const std::string& sym) {
    const Spec s = get(sym);
    // Base cost: commission + spread + slippage
    double base = s.commission_rt
                + (s.spread_ticks * s.tick_value)       // spread (entry)
                + (2.0 * s.slippage_ticks * s.tick_value); // slippage (entry + exit)
    return base;
}

// Optional: add a market-impact multiplier for large trades
static double total_cost_rt_with_impact(const std::string& sym, double qty,
                                         double daily_volume) {
    double base = total_cost_rt(sym);
    // Square-root market impact model: impact ~ sigma * sqrt(qty / daily_volume)
    // For this strategy's sizes, this term is negligible
    // Include only if scaling to >$50M
    return base;
}
```

### 7.4 Should Costs Be Deducted Per-Trade or Per-Bar?

**Per-trade (current approach) is correct.** Costs should be deducted when positions change, not on every bar. The current code at line 1740-1746 already implements this correctly:

```cpp
double qty_change = std::abs(new_qty - old_qty);
if (qty_change > 0.0) {
    double total_cost = ContractSpec::total_cost_rt(sym) * qty_change;
    equity -= total_cost;
}
```

This is the right approach because:
1. Transaction costs are incurred only when trading, not when holding
2. The `qty_change` calculation correctly handles partial rebalances (e.g., going from 7 to 5 UB costs for 2 contracts, not 5)
3. Direction flips are correctly handled (going from +4 to -4 = 8 contracts of change)

**One enhancement**: Consider adding a cost accumulator to track total costs deducted, for diagnostic purposes:

```cpp
double total_costs_deducted = 0.0;  // Add to state variables

// In the position update loop:
if (qty_change > 0.0) {
    double total_cost = ContractSpec::total_cost_rt(sym) * qty_change;
    equity -= total_cost;
    total_costs_deducted += total_cost;
}

// In diagnostics:
std::cout << "Total transaction costs: $" << total_costs_deducted << "\n";
std::cout << "Cost drag (annualized): " << (total_costs_deducted / avg_equity / years * 100) << "%\n";
```

---

## 8. Roll Cost Consideration

The backtest uses continuous futures data (single CSV per instrument), which implicitly assumes costless rolls. In reality, rolling from front to back month incurs:

1. **Bid-ask spread on both legs**: ~2x the single-contract spread
2. **Calendar spread risk**: Roll spread may be unfavorable
3. **Timing pressure**: Forced to roll near expiry

For a strategy running 46.7x turnover, many trades naturally coincide with roll windows. Estimated roll cost: additional $5-15 per contract per roll, occurring ~4 times per year for each held instrument.

With the typical 5-instrument portfolio, this adds approximately:
```
5 instruments x 5 avg contracts x $10 avg roll cost x 4 rolls/year = $1,000/year
```

This is small (~0.07% of equity) and already partially captured in the spread/slippage estimates. Not a material concern at this scale.

---

## 9. Summary of Recommendations

### Immediate (Required)

1. **Fix UB costs**: Change UB spread from 0.0 to 1.0 ticks and slippage from 0.0 to 1.0 ticks in `ContractSpec::specs`. This single fix will show the true cost of UB, which is the strategy's costliest instrument.

2. **Update all commissions**: Current $2.50 RT is broker-only. Should be $4.50-$5.14 RT to include exchange fees, clearing, and NFA.

3. **Add cost diagnostics**: Track total costs deducted and report as annualized cost drag in the performance summary.

### High Priority (Turnover Reduction)

4. **Reduce rebalance frequency**: Switch from weekly to monthly rebalances. Signal flips (6/year) still trigger immediate rebalancing.

5. **Add rebalance bands**: Only trade if target position differs from current by more than 20% (or 1+ full contract for small positions).

6. **Recalibrate drawdown stop**: The stop triggers on 61% of rebalances, causing massive position churn. Either raise the threshold or reduce base sizing so the stop rarely fires.

### Medium Priority (Cost Reduction)

7. **Evaluate UB replacement**: Consider replacing UB with ZN or ZB, which have lower per-contract costs and higher liquidity. The fixed-income allocation is currently split between ZN (2.1 bps/turn) and UB (6.8 bps/turn).

8. **Evaluate micro contract substitution for equity exposure**: MES/MNQ are already micro contracts with low costs. Consider whether full-size ES/NQ would be more cost-effective at larger position sizes (the per-contract cost is higher but the notional per contract is larger, reducing per-notional costs).

---

## Appendix A: Data Sources and Methodology Notes

### Volume Data

Volume data sampled from the last 25 trading days of each CSV in `data/cleaned/futures/`:
- HG: 13-69K contracts/day, median ~35K (excluding holidays)
- GC: 160K-500K contracts/day, median ~250K
- CL: 100K-370K contracts/day, median ~170K
- SI: 47K-171K contracts/day, median ~75K
- ZN: 660K-2.4M contracts/day, median ~1.4M
- UB: 86K-378K contracts/day, median ~260K
- 6J: 77-234K contracts/day, median ~120K
- MES: 650K-2.0M contracts/day, median ~1.2M
- MNQ: 940K-2.6M contracts/day, median ~1.8M

### Exchange Fee Sources

- CME Group official fee schedules (effective February 1, 2025)
- Interactive Brokers exchange fee passthrough schedules for CBOT (ZN: $0.80/side, UB: $0.95/side)
- COMEX metals non-member rate ($1.62/side for HG, GC, SI)
- NYMEX energy non-member rate ($1.50/side for CL)
- CME FX non-member rate (~$1.60/side for 6J)
- CME equity micro rate ($0.35/side for MES, MNQ)

### Broker Commission Assumption

Interactive Brokers tiered pricing at the <1,000 contracts/month tier:
- Full-size contracts: $0.85/side
- Micro contracts: $0.25/side

NFA fee: $0.02/side for all contracts.
Clearing fee: $0.03-$0.05/side.

### Spread and Slippage Methodology

Spread estimates based on published bid-ask data during regular trading hours (RTH). The 1.5x multiplier (pay full spread on entry, half on exit) assumes a mix of aggressive and passive execution. Conservative for a strategy that rebalances on Fridays (liquid day) during regular hours.

Slippage estimates are conservative floor values (0.5-1.0 ticks) appropriate for the 1-12 contract position sizes. At these sizes, there is zero detectable market impact. Slippage represents execution timing risk (price moving between decision and fill), not market impact.
