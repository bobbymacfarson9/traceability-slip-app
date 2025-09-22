# egg_loading_slip_parser.py
# Python 3.10+
# pip install pandas openpyxl

from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd


# ----------------------------
# Marker patterns & defaults
# ----------------------------
START_PATTERNS = {
    "DAILY_TOTALS": re.compile(r"DAILY\s*TOTALS", re.IGNORECASE),
    "OUR_COMPLIMENTS": re.compile(r"Our\s*Compliments", re.IGNORECASE),
    "SMALL_TALLY": re.compile(r"Small\s*Tally", re.IGNORECASE),
    "CARTS": re.compile(r"Carts?", re.IGNORECASE),
}

# Fallback row ranges if markers aren't found (inclusive indices)
DEFAULT_RANGES = {
    "Mon":   (67, 82),
    "Tues":  (40, 55),
    "Wed":   (39, 54),
    "Thurs": (69, 84),
    "Fri":   (41, 56),
}


# ----------------------------
# Low-level helpers
# ----------------------------
def first_index_matching(df: pd.DataFrame, pat: re.Pattern) -> Optional[int]:
    """Return first row index where ANY cell matches regex; else None."""
    mask = df.apply(lambda r: r.astype(str).str.contains(pat).any(), axis=1)
    idxs = df.index[mask]
    return int(idxs[0]) if len(idxs) else None


def find_markers(df: pd.DataFrame) -> Dict[str, Optional[int]]:
    return {k: first_index_matching(df, p) for k, p in START_PATTERNS.items()}


def detect_totals_block(df: pd.DataFrame, day: str) -> Tuple[int, int]:
    """
    Detect [start, stop] for the Daily Totals (inclusive indices).
    Strategy:
      - start at 'Our Compliments' row (preferred) OR 'DAILY TOTALS' + 1 row
      - stop at first of ('Small Tally', 'Carts') - 1
      - fallback to default ranges if markers not found
    """
    marks = find_markers(df)
    start = marks["OUR_COMPLIMENTS"]
    if start is None and marks["DAILY_TOTALS"] is not None:
        start = marks["DAILY_TOTALS"] + 1
    stops = [i for i in (marks["SMALL_TALLY"], marks["CARTS"]) if i is not None]
    stop = min(stops) - 1 if stops else None
    if start is None or stop is None:
        start, stop = DEFAULT_RANGES.get(day, (None, None))
    return start, stop


