"""
V5 Signal Research: HY Spread + VIX as Cu/Au Confirmation Signals
Analyzes correlation structure, rolling stability, and simple signal rules.
"""
import pandas as pd
import numpy as np
import sys

DATA_DIR = "/home/riley/Code/claude_testing_1/data/raw"

# ── Load data ──
print("=" * 70)
print("V5 SIGNAL RESEARCH: HY SPREAD + VIX ANALYSIS")
print("=" * 70)

# Futures
hg = pd.read_csv(f"{DATA_DIR}/futures/HG.csv", parse_dates=["date"]).set_index("date")["close"]
gc = pd.read_csv(f"{DATA_DIR}/futures/GC.csv", parse_dates=["date"]).set_index("date")["close"]

# Macro
hy = pd.read_csv(f"{DATA_DIR}/macro/high_yield_spread.csv", parse_dates=["date"]).set_index("date")["high_yield_spread"]
vix = pd.read_csv(f"{DATA_DIR}/macro/vix.csv", parse_dates=["date"]).set_index("date")["vix"]
dxy = pd.read_csv(f"{DATA_DIR}/macro/dxy.csv", parse_dates=["date"]).set_index("date")["dxy"]
t10y = pd.read_csv(f"{DATA_DIR}/macro/treasury_10y.csv", parse_dates=["date"]).set_index("date")["treasury_10y"]
be10y = pd.read_csv(f"{DATA_DIR}/macro/breakeven_10y.csv", parse_dates=["date"]).set_index("date")["breakeven_10y"]

# Compute Cu/Au ratio (notional normalization matching the C++ code)
cu_notional = hg * 25000.0
au_notional = gc * 100.0
cu_au = cu_notional / au_notional
cu_au.name = "cu_au_ratio"

print(f"\nData ranges:")
print(f"  HG futures:    {hg.index.min().date()} to {hg.index.max().date()} ({len(hg)} bars)")
print(f"  GC futures:    {gc.index.min().date()} to {gc.index.max().date()} ({len(gc)} bars)")
print(f"  Cu/Au ratio:   {cu_au.dropna().index.min().date()} to {cu_au.dropna().index.max().date()}")
print(f"  HY spread:     {hy.dropna().index.min().date()} to {hy.dropna().index.max().date()} ({len(hy.dropna())} obs)")
print(f"  VIX:           {vix.dropna().index.min().date()} to {vix.dropna().index.max().date()} ({len(vix.dropna())} obs)")
print(f"  DXY:           {dxy.dropna().index.min().date()} to {dxy.dropna().index.max().date()}")
print(f"  10Y Treasury:  {t10y.dropna().index.min().date()} to {t10y.dropna().index.max().date()}")
print(f"  10Y Breakeven: {be10y.dropna().index.min().date()} to {be10y.dropna().index.max().date()}")

# ── Align to common daily index ──
df = pd.DataFrame({
    "cu_au": cu_au,
    "hy": hy,
    "vix": vix,
    "dxy": dxy,
    "t10y": t10y,
    "be10y": be10y,
}).ffill()

# Restrict to backtest period (2010-06 onward, matching HG start)
df = df.loc["2010-06-01":].dropna(subset=["cu_au"])
print(f"\nAligned dataset: {df.index.min().date()} to {df.index.max().date()} ({len(df)} days)")

# ── Compute derived series ──
df["cu_au_roc20"] = df["cu_au"].pct_change(20)
df["hy_chg20"] = df["hy"].diff(20)
df["vix_chg20"] = df["vix"].diff(20)
df["cu_au_ret"] = df["cu_au"].pct_change(1)

# Z-scores (120-day, matching strategy)
for col in ["cu_au", "hy", "vix"]:
    df[f"{col}_z120"] = (df[col] - df[col].rolling(120).mean()) / df[col].rolling(120).std()

# ================================================================
# SECTION 1: STATIC CORRELATIONS
# ================================================================
print("\n" + "=" * 70)
print("SECTION 1: STATIC CORRELATIONS (full sample)")
print("=" * 70)

