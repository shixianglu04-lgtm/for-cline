#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 data/liepin*/**/*.json, 过滤出 深圳+实习+机器人行业+三类岗位 的候选清单"""
import json, glob, re, os, sys

ROLE = [
    ("产品经理", r"产品经理|产品助理|产品策划|产品设计|产品实习"),
    ("技术支持", r"技术支持|售前|售后|客户成功|客户支持|服务工程师|客服|实施|驻场"),
    ("应用工程师", r"应用工程师|现场应用|FAE|fae|应用开发|解决方案|交付|部署|调试|应用工程"),
]
ROBOT = (r"机器人|具身|机械臂|人形|AGV|AMR|无人机|外骨骼|无人驾驶|自动驾驶|激光雷达|"
         r"SLAM|运动控制|伺服|灵巧手|感知|智能硬件|机器视觉|Robo|robot|清洁机器|扫地")
INTERN = r"实习|Intern|intern"

recs = {}
for f in glob.glob("/workspace/data/liepin*/*.json") + glob.glob("/workspace/data/liepin_scan/*.json"):
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for r in data:
        jid = r.get("job_id")
        if not jid:
            continue
        r.setdefault("keywords", [])
        kw = os.path.basename(f).replace(".json", "")
        if jid in recs:
            if kw not in recs[jid]["keywords"]:
                recs[jid]["keywords"].append(kw)
            continue
        r["keywords"] = [kw]
        recs[jid] = r

rows = list(recs.values())
print("unique liepin jobs:", len(rows), file=sys.stderr)

cand = []
for r in rows:
    t = r.get("job_title", "") or ""
    if not re.search(INTERN, t) and r.get("job_kind") != "实习":
        continue
    fam = None
    for name, pat in ROLE:
        if re.search(pat, t):
            fam = name
            break
    if not fam:
        continue
    robot = bool(re.search(ROBOT, t) or re.search(ROBOT, r.get("company", "") or "")
                 or re.search(ROBOT, r.get("industry", "") or ""))
    if not robot:
        continue
    r["job_family"] = fam
    r["city_shenzhen"] = (r.get("city_area") or "").startswith("深圳")
    cand.append(r)

cand.sort(key=lambda r: (r["job_family"], not r["city_shenzhen"]))
json.dump(cand, open("/workspace/data/liepin_candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("candidates:", len(cand), file=sys.stderr)
for r in cand:
    print("%s | %s | %s | %s | %s | %s | kw=%s" %
          (r["job_family"], r["job_id"], r.get("job_title"), r.get("company"),
           r.get("city_area"), r.get("education"), ",".join(r["keywords"])))
