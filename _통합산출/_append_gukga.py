# -*- coding: utf-8 -*-
"""국가직_rows.csv -> 검증_data.csv 끝에 추가 (백업 후). 중복 방지 가드 포함."""
import csv, os, shutil

D = os.path.dirname(__file__)
SRC = os.path.join(D, "검증_data.csv")
ADD = os.path.join(D, "국가직_rows.csv")

with open(SRC, encoding="utf-8-sig") as fp:
    base = list(csv.DictReader(fp))
    cols = list(csv.DictReader(open(SRC, encoding="utf-8-sig")).fieldnames)

# 중복 가드: 이미 국가직이 있으면 중단
if any(r.get("지역") == "국가직" for r in base):
    print("ABORT: 검증_data.csv에 이미 '국가직' 행이 있음. 추가하지 않음.")
    raise SystemExit(1)

with open(ADD, encoding="utf-8-sig") as fp:
    add = list(csv.DictReader(fp))

# 백업
bak = os.path.join(D, "검증_data.csv.bak")
shutil.cop2 = shutil.copy2
shutil.copy2(SRC, bak)

# 추가 (append, BOM 없이)
with open(SRC, "a", encoding="utf-8", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=cols)
    for r in add:
        w.writerow({c: r.get(c, "") for c in cols})

print(f"백업: {bak}")
print(f"기존 {len(base)}행 + 국가직 {len(add)}행 = {len(base)+len(add)}행")