# Level correlations
pairs = [
    ("cu_au", "hy", "Cu/Au Level vs HY Spread Level"),
    ("cu_au", "vix", "Cu/Au Level vs VIX Level"),
    ("cu_au_roc20", "hy_chg20", "Cu/Au 20d ROC vs HY 20d Change"),
    ("cu_au_roc20", "vix_chg20", "Cu/Au 20d ROC vs VIX 20d Change"),
    ("cu_au_z120", "hy_z120", "Cu/Au Z-score vs HY Z-score (120d)"),
    ("cu_au_z120", "vix_z120", "Cu/Au Z-score vs VIX Z-score (120d)"),
]

print(f"\n{'Pair':<50s} {'Corr':>8s} {'N':>6s}")
print("-" * 66)
for a, b, label in pairs:
    mask = df[[a, b]].dropna()
    corr = mask[a].corr(mask[b])
    print(f"{label:<50s} {corr:>8.3f} {len(mask):>6d}")

# ================================================================
# SECTION 2: ROLLING CORRELATIONS (252-day)
# ================================================================
print("\n" + "=" * 70)
print("SECTION 2: ROLLING 252-DAY CORRELATIONS")
print("=" * 70)

rolling_pairs = [
    ("cu_au", "hy", "Cu/Au vs HY (level)"),
    ("cu_au_roc20", "hy_chg20", "Cu/Au ROC vs HY chg (20d)"),
    ("cu_au", "vix", "Cu/Au vs VIX (level)"),
    ("cu_au_roc20", "vix_chg20", "Cu/Au ROC vs VIX chg (20d)"),
]

for a, b, label in rolling_pairs:
    rc = df[a].rolling(252).corr(df[b])
    valid = rc.dropna()
    print(f"\n{label}:")
    print(f"  Mean: {valid.mean():.3f}  Std: {valid.std():.3f}  "
          f"Min: {valid.min():.3f}  Max: {valid.max():.3f}")
    # Stability: % of time sign is consistent
    pct_neg = (valid < 0).mean() * 100
    pct_pos = (valid > 0).mean() * 100
    print(f"  Sign: {pct_neg:.1f}% negative, {pct_pos:.1f}% positive")
    # Quintile breakdown by year
    yearly = rc.resample("YE").mean().dropna()
    for yr in yearly.index:
        print(f"    {yr.year}: {yearly.loc[yr]:.3f}")

# ================================================================
# SECTION 3: SIGNAL RULE TESTING
# ================================================================
print("\n" + "=" * 70)
print("SECTION 3: SIGNAL RULE TESTING")
print("=" * 70)

# Reconstruct Cu/Au signal (simplified: just use composite sign as proxy)
# ROC20 sign + SMA crossover + Z-score sign → composite
df["sma10"] = df["cu_au"].rolling(10).mean()
df["sma50"] = df["cu_au"].rolling(50).mean()
df["sma_signal"] = np.where(df["sma10"] > df["sma50"], 1.0, -1.0)
df["roc20_sign"] = np.where(df["cu_au_roc20"] > 0, 1.0, -1.0)
df["z_signal"] = np.where(df["cu_au_z120"] > 0.5, 1.0,
                 np.where(df["cu_au_z120"] < -0.5, -1.0, 0.0))
df["composite"] = 0.33 * df["roc20_sign"] + 0.33 * df["sma_signal"] + 0.34 * df["z_signal"]
df["macro_tilt"] = np.where(df["composite"] > 0, 1, np.where(df["composite"] < 0, -1, 0))

# Cu/Au "returns" for the strategy: if RISK_ON, we're long risk → use cu_au daily return as proxy
# (In reality, returns come from the multi-instrument portfolio, but Cu/Au direction is the core)
df["strat_ret"] = df["macro_tilt"].shift(1) * df["cu_au_ret"]

