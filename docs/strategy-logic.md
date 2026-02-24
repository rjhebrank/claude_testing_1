# Copper-Gold Ratio Economic Regime Strategy v2.0 -- Strategy Logic Document

**Source**: `/home/riley/Code/claude_testing_1/copper_gold_strategy.cpp` (1870 lines)
**Analysis date**: 2026-02-24

---

## Table of Contents

1. [Core Trading Thesis](#1-core-trading-thesis)
2. [Signal Generation Logic](#2-signal-generation-logic)
3. [Entry Rules](#3-entry-rules)
4. [Exit Rules](#4-exit-rules)
5. [Position Sizing](#5-position-sizing)
6. [Risk Management](#6-risk-management)
7. [Parameters & Thresholds](#7-parameters--thresholds)
8. [Execution Logic](#8-execution-logic)
9. [Audit Notes & Concerns](#9-audit-notes--concerns)

---

## 1. Core Trading Thesis

The strategy uses the **copper-to-gold notional ratio** as a macro regime indicator to trade a multi-asset futures portfolio across equities, commodities, fixed income, and FX.

**Fundamental premise**: Copper is a cyclical industrial metal whose demand reflects real economic activity. Gold is a safe-haven asset that rises during risk aversion, monetary easing, and inflation fears. The ratio of copper notional value to gold notional value is therefore a barometer of the global growth/risk-on vs. contraction/risk-off balance.

- **Rising Cu/Au ratio** --> Economic expansion, risk appetite increasing --> Go long risk assets (equities, copper, oil), short safe havens (gold, treasuries, yen).
- **Falling Cu/Au ratio** --> Economic contraction, risk aversion increasing --> Short risk assets, long safe havens.

The strategy layers three signal tiers:

1. **Layer 1**: Cu/Gold ratio momentum and mean-reversion signals --> produces a `MacroTilt` (RISK_ON / RISK_OFF / NEUTRAL).
2. **Layer 2**: Macro regime classifier (growth, inflation, liquidity) --> produces a `Regime` that modifies trade expressions and sizing.
3. **Layer 3**: DXY (US Dollar Index) filter --> confirms or discounts the primary signal.

Additional overlays include a China CLI filter, BOJ intervention detector, safe-haven gold override, and correlation spike dampener.

**Traded instruments** (9 futures):

| Symbol | Asset | Point Value | Asset Class |
|--------|-------|-------------|-------------|
| HG | Copper | $250/cent | Commodities |
| GC | Gold | $100/point | Commodities |
| CL | Crude Oil | $1,000/point | Commodities |
| SI | Silver | $5,000/point | Commodities |
| ZN | 10Y T-Note | $1,000/point | Fixed Income |
| UB | Ultra Bond | $1,000/point | Fixed Income |
| 6J | Japanese Yen | $12.50/pip | FX |
| MES | Micro E-mini S&P | $5/point | Equity Index |
| MNQ | Micro E-mini Nasdaq | $2/point | Equity Index |

---

## 2. Signal Generation Logic

### 2.1 Layer 1: Cu/Gold Ratio Signal

#### Ratio Construction (lines 577-586)

The ratio uses **notional normalization**, not a raw price ratio:

```cpp
double cu_notional = hg[i] * 25000.0;   // HG price * contract multiplier
double au_notional = gc[i] * 100.0;      // GC price * contract multiplier
ratio[i] = cu_notional / au_notional;
```

Expected range: approximately [0.2, 1.2].

**NOTE**: HG prices are in dollars per pound (the code comment on line 94 says "$/lb"). The multiplier 25,000 represents the HG contract size (25,000 lbs). GC multiplier is 100 (troy oz per contract). This produces a dimensionless notional ratio, not a price ratio.

#### Sub-signals

Three sub-signals are computed and combined:

**A. Rate-of-Change (ROC) momentum** (lines 723-728):

```
ROC_n = (ratio[i] / ratio[i - n]) - 1.0
```

Computed for windows 10, 20, and 60 days. Only ROC_20 feeds the composite directly (as its sign).

**B. Moving Average Crossover** (lines 730-732):

```
signal_ma = +1.0 if SMA(10) > SMA(50), else -1.0
```

A binary directional signal based on fast/slow MA crossover of the ratio.

**C. Z-Score Mean Reversion** (lines 734-740):

```
zscore = (ratio[i] - SMA(120)) / StdDev(120)
signal_z = +1.0 if zscore > 0.5
signal_z = -1.0 if zscore < -0.5
signal_z =  0.0 otherwise
```

The z-score uses a 120-day lookback with a threshold of 0.5 standard deviations.

#### Composite Signal (lines 742-746)

```
composite = w1 * sign(ROC_20) + w2 * signal_ma + w3 * signal_z
```

Where `w1 = 0.33`, `w2 = 0.33`, `w3 = 0.34`. All weights are approximately equal.

The composite is a weighted vote of three binary-ish signals, producing a value in [-1, +1].

#### MacroTilt Determination (lines 748-772)

```
raw_tilt = RISK_ON   if composite > 0.0
raw_tilt = RISK_OFF  if composite < 0.0
raw_tilt = NEUTRAL   if composite == 0.0
```

**Note**: `composite_thresh` defaults to 0.0, meaning ANY positive composite triggers RISK_ON. There is no dead zone -- the threshold is effectively zero.

**Minimum holding period filter** (lines 755-772): The raw tilt must persist for `min_hold_days` (default: 5) consecutive days before the confirmed `macro_tilt` flips. This is a debounce mechanism implemented as a pending-count state machine:

- If raw tilt differs from confirmed tilt, a pending counter increments.
- If the pending tilt is the same for 5 consecutive days, the confirmed tilt changes.
- If the raw tilt reverts before 5 days, the pending counter resets.

#### Signal Flip Tracking (lines 780-789)

Signal flips in a trailing 252-day window are counted using a deque. The code tracks total flips per year with a documented target of 8-12 flips/year max. A kill criterion fires if flips exceed 20/year.

### 2.2 Layer 2: Regime Classifier

The regime classifier categorizes the macro environment into one of five states:

| Regime | Condition | Priority |
|--------|-----------|----------|
| LIQUIDITY_SHOCK | `liquidity < -1.5` | 1 (highest) |
| INFLATION_SHOCK | `inflation > 0.10` AND `growth < 0.5` | 2 |
| GROWTH_POSITIVE | `growth > 0.5` | 3 |
| GROWTH_NEGATIVE | `growth < -0.5` | 4 |
| NEUTRAL | none of the above | 5 (lowest) |

**Evaluation is short-circuit / waterfall**: liquidity shock takes priority over all others. The `else if` chain means inflation shock is only checked when liquidity is normal.

#### Growth Signal (lines 594-598)

```
growth = SPX 60-day momentum (%)
       = ((SPX[i] / SPX[i-60]) - 1.0) * 100.0
```

Uses S&P 500 price series. Units are percentage points (e.g., +5.0 means SPX is up 5% over 60 days).

#### Inflation Signal (lines 601-606)

```
inflation = breakeven_10y[i] - breakeven_10y[i - 20]
```

This is the 20-day absolute change in 10-year breakeven inflation rate. Units are percentage points of yield (e.g., 0.10 = 10 basis points).

**CRITICAL OBSERVATION**: The inflation shock threshold is `0.10` (line 855). If breakeven data is in percentage points (e.g., 2.50 = 2.50%), then a 20-day change of 0.10 is only 10 basis points. This fires extremely frequently -- the code's own diagnostic section (lines 1652-1659) explicitly flags this concern: "threshold 0.10 = 10bp change over 20d (fires easily)". The document apparently intended 100bp, not 10bp. This is likely a units mismatch bug.

#### Liquidity Score (lines 804-836)

Composite liquidity indicator is the average of three z-scored components:

```
vix_component = -1 * (VIX_percentile_60d * 6.0 - 3.0)
hy_component  = -1 * HY_spread_zscore_60d
fbs_component = Fed_BS_YoY_growth * 10.0

liquidity = (vix_component + hy_component + fbs_component) / 3.0
```

Where:
- **VIX percentile**: rank of current VIX within a 60-day rolling window, rescaled to [-3, +3] range, then inverted (high VIX = bad liquidity).
- **HY spread z-score**: 60-day rolling z-score of high-yield credit spreads, inverted (widening spreads = bad liquidity).
- **Fed balance sheet YoY growth**: year-over-year change in Fed balance sheet, scaled by 10x to match [-3, +3] range of other components.

Liquidity shock triggers at `liquidity < -1.5`.

**CONCERN**: The scaling factors (6.0, 3.0, 10.0) are hardcoded magic numbers. The VIX percentile is rescaled via `percentile * 6.0 - 3.0`, which maps [0,1] to [-3,+3]. The Fed BS growth scaling of 10x assumes typical YoY growth is in the range +/-30% -- this is regime-dependent and may not hold across all periods.

#### Real Rate Signals (lines 608-621)

```
real_rate     = treasury_10y - breakeven_10y
rr_chg        = real_rate[i] - real_rate[i - 20]      (20-day change)
rr_zscore     = rolling_zscore(real_rate, 120)         (120-day z-score)
```

These are computed but **not directly used in the regime classifier**. They are stored in `DailySignal` for output/monitoring but have no effect on trading decisions in the current code.

### 2.3 Layer 3: DXY Filter

#### DXY Trend (lines 885-891)

```
STRONG  if DXY > SMA(50) AND SMA(50) > SMA(200)
WEAK    if DXY < SMA(50) AND SMA(50) < SMA(200)
NEUTRAL otherwise
```

**NOTE**: `dxy_trend` is computed but **never used** in any trading decision. It is stored in the signal struct but has no downstream effect.

#### DXY Momentum (lines 893-895)

```
dxy_mom = (DXY[i] / DXY[i - 20]) - 1.0
```

20-day DXY return (as a fraction, not percentage).

#### DXY Filter Logic (lines 897-920)

The filter cross-references DXY momentum direction with the current macro tilt:

| DXY Momentum | MacroTilt | DXYFilter | Interpretation |
|-------------|-----------|-----------|----------------|
| > +3% | RISK_ON | SUSPECT | May be USD squeeze, not genuine growth |
| > +3% | RISK_OFF | CONFIRMED | Confirmed risk-off + USD strength |
| < -3% | RISK_ON | CONFIRMED | Confirmed risk-on + USD weakness |
| < -3% | RISK_OFF | SUSPECT | May be inflation/gold bid, not true risk-off |
| within +/-3% | any | NEUTRAL | Trust Cu/Gold signal at full size |

When `DXYFilter == SUSPECT`, position size is halved (via `size_mult *= 0.5`).

### 2.4 Auxiliary Filters

#### Safe-Haven Gold Override (lines 923-941)

Prevents shorting gold when all three conditions hold simultaneously:

```
1. VIX > 90th percentile (60-day window)
2. Gold daily return > +1.5%
3. S&P 500 daily return < -1.5%
```

When active, `skip_gold_short = true`, and any gold short position is zeroed.

#### China CLI Filter (lines 944-948)

```
china_adj = 0.7   if (china_cli[i] - SMA_65(china_cli)) < -2.0
china_adj = 1.0   otherwise
```

When China's leading indicator is more than 2.0 below its 65-day average, copper exposure is reduced by 30% (multiplier of 0.7). This reflects that weak Chinese demand undermines the copper demand thesis.

The China adjustment is applied specifically to HG (copper) position sizing via `contracts_for("HG", 1.0) * china_adj`.

#### BOJ Intervention Filter (lines 951-955)

```
boj_intervention = true  if |JPY daily return| > 2%
```

When triggered, 6J (Yen futures) position is halved (`boj_factor = 0.5`).

#### Correlation Spike Detector (lines 958-960)

```
corr_spike = true  if avg_pairwise_correlation(all 9 instruments, 20-day) > 0.70
```

When active, `size_mult *= 0.5` -- all positions are halved because high cross-asset correlation signals a regime break where diversification fails.

The average pairwise correlation is computed across all 9 instruments using log returns over a 20-day rolling window (lines 212-246).

---

## 3. Entry Rules

### 3.1 Rebalance Triggers

Positions are **only** adjusted on rebalance days. A rebalance occurs when ANY of the following is true (lines 1125-1126):

1. **Friday** (weekly calendar rebalance)
2. **Tilt change** (confirmed `macro_tilt` just flipped)
3. **Regime change** (regime classifier changed state, confirmed for 3+ consecutive days)
4. **Filter trigger** (DXY filter newly became SUSPECT)
5. **Stop triggered** (drawdown warning or drawdown stop activated)
6. **Force rebalance** (no positions held but `size_mult > 0` -- prevents getting stuck flat)

Regime changes require a 3-day confirmation period (lines 1106-1119), analogous to the 5-day tilt debounce.

### 3.2 Trade Expressions by Tilt + Regime

The strategy has **6 distinct trade expression tables**:

#### RISK_ON + Default (non-inflation):
| Instrument | Direction | Notes |
|-----------|-----------|-------|
| MES | Long | |
| MNQ | Long | |
| HG | Long | * china_adj |
| CL | Long | |
| SI | Long | * vol_adj (ATR-based) |
| GC | Short | Zeroed if skip_gold_short |
| ZN | Short | |
| UB | Short | |
| 6J | Short | * boj_factor |

#### RISK_ON + INFLATION_SHOCK:
| Instrument | Direction | Notes |
|-----------|-----------|-------|
| MES | **Flat** | Equities removed |
| MNQ | **Flat** | Equities removed |
| HG | Long | * china_adj |
| CL | Long | |
| SI | Long | * vol_adj |
| GC | Short | Zeroed if skip_gold_short |
| ZN | Short | |
| UB | Short | |
| 6J | Short | * boj_factor |

Rationale: During inflation shocks with risk-on signal, the strategy drops equity exposure (inflation hurts P/E multiples) but keeps commodity longs and bond shorts.

#### RISK_OFF + Default (non-inflation):
| Instrument | Direction | Notes |
|-----------|-----------|-------|
| MES | Short | |
| MNQ | Short | |
| HG | Short | |
| CL | Short | |
| SI | Long | Safe haven |
| GC | Long | Safe haven |
| ZN | Long | Flight to quality |
| UB | Long | Flight to quality |
| 6J | Long | * boj_factor |

#### RISK_OFF + INFLATION_SHOCK:
| Instrument | Direction | Notes |
|-----------|-----------|-------|
| MES | Short (half size, -0.5) | Reduced |
| MNQ | Short (half size, -0.5) | Reduced |
| HG | **Flat** | Copper ambiguous in stagflation |
| CL | **Flat** | Oil ambiguous in stagflation |
| SI | Long | * vol_adj |
| GC | Long | Gold benefits from inflation + risk-off |
| ZN | Short | Rising rates in inflation |
| UB | Short | Rising rates in inflation |
| 6J | **Flat** | |

This is the "stagflation" book: long precious metals, short bonds, reduced short equities.

**CONCERN**: In RISK_OFF + INFLATION_SHOCK, ZN and UB are **short** (expecting rising rates from inflation), which contradicts the typical RISK_OFF playbook (long bonds for safety). This is internally consistent with the inflation thesis but creates a scenario where the strategy is short equities AND short bonds simultaneously -- a double-short that only works if inflation is genuinely accelerating.

#### NEUTRAL Tilt:
All positions zeroed. The strategy goes completely flat.

### 3.3 Silver Volatility Adjustment

Silver position size is scaled by a gold/silver ATR ratio (lines 1219-1225):

```cpp
double gc_dollar_atr = gc_atr[i] * 100.0;     // GC point value
double si_dollar_atr = si_atr[i] * 5000.0;    // SI point value
si_adj = gc_dollar_atr / si_dollar_atr;
```

This vol-normalizes silver to have similar dollar risk per contract as gold. If silver ATR data is unavailable, SI position is zeroed entirely.

---

## 4. Exit Rules

### 4.1 Position-Level ATR Stop Loss (lines 1003-1043)

Each position is checked daily for stop-loss regardless of rebalance schedule:

```
dollar_atr = ATR(20) * |position_qty| * point_value
position_dollar_loss = -(qty * (current_price - entry_price) * point_value)

EXIT if position_dollar_loss > 2.0 * dollar_atr
```

This is a **2x ATR trailing-from-entry stop**. When triggered:
- Position is zeroed immediately.
- Entry price is cleared.
- The symbol is added to `stopped_out_today` set, preventing re-entry on the same day (line 1408).

**NOTE**: This uses dollar ATR scaled by position size, not per-contract ATR. A 10-contract position has 10x the ATR threshold of a 1-contract position. The stop is proportional to total position risk.

**CONCERN**: The ATR stop uses `entry_price` but there is no trailing logic -- it is a fixed stop from entry. This is not a "trailing stop" despite common usage of ATR stops. The stop distance widens with position size, which may be undesirable.

### 4.2 Portfolio-Level Drawdown Stop (lines 1064-1076)

```
drawdown = (peak_equity - equity) / peak_equity

if drawdown > 15%: size_mult = 0.0 (all positions closed on next rebalance)
if drawdown > 10%: size_mult *= 0.5 (positions halved)
```

When drawdown stop is active and all positions are zero, peak equity is reset:
```cpp
if (dd_stop && all_positions_zero(positions)) {
    peak_equity = equity;
}
```

This allows the strategy to resume trading after a drawdown-triggered flat period once it is fully unwound.

### 4.3 Signal Reversal Exit

There is no explicit exit signal. Exits happen implicitly when:
- MacroTilt flips (e.g., RISK_ON to RISK_OFF), causing all positions to reverse direction at the next rebalance.
- MacroTilt goes NEUTRAL, causing all positions to be zeroed.
- size_mult drops to 0 (e.g., LIQUIDITY_SHOCK regime), zeroing all positions.

### 4.4 Time-Based Exit

There is no explicit time-based exit. The minimum holding period (5-day debounce on tilt flips, 3-day debounce on regime changes) serves as an indirect minimum hold time but does not guarantee any maximum hold duration.

---

## 5. Position Sizing

The strategy has two modes controlled by `use_fixed_positions`:

### 5.1 Full Position Sizing Mode (default)

The core sizing formula (lines 1204-1216):

```cpp
double w = ASSET_WEIGHTS[asset_class(sym)];          // class weight
double notional_alloc = equity * leverage_target * w; // target notional exposure
double raw = (notional_alloc / spec.notional) * size_mult * vol_adj;
return floor(raw * direction + 0.5);                  // round to whole contracts
```

This is a **notional allocation model**:

1. Start with current equity.
2. Multiply by leverage target (2.0x) to get gross notional.
3. Allocate across asset classes by weight.
4. Divide by contract notional to get number of contracts.
5. Apply size multiplier (from regime/filter overlays) and volatility adjustment.
6. Round to nearest integer (whole contracts only).

Asset class weights:

| Asset Class | Weight | Instruments |
|-------------|--------|-------------|
| Equity Index | 30% | MES, MNQ |
| Commodities | 35% | CL, HG, GC, SI |
| Fixed Income | 25% | ZN, UB |
| FX | 10% | 6J |

**This is NOT Kelly criterion or fixed fractional.** It is a target-notional-allocation approach with 2x leverage.

### 5.2 Size Multiplier Cascade

The `size_mult` starts at 1.0 and is reduced multiplicatively by various conditions (lines 966-986):

| Condition | Effect |
|-----------|--------|
| LIQUIDITY_SHOCK regime | size_mult = 0.0 (all flat) |
| RISK_ON + GROWTH_NEGATIVE | size_mult = 0.5 |
| NEUTRAL regime | size_mult = 0.5 |
| INFLATION_SHOCK regime | size_mult = 0.5 |
| DXY filter SUSPECT | size_mult *= 0.5 |
| Liquidity < -1.5 | size_mult *= 0.25 |
| Correlation spike | size_mult *= 0.5 |
| China CLI weak | size_mult *= 0.7 (via china_adj) |
| Drawdown > 15% | size_mult = 0.0 |
| Drawdown > 10% | size_mult *= 0.5 |

These stack multiplicatively. Worst case (non-liquidity-shock): `0.5 * 0.5 * 0.25 * 0.5 * 0.7 * 0.5 = 0.0109375` -- less than 1.1% of full size.

**CONCERN**: The liquidity check appears twice -- once in the regime classifier (LIQUIDITY_SHOCK sets size_mult = 0.0) and again as a standalone check (line 980-981: `if liquidity < liquidity_thresh: size_mult *= 0.25`). Since LIQUIDITY_SHOCK already zeroes size_mult, the standalone check is redundant when it triggers LIQUIDITY_SHOCK. However, the waterfall `else if` structure means the regime classifier checks liquidity first, so if `liquidity < -1.5`, size_mult is already 0.0 before line 980 runs. The standalone check at line 980 is therefore dead code when the regime is LIQUIDITY_SHOCK, but would fire if the liquidity threshold were different from the regime threshold.

### 5.3 Fixed Position Mode (test mode)

When `use_fixed_positions = true`, all positions are set to +/- `fixed_position_size` (default 1 contract) times `size_mult`, with the same directional logic as the full mode. No notional calculations are performed.

---

## 6. Risk Management

### 6.1 Position Limits

**Per-instrument notional caps** (lines 1299-1305):

| Symbol | Max Notional (% of equity) |
|--------|---------------------------|
| MES | 20% |
| MNQ | 20% |
| HG | 15% |
| GC | 15% |
| CL | 15% |
| SI | 15% |
| ZN | No per-instrument limit |
| UB | No per-instrument limit |
| 6J | No per-instrument limit |

Implementation: `max_contracts = floor(equity * limit% / contract_notional)`. If position exceeds this, it is capped to the maximum.

**Total asset class caps** (lines 1307-1343):

| Asset Class | Max Total Notional (% of equity) |
|-------------|----------------------------------|
| Equity Index (MES + MNQ) | 35% |
| Commodities (HG + GC + CL + SI) | 40% |

If total class notional exceeds the cap, all positions in that class are scaled proportionally.

**No caps for fixed income or FX** -- ZN, UB, and 6J have no per-instrument or per-class limits in the current code.

### 6.2 Margin Utilization Cap (lines 1346-1355)

```
margin_util = sum(|qty| * margin_per_contract) / equity
if margin_util > 50%:
    scale all positions by (50% / margin_util)
```

This is the final position limit check. It acts as a hard leverage ceiling.

### 6.3 Drawdown Management

- **Warning at 10%**: positions halved.
- **Stop at 15%**: all positions closed.
- **Peak equity resets** when drawdown stop is active and portfolio is flat.

### 6.4 Correlation Circuit Breaker

When average pairwise 20-day correlation across all 9 instruments exceeds 0.70, all positions are halved. This protects against crisis-correlation regimes where diversification breaks down.

### 6.5 Performance Acceptance Criteria (lines 1734-1858)

The code evaluates post-backtest performance against documented thresholds:

| Metric | Threshold | Direction |
|--------|-----------|-----------|
| Sharpe Ratio | >= 0.8 | Higher is better |
| Sortino Ratio | >= 1.0 | Higher is better |
| Max Drawdown | < 20% | Lower is better |
| Win Rate | >= 45% | Higher is better |
| Profit Factor | >= 1.3 | Higher is better |
| Annual Turnover | < 15x | Lower is better |
| Correlation to SPX | < 0.5 | Lower is better |
| Signal Flips/Year | <= 12 | Lower is better |

**Kill criterion**: If signal flips exceed 20/year, development should be stopped (overfit warning).

---

## 7. Parameters & Thresholds

### Complete Parameter Catalog

#### Layer 1: Cu/Gold Ratio Signal

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `roc_10_window` | 10 | int | ROC lookback (short-term) |
| `roc_20_window` | 20 | int | ROC lookback (medium-term, used in composite) |
| `roc_60_window` | 60 | int | ROC lookback (long-term) |
| `ma_fast` | 10 | int | Fast SMA window for crossover signal |
| `ma_slow` | 50 | int | Slow SMA window for crossover signal |
| `zscore_window` | 120 | int | Rolling window for ratio z-score |
| `zscore_thresh` | 0.5 | double | Z-score threshold for signal_z activation |
| `composite_thresh` | 0.0 | double | Composite threshold for tilt determination |
| `w1` | 0.33 | double | Weight for sign(ROC_20) in composite |
| `w2` | 0.33 | double | Weight for signal_ma in composite |
| `w3` | 0.34 | double | Weight for signal_z in composite |

#### Layer 2: Regime Classifier

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `spx_mom_window` | 60 | int | SPX momentum lookback (days) |
| `breakeven_window` | 20 | int | Breakeven change lookback (days) |
| `liq_zscore_window` | 60 | int | Z-score window for VIX, HY, Fed BS |
| `real_rate_chg_window` | 20 | int | Real rate change lookback |
| `real_rate_z_window` | 120 | int | Real rate z-score window |
| `liquidity_thresh` | -1.5 | double | Liquidity score below which LIQUIDITY_SHOCK fires |

#### Layer 3: DXY Filter

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `dxy_mom_window` | 20 | int | DXY momentum lookback (days) |
| `dxy_mom_thresh` | 0.03 | double | DXY momentum threshold (3% as fraction) |

#### Auxiliary Filters

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `corr_window` | 20 | int | Pairwise correlation lookback |
| `corr_thresh` | 0.70 | double | Correlation threshold for spike detection |
| `boj_move_thresh` | 0.02 | double | JPY daily move threshold for BOJ filter (2%) |
| `use_china_filter` | true | bool | Enable/disable China CLI filter |
| `china_cli_thresh` | -2.0 | double | China CLI deviation threshold |

#### Risk Management

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `leverage_target` | 2.0 | double | Target gross leverage |
| `max_margin_util` | 0.50 | double | Maximum margin utilization (50% of equity) |
| `drawdown_warn` | 0.10 | double | Drawdown level for position halving (10%) |
| `drawdown_stop` | 0.15 | double | Drawdown level for full stop (15%) |
| `min_hold_days` | 5 | int | Minimum days before tilt can flip |

#### Sizing & Capital

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `initial_capital` | 1,000,000.0 | double | Starting equity ($) |
| `use_fixed_positions` | false | bool | Fixed 1-contract mode vs. full sizing |
| `fixed_position_size` | 1.0 | double | Contract count in fixed mode |

### Hardcoded Constants (not in StrategyParams)

| Constant | Value | Location | Description |
|----------|-------|----------|-------------|
| ATR stop multiplier | 2.0 | line 1036 | Position stop at 2x ATR |
| ATR window | 20 | line 1013 | ATR lookback for stops |
| VIX 90th pctile for gold override | 0.90 | line 932 | VIX percentile threshold |
| Gold return threshold for override | 1.5% | line 939 | Min gold rally for safe-haven flag |
| SPX return threshold for override | -1.5% | line 939 | Min SPX drop for safe-haven flag |
| DXY SMA windows | 50, 200 | lines 639-640 | DXY trend MAs (hardcoded) |
| China SMA window | 65 | line 643 | China CLI smoothing (hardcoded) |
| Regime change confirmation | 3 days | line 1119 | Days to confirm regime change |
| Fed BS YoY lookback | 252 | line 629 | Trading days in a year |
| VIX percentile rescale | `* 6.0 - 3.0` | line 833 | Map [0,1] to [-3,+3] |
| Fed BS growth scale | `* 10.0` | line 835 | Scale YoY growth to z-score range |
| Inflation shock threshold | 0.10 | line 855 | Breakeven 20d change for inflation |
| Growth thresholds | +/-0.5 | lines 857-860 | SPX 60d momentum (%) |
| Equity class notional cap | 35% | line 342 | MAX_TOTAL_EQUITY_NOTIONAL |
| Commodity class notional cap | 40% | line 343 | MAX_TOTAL_COMMODITY_NOTIONAL |
| Per-instrument notional caps | 15-20% | lines 337-340 | SINGLE_NOTIONAL_LIMIT |
| RISK_OFF + INFL equity direction | -0.5 | lines 1257-1258 | Half-sized equity short in stagflation |
| Flip kill criterion | 20/year | line 1862 | Max flips before development kill |

---

## 8. Execution Logic

### 8.1 Order Types and Fill Assumptions

The strategy uses **no explicit order types** -- it is a daily close-to-close backtesting framework. Positions are adjusted at the daily close price with costs applied as a flat per-contract deduction.

All fills are assumed at the closing price of the rebalance day:
```cpp
entry_prices[sym] = (*px)[i];  // close price on rebalance day
```

### 8.2 Transaction Cost Model (lines 308-315)

Round-trip cost per contract:
```
total_cost_rt = commission + (spread_ticks * tick_value) + (2 * slippage_ticks * tick_value)
```

| Symbol | Commission | Spread Cost | Slippage (2-way) | Total RT |
|--------|-----------|-------------|------------------|----------|
| HG | $2.50 | 0.5 * $12.50 = $6.25 | 2 * 0.5 * $12.50 = $12.50 | $21.25 |
| GC | $2.50 | 1.0 * $10.00 = $10.00 | 2 * 0.5 * $10.00 = $10.00 | $22.50 |
| CL | $2.50 | 1.0 * $10.00 = $10.00 | 2 * 1.0 * $10.00 = $20.00 | $32.50 |
| MES | $0.50 | 1.0 * $1.25 = $1.25 | 2 * 0.5 * $1.25 = $1.25 | $3.00 |
| MNQ | $0.50 | 1.0 * $0.50 = $0.50 | 2 * 0.5 * $0.50 = $0.50 | $1.50 |
| ZN | $1.50 | 0.5 * $15.625 = $7.81 | 2 * 0.5 * $15.625 = $15.63 | $24.94 |
| UB | $2.50 | 0 | 0 | $2.50 |
| 6J | $2.50 | 1.0 * $12.50 = $12.50 | 2 * 0.5 * $12.50 = $12.50 | $27.50 |
| SI | $2.50 | 1.0 * $25.00 = $25.00 | 2 * 1.0 * $25.00 = $50.00 | $77.50 |

Transaction costs are deducted from equity on every position change:
```cpp
double qty_change = abs(new_qty - old_qty);
equity -= total_cost_rt(sym) * qty_change;
```

Costs are charged on the **delta** of position, not total position. A change from +5 to +3 contracts incurs cost on 2 contracts (not 3, not 5).

**NOTE on UB**: Ultra Bond spread and slippage are both 0 -- the code comment says "not in doc cost table". This means UB trades are unrealistically cheap. In reality, UB has meaningful bid-ask spreads.

### 8.3 P&L Calculation (lines 992-1001)

Daily mark-to-market:
```cpp
daily_pnl += qty * (price[i] - price[i-1]) * point_value;
```

This is a standard daily close-to-close P&L. No intraday MTM.

### 8.4 Rebalance Timing

The strategy checks for rebalance on every bar (daily). Non-rebalance days carry positions forward with no changes (except ATR stops which fire daily). Transaction costs are only incurred on rebalance days when positions actually change.

---

## 9. Audit Notes & Concerns

### 9.1 Likely Bugs

1. **Inflation shock threshold units mismatch** (line 855): The threshold of `0.10` for breakeven 20-day change appears to be in percentage-point units, meaning 10 basis points. This fires extremely frequently. The code's own diagnostic section warns about this. If the document intended 100bp, this should be `1.0`, not `0.10`.

2. **Redundant liquidity check** (lines 967-968 vs. 980-981): LIQUIDITY_SHOCK already sets `size_mult = 0.0`, but a separate check at line 980 multiplies by 0.25 for the same threshold. Since the first check zeroes size_mult, the second check is dead code when both use the same threshold. If they were intended to be different thresholds, the second one should have its own parameter.

3. **`static` variables inside the main loop** (lines 877, 1106-1107): `last_debug_regime`, `pending_regime`, and `pending_regime_count` are declared `static` inside the loop body. While this works for a single-run backtest, it would cause state leakage if `run()` were called multiple times. The persistent state variables (`prev_regime_state`, `prev_dxy_filter_state`) are correctly declared as locals before the loop, but these three are inconsistent.

4. **Rolling std uses population variance** (line 175): `var / window` instead of `var / (window - 1)`. This produces slightly biased standard deviation estimates, which affects z-score calculations. For window=120, the bias is small (~0.4%), but it is technically incorrect for sample statistics.

### 9.2 Dead Code / Unused Features

1. **`dxy_trend`** (STRONG/WEAK/NEUTRAL): Computed but never used in any decision logic. Only stored in `DailySignal`.
2. **`real_rate_10y`**, **`real_rate_chg_20d`**, **`real_rate_zscore`**: Computed and stored but have zero effect on trading decisions.
3. **`roc_10`** and **`roc_60`**: Computed but not used in the composite signal (only `roc_20` is used). They appear in the output struct but serve no trading purpose.
4. **`tips_ts_`** and **`cny_usd_ts_`**: Loaded from CSV files but never referenced in any calculation.
5. **`fed_bs_yoy_z60`**: Computed at line 636 but never used. The raw `fed_bs_yoy` with hardcoded 10x scaling is used instead.

### 9.3 Design Concerns

1. **Zero composite threshold**: With `composite_thresh = 0.0`, the strategy has no dead zone. The smallest positive composite triggers RISK_ON. Combined with the 5-day debounce, this means the strategy will almost always be in RISK_ON or RISK_OFF, rarely NEUTRAL. This maximizes time-in-market but increases whipsaw risk.

2. **No position exit/sell logic**: The strategy can only set target positions. It cannot place sell orders or stop-limit orders. Exits happen only through rebalance target changes. Between rebalance days, the only exit mechanism is the ATR stop.

3. **Hardcoded scaling factors in liquidity score**: The factors `6.0`, `3.0`, and `10.0` in the liquidity composite are arbitrary normalizations. Different market regimes could cause these components to have very different scales, making the composite unreliable.

4. **UB transaction costs are zero**: Ultra Bond has no spread or slippage costs modeled, which is unrealistic and biases backtest results favorably for any UB position.

5. **Forward-fill of missing data**: All time series use forward-fill (`ffill`), which is standard practice but means stale data can persist for extended periods during holidays or data gaps without any staleness detection.

6. **No overnight/weekend gap handling**: The daily P&L calculation assumes continuous pricing. Large gap moves (e.g., Sunday futures open) are fully captured in the next day's P&L with no special handling.

7. **Profit factor calculation uses initial equity** (line 1788): `pnl = r * daily_equity[0]` uses initial capital for all days rather than the actual equity on that day. This distorts the metric as equity grows or shrinks.

### 9.4 Architecture

The entire strategy is a single 1870-line C++ file with:
- No separate header files.
- No unit tests.
- No configuration file parser (parameters are hardcoded in `StrategyParams` defaults).
- Debug output interleaved with production logic.
- Multiple `std::cout` debug statements that would need to be removed for production use.

The strategy takes command-line arguments for `data_dir`, `initial_capital`, and `"fixed"` mode, but all other parameters are compile-time constants.
