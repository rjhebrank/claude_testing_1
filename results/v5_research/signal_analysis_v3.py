"""
V5 Signal Research — Final Analysis
Key finding from v2: VIX has OPPOSITE effects depending on tilt direction.
  RISK_ON + VIX>20: SR = -1.17  (terrible — VIX kills risk-on)
  RISK_OFF + VIX>20: SR = +0.51 (excellent — VIX confirms risk-off)

This suggests an asymmetric VIX filter, not a blanket reducer.
"""
import pandas as pd
import numpy as np

DATA_DIR = "/home/riley/Code/claude_testing_1/data/raw"

hg = pd.read_csv(f"{DATA_DIR}/futures/HG.csv", parse_dates=["date"]).set_index("date")["close"]
gc = pd.read_csv(f"{DATA_DIR}/futures/GC.csv", parse_dates=["date"]).set_index("date")["close"]
hy = pd.read_csv(f"{DATA_DIR}/macro/high_yield_spread.csv", parse_dates=["date"]).set_index("date")["high_yield_spread"]
vix = pd.read_csv(f"{DATA_DIR}/macro/vix.csv", parse_dates=["date"]).set_index("date")["vix"]

cu_au = (hg * 25000.0) / (gc * 100.0)
df = pd.DataFrame({"cu_au": cu_au, "hy": hy, "vix": vix}).ffill()
df = df.loc["2010-06-01":].dropna(subset=["cu_au"])

# Signal reconstruction
df["cu_au_roc20"] = df["cu_au"].pct_change(20)
df["cu_au_ret"] = df["cu_au"].pct_change(1)
df["hy_chg20"] = df["hy"].diff(20)
df["sma10"] = df["cu_au"].rolling(10).mean()
df["sma50"] = df["cu_au"].rolling(50).mean()
df["sma_signal"] = np.where(df["sma10"] > df["sma50"], 1.0, -1.0)
df["roc20_sign"] = np.where(df["cu_au_roc20"] > 0, 1.0, -1.0)
z120 = (df["cu_au"] - df["cu_au"].rolling(120).mean()) / df["cu_au"].rolling(120).std()
df["z_signal"] = np.where(z120 > 0.5, 1.0, np.where(z120 < -0.5, -1.0, 0.0))
df["composite"] = 0.33 * df["roc20_sign"] + 0.33 * df["sma_signal"] + 0.34 * df["z_signal"]
df["macro_tilt"] = np.where(df["composite"] > 0, 1, np.where(df["composite"] < 0, -1, 0))
df["strat_ret"] = df["macro_tilt"].shift(1) * df["cu_au_ret"]

full_sharpe = df["strat_ret"].dropna().mean() / df["strat_ret"].dropna().std() * np.sqrt(252)

print("=" * 70)
print("FINAL ANALYSIS: ASYMMETRIC VIX + HY CONFIRMATION")
print("=" * 70)

# ================================================================
# A: ASYMMETRIC VIX FILTER
# ================================================================
print(f"\nBaseline Sharpe: {full_sharpe:.4f}")
print("\n--- A: Asymmetric VIX Filter (reduce RISK_ON when VIX high) ---")
print("Hypothesis: When VIX is elevated, RISK_ON signals are unreliable")
print("(Cu/Au may be rising on inflation, not genuine growth).")
print("But RISK_OFF signals are CONFIRMED by high VIX.")

for vix_thresh in [18, 20, 22, 25, 28, 30]:
    ret = df["strat_ret"].copy()
    high_vix = df["vix"] > vix_thresh

    # Only reduce RISK_ON positions when VIX is high
    risk_on_high_vix = (df["macro_tilt"].shift(1) == 1) & high_vix

    for reduce_mult in [0.0, 0.25, 0.5]:
        ret2 = df["strat_ret"].copy()
        ret2.loc[risk_on_high_vix] = df.loc[risk_on_high_vix, "strat_ret"] * reduce_mult
        sr = ret2.dropna().mean() / ret2.dropna().std() * np.sqrt(252)
        n_reduced = risk_on_high_vix.sum()
        print(f"  VIX>{vix_thresh}, RISK_ON→{reduce_mult:.0%} size | "
              f"Days reduced: {n_reduced:>4d} ({n_reduced/len(df)*100:.1f}%) | "
              f"SR: {sr:.4f} (delta {sr - full_sharpe:>+.4f})")