# ── Test 3a: HY spread widening → RISK_OFF confirmation ──
print("\n--- 3a: HY Spread Widening as Risk-Off Confirmation ---")
for thresh_bp in [25, 50, 75, 100]:
    thresh = thresh_bp / 100.0  # HY spread is in percentage points
    df["hy_widening"] = df["hy_chg20"] > thresh
    df["hy_narrowing"] = df["hy_chg20"] < -thresh

    # When Cu/Au says RISK_OFF and HY confirms (widening) → full size
    # When Cu/Au says RISK_OFF but HY doesn't confirm → half size
    mask_roff = df["macro_tilt"] == -1
    confirmed = mask_roff & df["hy_widening"]
    unconfirmed = mask_roff & ~df["hy_widening"]

    ret_confirmed = df.loc[confirmed, "strat_ret"]
    ret_unconfirmed = df.loc[unconfirmed, "strat_ret"]

    sr_conf = ret_confirmed.mean() / ret_confirmed.std() * np.sqrt(252) if len(ret_confirmed) > 20 else np.nan
    sr_unconf = ret_unconfirmed.mean() / ret_unconfirmed.std() * np.sqrt(252) if len(ret_unconfirmed) > 20 else np.nan

    print(f"  Threshold: {thresh_bp}bp | Confirmed days: {confirmed.sum():>5d} | "
          f"Unconfirmed: {unconfirmed.sum():>5d} | "
          f"Sharpe (conf): {sr_conf:>6.2f} | Sharpe (unconf): {sr_unconf:>6.2f} | "
          f"Delta: {(sr_conf - sr_unconf):>+6.2f}")

# ── Same for RISK_ON ──
print("\n  RISK_ON side (HY narrowing confirms risk-on):")
for thresh_bp in [25, 50, 75, 100]:
    thresh = thresh_bp / 100.0
    df["hy_narrowing"] = df["hy_chg20"] < -thresh

    mask_ron = df["macro_tilt"] == 1
    confirmed = mask_ron & df["hy_narrowing"]
    unconfirmed = mask_ron & ~df["hy_narrowing"]

    ret_confirmed = df.loc[confirmed, "strat_ret"]
    ret_unconfirmed = df.loc[unconfirmed, "strat_ret"]

    sr_conf = ret_confirmed.mean() / ret_confirmed.std() * np.sqrt(252) if len(ret_confirmed) > 20 else np.nan
    sr_unconf = ret_unconfirmed.mean() / ret_unconfirmed.std() * np.sqrt(252) if len(ret_unconfirmed) > 20 else np.nan

    print(f"  Threshold: {thresh_bp}bp | Confirmed days: {confirmed.sum():>5d} | "
          f"Unconfirmed: {unconfirmed.sum():>5d} | "
          f"Sharpe (conf): {sr_conf:>6.2f} | Sharpe (unconf): {sr_unconf:>6.2f} | "
          f"Delta: {(sr_conf - sr_unconf):>+6.2f}")

# ── Test 3b: VIX level → Position size reduction ──
print("\n--- 3b: VIX Level as Position Size Modifier ---")
# Full sample strategy Sharpe
full_sharpe = df["strat_ret"].dropna().mean() / df["strat_ret"].dropna().std() * np.sqrt(252)
print(f"  Baseline strategy Sharpe (Cu/Au composite, no filters): {full_sharpe:.3f}")

for vix_thresh, size_mult in [(20, 0.5), (25, 0.5), (30, 0.5), (35, 0.5),
                               (25, 0.25), (30, 0.25)]:
    df["vix_adj_ret"] = df["strat_ret"].copy()
    high_vix = df["vix"] > vix_thresh
    df.loc[high_vix, "vix_adj_ret"] = df.loc[high_vix, "strat_ret"] * size_mult

    adj_sr = df["vix_adj_ret"].dropna().mean() / df["vix_adj_ret"].dropna().std() * np.sqrt(252)
    pct_reduced = high_vix.mean() * 100

    print(f"  VIX > {vix_thresh} → {size_mult:.0%} size | "
          f"Days reduced: {high_vix.sum():>5d} ({pct_reduced:.1f}%) | "
          f"Adj Sharpe: {adj_sr:.3f} | Delta: {adj_sr - full_sharpe:>+.3f}")

# ── Test 3b2: VIX tiered reduction ──
print("\n  Tiered VIX reduction:")
for t1, s1, t2, s2 in [(25, 0.5, 35, 0.25), (20, 0.75, 30, 0.5), (25, 0.75, 35, 0.5)]:
    df["vix_tier_ret"] = df["strat_ret"].copy()
    tier2 = df["vix"] > t2
    tier1 = (df["vix"] > t1) & (~tier2)
    df.loc[tier1, "vix_tier_ret"] = df.loc[tier1, "strat_ret"] * s1
    df.loc[tier2, "vix_tier_ret"] = df.loc[tier2, "strat_ret"] * s2

    adj_sr = df["vix_tier_ret"].dropna().mean() / df["vix_tier_ret"].dropna().std() * np.sqrt(252)
    print(f"  VIX>{t1}→{s1:.0%}, VIX>{t2}→{s2:.0%} | "
          f"Adj Sharpe: {adj_sr:.3f} | Delta: {adj_sr - full_sharpe:>+.3f}")

