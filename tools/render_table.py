#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 data/final_jobs.json 渲染成 jobs_table.md 与 jobs_table.csv"""
import json, csv, os, re

ROOT = "/workspace"
SRC = os.path.join(ROOT, "data/final_jobs.json")
rows = json.load(open(SRC, encoding="utf-8"))

MD_COLS = ["序号", "公司", "岗位名称", "岗位类别", "工作地点", "薪资", "学历",
           "实习时长/出勤", "经验门槛", "毕业时间限制", "岗位要求（要点）", "信息来源"]


def cell(s, limit=None):
    if s is None:
        return "页面未标注"
    s = str(s).replace("|", "／").replace("\n", "；")
    if limit and len(s) > limit:
        s = s[:limit] + "…"
    return s


lines = []
lines.append("# 深圳机器人行业实习岗位表（应用工程师 / 技术支持 / 产品经理）\n")
lines.append("> 采集时间：2026-10-09（UTC）｜ 数据来源：猎聘、实习僧、职友集、企业官网招聘系统（北森/MokaHR）\n")
lines.append("> 说明：全部为**实习岗位**；「经验门槛」「毕业时间限制」均取自招聘页原文；"
             "标注「页面未标注」表示该字段在原始页面无对应信息（未做推测填充）。\n")

lines.append("| " + " | ".join(MD_COLS) + " |")
lines.append("|" + "---|" * len(MD_COLS))
for i, r in enumerate(rows, 1):
    req = r.get("requirements") or []
    req_txt = "；".join(req)
    lines.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        i, cell(r.get("company")), cell(r.get("job_title")), cell(r.get("job_family")),
        cell(r.get("city")), cell(r.get("salary")), cell(r.get("education")),
        cell(r.get("internship_terms")), cell(r.get("experience_threshold"), 160),
        cell(r.get("graduation_limit"), 200), cell(req_txt, 420),
        cell(r.get("source_platform"))))

lines.append("\n## 逐条岗位详情与原文证据\n")
for i, r in enumerate(rows, 1):
    lines.append("### %d. %s — %s\n" % (i, r.get("company"), r.get("job_title")))
    lines.append("- **岗位类别**：%s ｜ **工作地点**：%s" % (r.get("job_family"), cell(r.get("city"))))
    lines.append("- **薪资/学历/实习要求**：%s ｜ %s ｜ %s" %
                 (cell(r.get("salary")), cell(r.get("education")), cell(r.get("internship_terms"))))
    lines.append("- **经验门槛**：%s" % cell(r.get("experience_threshold")))
    lines.append("- **毕业时间限制**：%s" % cell(r.get("graduation_limit")))
    lines.append("- **岗位要求（原文要点）**：")
    for q in (r.get("requirements") or []):
        lines.append("    - %s" % q)
    lines.append("- **来源**：%s ｜ %s" % (r.get("source_platform"), r.get("source_url")))
    lines.append("- **采集时间**：%s" % r.get("collected_at"))
    if r.get("evidence"):
        lines.append("- **原文证据摘录**：\n\n  ```\n  %s\n  ```" % r["evidence"].replace("\n", "\n  "))
    if r.get("notes"):
        lines.append("- **备注**：%s" % r["notes"])
    lines.append("")

open(os.path.join(ROOT, "jobs_table.md"), "w", encoding="utf-8").write("\n".join(lines))

csv_cols = ["company", "job_title", "job_family", "city", "salary", "education",
            "internship_terms", "experience_threshold", "graduation_limit",
            "requirements", "source_platform", "source_url", "collected_at", "evidence", "notes"]
with open(os.path.join(ROOT, "jobs_table.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["序号"] + csv_cols)
    for i, r in enumerate(rows, 1):
        vals = []
        for c in csv_cols:
            v = r.get(c)
            if isinstance(v, list):
                v = "；".join(v)
            vals.append("" if v is None else v)
        w.writerow([i] + vals)

print("rows:", len(rows))
print("written: jobs_table.md, jobs_table.csv")
