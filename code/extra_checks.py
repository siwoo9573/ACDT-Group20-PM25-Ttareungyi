"""
Reproduces three numbers shown on the webpage that are not in the main DML notebook output:
  1) Han River 500 m share of all rides (6.2%)
  2) Season-by-season least-squares slope of daily rides on PM2.5 (per +10 ug/m3)
  3) DML effect of a Bad-air day (PM2.5 > 35, Very Bad merged) on daily rides (RF, +1.1%)

Run from the code/ folder:  python extra_checks.py
Uses the same load() and dml() functions as Group20_W6_DML_wonjae.ipynb.
"""
import json
import numpy as np

nb = json.load(open("Group20_W6_DML_wonjae.ipynb", encoding="utf-8"))
g = {}
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if cell["cell_type"] == "code" and ("def load" in src or "def dml" in src):
        exec(src, g)

d = g["load"]()
base = d[(d.truncated_flag == 0) & d.wind.notna()].copy()  # 727 days
print(f"days: {len(base)}  total rides: {int(base.total.sum()):,}")

# 1) Han River 500 m share of all rides
print(f"Han River 500 m share of all rides: {base.h500.sum() / base.total.sum():.2%}")

# 2) Season slopes (descriptive least-squares lines, not causal)
season = base.month.map({12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
                         6: "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall"})
print(f"All days slope per +10 ug/m3: {np.polyfit(base.pm25, base.total, 1)[0] * 10:+,.0f}")
for s in ["Winter", "Spring", "Summer", "Fall"]:
    sub = base[season == s]
    print(f"{s:6s} slope per +10 ug/m3: {np.polyfit(sub.pm25, sub.total, 1)[0] * 10:+,.0f}  (n={len(sub)})")

# 3) Bad-air day DML (treatment = PM2.5 > 35, i.e. Bad incl. the single Very Bad day)
base["bad"] = (base.pm25 > 35).astype(float)
C = g["BASE"] + g["HUM"]
for kind in ("RF", "GB"):
    r = g["dml"](base, "ln_total", C, kind, treat="bad")
    pct = g["pct"]
    print(f"Bad-day DML {kind}: {pct(r['theta']):+.2f}%  95% CI [{pct(r['ci_lo']):+.2f}, {pct(r['ci_hi']):+.2f}]  "
          f"p = {r['p']:.3f}")
