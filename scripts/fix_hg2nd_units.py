"""
Fix unit mismatch in HG_2nd (copper 2nd-month futures) data.

Problem:
    HG.csv (front month) has prices in dollars/lb (e.g., 2.76 - 5.08).
    HG_2nd.csv (2nd month) has prices in cents/lb (e.g., 338 - 600).
    They need to be in the same unit (dollars/lb) for downstream analysis.

Solution:
    Divide all price columns (open, high, low, close) by 100.0.
    Leave date and volume untouched.
    Write the corrected file to data/cleaned/futures/HG_2nd.csv.
    The original file is never modified.
"""

import os
from pathlib import Path

import pandas as pd


# Project root — all paths relative to this
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Input / output paths
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "futures" / "HG_2nd.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "futures" / "HG_2nd.csv"

# Columns that contain prices (in cents/lb) and need to be divided by 100
PRICE_COLUMNS = ["open", "high", "low", "close"]


def load_raw(path: Path) -> pd.DataFrame:
    """Load the raw CSV, parsing dates but leaving price columns as-is."""
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def convert_cents_to_dollars(df: pd.DataFrame, price_cols: list[str]) -> pd.DataFrame:
    """
    Divide the specified price columns by 100.0 to convert cents/lb -> dollars/lb.

    NaN values are preserved (NaN / 100.0 = NaN in pandas).
    Non-price columns (date, volume) are left untouched.
    """
    df = df.copy()
    for col in price_cols:
        if col not in df.columns:
            raise KeyError(f"Expected price column '{col}' not found in DataFrame. "
                           f"Available columns: {list(df.columns)}")
        df[col] = df[col] / 100.0
    return df


def print_summary(label: str, df: pd.DataFrame, n: int = 5) -> None:
    """Print the first and last n rows of the DataFrame for visual verification."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"\nFirst {n} rows:")
    print(df.head(n).to_string(index=False))
    print(f"\nLast {n} rows:")
    print(df.tail(n).to_string(index=False))
    print()


def main() -> None:
    # --- Load ---
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df_raw = load_raw(INPUT_PATH)
    print(f"Loaded {len(df_raw):,} rows from {INPUT_PATH}")

    # --- Before summary ---
    print_summary("BEFORE (cents/lb)", df_raw)

    # --- Convert ---
    df_fixed = convert_cents_to_dollars(df_raw, PRICE_COLUMNS)

    # --- After summary ---
    print_summary("AFTER (dollars/lb)", df_fixed)

    # --- Sanity check: prices should now be in a plausible dollars/lb range ---
    for col in PRICE_COLUMNS:
        col_min = df_fixed[col].min()
        col_max = df_fixed[col].max()
        if col_max > 20.0 or col_min < 0.5:
            print(f"WARNING: {col} range [{col_min:.4f}, {col_max:.4f}] looks unusual "
                  f"for copper in dollars/lb. Double-check the conversion.")

    # --- Write ---
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_fixed.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(df_fixed):,} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
