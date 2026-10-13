"""
Build roundtrip_daily.csv from Seoul Ttareungyi trip-level rental history (OA-15182).

Usage (from a terminal, in the folder that contains this script):
    python make_roundtrip_daily.py --zips 2024.zip 2025.zip \
        --stations stations_union_2312_2512_hangang.csv \
        --out roundtrip_daily.csv

- The zip files do NOT need to be unzipped. The script reads every CSV inside them in chunks,
  so it works on a normal laptop even though the data is several GB.
- If you already unzipped them, pass the CSV files with --csvs instead of --zips.

Rules (fixed before seeing any results):
- Date = rental date (from the rental datetime column), not the return date.
- Round trip = rental station number == return station number.
- One-way   = rental station number != return station number.
- Excluded  = same-station returns with use time <= 2 minutes (likely bike swaps / cancellations),
              or rows with a missing rental/return station.
- Only rentals dated 2024-01-01 to 2025-12-31 are kept.
"""
import argparse
import io
import sys
import zipfile

import pandas as pd

# Possible column names (Korean CSV headers and OpenAPI names). The script picks the first match.
CANDIDATES = {
    "rent_dt": ["대여일시", "대여 일시", "RENT_DT"],
    "rent_st": ["대여 대여소번호", "대여대여소번호", "대여소번호", "RENT_ID"],
    "rtn_st": ["반납대여소번호", "반납 대여소번호", "RTN_ID"],
    "use_min": ["이용시간(분)", "이용시간", "사용(분)", "USE_MIN"],
}
CHUNK = 100_000
START, END = "2024-01-01", "2025-12-31"


def pick_columns(header):
    clean = {h.strip().replace("﻿", ""): h for h in header}
    found = {}
    for key, names in CANDIDATES.items():
        for n in names:
            if n in clean:
                found[key] = clean[n]
                break
        if key not in found:
            sys.exit(f"[ERROR] Could not find a column for '{key}'. Header is: {list(clean)}\n"
                     f"Send this header line to Junsang.")
    return found


def detect_encoding(opener):
    # Look at the first 1 MB only, so large files are never loaded fully into memory.
    with opener() as f:
        sample = f.read(1_000_000)
    for enc in ("cp949", "utf-8-sig"):
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError as e:
            if e.start > len(sample) - 4:  # cut in the middle of a character at the edge
                return enc
    sys.exit("[ERROR] Could not decode file as cp949 or utf-8.")


def to_station(s):
    # Station numbers may come as '00102' or '102' or '102.0'. Normalize to integers.
    return pd.to_numeric(s.astype(str).str.strip().str.lstrip("0").replace("", "0"), errors="coerce")


def process_csv(opener, name, han500, acc):
    enc = detect_encoding(opener)
    with opener() as f:
        header = pd.read_csv(io.TextIOWrapper(f, encoding=enc), nrows=0).columns.tolist()
    cols = pick_columns(header)
    print(f"  reading {name} ({enc}) | columns used: {cols}")
    f = opener()
    text_io = io.TextIOWrapper(f, encoding=enc, errors="replace")
    reader = pd.read_csv(text_io, usecols=list(cols.values()), dtype=str, chunksize=CHUNK)
    n = 0
    for ch in reader:
        ch = ch.rename(columns={v: k for k, v in cols.items()})
        date = pd.to_datetime(ch["rent_dt"].str.strip(), errors="coerce").dt.strftime("%Y-%m-%d")
        rs, ts = to_station(ch["rent_st"]), to_station(ch["rtn_st"])
        minutes = pd.to_numeric(ch["use_min"], errors="coerce")

        same = rs == ts
        missing = rs.isna() | ts.isna()
        excluded = missing | (same & (minutes <= 2))
        round_trip = same & ~excluded
        one_way = ~same & ~excluded
        near = rs.isin(han500)

        df = pd.DataFrame({
            "date": date,
            "round_trip": round_trip.astype(int),
            "one_way": one_way.astype(int),
            "excluded": excluded.astype(int),
            "round_trip_han500": (round_trip & near).astype(int),
            "one_way_han500": (one_way & near).astype(int),
            "total_rows": 1,
        })
        df = df[(df["date"] >= START) & (df["date"] <= END)]
        acc.append(df.groupby("date").sum())
        n += len(ch)
    f.close()
    print(f"    rows read: {n:,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", nargs="*", default=[])
    ap.add_argument("--csvs", nargs="*", default=[])
    ap.add_argument("--stations", required=True)
    ap.add_argument("--out", default="roundtrip_daily.csv")
    a = ap.parse_args()

    st = pd.read_csv(a.stations, encoding="utf-8-sig")
    han500 = set(st.loc[st["hangang_500"] == 1, "station_id"].astype(int))
    print(f"Han River 500m stations: {len(han500)}")

    acc = []
    for z in a.zips:
        zf = zipfile.ZipFile(z)
        for info in zf.infolist():
            if info.filename.lower().endswith(".csv"):
                process_csv(lambda info=info: zf.open(info), f"{z}:{info.filename}", han500, acc)
    for c in a.csvs:
        process_csv(lambda c=c: open(c, "rb"), c, han500, acc)

    if not acc:
        sys.exit("[ERROR] No CSV files were read.")
    out = pd.concat(acc).groupby(level=0).sum().reset_index()
    out = out.sort_values("date")
    out.to_csv(a.out, index=False, encoding="utf-8-sig")

    print("\n=== Summary ===")
    print(f"days: {len(out)} ({out['date'].min()} ~ {out['date'].max()})")
    tot = out[["round_trip", "one_way", "excluded"]].sum()
    print(f"round trip: {tot['round_trip']:,} | one-way: {tot['one_way']:,} | excluded: {tot['excluded']:,}")
    print(f"round-trip share (of kept): {tot['round_trip'] / (tot['round_trip'] + tot['one_way']):.1%}")
    print(f"days with 0 round trips: {(out['round_trip'] == 0).sum()}")
    print(f"saved -> {a.out}")


if __name__ == "__main__":
    main()
