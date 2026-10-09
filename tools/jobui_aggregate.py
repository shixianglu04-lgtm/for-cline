#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 data/jobui/*.json 与 data/jobui_com/*.json, 去重, 输出候选岗位清单"""
import json, glob, re, os, sys

ROLE_PAT = re.compile(
    r"(应用工程师|现场应用|FAE|fae|应用开发|解决方案|技术支持|售前|售后|客户成功|"
    r"产品经理|产品助理|产品策划|交付|实施|调试|部署|客户支持|服务工程师)")
INTERN_PAT = re.compile(r"(实习|Intern|intern|实习岗)")
ROBOT_HINT = re.compile(
    r"(机器人|robot|机械臂|具身|AGV|AMR|无人机|外骨骼|智能硬件|无人驾驶|自动驾驶|"
    r"激光雷达|传感|运动控制|伺服|减速|视觉|SLAM|灵巧手)")

recs = {}
for f in glob.glob("/workspace/data/jobui/*.json") + glob.glob("/workspace/data/jobui_com/*.json"):
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for r in data:
        jid = r.get("jobui_id")
        if not jid:
            continue
        r.setdefault("keywords", [])
        kw = os.path.basename(f).replace(".json", "")
        if jid in recs:
            if kw not in recs[jid]["keywords"]:
                recs[jid]["keywords"].append(kw)
            continue
        r["keywords"] = [kw]
        r["src_file"] = os.path.basename(f)
        recs[jid] = r

rows = list(recs.values())
print("unique jobui jobs:", len(rows), file=sys.stderr)

def role_of(t):
    if re.search(r"产品经理|产品助理|产品策划|产品设计", t):
        return "产品经理"
    if re.search(r"技术支持|售前|售后|客户成功|客户支持|服务工程师", t):
        return "技术支持"
    if re.search(r"应用工程师|现场应用|FAE|fae|应用开发|解决方案|交付|实施|调试|部署", t):
        return "应用工程师"
    return None

cand = []
for r in rows:
    t = r.get("job_title", "") or ""
    fam = role_of(t)
    if not fam:
        continue
    r["job_family"] = fam
    r["title_has_intern"] = bool(INTERN_PAT.search(t))
    r["robot_hint"] = bool(ROBOT_HINT.search(t) or ROBOT_HINT.search(r.get("company", "") or "")
                           or ROBOT_HINT.search(r.get("company_intro", "") or ""))
    cand.append(r)

cand.sort(key=lambda r: (not r["robot_hint"], r.get("job_family", "")))
json.dump(cand, open("/workspace/data/jobui_candidates.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("candidates:", len(cand), file=sys.stderr)
for r in cand:
    print("%s | %s | %s | %s | %s | robot=%s | kw=%s" %
          (r.get("job_family"), r.get("job_title"), r.get("company"),
           r.get("experience"), r.get("education"), r["robot_hint"],
           ",".join(r["keywords"])))
