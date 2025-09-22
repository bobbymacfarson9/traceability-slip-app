# egg_packing_predictor_universal.py
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
# UNIVERSAL PARSER (handles different column structures per day)
# ----------------------------

def parse_daily_totals_universal(file_path: Path, sheet: str) -> pd.DataFrame:
    """Parse Daily Totals section handling different column structures per day"""
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    file_name = file_path.name
    week_num, year = parse_week_meta(file_name)
    
    records = []
    
    # Find the Daily Totals section
    daily_totals_start = None
    daily_totals_end = None
    
    for idx, row in df.iterrows():
        row_str = " ".join(str(cell) for cell in row.values if pd.notna(cell))
        
        # Look for "DAILY TOTALS" marker
        if "DAILY TOTALS" in row_str.upper():
            daily_totals_start = idx + 1  # Start after the header
            break
    
    if daily_totals_start is None:
        return pd.DataFrame(columns=["file", "day", "product", "boxes", "week_num", "year"])
    
    # Find the end of Daily Totals section
    for idx in range(daily_totals_start, len(df)):
        row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
        if "SMALL TALLY" in row_str.upper() or "CARTS" in row_str.upper() or "SPECIALTY" in row_str.upper():
            daily_totals_end = idx - 1
            break
    
    if daily_totals_end is None:
        daily_totals_end = len(df) - 1
    
    # Find the header row that shows the column structure
    header_row = None
    for idx in range(daily_totals_start, daily_totals_end + 1):
        row_str = " ".join(str(cell) for cell in df.iloc[idx].values if pd.notna(cell))
        if "Our Compliments" in row_str or "Walmart" in row_str or "Loblaws" in row_str or "Eyking" in row_str:
            header_row = idx
            break
    
    if header_row is None:
        return pd.DataFrame(columns=["file", "day", "product", "boxes", "week_num", "year"])
    
    # Parse data rows (skip the header row)
    for idx in range(header_row + 1, daily_totals_end + 1):
        row = df.iloc[idx]
        row_values = [str(cell) if pd.notna(cell) else "" for cell in row.values]
        
        # Skip empty rows
        if not any(v.strip() for v in row_values):
            continue
        
        # Handle different day structures
        if sheet == "Mon":
            _parse_mon_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Tues":
            _parse_tues_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Wed":
            _parse_wed_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Thurs":
            _parse_thurs_structure(row_values, idx, records, file_name, sheet, week_num, year)
        elif sheet == "Fri":
            _parse_fri_structure(row_values, idx, records, file_name, sheet, week_num, year)
    
    return pd.DataFrame.from_records(records)

def _parse_mon_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Monday structure: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[2], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[5], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[8], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[11], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass

def _parse_tues_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Tuesday structure: Our Compliments (B,C), Walmart (D,E), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[2], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Walmart: Column D (quantity), Column E (product)
    if len(row_values) > 4 and row_values[3].strip() and row_values[4].strip():
        try:
            qty = float(row_values[3])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[4], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[8], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[11], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass

def _parse_wed_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Wednesday structure: Our Compliments (B,C), Walmart (D,E), Loblaws (G,H), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[2], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Walmart: Column D (quantity), Column E (product)
    if len(row_values) > 4 and row_values[3].strip() and row_values[4].strip():
        try:
            qty = float(row_values[3])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[4], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Loblaws: Column G (product), Column H (quantity)
    if len(row_values) > 8 and row_values[6].strip() and row_values[7].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[6], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product) - FIXED: was looking in wrong columns
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[11], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass

def _parse_thurs_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Thursday structure: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product) - FIXED: was looking in wrong columns
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[2], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[5], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product) - FIXED: was looking in wrong columns
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[8], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[11], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass

def _parse_fri_structure(row_values, idx, records, file_name, sheet, week_num, year):
    """Parse Friday structure: Our Compliments (B,C), Walmart (E,F), Loblaws (H,I), Eyking (K,L)"""
    # Our Compliments: Column B (quantity), Column C (product)
    if len(row_values) > 2 and row_values[1].strip() and row_values[2].strip():
        try:
            qty = float(row_values[1])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[2], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Walmart: Column E (quantity), Column F (product)
    if len(row_values) > 5 and row_values[4].strip() and row_values[5].strip():
        try:
            qty = float(row_values[4])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[5], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Loblaws: Column H (quantity), Column I (product)
    if len(row_values) > 8 and row_values[7].strip() and row_values[8].strip():
        try:
            qty = float(row_values[7])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[8], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass
    
    # Eyking: Column K (quantity), Column L (product)
    if len(row_values) > 11 and row_values[10].strip() and row_values[11].strip():
        try:
            qty = float(row_values[10])
            if qty > 0:
                record = _create_record(file_name, sheet, week_num, year, row_values[11], qty)
                if record:
                    records.append(record)
        except ValueError:
            pass

def _create_record(file_name, sheet, week_num, year, product, qty):
    """Create a standardized record"""
    # Validate that product is not just a number
    if product.isdigit():
        return None
    
    return {
        "file": file_name,
        "day": sheet,
        "product": product,
        "boxes": int(qty),
        "week_num": week_num,
        "year": year
    }

def parse_week_file(file_path: Path) -> pd.DataFrame:
    """
    Returns normalized rows for Mon–Fri using universal parser:
    file, week_num, year, day, product, boxes
    """
    week_num, year = parse_week_meta(file_path.name)
    records = []
    
    for day in WEEKDAY_SHEETS:
        try:
            day_data = parse_daily_totals_universal(file_path, day)
            if not day_data.empty:
                records.append(day_data)
        except Exception as e:
            print(f"Error parsing {file_path.name} sheet {day}: {e}")
            continue
    
    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame(columns=["file","week_num","year","day","product","boxes"])

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
# FORECASTING
# ----------------------------

def _last_n_weekday(history: pd.DataFrame, day: str, n: int, target_year: int|None=None, target_week: int|None=None, exclude_outliers: bool = True) -> pd.DataFrame:
    """
    Return last N occurrences (per product) of the given weekday BEFORE (target_year, target_week), or from the end if target not provided.
    """
    h = history[history["day"] == day].copy()
    if target_year is not None and target_week is not None:
        # keep rows strictly before target (year, week)
        h = h[(h["year"] < target_year) | ((h["year"] == target_year) & (h["week_num"] < target_week))]
    if h.empty:
        return h
    
    # For each product, take last N rows (chronological order -> take tail)
    h = h.sort_values(["year","week_num","file"])
    
    if exclude_outliers:
        # Detect and exclude outlier weeks for each product
        outlier_weeks = _detect_outlier_weeks(h)
        h = h[~h['week_num'].isin(outlier_weeks)]
    
    lastn = (h.groupby("product").tail(n))
    return lastn

def _detect_outlier_weeks(history: pd.DataFrame) -> set:
    """Detect weeks with outlier demand patterns using IQR method"""
    if history.empty:
        return set()
    
    # Group by week and calculate total demand
    weekly_totals = history.groupby(['year', 'week_num'])['boxes'].sum().reset_index()
    
    if len(weekly_totals) < 4:  # Need at least 4 weeks for IQR
        return set()
    
    # Calculate IQR
    Q1 = weekly_totals['boxes'].quantile(0.25)
    Q3 = weekly_totals['boxes'].quantile(0.75)
    IQR = Q3 - Q1
    
    # Define outliers (beyond 1.5 * IQR)
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Find outlier weeks
    outliers = weekly_totals[
        (weekly_totals['boxes'] < lower_bound) | 
        (weekly_totals['boxes'] > upper_bound)
    ]
    
    return set(outliers['week_num'].tolist())

