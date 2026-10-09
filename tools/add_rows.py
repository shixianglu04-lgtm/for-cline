#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一批新岗位记录合并进 data/final_jobs.json（按 id 去重）"""
import json, sys, os

TARGET = "/workspace/data/final_jobs.json"
rows = json.load(open(TARGET, encoding="utf-8"))
batch = json.load(open(sys.argv[1], encoding="utf-8"))
have = {r["id"] for r in rows}
for r in batch:
    if r["id"] in have:
        print("skip dup", r["id"])
        continue
    rows.append(r)
json.dump(rows, open(TARGET, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total rows:", len(rows))
