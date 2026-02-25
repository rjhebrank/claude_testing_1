#!/usr/bin/env python3
"""
Production data cleaning script for futures and macro CSV datasets.

Processes all CSVs in data/raw/futures/ and data/raw/macro/, applying:
  - Date parsing and validation
  - Weekend row removal (futures only)
  - Forward-fill of missing values (max 5 business days gap)
  - Suspicious value flagging (futures: zero/negative prices, zero weekday volume)
  - Per-file cleaning report

Output structure mirrors input:
  data/cleaned/futures/<same_filename>.csv
  data/cleaned/macro/<same_filename>.csv
  data/cleaned/cleaning_report.csv

Author: Quant Data Engineering
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum number of consecutive business days to forward-fill.
# Beyond this gap we leave NaN -- the downstream consumer must decide
# whether to interpolate, drop, or raise.
MAX_FFILL_LIMIT = 5

# Single-bar percentage move threshold for spike detection (futures only).
# Any OHLC column that moves more than this fraction in one bar is treated
# as a data error.  The spiked row AND the next row (the reversion bar)
# are both forward-filled from the last known good values.
# 0.50 = 50 %  -- no legitimate commodity future moves 50 % in a single day.
SPIKE_THRESHOLD = 0.50

# Columns that we expect in a well-formed futures CSV.
# The script will still work if extra columns exist; it only needs 'date'.
FUTURES_PRICE_COLS = ["open", "high", "low", "close"]
FUTURES_VOLUME_COL = "volume"

# Name of the flag column appended to futures output files.
SUSPICIOUS_FLAG_COL = "suspicious_flag"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_read_csv(filepath: Path) -> Optional[pd.DataFrame]:
    """
    Read a CSV defensively. Returns None if the file is empty, unreadable,
    or contains no data rows.
    """
    try:
        # Peek at the file to catch truly empty files (0 bytes or header-only).
        file_size = filepath.stat().st_size
        if file_size == 0:
            log.warning("Skipping empty file (0 bytes): %s", filepath)
            return None

        df = pd.read_csv(filepath)

        if df.empty:
            log.warning("Skipping file with no data rows: %s", filepath)
            return None

        return df

    except pd.errors.EmptyDataError:
        log.warning("Skipping file (EmptyDataError): %s", filepath)
        return None
    except pd.errors.ParserError as exc:
        log.error("CSV parse error in %s: %s", filepath, exc)
        return None
    except Exception as exc:
        log.error("Unexpected error reading %s: %s", filepath, exc)
        return None


def _parse_date_column(df: pd.DataFrame, filepath: Path) -> Optional[pd.DataFrame]:
    """
    Identify and parse the date column. We look for a column literally named
    'date' (case-insensitive). If none exists, we try the first column under
    the assumption that single-column or two-column macro files put the date
    first.

    Returns the dataframe with a proper datetime 'date' column sorted
    ascending, or None if parsing fails entirely.
    """
    # Normalise column names to lowercase for matching.
    col_map = {c: c.lower().strip() for c in df.columns}
    df = df.rename(columns=col_map)

    date_col = None
    if "date" in df.columns:
        date_col = "date"
    else:
        # Heuristic: first column is the date.
        first_col = df.columns[0]
        log.info(
            "No 'date' column in %s; treating first column '%s' as date.",
            filepath.name,
            first_col,
        )
        df = df.rename(columns={first_col: "date"})
        date_col = "date"

    # Attempt to parse dates. coerce invalid entries to NaT.
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    unparseable_count = df[date_col].isna().sum()
    if unparseable_count == len(df):
        log.error(
            "All dates unparseable in %s -- skipping file.", filepath.name
        )
        return None

    if unparseable_count > 0:
        log.warning(
            "%d unparseable date(s) dropped from %s.",
            unparseable_count,
            filepath.name,
        )
        df = df.dropna(subset=[date_col])

    # Sort chronologically and reset index.
    df = df.sort_values(date_col).reset_index(drop=True)
    return df


def _is_weekend(dt_series: pd.Series) -> pd.Series:
    """Return boolean Series: True where date falls on Saturday (5) or Sunday (6)."""
    return dt_series.dt.dayofweek.isin([5, 6])


# ---------------------------------------------------------------------------
# Futures cleaning
# ---------------------------------------------------------------------------


def clean_futures_file(filepath: Path) -> Optional[dict]:
    """
    Clean a single futures CSV.

    Returns a dict with cleaning report metrics, or None if the file
    could not be processed.
    """
    log.info("Processing futures file: %s", filepath.name)

    df = _safe_read_csv(filepath)
    if df is None:
        return None

    original_rows = len(df)

    df = _parse_date_column(df, filepath)
    if df is None:
        return None

    # ------------------------------------------------------------------
    # 1. Remove weekend rows
    # ------------------------------------------------------------------
    weekend_mask = _is_weekend(df["date"])
    weekend_count = weekend_mask.sum()
    df = df[~weekend_mask].reset_index(drop=True)
    log.info("  Removed %d weekend rows.", weekend_count)

    # ------------------------------------------------------------------
    # 2. Forward-fill missing values (max 5 business days)
    # ------------------------------------------------------------------
    # Identify numeric columns to fill.  We exclude 'date' and any flag cols.
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # Count total NaNs across numeric columns before fill.
    missing_before = df[numeric_cols].isna().sum().sum() if numeric_cols else 0

    if numeric_cols:
        df[numeric_cols] = df[numeric_cols].ffill(limit=MAX_FFILL_LIMIT)

    missing_after = df[numeric_cols].isna().sum().sum() if numeric_cols else 0
    missing_filled = int(missing_before - missing_after)
    log.info("  Forward-filled %d missing value(s).", missing_filled)

    # ------------------------------------------------------------------
    # 3. Spike detection — flag AND forward-fill single-bar blowups
    # ------------------------------------------------------------------
    # Walk through rows comparing each price against the last known good
    # value.  If any OHLC column moved more than SPIKE_THRESHOLD, the row
    # is marked as bad and its price+volume values are set to NaN.  Good
    # rows update the reference.  One final forward-fill replaces all bad
    # rows at once.  This handles multi-bar unit shifts (e.g. a week of
    # 100x prices) in a single pass without iteration.

    spike_rows: set[int] = set()

    # Determine which columns to overwrite: all price cols + volume.
    cols_to_fill = [
        c for c in FUTURES_PRICE_COLS + [FUTURES_VOLUME_COL] if c in df.columns
    ]
    price_cols_present = [c for c in FUTURES_PRICE_COLS if c in df.columns]

    # Single-pass spike detection: walk through rows in order, comparing
    # each row's prices against the last known good values.  If any price
    # column moved more than SPIKE_THRESHOLD vs. the last good value, the
    # row is bad.  Bad rows are set to NaN and skipped; good rows update
    # the reference.  After marking, one forward-fill fixes everything.
    if price_cols_present:
        # Find the first row with all non-NaN prices as the initial
        # reference ("last known good").
        last_good: dict[str, float] = {}
        start_idx = 0
        for i in df.index:
            vals = {c: df.at[i, c] for c in price_cols_present}
            if all(pd.notna(v) for v in vals.values()):
                last_good = vals
                start_idx = i + 1
                break

        if last_good:
            for i in df.index[df.index >= start_idx]:
                is_spike = False
                for col in price_cols_present:
                    cur = df.at[i, col]
                    if pd.isna(cur) or last_good[col] == 0:
                        continue
                    pct = abs(cur - last_good[col]) / abs(last_good[col])
                    if pct > SPIKE_THRESHOLD:
                        is_spike = True
                        break

                if is_spike:
                    spike_rows.add(i)
                    df.loc[i, cols_to_fill] = pd.NA
                else:
                    # Update last known good reference.
                    for col in price_cols_present:
                        val = df.at[i, col]
                        if pd.notna(val):
                            last_good[col] = val

            # One forward-fill replaces all spiked rows at once.
            if spike_rows:
                df[cols_to_fill] = df[cols_to_fill].ffill()

    spike_count = len(spike_rows)
    spike_indices_sorted: list[int] = sorted(spike_rows)

    if spike_count > 0:
        log.info(
            "  Detected %d spike row(s) (threshold=%.0f%%). "
            "Forward-filled from last good values.",
            spike_count,
            SPIKE_THRESHOLD * 100,
        )

    # ------------------------------------------------------------------
    # 4. Flag suspicious rows (do NOT delete)
    # ------------------------------------------------------------------
    # Initialise flag column with empty strings; we will concatenate reasons.
    df[SUSPICIOUS_FLAG_COL] = ""

    suspicious_count = 0

    # 4a. Mark spike/reversion rows that were forward-filled in step 3.
    if spike_count > 0:
        for idx in spike_indices_sorted:
            df.loc[idx, SUSPICIOUS_FLAG_COL] = "spike_ffilled;"
        log.info("  Flagged %d row(s) as spike_ffilled.", spike_count)

    # 4b. Zero price in any OHLC column
    for col in FUTURES_PRICE_COLS:
        if col in df.columns:
            zero_mask = df[col] == 0
            count = zero_mask.sum()
            if count > 0:
                df.loc[zero_mask, SUSPICIOUS_FLAG_COL] = (
                    df.loc[zero_mask, SUSPICIOUS_FLAG_COL]
                    .apply(lambda s, c=col: f"{s}zero_{c};" if s else f"zero_{c};")
                )
                log.info("  Flagged %d row(s) with zero %s.", count, col)

    # 4c. Negative price in any OHLC column
    for col in FUTURES_PRICE_COLS:
        if col in df.columns:
            neg_mask = df[col] < 0
            count = neg_mask.sum()
            if count > 0:
                df.loc[neg_mask, SUSPICIOUS_FLAG_COL] = (
                    df.loc[neg_mask, SUSPICIOUS_FLAG_COL]
                    .apply(lambda s, c=col: f"{s}negative_{c};" if s else f"negative_{c};")
                )
                log.info("  Flagged %d row(s) with negative %s.", count, col)

    # 4d. Zero volume on a weekday
    if FUTURES_VOLUME_COL in df.columns:
        zero_vol_mask = df[FUTURES_VOLUME_COL] == 0
        count = zero_vol_mask.sum()
        if count > 0:
            df.loc[zero_vol_mask, SUSPICIOUS_FLAG_COL] = (
                df.loc[zero_vol_mask, SUSPICIOUS_FLAG_COL]
                .apply(lambda s: f"{s}zero_volume;" if s else "zero_volume;")
            )
            log.info("  Flagged %d row(s) with zero weekday volume.", count)

    suspicious_count = (df[SUSPICIOUS_FLAG_COL] != "").sum()

    # ------------------------------------------------------------------
    # Build report row
    # ------------------------------------------------------------------
    cleaned_rows = len(df)

    # Determine date range from the cleaned data.
    date_start = df["date"].min().strftime("%Y-%m-%d") if cleaned_rows > 0 else ""
    date_end = df["date"].max().strftime("%Y-%m-%d") if cleaned_rows > 0 else ""

    report = {
        "filename": filepath.name,
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": original_rows - cleaned_rows,
        "missing_values_filled": missing_filled,
        "spike_rows_ffilled": spike_count,
        "suspicious_rows_flagged": int(suspicious_count),
        "date_range_start": date_start,
        "date_range_end": date_end,
    }

    # Attach the cleaned dataframe for the caller to persist.
    report["_df"] = df

    return report


# ---------------------------------------------------------------------------
# Macro cleaning
# ---------------------------------------------------------------------------


def clean_macro_file(filepath: Path) -> Optional[dict]:
    """
    Clean a single macro CSV.

    Macro files are heterogeneous in frequency (daily, weekly, monthly) and
    may have large stretches of empty values. We only forward-fill within a
    5-row limit (treating each row as one observation period, regardless of
    calendar frequency) and leave remaining NaNs intact.

    Returns a dict with cleaning report metrics, or None on failure.
    """
    log.info("Processing macro file: %s", filepath.name)

    df = _safe_read_csv(filepath)
    if df is None:
        return None

    original_rows = len(df)

    df = _parse_date_column(df, filepath)
    if df is None:
        return None

    # ------------------------------------------------------------------
    # No weekend removal for macro files -- macro data can be released on
    # any calendar day, and weekly/monthly series use end-of-period dates
    # that may land on weekends (e.g. 2010-01-31 is a Sunday).
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Forward-fill missing values (max 5 rows)
    # ------------------------------------------------------------------
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    missing_before = df[numeric_cols].isna().sum().sum() if numeric_cols else 0

    if numeric_cols:
        df[numeric_cols] = df[numeric_cols].ffill(limit=MAX_FFILL_LIMIT)

    missing_after = df[numeric_cols].isna().sum().sum() if numeric_cols else 0
    missing_filled = int(missing_before - missing_after)
    log.info("  Forward-filled %d missing value(s).", missing_filled)

    # ------------------------------------------------------------------
    # Build report row
    # ------------------------------------------------------------------
    cleaned_rows = len(df)
    date_start = df["date"].min().strftime("%Y-%m-%d") if cleaned_rows > 0 else ""
    date_end = df["date"].max().strftime("%Y-%m-%d") if cleaned_rows > 0 else ""

    report = {
        "filename": filepath.name,
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": original_rows - cleaned_rows,
        "missing_values_filled": missing_filled,
        "spike_rows_ffilled": 0,  # No spike detection for macro.
        "suspicious_rows_flagged": 0,  # No suspicious-value flagging for macro.
        "date_range_start": date_start,
        "date_range_end": date_end,
    }
    report["_df"] = df

    return report


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_pipeline(input_dir: Path, output_dir: Path) -> None:
    """
    Main entry point. Discovers CSVs, cleans them, writes output, and
    produces the summary report.
    """
    futures_input = input_dir / "futures"
    macro_input = input_dir / "macro"
    futures_output = output_dir / "futures"
    macro_output = output_dir / "macro"

    # Validate that at least one input directory exists.
    if not futures_input.is_dir() and not macro_input.is_dir():
        log.error(
            "Neither %s nor %s exist. Nothing to process.", futures_input, macro_input
        )
        sys.exit(1)

    # Create output directories.
    futures_output.mkdir(parents=True, exist_ok=True)
    macro_output.mkdir(parents=True, exist_ok=True)

    report_rows: list[dict] = []

    # ------------------------------------------------------------------
    # Futures
    # ------------------------------------------------------------------
    if futures_input.is_dir():
        futures_files = sorted(futures_input.glob("*.csv"))
        log.info(
            "Found %d futures CSV(s) in %s.", len(futures_files), futures_input
        )
        for fpath in futures_files:
            result = clean_futures_file(fpath)
            if result is None:
                log.warning("  Skipped %s (could not process).", fpath.name)
                continue

            df = result.pop("_df")
            out_path = futures_output / fpath.name

            # Write cleaned CSV.  Format date as YYYY-MM-DD to stay consistent.
            df.to_csv(out_path, index=False, date_format="%Y-%m-%d")
            log.info(
                "  Wrote %d rows -> %s", len(df), out_path
            )
            report_rows.append(result)
    else:
        log.info("No futures directory at %s -- skipping.", futures_input)

    # ------------------------------------------------------------------
    # Macro
    # ------------------------------------------------------------------
    if macro_input.is_dir():
        macro_files = sorted(macro_input.glob("*.csv"))
        log.info(
            "Found %d macro CSV(s) in %s.", len(macro_files), macro_input
        )
        for fpath in macro_files:
            result = clean_macro_file(fpath)
            if result is None:
                log.warning("  Skipped %s (could not process).", fpath.name)
                continue

            df = result.pop("_df")
            out_path = macro_output / fpath.name

            df.to_csv(out_path, index=False, date_format="%Y-%m-%d")
            log.info(
                "  Wrote %d rows -> %s", len(df), out_path
            )
            report_rows.append(result)
    else:
        log.info("No macro directory at %s -- skipping.", macro_input)

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    if report_rows:
        report_df = pd.DataFrame(report_rows)
        # Enforce column order for readability.
        col_order = [
            "filename",
            "original_rows",
            "cleaned_rows",
            "rows_removed",
            "missing_values_filled",
            "spike_rows_ffilled",
            "suspicious_rows_flagged",
            "date_range_start",
            "date_range_end",
        ]
        report_df = report_df[[c for c in col_order if c in report_df.columns]]

        report_path = output_dir / "cleaning_report.csv"
        report_df.to_csv(report_path, index=False)
        log.info("Cleaning report written to %s (%d files).", report_path, len(report_df))

        # Print a compact summary to stdout.
        total_original = report_df["original_rows"].sum()
        total_cleaned = report_df["cleaned_rows"].sum()
        total_removed = report_df["rows_removed"].sum()
        total_filled = report_df["missing_values_filled"].sum()
        total_spikes = report_df["spike_rows_ffilled"].sum()
        total_flagged = report_df["suspicious_rows_flagged"].sum()

        log.info("=" * 60)
        log.info("PIPELINE SUMMARY")
        log.info("  Files processed   : %d", len(report_df))
        log.info("  Total original rows: %d", total_original)
        log.info("  Total cleaned rows : %d", total_cleaned)
        log.info("  Total rows removed : %d", total_removed)
        log.info("  Total values filled: %d", total_filled)
        log.info("  Total spike rows   : %d", total_spikes)
        log.info("  Total rows flagged : %d", total_flagged)
        log.info("=" * 60)
    else:
        log.warning("No files were successfully processed. No report generated.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clean raw futures and macro CSV data. "
            "Removes weekend rows from futures, forward-fills gaps, "
            "flags suspicious values, and writes a cleaning report."
        ),
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help=(
            "Root input directory containing 'futures/' and/or 'macro/' "
            "subdirectories. Default: data/raw"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/cleaned"),
        help=(
            "Root output directory. Cleaned files go into 'futures/' and "
            "'macro/' subdirectories. Default: data/cleaned"
        ),
    )

    args = parser.parse_args()

    log.info("Input directory : %s", args.input_dir.resolve())
    log.info("Output directory: %s", args.output_dir.resolve())

    run_pipeline(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
