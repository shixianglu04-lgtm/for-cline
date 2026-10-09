#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3 汇总脚本: 把 猎聘(SSR原文页) + 职友集(聚合索引) 的深圳·机器人·实习(三类岗位)
整理为 /workspace/data/boss_liepin_jobs.json 与 boss_liepin_evidence.md

证据等级:
  "原文页"      = 成功打开并抓取到岗位原文(猎聘详情页)
  "聚合站索引"  = 职友集列表元数据(未打开原始平台原页)
字段缺失写 null, 不做推测填充。
"""
import json, re, glob, os, sys, html, time, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from liepin_scrape import fetch as lp_fetch, parse_detail  # noqa

ROOT = "/workspace"
NOW = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                     capture_output=True, text=True).stdout.strip()

ROBOT = (r"机器人|具身|机械臂|人形|AGV|AMR|无人机|外骨骼|无人驾驶|自动驾驶|激光雷达|"
         r"SLAM|运动控制|伺服|灵巧手|感知|智能硬件|机器视觉|Robo|robot|清洁机器|扫地|"
         r"协作机器|工业机器|服务机器|医疗机器|配送机器|巡检机器|四足|足式|"
         r"越疆|优必选|普渡|云鲸|乐聚|逐际动力|众擎|海柔|宇树|云迹|高仙|擎朗|"
         r"道通|影石|Insta360|拓竹|大疆|DJI|奥比中光|思必驰|自变量|智平方|灵初|跨维|星尘")
INTERN = r"实习|Intern|intern|寒暑期|暑期|寒假|日常实习|学生可投|在校"
FAMILY = [
    ("产品经理", r"产品经理|产品助理|产品策划|产品设计|产品实习|产品专员|产品岗|GTM|PM实习"),
    ("技术支持", r"技术支持|售前|售后|客户成功|客户支持|服务工程师|客服|实施|驻场|技术运维|运维支持"),
    ("应用工程师", r"应用工程师|现场应用|FAE|fae|应用开发|解决方案|交付|部署|调试|应用工程|应用岗|应用实习"),
]


def family_of(title):
    for name, pat in FAMILY:
        if re.search(pat, title or ""):
            return name
    return None


def is_robot(title, company, industry):
    blob = " ".join([title or "", company or "", industry or ""])
    return bool(re.search(ROBOT, blob))


def liepin_candidates():
    files = (glob.glob(f"{ROOT}/data/liepin/*.json")
             + glob.glob(f"{ROOT}/data/liepin2/*.json")
             + glob.glob(f"{ROOT}/data/liepin_supp/*.json")
             + glob.glob(f"{ROOT}/data/liepin_scan/*.json"))
    recs = {}
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        kw = os.path.basename(f).replace(".json", "")
        for r in data:
            jid = r.get("job_id")
            if not jid:
                continue
            if jid in recs:
                if kw not in recs[jid]["keywords"]:
                    recs[jid]["keywords"].append(kw)
                continue
            r["keywords"] = [kw]
            recs[jid] = r
    cand = []
    for r in recs.values():
        t = r.get("job_title") or ""
        if not (r.get("city_area") or "").startswith("深圳"):
            continue
        if not (re.search(INTERN, t) or r.get("job_kind") == "实习"):
            continue
        fam = family_of(t)
        if not fam:
            continue
        if not is_robot(t, r.get("company"), r.get("industry")):
            continue
        r["job_family"] = fam
        cand.append(r)
    return cand

REQ_HEADS = ["岗位职责", "职位职责", "工作内容", "任职要求", "职位要求", "岗位要求",
             "任职资格", "我们希望你", "工作职责", "职责描述"]


def get_detail_html(jid):
    p2 = "/tmp/lp_pages/%s.html" % jid
    if os.path.exists(p2) and os.path.getsize(p2) > 20000:
        h = open(p2, encoding="utf-8", errors="ignore").read()
        if "职位介绍" in h and "我们找遍了所有地方" not in h:
            return h, "https://www.liepin.com/job/%s.shtml" % jid
    url = "https://www.liepin.com/job/%s.shtml" % jid
    h = lp_fetch(url, "detail_%s" % jid)
    for alt in ("https://www.liepin.com/a/%s.shtml" % jid,
                "https://www.liepin.com/lptjob/%s/" % jid):
        if len(h) > 20000 and "职位介绍" in h:
            break
        url, h = alt, lp_fetch(alt, "detail_alt_%s" % jid)
    return h, url


def detail_to_record(c):
    jid = c["job_id"]
    h, url = get_detail_html(jid)
    ok = len(h) > 20000 and "职位介绍" in h
    d = parse_detail(h, jid, url)
    body = d.get("body") or ""
    head = d.get("head") or ""

    text = re.sub(r"\s+", " ", body)
    req_block = text
    for st in REQ_HEADS:
        i = text.find(st)
        if i >= 0:
            req_block = text[i:]
            break
    parts = re.split(r"(?=\d+[、.．)])|(?<=[；;])", req_block)
    reqs = [p.strip(" ；;、|") for p in parts if len(p.strip(" ；;、|")) >= 6]
    reqs = [r for r in reqs if not r.startswith("猎聘")][:16]

    segs = [s.strip() for s in head.split("|") if s.strip()]
    education = c.get("education")
    terms = []
    for s in segs:
        if re.match(r"^\d+天/周", s) or re.match(r"^\d+个月$", s) or s in ("学生可投", "提供转正"):
            terms.append(s)
        if s in ("大专", "本科", "硕士", "博士", "学历不限", "统招本科", "高中"):
            education = s
    if "实习" in segs:
        terms.insert(0, "实习")

    salary = c.get("salary")
    msal = re.search(r"(\d+-\d+元/天|\d+-\d+k|\d+k-\d+k|\d+-\d+元/时)", head)
    if msal:
        salary = msal.group(1)

    grad = None
    gm = re.search(r"((?:\d{2}|\d{4})\s*[-~至]?\s*(?:\d{2}|\d{4})?\s*届[^，。；;|]{0,20}|"
                   r"\d{4}\s*年\s*(?:应届|毕业)|应届生|在校生|在读|\d{2}届)", text)
    if gm:
        grad = gm.group(1).strip()

    exp = None
    em = re.search(r"(经验不限|不限经验|应届生|\d+年(?:以上)?(?:相关)?工作经验|\d+-\d+年)", text)
    if em:
        exp = em.group(1)

    return {
        "source": "猎聘",
        "source_url": d.get("source_url") or url,
        "company": c.get("company"),
        "job_title": c.get("job_title"),
        "city": c.get("city_area"),
        "job_family": c["job_family"],
        "requirements": reqs,
        "experience_threshold": exp,
        "graduation_limit": grad,
        "education": education,
        "internship_terms": ",".join(dict.fromkeys(terms)) or None,
        "salary": salary,
        "evidence": re.sub(r"\s+", " ", body)[:1200],
        "evidence_level": "原文页" if ok else "聚合站索引",
        "collected_at": NOW,
        "notes": None if ok else "详情页未成功抓取(限流/空壳), 字段来自列表页元数据",
    }, ok, d


def main():
    cand = liepin_candidates()
    print("liepin candidates:", len(cand), file=sys.stderr)
    records, evidence = [], []
    for c in cand:
        rec, ok, d = detail_to_record(c)
        records.append(rec)
        evidence.append("\n".join([
            "## [%s] %s | %s | %s" % (rec["evidence_level"], rec["company"],
                                      rec["job_title"], rec["job_family"]),
            "",
            "- source_url: %s" % rec["source_url"],
            "- 关键词: %s" % ",".join(c.get("keywords", [])),
            "- 采集时间(UTC): %s" % NOW,
            "- 薪资/城市/学历: %s | %s | %s" % (rec["salary"], rec["city"], rec["education"]),
            "- 实习条件: %s | 届别: %s | 经验: %s" % (
                rec["internship_terms"], rec["graduation_limit"], rec["experience_threshold"]),
            "- 截止日期: %s" % (d.get("deadline") or "页面未标注"),
            "- 职位地址: %s" % (d.get("address") or "页面未标注"),
            "",
            "```", rec["evidence"][:2400], "```", "",
        ]))
        print("  %s | %s | %s | %s" % (rec["evidence_level"], rec["company"],
                                       rec["job_title"], rec["job_family"]), file=sys.stderr)
        time.sleep(1.0)
    json.dump(records, open(f"{ROOT}/data/boss_liepin_jobs_liepin.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(f"{ROOT}/data/boss_liepin_evidence_liepin.md", "w", encoding="utf-8").write(
        "# 猎聘 深圳·机器人·实习 岗位证据原文\n\n采集时间(UTC): %s\n\n" % NOW + "\n".join(evidence))
    print("records:", len(records), file=sys.stderr)


if __name__ == "__main__":
    main()

