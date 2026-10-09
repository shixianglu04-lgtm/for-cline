#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3 最终装配: 合并 猎聘(原文页) + 职友集(聚合索引) 的 深圳·机器人·实习(三类岗位) 记录,
去重后输出:
  /workspace/data/boss_liepin_jobs.json
  /workspace/data/boss_liepin_evidence.md
"""
import json, re, glob, os, subprocess

ROOT = "/workspace"
NOW = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                     capture_output=True, text=True).stdout.strip()

ROBOT = (r"机器人|具身|机械臂|人形|AGV|AMR|无人机|外骨骼|无人驾驶|自动驾驶|激光雷达|"
         r"SLAM|运动控制|伺服|灵巧手|感知|智能硬件|机器视觉|Robo|robot|协作机器|工业机器|"
         r"服务机器|医疗机器|配送机器|巡检机器|四足|越疆|优必选|普渡|云鲸|乐聚|逐际|众擎|"
         r"海柔|宇树|云迹|高仙|擎朗|道通|影石|拓竹|大疆|奥比中光|思必驰|自变量|智平方|"
         r"灵初|跨维|星尘|莫界")
FAMILY = [
    ("产品经理", r"产品经理|产品助理|产品策划|产品设计|产品实习|产品专员|产品岗|GTM"),
    ("技术支持", r"技术支持|售前|售后|客户成功|客户支持|服务工程师|客服|实施|驻场|技术运维"),
    ("应用工程师", r"应用工程师|现场应用|FAE|fae|应用开发|解决方案|交付|部署|调试|应用工程"),
]


def family_of(t):
    for name, pat in FAMILY:
        if re.search(pat, t or ""):
            return name
    return None


def load_liepin():
    p = f"{ROOT}/data/boss_liepin_jobs_liepin.json"
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def load_jobui():
    seen, rows = set(), []
    files = [f"{ROOT}/data/jobui_candidates.json"] + glob.glob(f"{ROOT}/data/jobui_zp/*.json")
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for r in data:
            jid = r.get("jobui_id")
            if not jid or jid in seen:
                continue
            seen.add(jid)
            t = r.get("job_title") or ""
            fam = r.get("job_family") or family_of(t)
            if not fam:
                continue
            if not re.search(r"实习|Intern|intern|在校|学生可投", t) and \
               r.get("job_type_filter") != "实习":
                continue
            blob = " ".join([t, r.get("company") or "", r.get("company_intro") or "",
                             r.get("industry") or ""])
            if not re.search(ROBOT, blob):
                continue
            rows.append((r, fam))
    return rows


def main():
    liepin = load_liepin()
    out = list(liepin)
    key = {(r["company"], r["job_title"]) for r in out}

    for r, fam in load_jobui():
        if (r.get("company"), r.get("job_title")) in key:
            continue
        sal = re.sub(r"\s+", "", r.get("salary") or "") or None
        od = r.get("original_domain")
        ev = ("职友集列表页(深圳·实习筛选): 岗位=%s; 公司=%s; 经验=%s; 学历=%s; "
              "薪资=%s; 更新时间=%s; 原始发布平台=%s %s") % (
            r.get("job_title"), r.get("company"), r.get("experience"),
            r.get("education"), sal or "页面未标注", r.get("updated"),
            od or "未解析", r.get("original_url") or "")
        out.append({
            "source": "职友集(jobui.com)聚合",
            "source_url": r.get("jobui_url"),
            "company": r.get("company"),
            "job_title": r.get("job_title"),
            "city": "深圳",
            "job_family": fam,
            "requirements": [],
            "experience_threshold": r.get("experience"),
            "graduation_limit": None,
            "education": r.get("education"),
            "internship_terms": "实习",
            "salary": sal,
            "evidence": ev,
            "evidence_level": "聚合站索引",
            "collected_at": NOW,
            "notes": "来自职友集聚合列表页元数据; 原始发布平台=%s; 未打开原始平台原页(仅索引级证据)"
                     % (od or "未解析"),
        })
        key.add((r.get("company"), r.get("job_title")))

    # 排序: 原文页优先, 再按岗位族
    out.sort(key=lambda r: (r["evidence_level"] != "原文页", r["job_family"]))
    json.dump(out, open(f"{ROOT}/data/boss_liepin_jobs.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 证据文件 = 猎聘原文页证据 + 职友集索引证据
    parts = []
    lp_md = f"{ROOT}/data/boss_liepin_evidence_liepin.md"
    if os.path.exists(lp_md):
        parts.append(open(lp_md, encoding="utf-8").read())
    parts.append("\n\n# 职友集(聚合站)索引级证据\n\n采集时间(UTC): %s\n\n"
                 "> 以下为职友集列表页元数据(未打开原始平台原页), evidence_level=聚合站索引。\n\n" % NOW)
    for r in out:
        if r["evidence_level"] == "聚合站索引":
            parts.append("\n".join([
                "## [聚合站索引] %s | %s | %s" % (r["company"], r["job_title"], r["job_family"]),
                "", "- source_url: %s" % r["source_url"],
                "- 采集时间(UTC): %s" % NOW, "", "```", r["evidence"], "```", "",
            ]))
    open(f"{ROOT}/data/boss_liepin_evidence.md", "w", encoding="utf-8").write("\n".join(parts))

    import collections
    print("TOTAL:", len(out))
    print("evidence_level:", dict(collections.Counter(r["evidence_level"] for r in out)))
    print("job_family:", dict(collections.Counter(r["job_family"] for r in out)))
    print("source:", dict(collections.Counter(r["source"] for r in out)))


if __name__ == "__main__":
    main()