# ── Test 3c: HY + Cu/Au agreement/disagreement ──
print("\n--- 3c: HY + Cu/Au Agreement vs Disagreement ---")
# Define HY signal: widening = risk-off, narrowing = risk-on
for hy_thresh_bp in [25, 50]:
    thresh = hy_thresh_bp / 100.0
    df["hy_signal"] = 0
    df.loc[df["hy_chg20"] < -thresh, "hy_signal"] = 1   # narrowing = risk-on
    df.loc[df["hy_chg20"] > thresh, "hy_signal"] = -1    # widening = risk-off

    agree = df["macro_tilt"] == df["hy_signal"]
    disagree = (df["macro_tilt"] != 0) & (df["hy_signal"] != 0) & (df["macro_tilt"] != df["hy_signal"])
    neutral_hy = df["hy_signal"] == 0

    # Agreement → full size, disagreement → half size, HY neutral → full size
    df["agree_ret"] = df["strat_ret"].copy()
    df.loc[disagree, "agree_ret"] = df.loc[disagree, "strat_ret"] * 0.5

    adj_sr = df["agree_ret"].dropna().mean() / df["agree_ret"].dropna().std() * np.sqrt(252)

    ret_agree = df.loc[agree & (df["macro_tilt"] != 0), "strat_ret"]
    ret_disagree = df.loc[disagree, "strat_ret"]
    sr_agree = ret_agree.mean() / ret_agree.std() * np.sqrt(252) if len(ret_agree) > 20 else np.nan
    sr_disagree = ret_disagree.mean() / ret_disagree.std() * np.sqrt(252) if len(ret_disagree) > 20 else np.nan

    print(f"  HY thresh: {hy_thresh_bp}bp | "
          f"Agree: {agree.sum():>5d} days (SR {sr_agree:.3f}) | "
          f"Disagree: {disagree.sum():>5d} days (SR {sr_disagree:.3f}) | "
          f"HY neutral: {neutral_hy.sum():>5d} | "
          f"Portfolio SR: {adj_sr:.3f} (delta {adj_sr - full_sharpe:>+.3f})")

# ================================================================
# SECTION 4: COMPLEMENTARY SIGNAL ANALYSIS
# ================================================================
print("\n" + "=" * 70)
print("SECTION 4: ADDITIONAL SIGNAL IDEAS")
print("=" * 70)

# ── 4a: HY Spread Z-score as standalone regime indicator ──
print("\n--- 4a: HY Spread Z-score Regime ---")
df["hy_z60"] = (df["hy"] - df["hy"].rolling(60).mean()) / df["hy"].rolling(60).std()
for z_thresh in [0.5, 1.0, 1.5, 2.0]:
    hy_stress = df["hy_z60"] > z_thresh
    ret_stress = df.loc[hy_stress, "strat_ret"]
    ret_normal = df.loc[~hy_stress, "strat_ret"]
    sr_stress = ret_stress.mean() / ret_stress.std() * np.sqrt(252) if len(ret_stress) > 20 else np.nan
    sr_normal = ret_normal.mean() / ret_normal.std() * np.sqrt(252) if len(ret_normal) > 20 else np.nan
    print(f"  HY Z > {z_thresh:.1f} | Stress days: {hy_stress.sum():>5d} ({hy_stress.mean()*100:.1f}%) | "
          f"SR(stress): {sr_stress:.3f} | SR(normal): {sr_normal:.3f} | Gap: {sr_normal - sr_stress:>+.3f}")

# ── 4b: VIX term structure proxy (VIX level vs 20d MA) ──
print("\n--- 4b: VIX Mean-Reversion (VIX vs 20d MA as term structure proxy) ---")
df["vix_ratio"] = df["vix"] / df["vix"].rolling(20).mean()
for ratio_thresh in [1.1, 1.2, 1.3, 1.5]:
    vix_spike = df["vix_ratio"] > ratio_thresh
    ret_spike = df.loc[vix_spike, "strat_ret"]
    ret_normal = df.loc[~vix_spike, "strat_ret"]
    sr_spike = ret_spike.mean() / ret_spike.std() * np.sqrt(252) if len(ret_spike) > 20 else np.nan
    sr_normal = ret_normal.mean() / ret_normal.std() * np.sqrt(252) if len(ret_normal) > 20 else np.nan
    print(f"  VIX/MA20 > {ratio_thresh:.1f} | Spike days: {vix_spike.sum():>5d} ({vix_spike.mean()*100:.1f}%) | "
          f"SR(spike): {sr_spike:.3f} | SR(normal): {sr_normal:.3f}")