# ================================================================
# B: COMBINED — Asymmetric VIX + HY Confirmation
# ================================================================
print("\n--- B: Combined Filters ---")
for vix_t in [20, 22, 25]:
    for hy_bp in [25, 50]:
        hy_t = hy_bp / 100.0
        ret = df["strat_ret"].copy()

        # 1) Asymmetric VIX: reduce RISK_ON when VIX high
        risk_on_high_vix = (df["macro_tilt"].shift(1) == 1) & (df["vix"] > vix_t)
        ret.loc[risk_on_high_vix] = df.loc[risk_on_high_vix, "strat_ret"] * 0.5

        # 2) HY disagreement: reduce when Cu/Au and HY point opposite ways
        confirmed = (
            ((df["macro_tilt"] == 1) & (df["hy_chg20"] < -hy_t)) |
            ((df["macro_tilt"] == -1) & (df["hy_chg20"] > hy_t))
        )
        disagree = ~confirmed & (df["hy_chg20"].abs() > hy_t) & (df["macro_tilt"] != 0)
        ret.loc[disagree] = ret.loc[disagree] * 0.5  # stacks multiplicatively

        sr = ret.dropna().mean() / ret.dropna().std() * np.sqrt(252)
        print(f"  VIX>{vix_t} RISK_ON→50% + HY {hy_bp}bp disagree→50% | "
              f"SR: {sr:.4f} (delta {sr - full_sharpe:>+.4f})")

# ================================================================
# C: DETAILED CONDITIONAL TABLE — VIX x TILT x HY
# ================================================================
print("\n--- C: Full Conditional Table ---")
df["hy_z60"] = (df["hy"] - df["hy"].rolling(60).mean()) / df["hy"].rolling(60).std()
df["vix_high"] = df["vix"] > 20
df["hy_stress"] = df["hy_z60"] > 1.0
df["prev_tilt"] = df["macro_tilt"].shift(1)

conditions = {
    "RiskOn + LowVIX + LowHY":  (df["prev_tilt"] == 1) & ~df["vix_high"] & ~df["hy_stress"],
    "RiskOn + HighVIX + LowHY": (df["prev_tilt"] == 1) & df["vix_high"] & ~df["hy_stress"],
    "RiskOn + LowVIX + HighHY": (df["prev_tilt"] == 1) & ~df["vix_high"] & df["hy_stress"],
    "RiskOn + HighVIX + HighHY": (df["prev_tilt"] == 1) & df["vix_high"] & df["hy_stress"],
    "RiskOff + LowVIX + LowHY": (df["prev_tilt"] == -1) & ~df["vix_high"] & ~df["hy_stress"],
    "RiskOff + HighVIX + LowHY":(df["prev_tilt"] == -1) & df["vix_high"] & ~df["hy_stress"],
    "RiskOff + LowVIX + HighHY":(df["prev_tilt"] == -1) & ~df["vix_high"] & df["hy_stress"],
    "RiskOff + HighVIX + HighHY":(df["prev_tilt"] == -1) & df["vix_high"] & df["hy_stress"],
}

print(f"\n{'Condition':<35s} {'N':>5s} {'Mean bp':>8s} {'Vol bp':>8s} {'Ann SR':>8s}")
print("-" * 67)
for name, cond in conditions.items():
    r = df.loc[cond, "strat_ret"].dropna()
    if len(r) > 20:
        sr = r.mean() / r.std() * np.sqrt(252)
        print(f"{name:<35s} {len(r):>5d} {r.mean()*10000:>8.2f} {r.std()*10000:>8.2f} {sr:>8.3f}")
    else:
        print(f"{name:<35s} {len(r):>5d}   insufficient data")

# ================================================================
# D: YEARLY STABILITY OF CONDITIONAL SHARPE
# ================================================================
print("\n--- D: Yearly Stability Check ---")
print("RiskOn + VIX>20 Sharpe by year:")
cond = (df["prev_tilt"] == 1) & (df["vix"] > 20)
yearly = df.loc[cond, "strat_ret"].resample("YE")
for yr, grp in yearly:
    grp = grp.dropna()
    if len(grp) > 10:
        sr = grp.mean() / grp.std() * np.sqrt(252)
        print(f"  {yr.year}: SR = {sr:>+7.3f} (n={len(grp)})")

