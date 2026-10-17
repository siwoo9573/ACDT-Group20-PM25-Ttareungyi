# Does fine dust (PM2.5) reduce Seoul's Ttareungyi bike rentals?

ACDT 2026-2 Group Project 1 · Group 20 (Hanyang University)

**Webpage:** https://siwoo9573.github.io/ACDT-Group20-PM25-Ttareungyi/  (open `index.html` locally if Pages is off)

## Repository structure
| Path | Contents |
|---|---|
| `index.html` | Data-story webpage (single file, maps embedded) |
| `data/Group20_통합데이터_v3_final.xlsx` | Merged daily dataset, 731 days (2024-01-01 to 2025-12-31); formulas stored as values |
| `data/stations_union_2312_2512_hangang.csv` | 2,904 stations with lat/lon and distance to the Han River (`hangang_500`, `hangang_1km`) |
| `data/roundtrip_daily.csv` | Daily round-trip / one-way counts from trip-level history |
| `data/web_materials.xlsx` | All numbers used on the webpage |
| `data/results_table.xlsx` | Full DML results and day-off vs workday difference tests |
| `code/Group20_W6_DML_wonjae.ipynb` | DML analysis (reads `../data/Group20_통합데이터_v3_final.xlsx`) |
| `code/make_roundtrip_daily.py` | Builds `roundtrip_daily.csv` from trip-level history zips |
| `results/` | Figures, carbon scenario note, trip comparison tables |

## Data sources
| Data | Source |
|---|---|
| Daily rentals by station | Seoul Open Data Plaza OA-15246 |
| Station locations (snapshots 2023-12, 2024-06, 2024-12, 2025-06, 2025-12) | Seoul Open Data Plaza OA-13252 |
| Trip-level rental history (rental / return station) | Seoul Open Data Plaza OA-15182 |
| PM2.5 daily average | Seoul Open Data Plaza OA-2220 |
| Weather (temperature, rain, wind, humidity, sunshine, cloud) | KMA ASOS station 108 (Seoul) |
| Han River water polygon | [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL](https://opendatacommons.org/licenses/odbl/1-0/) |

Raw trip-level files are several GB and are not stored here; download them from the sources above.

Han River classification uses straight-line distance to OSM water polygons in EPSG:5186. The classification script is not included; the resulting station CSV is provided.

## Analysis rules (fixed in advance)
- Sample: 727 days = 731 days − 3 days with missing wind (2024-03-11, 03-12, 03-14) − 2025-02-28 (truncated source file).
- Han River station: straight-line distance to the water boundary ≤ 500 m (159 stations) or ≤ 1 km (405).
- Round trip: rental station = return station; same-station returns of ≤ 2 minutes and missing stations excluded.
- DML: partially linear model, random forest / gradient boosting, 5-fold cross-fitting, median of 5 seeds, cross-fitted standard errors (Newey–West only for regressions).

## How to reproduce
1. `pip install pandas numpy scipy scikit-learn openpyxl`
2. Open `code/Group20_W6_DML_wonjae.ipynb` from the `code/` folder and run all cells.
3. (Optional) Rebuild round trips: `python code/make_roundtrip_daily.py --zips <2024.zip> <2025.zip> --stations data/stations_union_2312_2512_hangang.csv --out data/roundtrip_daily.csv`

## Team
Yoon Junsang · Byun Yisol · Shin Sua · Choi Seoyun · Lee Siwoo · Sung Wonjae
