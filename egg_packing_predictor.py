# egg_packing_predictor.py
# Python 3.10+
# pip install pandas openpyxl python-dateutil

from __future__ import annotations
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import tz
import pandas as pd
import numpy as np

# ----------------------------
# CONFIG / CONSTANTS
# ----------------------------
WEEK_GLOB = "Week *Loading Slip*.xlsx"  # folder glob; change via --root if needed
WEEKDAY_SHEETS = ["Mon", "Tues", "Wed", "Thurs", "Fri"]
START_MARKERS = re.compile(r"(Our Compliments|DAILY TOTALS)", re.IGNORECASE)
STOP_MARKERS  = re.compile(r"(Small Tally|Carts)", re.IGNORECASE)

# Fallback row ranges if markers aren't found (inclusive indices)
DEFAULT_RANGES = {
    "Mon":   (67, 82),
    "Tues":  (40, 55),
    "Wed":   (39, 54),
    "Thurs": (69, 84),
    "Fri":   (41, 56),
}

LOCAL_TZ = tz.gettz("America/Moncton")

# ----------------------------
# FILENAME PARSING
# ----------------------------
WEEK_FILE_RE = re.compile(r"Week\s+(\d+).*?(\d{4})")

def parse_week_meta(file_name: str) -> tuple[int|None, int|None]:
    """
    Extract (iso_week, year) from file name like 'Week 5 Loading Slip 2025.xlsx'.
    Returns (None, None) if not matched.
    """
    m = WEEK_FILE_RE.search(file_name)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))

# ----------------------------
# PARSER UTILITIES (robust to drift)
# ----------------------------
def _first_index_matching(df: pd.DataFrame, pattern: re.Pattern) -> int | None:
    for idx, row in df.iterrows():
        row_str = " ".join(map(str, row.values))
        if pattern.search(row_str):
            return int(idx)
    return None

def _detect_block(df: pd.DataFrame, day: str) -> tuple[int, int]:
    """
    Detect [start, stop] row indices for the totals block on a weekday sheet:
    - start: row containing 'Our Compliments', or if 'DAILY TOTALS' then start+1
    - stop: row above first 'Small Tally' or 'Carts'
    Fallback: DEFAULT_RANGES
    """
    start_idx = _first_index_matching(df, START_MARKERS)
    stop_idx  = _first_index_matching(df, STOP_MARKERS)

    if start_idx is not None:
        row_str = " ".join(map(str, df.loc[start_idx].values))
        if re.search(r"DAILY TOTALS", row_str, re.IGNORECASE):
            start_idx = start_idx + 1

    if start_idx is None or stop_idx is None:
        start_idx, stop_idx = DEFAULT_RANGES[day]
    else:
        stop_idx = stop_idx - 1

    return start_idx, stop_idx

def _coerce_qty(val) -> float | np.nan:
    try:
        if pd.isna(val): return np.nan
        if isinstance(val, str) and val.strip() == "":
            return np.nan
        return pd.to_numeric(val, errors="coerce")
    except Exception:
        return np.nan