def detect_section_after(df: pd.DataFrame, marker_key: str, next_markers: List[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Return (start, stop) for a section beginning AFTER 'marker_key' row,
    ending BEFORE the earliest of next_markers.
    If marker not found -> (None, None).
    """
    marks = find_markers(df)
    start_marker = marks.get(marker_key, None)
    if start_marker is None:
        return None, None
    start = start_marker + 1
    next_idxs = [marks[k] for k in next_markers if marks.get(k) is not None]
    stop = min(next_idxs) - 1 if next_idxs else df.index.max()
    if start is not None and stop is not None and start > stop:
        return None, None
    return start, stop


def coerce_qty(cell):
    try:
        if pd.isna(cell):
            return np.nan
        if isinstance(cell, str):
            s = cell.strip()
            if s == "":
                return np.nan
        return pd.to_numeric(cell, errors="coerce")
    except Exception:
        return np.nan


def row_to_product_qty(row: pd.Series) -> Tuple[Optional[str], Optional[float]]:
    """
    Heuristic extraction per row:
      - product = the longest non-empty text cell that isn't a unit/retailer token
      - qty = the first non-zero numeric-looking cell (or max if all zeros)
    """
    texts: List[str] = []
    nums: List[float] = []
    skip_tokens = {"pcs", "case", "cases", "ea", "each", "pk", "pack", "pks", "walmart", "sobeys", "superstore", "co-op"}
    for c in row.index:
        val = row[c]
        q = coerce_qty(val)
        if not pd.isna(q):
            nums.append(q)
        if isinstance(val, str):
            s = val.strip()
            if s and not s.isnumeric() and s.lower() not in skip_tokens:
                texts.append(s)
    product = max(texts, key=len) if texts else None
    qty = None
    if nums:
        nonzero = [n for n in nums if n != 0]
        qty = nonzero[0] if nonzero else max(nums)
    return product, qty


def parse_section(df: pd.DataFrame, start: Optional[int], stop: Optional[int], day: str, section: str, file_name: str) -> pd.DataFrame:
    if start is None or stop is None:
        return pd.DataFrame(columns=["file","day","section","product","qty"])
    block = df.loc[start:stop]
    records = []
    for _, row in block.iterrows():
        product, qty = row_to_product_qty(row)
        if product is None and (pd.isna(qty) or qty is None):
            continue
        if product is None:
            for alt_col in [2, 1, 0, 3, 4]:
                if alt_col in row and isinstance(row[alt_col], str) and row[alt_col].strip():
                    product = row[alt_col].strip()
                    break
        records.append({
            "file": file_name,
            "day": day,
            "section": section,
            "product": product,
            "qty": None if (qty is None or pd.isna(qty)) else float(qty)
        })
    return pd.DataFrame.from_records(records)


def parse_sheet(file_path: Path, sheet: str) -> Dict[str, pd.DataFrame]:
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    # DAILY TOTALS
    totals_start, totals_stop = detect_totals_block(df, sheet)
    totals_df = parse_section(df, totals_start, totals_stop, sheet, "DAILY_TOTALS", file_path.name)
    # SMALL TALLY
    st_start, st_stop = detect_section_after(df, "SMALL_TALLY", ["CARTS"])
    small_tally_df = parse_section(df, st_start, st_stop, sheet, "SMALL_TALLY", file_path.name)
    # CARTS
    carts_start, carts_stop = detect_section_after(df, "CARTS", [])
    carts_df = parse_section(df, carts_start, carts_stop, sheet, "CARTS", file_path.name)
    return {
        "DAILY_TOTALS": totals_df,
        "SMALL_TALLY": small_tally_df,
        "CARTS": carts_df
    }


def parse_file(file_path: Path, days: List[str] = ["Mon","Tues","Wed","Thurs","Fri"]) -> pd.DataFrame:
    frames = []
    for day in days:
        try:
            out = parse_sheet(file_path, day)
            for sec_df in out.values():
                if not sec_df.empty:
                    frames.append(sec_df)
        except Exception as e:
            frames.append(pd.DataFrame([{
                "file": file_path.name,
                "day": day,
                "section": "ERROR",
                "product": f"Error: {e}",
                "qty": None
            }]))
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=["file","day","section","product","qty"])


def parse_folder(root: Path | str = ".", glob: str = "Week *Loading Slip*.xlsx") -> pd.DataFrame:
    files = sorted(Path(root).glob(glob))
    frames = []
    for f in files:
        frames.append(parse_file(f))
    if not frames:
        return pd.DataFrame(columns=["file","day","section","product","qty"])
    return pd.concat(frames, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description="Parse Daily Totals, Small Tally, and Carts from weekly loading slips (Mon–Fri).")
    ap.add_argument("--root", default=".", help="Folder containing week files")
    ap.add_argument("--glob", default="Week *Loading Slip*.xlsx", help="Glob pattern for week files")
    ap.add_argument("--outdir", default="./parsed_loading_slips", help="Output directory for CSVs")
    ap.add_argument("--split-per-file", action="store_true", help="Also write one CSV per input file")
    args = ap.parse_args()

    root = Path(args.root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_data = parse_folder(root, args.glob)
    master_path = outdir / "all_parsed_totals_tally_carts.csv"
    all_data.to_csv(master_path, index=False)

    if args.split_per_file and not all_data.empty:
        for fname, sub in all_data.groupby("file"):
            (outdir / f"{Path(fname).stem}_parsed.csv").write_text(sub.to_csv(index=False))

    print(f"Wrote master CSV: {master_path}")
    print(f"Rows parsed: {len(all_data)}")
    if not all_data.empty:
        print("\nSample (first 20 rows):")
        print(all_data.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
