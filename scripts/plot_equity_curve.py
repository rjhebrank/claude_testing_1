"""
Generate presentation-quality equity curve chart for Copper-Gold Macro Strategy V5.
Parses daily equity from backtest log [SIZING] lines and produces a PNG.
"""

import re
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np

# ---------------------------------------------------------------------------
# 1. Parse equity data from backtest log
# ---------------------------------------------------------------------------
INPUT  = Path(__file__).resolve().parent.parent / "results" / "backtest_output_v5.txt"
OUTPUT = Path(__file__).resolve().parent.parent / "results" / "v5_equity_curve.png"

sizing_re = re.compile(
    r"\[SIZING\]\s+(\d{4}-\d{2}-\d{2})\s+equity=([\d.]+)"
)

dates = []
equities = []

with open(INPUT) as f:
    for line in f:
        m = sizing_re.search(line)
        if m:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d")
            eq = float(m.group(2))
            # Keep only the first SIZING entry per date (avoid duplicates from
            # multiple SIZING lines on the same day)
            if not dates or dt != dates[-1]:
                dates.append(dt)
                equities.append(eq)

dates = np.array(dates)
equities = np.array(equities)

print(f"Parsed {len(dates)} daily equity observations")
print(f"Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
print(f"Equity range: ${equities.min():,.0f} - ${equities.max():,.0f}")

# ---------------------------------------------------------------------------
# 2. Compute drawdown series
# ---------------------------------------------------------------------------
running_max = np.maximum.accumulate(equities)
drawdown = (equities - running_max) / running_max  # negative values

# Find max drawdown period
dd_end_idx = np.argmin(drawdown)
dd_start_idx = np.argmax(equities[:dd_end_idx + 1])

print(f"Max drawdown: {drawdown[dd_end_idx]*100:.2f}% "
      f"({dates[dd_start_idx].strftime('%Y-%m-%d')} to "
      f"{dates[dd_end_idx].strftime('%Y-%m-%d')})")

# ---------------------------------------------------------------------------
# 3. Build the chart
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Drawdown shading (fill between equity and running max)
ax.fill_between(
    dates, equities, running_max,
    where=(equities < running_max),
    color='#e74c3c', alpha=0.15,
    label='Drawdown',
    interpolate=True,
)

# Equity curve
ax.plot(
    dates, equities,
    color='#2471A3', linewidth=1.8,
    label='Portfolio Equity', zorder=3,
)

# Running-max (high-water mark) as a subtle dashed line
ax.plot(
    dates, running_max,
    color='#2471A3', linewidth=0.6, linestyle='--', alpha=0.35,
    label='High-Water Mark', zorder=2,
)

# Starting capital reference line
ax.axhline(
    y=1_000_000, color='#7f8c8d', linewidth=1.0, linestyle=':',
    zorder=1,
)
ax.annotate(
    '$1,000,000 starting capital',
    xy=(dates[int(len(dates) * 0.02)], 1_000_000),
    xytext=(dates[int(len(dates) * 0.02)], 940_000),
    fontsize=9, color='#7f8c8d',
    arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=0.8),
)

# Annotate max drawdown trough
ax.annotate(
    f'Max DD: {drawdown[dd_end_idx]*100:.1f}%\n{dates[dd_end_idx].strftime("%b %Y")}',
    xy=(dates[dd_end_idx], equities[dd_end_idx]),
    xytext=(dates[dd_end_idx], equities[dd_end_idx] - 120_000),
    fontsize=9, color='#c0392b', fontweight='bold',
    ha='center',
    arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.0),
    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#c0392b', alpha=0.85),
    zorder=5,
)

# ---------------------------------------------------------------------------
# 4. Formatting
# ---------------------------------------------------------------------------

# Title + subtitle
ax.set_title(
    'Copper-Gold Macro Strategy \u2014 V5 Equity Curve',
    fontsize=16, fontweight='bold', pad=20,
)
fig.text(
    0.5, 0.92,
    'Sharpe 0.50  |  CAGR 4.34%  |  Max DD 14.1%',
    ha='center', fontsize=11, color='#555555',
    fontstyle='italic',
)

# Axes labels
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Portfolio Equity ($)', fontsize=12)

# Y-axis comma formatting
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

# X-axis date formatting
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_minor_locator(mdates.YearLocator(1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.autofmt_xdate(rotation=0, ha='center')

# Grid
ax.grid(True, which='major', axis='both', color='#e0e0e0', linewidth=0.7)
ax.grid(True, which='minor', axis='x', color='#f0f0f0', linewidth=0.4)
ax.set_axisbelow(True)

# Tick styling
ax.tick_params(axis='both', which='major', labelsize=11)

# Legend
ax.legend(
    loc='upper left', fontsize=10, frameon=True,
    facecolor='white', edgecolor='#cccccc', framealpha=0.9,
)

# Tight margins
fig.tight_layout(rect=[0, 0, 1, 0.91])

# ---------------------------------------------------------------------------
# 5. Save
# ---------------------------------------------------------------------------
fig.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)

print(f"\nSaved to {OUTPUT}")
print(f"File size: {OUTPUT.stat().st_size / 1024:.0f} KB")