def parse_week_file(file_path: Path) -> pd.DataFrame:
    """
    Returns normalized rows for Mon–Fri:
      file, week_num, year, day, product, boxes
    - Excludes 'Small Tally'/'Carts' and blank products
    - Infers columns if layout drifts (numeric = qty, text = product)
    """
    week_num, year = parse_week_meta(file_path.name)
    records = []

    for day in WEEKDAY_SHEETS:
        try:
            df = pd.read_excel(file_path, sheet_name=day, header=None)
        except Exception:
            continue

        start_idx, stop_idx = _detect_block(df, day)
        block = df.loc[start_idx:stop_idx].copy()

        for _, row in block.iterrows():
            # hard stop if marker text appears (defensive)
            row_str = " ".join(map(str, row.values))
            if STOP_MARKERS.search(row_str):
                continue

            # primary guess: col1=qty, col2=product
            product = row.get(2, None)
            qty = _coerce_qty(row.get(1, None))

            # fallback inference: first non-empty text = product, first numeric = qty
            if (product is None or str(product).strip() == "") or pd.isna(qty):
                prod_candidate, qty_candidate = None, None
                for c in row.index:
                    cell = row[c]
                    # pick a reasonable product candidate
                    if prod_candidate is None and isinstance(cell, str) and cell.strip() and not STOP_MARKERS.search(cell):
                        prod_candidate = cell.strip()
                    # pick first numeric-ish cell as qty
                    if qty_candidate is None and not pd.isna(_coerce_qty(cell)):
                        qty_candidate = _coerce_qty(cell)
                if prod_candidate is not None and qty_candidate is not None:
                    product, qty = prod_candidate, qty_candidate

            # validate & clean
            if product is None or str(product).strip() == "":
                continue
            pname = str(product).strip()
            if STOP_MARKERS.search(pname):
                continue

            if pd.isna(qty):
                qty = 0

            records.append({
                "file": file_path.name,
                "week_num": week_num,
                "year": year,
                "day": day,
                "product": pname,
                "boxes": int(round(qty)),
            })

    return pd.DataFrame.from_records(records)

def load_all_history(root: Path | str = ".") -> pd.DataFrame:
    files = sorted(Path(root).glob(WEEK_GLOB))
    frames = []
    for f in files:
        df = parse_week_file(f)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["file","week_num","year","day","product","boxes"])
    all_df = pd.concat(frames, ignore_index=True)
    # sort chronologically by (year, week_num, file) where possible
    all_df["year"] = pd.to_numeric(all_df["year"], errors="coerce")
    all_df["week_num"] = pd.to_numeric(all_df["week_num"], errors="coerce")
    all_df = all_df.sort_values(["year","week_num","file"], na_position="last").reset_index(drop=True)
    return all_df

# ----------------------------
# FORECASTING IMPROVEMENTS
# ----------------------------
def _detect_outlier_weeks(history: pd.DataFrame, day: str, target_year: int|None=None, target_week: int|None=None) -> set:
    """
    Detect outlier weeks (holidays, shutdowns) that should be excluded from training.
    Returns set of (year, week_num) tuples that are outliers.
    """
    h = history[history["day"] == day].copy()
    if target_year is not None and target_week is not None:
        h = h[(h["year"] < target_year) | ((h["year"] == target_year) & (h["week_num"] < target_week))]
    
    if h.empty:
        return set()
    
    # Group by week and calculate total boxes
    weekly_totals = h.groupby(["year", "week_num"])["boxes"].sum().reset_index()
    
    if len(weekly_totals) < 4:  # Need at least 4 weeks for outlier detection
        return set()
    
    # Use IQR method to detect outliers
    Q1 = weekly_totals["boxes"].quantile(0.25)
    Q3 = weekly_totals["boxes"].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Also flag zero-demand weeks as potential outliers
    outliers = weekly_totals[
        (weekly_totals["boxes"] < lower_bound) | 
        (weekly_totals["boxes"] > upper_bound) |
        (weekly_totals["boxes"] == 0)
    ]
    
    return set(zip(outliers["year"], outliers["week_num"]))

def _calculate_trend(history: pd.DataFrame, day: str, product: str, target_year: int|None=None, target_week: int|None=None) -> float:
    """
    Calculate trend coefficient for a product (positive = growing, negative = declining).
    Returns trend coefficient (slope of linear regression).
    """
    h = history[(history["day"] == day) & (history["product"] == product)].copy()
    if target_year is not None and target_week is not None:
        h = h[(h["year"] < target_year) | ((h["year"] == target_year) & (h["week_num"] < target_week))]
    
    if len(h) < 4:  # Need at least 4 data points for trend
        return 0.0
    
    # Create week index for trend calculation
    h = h.sort_values(["year", "week_num"])
    h["week_index"] = range(len(h))
    
    # Simple linear regression for trend
    x = h["week_index"].values
    y = h["boxes"].values
    
    if len(x) < 2:
        return 0.0
    
    # Calculate slope (trend)
    n = len(x)
    sum_x = x.sum()
    sum_y = y.sum()
    sum_xy = (x * y).sum()
    sum_x2 = (x * x).sum()
    
    if n * sum_x2 - sum_x * sum_x == 0:
        return 0.0
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    return slope