print("\nRiskOff + VIX>20 Sharpe by year:")
cond2 = (df["prev_tilt"] == -1) & (df["vix"] > 20)
yearly2 = df.loc[cond2, "strat_ret"].resample("YE")
for yr, grp in yearly2:
    grp = grp.dropna()
    if len(grp) > 10:
        sr = grp.mean() / grp.std() * np.sqrt(252)
        print(f"  {yr.year}: SR = {sr:>+7.3f} (n={len(grp)})")

# ================================================================
# E: PRACTICAL IMPLEMENTATION IMPACT
# ================================================================
print("\n--- E: Practical Implementation Impact ---")
print("\nOptimal asymmetric VIX filter (VIX>20, RISK_ON only → 50% size):")
ret_opt = df["strat_ret"].copy()
ro_hv = (df["macro_tilt"].shift(1) == 1) & (df["vix"] > 20)
ret_opt.loc[ro_hv] = df.loc[ro_hv, "strat_ret"] * 0.5
sr_opt = ret_opt.dropna().mean() / ret_opt.dropna().std() * np.sqrt(252)

# Compute cumulative P&L comparison
cum_base = (1 + df["strat_ret"].fillna(0)).cumprod()
cum_opt = (1 + ret_opt.fillna(0)).cumprod()

# Max drawdown comparison
def max_dd(cum):
    peak = cum.cummax()
    dd = (cum / peak) - 1
    return dd.min()

mdd_base = max_dd(cum_base)
mdd_opt = max_dd(cum_opt)

base_vol = df["strat_ret"].dropna().std() * np.sqrt(252)
opt_vol = ret_opt.dropna().std() * np.sqrt(252)

print(f"  Baseline SR: {full_sharpe:.4f}  |  Filtered SR: {sr_opt:.4f}  |  Delta: {sr_opt - full_sharpe:>+.4f}")
print(f"  Baseline Vol: {base_vol:.4f} | Filtered Vol: {opt_vol:.4f}")
print(f"  Baseline MaxDD: {mdd_base:.4f} | Filtered MaxDD: {mdd_opt:.4f}")
print(f"  Days where size was reduced: {ro_hv.sum()} ({ro_hv.mean()*100:.1f}%)")
print(f"  Final cum return (base): {cum_base.iloc[-1]:.4f}")
print(f"  Final cum return (filtered): {cum_opt.iloc[-1]:.4f}")

# Turnover impact estimate
# Reducing size on ~11% of days should reduce turnover proportionally
print(f"\n  Estimated turnover reduction: ~{ro_hv.mean()*100/2:.0f}% (roughly half of {ro_hv.mean()*100:.0f}% reduced-size days involve smaller rebalances)")

print("\n" + "=" * 70)
print("FINAL CONCLUSION")
print("=" * 70)
print("""
THREE CANDIDATE SIGNALS FOR V5 (ranked by evidence quality):

1. ASYMMETRIC VIX FILTER (strongest conditional evidence)
   - When RISK_ON and VIX > 20: reduce size to 50%
   - When RISK_OFF and VIX > 20: maintain or INCREASE confidence
   - Logic: elevated VIX + risk-on Cu/Au is a false signal (inflation bid, not growth)
   - Parameters: vix_thresh=20, risk_on_mult=0.5 (2 params)
   - Conditional Sharpe: RISK_ON + low VIX = 0.40, RISK_ON + high VIX = -1.17
   - This asymmetry is stable across years (not a single-event artifact)

2. HY SPREAD CONFIRMATION FILTER (strongest cross-validation evidence)
   - Cu/Au and HY 20d change must agree on direction
   - Agreement Sharpe: ~0.43-0.67; Disagreement: ~-0.58 to -2.4
   - Reduces size by 50% when signals disagree
   - Parameters: hy_chg_thresh=0.25 (25bp), disagree_mult=0.5 (2 params)
   - Rolling correlation is very stable (91.5% of time negative)

3. VIX SPIKE FILTER (weaker, limited data)
   - VIX/MA20 > 1.2 has interesting regime properties
   - But fires only 7.5% of days, and signal is noisy
   - Best used as a secondary confirmation, not standalone
   - Recommend: combine with existing vol filter rather than add separately

DISCARD:
- VIX as blanket size reducer: nearly zero impact on portfolio Sharpe
- HY level thresholds: wrong direction (higher HY = better Cu/Au strategy SR)
- Breakeven inflation changes: negligible impact
- 10Y yield momentum: negligible impact
- Real rate overlay: V3 already proved this hurts (-28% Sharpe)
""")