# ── 4c: Combined VIX + HY stress indicator ──
print("\n--- 4c: Combined Stress Indicator (VIX > 25 AND HY Z60 > 1.0) ---")
combined_stress = (df["vix"] > 25) & (df["hy_z60"] > 1.0)
dual_stress_ret = df.loc[combined_stress, "strat_ret"]
normal_ret = df.loc[~combined_stress, "strat_ret"]
print(f"  Combined stress days: {combined_stress.sum()} ({combined_stress.mean()*100:.1f}%)")
if len(dual_stress_ret) > 20:
    print(f"  SR during stress: {dual_stress_ret.mean() / dual_stress_ret.std() * np.sqrt(252):.3f}")
    print(f"  SR normal:        {normal_ret.mean() / normal_ret.std() * np.sqrt(252):.3f}")

# Test as size modifier
for stress_size in [0.0, 0.25, 0.5]:
    df["combined_ret"] = df["strat_ret"].copy()
    df.loc[combined_stress, "combined_ret"] = df.loc[combined_stress, "strat_ret"] * stress_size
    adj_sr = df["combined_ret"].dropna().mean() / df["combined_ret"].dropna().std() * np.sqrt(252)
    print(f"  Stress → {stress_size:.0%} size: Adj Sharpe = {adj_sr:.3f} (delta {adj_sr - full_sharpe:>+.3f})")

# ── 4d: Real rate as additional context ──
print("\n--- 4d: Real Rate (10Y - Breakeven) ---")
df["real_rate"] = df["t10y"] - df["be10y"]
df["rr_chg20"] = df["real_rate"].diff(20)
corr_rr_cuau = df["rr_chg20"].corr(df["cu_au_roc20"])
print(f"  Corr(real rate 20d chg, Cu/Au ROC 20d): {corr_rr_cuau:.3f}")
print(f"  NOTE: V3 tried this as an overlay signal and it HURT Sharpe by 28%.")
print(f"  Including for completeness but NOT recommended as direct signal.")

# ================================================================
# SECTION 5: OPTIMAL PARAMETER SELECTION
# ================================================================
print("\n" + "=" * 70)
print("SECTION 5: PARAMETER SENSITIVITY GRID")
print("=" * 70)

# Best performing configurations from above
print("\n--- Best VIX threshold scan (single threshold, 50% size) ---")
best_vix_sr = full_sharpe
best_vix_t = None
for t in range(15, 46):
    ret = df["strat_ret"].copy()
    ret.loc[df["vix"] > t] = df.loc[df["vix"] > t, "strat_ret"] * 0.5
    sr = ret.dropna().mean() / ret.dropna().std() * np.sqrt(252)
    if sr > best_vix_sr:
        best_vix_sr = sr
        best_vix_t = t
if best_vix_t:
    print(f"  Best: VIX > {best_vix_t} → 50% size, Sharpe = {best_vix_sr:.3f} (delta {best_vix_sr - full_sharpe:>+.3f})")
else:
    print(f"  No VIX threshold improves on baseline {full_sharpe:.3f}")

print("\n--- Best HY Z-score stress threshold (flat size) ---")
best_hy_sr = full_sharpe
best_hy_z = None
best_hy_s = None
for z in np.arange(0.5, 2.5, 0.25):
    for s in [0.0, 0.25, 0.5]:
        ret = df["strat_ret"].copy()
        stress = df["hy_z60"] > z
        ret.loc[stress] = df.loc[stress, "strat_ret"] * s
        sr = ret.dropna().mean() / ret.dropna().std() * np.sqrt(252)
        if sr > best_hy_sr:
            best_hy_sr = sr
            best_hy_z = z
            best_hy_s = s
if best_hy_z:
    print(f"  Best: HY Z60 > {best_hy_z:.2f} → {best_hy_s:.0%} size, Sharpe = {best_hy_sr:.3f} (delta {best_hy_sr - full_sharpe:>+.3f})")