def _last_n_weekday(history: pd.DataFrame, day: str, n: int, target_year: int|None=None, target_week: int|None=None, exclude_outliers: bool = True) -> pd.DataFrame:
    """
    Return last N occurrences (per product) of the given weekday BEFORE (target_year, target_week),
    or from the end if target not provided. Optionally exclude outlier weeks.
    """
    h = history[history["day"] == day].copy()
    if target_year is not None and target_week is not None:
        # keep rows strictly before target (year, week)
        h = h[(h["year"] < target_year) | ((h["year"] == target_year) & (h["week_num"] < target_week))]
    
    if h.empty:
        return h
    
    # Exclude outlier weeks if requested
    if exclude_outliers:
        outlier_weeks = _detect_outlier_weeks(history, day, target_year, target_week)
        h = h[~h.apply(lambda row: (row["year"], row["week_num"]) in outlier_weeks, axis=1)]
    
    if h.empty:
        return h
    
    # For each product, take last N rows (chronological order -> take tail)
    h = h.sort_values(["year","week_num","file"])
    lastn = (h.groupby("product").tail(n))
    return lastn

def _same_week_last_year(history: pd.DataFrame, day: str, week_num: int, year: int) -> pd.DataFrame:
    """
    Return same ISO week number, previous year, for the given weekday.
    """
    h = history[(history["day"] == day) & (history["week_num"] == week_num) & (history["year"] == year - 1)]
    return h[["product","boxes"]].rename(columns={"boxes":"last_year_boxes"})

def forecast_weekday(history: pd.DataFrame, day: str, window: int = 8, alpha: float = 0.7,
                     target_week_num: int | None = None, target_year: int | None = None,
                     use_last_year: bool = True, exclude_outliers: bool = True, 
                     use_trend: bool = True, trend_weight: float = 0.1,
                     conservative_mode: bool = True) -> pd.DataFrame:
    """
    Enhanced forecasting with outlier detection, trend analysis, and improved blending.
    
    Improvements:
    1. Exclude outlier weeks (holidays, shutdowns) from training data
    2. Apply trend analysis for growing/declining products
    3. Use weighted average instead of simple mean
    4. Better handling of seasonal patterns
    """
    # Get recent data excluding outliers
    lastn = _last_n_weekday(history, day, n=window, target_year=target_year, 
                           target_week=target_week_num, exclude_outliers=exclude_outliers)
    if lastn.empty:
        return pd.DataFrame(columns=["product","forecast_boxes"])

    # Calculate weighted average (more recent weeks get higher weight)
    forecasts = []
    for product in lastn["product"].unique():
        product_data = lastn[lastn["product"] == product].copy()
        
        if len(product_data) < 2:
            # Not enough data, use simple mean
            forecast = product_data["boxes"].mean()
        else:
            # Calculate weighted average (exponential decay)
            product_data = product_data.sort_values(["year", "week_num"])
            weights = np.exp(np.linspace(-1, 0, len(product_data)))  # More weight to recent
            weights = weights / weights.sum()  # Normalize
            forecast = (product_data["boxes"] * weights).sum()
            
            # Apply trend if enabled and enough data
            if use_trend and len(product_data) >= 4:
                trend = _calculate_trend(history, day, product, target_year, target_week_num)
                # Apply trend adjustment (trend is per week, so multiply by weeks ahead)
                weeks_ahead = 1  # Forecasting 1 week ahead
                trend_adjustment = trend * weeks_ahead * trend_weight
                forecast = max(0, forecast + trend_adjustment)

        forecasts.append({"product": product, "rolling_boxes": forecast})

    roll = pd.DataFrame(forecasts)

    # Blend with last year (optional)
    if use_last_year and target_week_num is not None and target_year is not None:
        ly = _same_week_last_year(history, day, target_week_num, target_year)
        df = roll.merge(ly, on="product", how="left")
        
        # Enhanced blending: use last year only if it's not an outlier
        if not ly.empty:
            # Check if last year's data is reasonable (not zero or extreme)
            last_year_total = ly["last_year_boxes"].sum()
            recent_total = roll["rolling_boxes"].sum()
            
            if last_year_total > 0 and abs(last_year_total - recent_total) / recent_total < 2.0:
                # Last year data is reasonable, use blending
                df["forecast_boxes"] = (alpha * df["rolling_boxes"] + 
                                      (1 - alpha) * df["last_year_boxes"].fillna(df["rolling_boxes"]))
            else:
                # Last year data is outlier, use only recent data
                df["forecast_boxes"] = df["rolling_boxes"]
        else:
            df["forecast_boxes"] = df["rolling_boxes"]
            
        # Apply conservative mode if enabled
        if conservative_mode:
            # Reduce forecasts by 20% to avoid over-forecasting
            df["forecast_boxes"] = df["forecast_boxes"] * 0.8
            
        df["forecast_boxes"] = df["forecast_boxes"].round().astype(int)
        return df[["product","forecast_boxes"]].sort_values("product").reset_index(drop=True)
    else:
        roll = roll.rename(columns={"rolling_boxes":"forecast_boxes"})
        
        # Apply conservative mode if enabled
        if conservative_mode:
            # Reduce forecasts by 20% to avoid over-forecasting
            roll["forecast_boxes"] = roll["forecast_boxes"] * 0.8
            
        roll["forecast_boxes"] = roll["forecast_boxes"].round().astype(int)
        return roll.sort_values("product").reset_index(drop=True)