def _calculate_trend(history: pd.DataFrame, product: str, day: str) -> float:
    """Calculate trend for a specific product on a specific day"""
    product_data = history[(history['product'] == product) & (history['day'] == day)].copy()
    
    if len(product_data) < 3:
        return 0.0
    
    # Sort by time
    product_data = product_data.sort_values(['year', 'week_num'])
    
    # Calculate trend using linear regression
    x = np.arange(len(product_data))
    y = product_data['boxes'].values
    
    # Simple linear regression
    slope = np.polyfit(x, y, 1)[0]
    
    # Normalize trend (percentage change per week)
    if len(y) > 0 and y.mean() > 0:
        trend_pct = (slope / y.mean()) * 100
        return max(-10, min(10, trend_pct))  # Cap at ±10% per week
    
    return 0.0

def _same_week_last_year(history: pd.DataFrame, day: str, week_num: int, year: int) -> pd.DataFrame:
    """Return same ISO week number, previous year, for the given weekday."""
    h = history[(history["day"] == day) & (history["week_num"] == week_num) & (history["year"] == year - 1)]
    return h[["product","boxes"]].rename(columns={"boxes":"last_year_boxes"})

def forecast_weekday(history: pd.DataFrame, day: str, window: int = 8, alpha: float = 0.7, target_week_num: int | None = None, target_year: int | None = None, use_last_year: bool = True, include_outliers: bool = False, use_trend: bool = True, trend_weight: float = 0.1, conservative_mode: bool = True) -> pd.DataFrame:
    """
    Enhanced forecasting with outlier detection, trend analysis, and weighted averages.
    """
    # recent rolling
    lastn = _last_n_weekday(history, day, n=window, target_year=target_year, target_week=target_week_num, exclude_outliers=not include_outliers)
    if lastn.empty:
        return pd.DataFrame(columns=["product","forecast_boxes"])
    
    # Calculate weighted rolling average (more recent weeks get higher weight)
    forecasts = []
    for product in lastn['product'].unique():
        product_data = lastn[lastn['product'] == product].copy()
        
        if len(product_data) == 0:
            continue
        
        # Sort by time (most recent last)
        product_data = product_data.sort_values(['year', 'week_num'])
        
        # Calculate weighted average (exponential decay)
        weights = np.exp(np.linspace(-1, 0, len(product_data)))
        weights = weights / weights.sum()
        
        weighted_avg = np.average(product_data['boxes'].values, weights=weights)
        
        # Apply trend adjustment if enabled
        if use_trend:
            trend = _calculate_trend(history, product, day)
            trend_adjustment = weighted_avg * (trend / 100) * trend_weight
            weighted_avg += trend_adjustment
        
        forecasts.append({
            'product': product,
            'rolling_boxes': weighted_avg
        })
    
    if not forecasts:
        return pd.DataFrame(columns=["product","forecast_boxes"])
    
    roll = pd.DataFrame(forecasts)
    
    # blend with last year (optional)
    if use_last_year and target_week_num is not None and target_year is not None:
        ly = _same_week_last_year(history, day, target_week_num, target_year)
        df = roll.merge(ly, on="product", how="left")
        # if last-year missing, fall back to rolling only
        df["forecast_boxes"] = (alpha * df["rolling_boxes"] + (1 - alpha) * df["last_year_boxes"].fillna(df["rolling_boxes"]))
        result = df[["product","forecast_boxes"]].sort_values("product").reset_index(drop=True)
    else:
        roll = roll.rename(columns={"rolling_boxes":"forecast_boxes"})
        result = roll.sort_values("product").reset_index(drop=True)
    
    # Apply conservative mode (multiply by 0.8 to reduce over-forecasting)
    if conservative_mode:
        result["forecast_boxes"] = (result["forecast_boxes"] * 0.8).round().astype(int)
    else:
        result["forecast_boxes"] = result["forecast_boxes"].round().astype(int)
    
    return result