else:
    print(f"  No HY Z threshold improves on baseline {full_sharpe:.3f}")

# ================================================================
# SECTION 6: CORRELATION WITH EXISTING FILTERS
# ================================================================
print("\n" + "=" * 70)
print("SECTION 6: INDEPENDENCE FROM EXISTING FILTERS")
print("=" * 70)

# Check correlation between proposed signals and existing vol filter / DXY filter
# Vol filter: ratio_rvol_63 / ratio_rvol_252
df["cu_au_rvol63"] = df["cu_au_ret"].rolling(63).std()
df["cu_au_rvol252"] = df["cu_au_ret"].rolling(252).std()
df["vol_ratio"] = df["cu_au_rvol63"] / df["cu_au_rvol252"]

# DXY momentum (20d)
df["dxy_mom20"] = df["dxy"].pct_change(20)

print(f"\nCorrelation matrix of filter signals:")
filter_cols = ["vix", "hy_z60", "vol_ratio", "dxy_mom20"]
corr_matrix = df[filter_cols].dropna().corr()
print(corr_matrix.to_string(float_format=lambda x: f"{x:.3f}"))

print(f"\n  VIX vs Vol Ratio:  {df['vix'].corr(df['vol_ratio']):.3f}")
print(f"  HY Z60 vs Vol Ratio: {df['hy_z60'].corr(df['vol_ratio']):.3f}")
print(f"  VIX vs HY Z60:    {df['vix'].corr(df['hy_z60']):.3f}")
print(f"  VIX vs DXY Mom:   {df['vix'].corr(df['dxy_mom20']):.3f}")
print(f"  HY Z60 vs DXY Mom: {df['hy_z60'].corr(df['dxy_mom20']):.3f}")

# ================================================================
# SECTION 7: DRAWDOWN ANALYSIS — DO THE SIGNALS HELP WHEN IT MATTERS?
# ================================================================
print("\n" + "=" * 70)
print("SECTION 7: PERFORMANCE DURING STRATEGY DRAWDOWNS")
print("=" * 70)

# Identify strategy drawdown periods (cumulative return)
cum_ret = (1 + df["strat_ret"].fillna(0)).cumprod()
peak = cum_ret.cummax()
dd = (cum_ret / peak) - 1

# Major drawdown periods (DD > 10%)
major_dd = dd < -0.10
if major_dd.any():
    print(f"\nDays in >10% drawdown: {major_dd.sum()} ({major_dd.mean()*100:.1f}%)")
    print(f"  Mean VIX during DD: {df.loc[major_dd, 'vix'].mean():.1f} vs normal {df.loc[~major_dd, 'vix'].mean():.1f}")
    print(f"  Mean HY Z60 during DD: {df.loc[major_dd, 'hy_z60'].mean():.2f} vs normal {df.loc[~major_dd, 'hy_z60'].mean():.2f}")

    # Would the signals have reduced DD?
    for label, cond in [
        ("VIX > 25 → 50%", df["vix"] > 25),
        ("VIX > 30 → 50%", df["vix"] > 30),
        ("HY Z60 > 1.0 → 50%", df["hy_z60"] > 1.0),
        ("HY Z60 > 1.5 → 25%", df["hy_z60"] > 1.5),
        ("Combined (VIX>25 & HYZ>1) → 25%", (df["vix"] > 25) & (df["hy_z60"] > 1.0)),
    ]:
        # Count how many DD days would have been caught
        caught = (cond & major_dd).sum()
        pct_caught = caught / major_dd.sum() * 100 if major_dd.sum() > 0 else 0
        # False positive rate (triggered but not in DD)
        false_pos = (cond & ~major_dd).sum()
        total_triggered = cond.sum()
        false_pos_rate = false_pos / total_triggered * 100 if total_triggered > 0 else 0
        print(f"  {label:<45s} | Caught {caught:>4d}/{major_dd.sum()} DD days ({pct_caught:.0f}%) | "
              f"False pos: {false_pos_rate:.0f}%")
else:
    print("  No major drawdown periods > 10%")

# Minor drawdowns (5-10%)
minor_dd = (dd < -0.05) & (dd >= -0.10)
print(f"\nDays in 5-10% drawdown: {minor_dd.sum()}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