def forecast_week(history: pd.DataFrame, target_week_num: int, target_year: int,
                  window: int = 8, alpha: float = 0.7, use_last_year: bool = True) -> dict[str, pd.DataFrame]:
    """
    Build forecasts for Mon–Fri for a target (week_num, year).
    """
    out = {}
    for day in WEEKDAY_SHEETS:
        out[day] = forecast_weekday(history, day, window=window, alpha=alpha,
                                    target_week_num=target_week_num, target_year=target_year,
                                    use_last_year=use_last_year)
    return out

# ----------------------------
# ACTUALS (when orders are released)
# ----------------------------
def actuals_for_day(latest_file: Path, day: str) -> pd.DataFrame:
    df = parse_week_file(latest_file)
    return (df[df["day"] == day][["product","boxes"]]
              .sort_values("product").reset_index(drop=True))

def latest_week_file(root: Path | str = ".") -> Path | None:
    files = sorted(Path(root).glob(WEEK_GLOB))
    return files[-1] if files else None

# ----------------------------
# CLI
# ----------------------------
def main():
    p = argparse.ArgumentParser(description="Egg Room Packing Predictor (Mon–Fri)")
    p.add_argument("--root", default=".", help="Folder containing 'Week *Loading Slip*.xlsx' files")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Actuals
    s_act = sub.add_parser("actuals", help="Read actual totals for a weekday from the latest week file")
    s_act.add_argument("--day", required=True, choices=WEEKDAY_SHEETS, help="Weekday sheet (Mon/Tues/...)")
    s_act.add_argument("--out", help="Optional CSV path to save")

    # Forecast a single weekday (e.g., for next Monday on Thursday)
    s_fc = sub.add_parser("forecast-day", help="Forecast a weekday for a target ISO week+year")
    s_fc.add_argument("--day", required=True, choices=WEEKDAY_SHEETS)
    s_fc.add_argument("--week", type=int, required=True, help="ISO week number to forecast (e.g., next week's week number)")
    s_fc.add_argument("--year", type=int, required=True, help="Year for the target week")
    s_fc.add_argument("--window", type=int, default=8, help="Rolling window in weeks (6–8 recommended)")
    s_fc.add_argument("--alpha", type=float, default=0.7, help="Blend weight for recent vs last-year (0..1)")
    s_fc.add_argument("--no-last-year", action="store_true", help="Disable last-year blending")
    s_fc.add_argument("--include-outliers", action="store_true", help="Include outlier weeks in training (not recommended)")
    s_fc.add_argument("--no-trend", action="store_true", help="Disable trend analysis")
    s_fc.add_argument("--trend-weight", type=float, default=0.1, help="Weight for trend adjustment (0.0-0.5)")
    s_fc.add_argument("--no-conservative", action="store_true", help="Disable conservative mode (may over-forecast)")
    s_fc.add_argument("--out", help="Optional CSV path to save")

    # Forecast all weekdays for a target week (Mon–Fri at once)
    s_fcw = sub.add_parser("forecast-week", help="Forecast Mon–Fri for target ISO week+year")
    s_fcw.add_argument("--week", type=int, required=True)
    s_fcw.add_argument("--year", type=int, required=True)
    s_fcw.add_argument("--window", type=int, default=8)
    s_fcw.add_argument("--alpha", type=float, default=0.7)
    s_fcw.add_argument("--no-last-year", action="store_true")
    s_fcw.add_argument("--outdir", help="Optional folder to write CSVs per day")

    # Convenience: forecast next week (infer from latest file)
    s_next = sub.add_parser("forecast-next-week", help="Infer next ISO week from latest file and forecast Mon–Fri")
    s_next.add_argument("--window", type=int, default=8)
    s_next.add_argument("--alpha", type=float, default=0.7)
    s_next.add_argument("--no-last-year", action="store_true")
    s_next.add_argument("--outdir", help="Optional folder to write CSVs per day")

    args = p.parse_args()
    root = args.root
    history = load_all_history(root)

    if args.cmd == "actuals":
        lf = latest_week_file(root)
        if lf is None:
            print("No week files found.")
            return
        df = actuals_for_day(lf, args.day)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(args.out, index=False)
        print(df.to_string(index=False))
        return

    if args.cmd == "forecast-day":
        use_ly = not args.no_last_year
        exclude_outliers = not args.include_outliers
        use_trend = not args.no_trend
        conservative_mode = not args.no_conservative
        df = forecast_weekday(history, args.day, window=args.window, alpha=args.alpha,
                              target_week_num=args.week, target_year=args.year,
                              use_last_year=use_ly, exclude_outliers=exclude_outliers,
                              use_trend=use_trend, trend_weight=args.trend_weight,
                              conservative_mode=conservative_mode)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(args.out, index=False)
        print(df.to_string(index=False))
        return

    if args.cmd == "forecast-week":
        use_ly = not args.no_last_year
        forecasts = forecast_week(history, args.week, args.year,
                                  window=args.window, alpha=args.alpha, use_last_year=use_ly)
        if args.outdir:
            outdir = Path(args.outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            for day, df in forecasts.items():
                df.to_csv(outdir / f"{args.year}-W{args.week:02d}_{day}.csv", index=False)
        # pretty print
        for day, df in forecasts.items():
            print(f"\n=== {day} ===")
            print(df.to_string(index=False))
        return

    if args.cmd == "forecast-next-week":
        lf = latest_week_file(root)
        if lf is None:
            print("No week files found.")
            return
        cur_week, cur_year = parse_week_meta(lf.name)
        if cur_week is None or cur_year is None:
            print(f"Cannot infer current week/year from {lf.name}")
            return
        # naive next week; you can refine for year boundary if needed
        next_week, next_year = cur_week + 1, cur_year
        # handle year rollover (ISO week can go to 53)
        if next_week > 53:  # safe guard
            next_week = 1
            next_year = cur_year + 1
        use_ly = not args.no_last_year
        forecasts = forecast_week(history, next_week, next_year,
                                  window=args.window, alpha=args.alpha, use_last_year=use_ly)
        if args.outdir:
            outdir = Path(args.outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            for day, df in forecasts.items():
                df.to_csv(outdir / f"{next_year}-W{next_week:02d}_{day}.csv", index=False)
        for day, df in forecasts.items():
            print(f"\n=== {day} (next week) ===")
            print(df.to_string(index=False))
        return

if __name__ == "__main__":
    main()