def forecast_week(history: pd.DataFrame, target_week_num: int, target_year: int, window: int = 8, alpha: float = 0.7, use_last_year: bool = True, include_outliers: bool = False, use_trend: bool = True, trend_weight: float = 0.1, conservative_mode: bool = True) -> dict[str, pd.DataFrame]:
    """Build forecasts for Mon–Fri for a target (week_num, year)."""
    out = {}
    for day in WEEKDAY_SHEETS:
        out[day] = forecast_weekday(history, day, window=window, alpha=alpha, target_week_num=target_week_num, target_year=target_year, use_last_year=use_last_year, include_outliers=include_outliers, use_trend=use_trend, trend_weight=trend_weight, conservative_mode=conservative_mode)
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
    p = argparse.ArgumentParser(description="Egg Room Packing Predictor (Mon–Fri) - Universal Parser")
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
    s_fc.add_argument("--include-outliers", action="store_true", help="Include outlier weeks in forecasting")
    s_fc.add_argument("--no-trend", action="store_true", help="Disable trend analysis")
    s_fc.add_argument("--trend-weight", type=float, default=0.1, help="Weight for trend adjustment (0..1)")
    s_fc.add_argument("--no-conservative", action="store_true", help="Disable conservative mode (0.8x multiplier)")
    s_fc.add_argument("--out", help="Optional CSV path to save")
    
    # Forecast all weekdays for a target week (Mon–Fri at once)
    s_fcw = sub.add_parser("forecast-week", help="Forecast Mon–Fri for target ISO week+year")
    s_fcw.add_argument("--week", type=int, required=True)
    s_fcw.add_argument("--year", type=int, required=True)
    s_fcw.add_argument("--window", type=int, default=8)
    s_fcw.add_argument("--alpha", type=float, default=0.7)
    s_fcw.add_argument("--no-last-year", action="store_true")
    s_fcw.add_argument("--include-outliers", action="store_true")
    s_fcw.add_argument("--no-trend", action="store_true")
    s_fcw.add_argument("--trend-weight", type=float, default=0.1)
    s_fcw.add_argument("--no-conservative", action="store_true")
    s_fcw.add_argument("--outdir", help="Optional folder to write CSVs per day")
    
    # Convenience: forecast next week (infer from latest file)
    s_next = sub.add_parser("forecast-next-week", help="Infer next ISO week from latest file and forecast Mon–Fri")
    s_next.add_argument("--window", type=int, default=8)
    s_next.add_argument("--alpha", type=float, default=0.7)
    s_next.add_argument("--no-last-year", action="store_true")
    s_next.add_argument("--include-outliers", action="store_true")
    s_next.add_argument("--no-trend", action="store_true")
    s_next.add_argument("--trend-weight", type=float, default=0.1)
    s_next.add_argument("--no-conservative", action="store_true")
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
        use_trend = not args.no_trend
        conservative = not args.no_conservative
        df = forecast_weekday(history, args.day, window=args.window, alpha=args.alpha, target_week_num=args.week, target_year=args.year, use_last_year=use_ly, include_outliers=args.include_outliers, use_trend=use_trend, trend_weight=args.trend_weight, conservative_mode=conservative)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(args.out, index=False)
        print(df.to_string(index=False))
        return
    
    if args.cmd == "forecast-week":
        use_ly = not args.no_last_year
        use_trend = not args.no_trend
        conservative = not args.no_conservative
        forecasts = forecast_week(history, args.week, args.year, window=args.window, alpha=args.alpha, use_last_year=use_ly, include_outliers=args.include_outliers, use_trend=use_trend, trend_weight=args.trend_weight, conservative_mode=conservative)
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
        use_trend = not args.no_trend
        conservative = not args.no_conservative
        forecasts = forecast_week(history, next_week, next_year, window=args.window, alpha=args.alpha, use_last_year=use_ly, include_outliers=args.include_outliers, use_trend=use_trend, trend_weight=args.trend_weight, conservative_mode=conservative)
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
