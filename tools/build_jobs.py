#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把实习僧抓取的详情 (data/sxs_details.json + data/sxs_details2.json) 整理为
/workspace/data/sxs_jobs.json 与 /workspace/data/sxs_evidence.md

筛选口径: 机器人行业(公司/岗位含机器人相关) 且 深圳(或写明全国/多地且含深圳) 的实习岗。
字段全部来自页面原文, 缺失写 null 并在 notes 说明。
"""
import json, re, os, subprocess

ROOT = "/workspace"
DETAIL_FILES = [os.path.join(ROOT, "data/sxs_details.json"),
                os.path.join(ROOT, "data/sxs_details2.json")]
LIST_FILE = os.path.join(ROOT, "data/sxs_lists.json")

# (uuid, job_family) —— 命中三类岗位的机器人行业实习岗
CORE = [
    ("inn_dus7eglngvry", "应用工程师"),   # 云迹科技 机器人部署/维修实习生
    ("inn_hszxpawzyero", "应用工程师"),   # 法雷奥 机器人开发实习生
    ("inn_qwp4k76mlrim", "应用工程师"),   # BrainCo 机器人系统开发实习生
    ("inn_gcnariei6a0e", "技术支持"),     # BrainCo BrainAI赛事技术支持实习生
    ("inn_k1pckmm0yjrh", "技术支持"),     # 深圳科创学院 售前工程师——亚睿特机器人
    ("inn_08bb1o0o5lhd", "产品经理"),     # 脑回录科技Nanoloop AI产品经理实习生(硬件方向)
]
# 机器人行业其他实习岗位(对照)
OTHER = [
    "inn_6jo0nqorm1j0", "inn_svgvi2iv9oy7", "inn_2eea8t1kfdbw",
    "inn_ywsmwpxyulik", "inn_dprb8np09gqd", "inn_fwsvuecctoqe",
    "inn_kknuovfiq8gn", "inn_lzkjhnslo55u", "inn_r4q4ekteb8ic",
    "inn_0xyh05aidx3t", "inn_n12teze3cem6", "inn_lebmmck8i9da",
    "inn_pfvoudr6u1xn", "inn_7wh7dy8w07ap", "inn_mywamcxup67j",
    "inn_5dleevhlxjxh",
]


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


NOW = sh("date", "-u", "+%Y-%m-%dT%H:%M:%SZ")


def load_details():
    d = {}
    for f in DETAIL_FILES:
        if os.path.exists(f) and os.path.getsize(f) > 10:
            for rec in json.load(open(f, encoding="utf-8")):
                d[rec["uuid"]] = rec
    return d


def load_lists():
    if os.path.exists(LIST_FILE):
        return {j["uuid"]: j for j in json.load(open(LIST_FILE, encoding="utf-8"))}
    return {}


def split_seg(txt):
    return [s.strip() for s in txt.split("\x01") if s.strip()]


def parse_head(head):
    """从详情页头部概览解析 薪资/城市/学历/每周天数/实习月数"""
    seg = split_seg(head or "")
    out = {"salary": None, "city": None, "degree": None,
           "days_per_week": None, "months": None}
    for i, s in enumerate(seg):
        if re.match(r"^\d+天／周$", s):
            out["days_per_week"] = s.replace("／", "/")
            if i >= 1:
                out["degree"] = seg[i - 1]
            if i >= 2:
                out["city"] = seg[i - 2]
            if i >= 3:
                out["salary"] = seg[i - 3]
        m = re.match(r"^实习(\d+)个月$", s)
        if m:
            out["months"] = int(m.group(1))
    return out


def section(body, starts, ends):
    """取 body 中 starts 之一 到 ends 之一 之间的明文"""
    text = " ".join(split_seg(body or ""))
    for st in starts:
        i = text.find(st)
        if i >= 0:
            j = len(text)
            for en in ends:
                k = text.find(en, i + len(st))
                if k >= 0:
                    j = min(j, k)
            return text[i + len(st):j].strip(" :：")
    return ""


REQ_HEADS = ["任职要求", "岗位要求", "任职资格", "职位要求", "我们希望你", "岗位需求"]
REQ_ENDS = ["投递要求", "简历要求", "截止日期", "工作地点", "你将获得", "实习福利",
            "薪资福利", "加分项", "优先条件", "【加分项】", "此岗位为"]


def get_requirements(body):
    txt = re.sub(r"\s+", " ", section(body, REQ_HEADS, REQ_ENDS))
    parts = re.split(r"(?=\d+[、.．)])|(?<=[；;])", txt)
    out = [p.strip(" ；;、") for p in parts if len(p.strip(" ；;、")) >= 4]
    return out[:14] if out else ([txt[:600]] if txt else [])


GRAD_PATTERNS = [
    r"\d{2}\s*届", r"20\d{2}\s*届", r"应届",
    r"在校生", r"在读", r"在校",
    r"毕业(时间|年份|不限)", r"毕设(方向|课题)",
    r"(实习期|实习周期|实习时间|连续实习|至少实习|实习至少)[^。；;]{0,12}?\d+\s*(个月|月|天)",
    r"实习[^。；;]{0,10}?(不少于|至少|≥|不低于)\s*\d+\s*(个月|月)",
    r"每周[^。；;]{0,10}?(不少于|至少|≥|不低于|出勤)\s*\d+\s*天",
    r"每周到岗\s*\d+\s*天",
    r"稳定实习", r"长期稳定实习",
]


def _clauses(body):
    """按原文分段(\x01 为 HTML 文本节点边界)与句读切分"""
    text = (body or "")
    i = text.find("投递要求")
    if i > 0:
        text = text[:i]
    parts = re.split(r"[\x01。；;]+", text)
    return [re.sub(r"\s+", " ", p).strip(" :：,") for p in parts]


def get_graduation_limit(body):
    hits = []
    for s in _clauses(body):
        if not (4 <= len(s) <= 160):
            continue
        if any(re.search(p, s) for p in GRAD_PATTERNS):
            hits.append(s)
    hits = list(dict.fromkeys(hits))
    return "；".join(hits)[:400] if hits else None
EXP_PATTERNS = [
    r"经验要求[：:]\s*[^。；;]{0,20}",
    r"工作年限[：:]\s*[^。；;]{0,20}",
    r"\d+\s*年(及以上|以上|以上相关|及以上相关)?\s*(相关)?工作经验",
    r"\d+\s*年以上(工作)?经验",
    r"经验不限", r"不限经验",
]


def get_experience(body):
    hits = []
    for s in _clauses(body):
        if not (4 <= len(s) <= 160):
            continue
        if any(re.search(p, s) for p in EXP_PATTERNS):
            hits.append(s)
    hits = list(dict.fromkeys(hits))
    return "；".join(hits)[:250] if hits else None


NOTES = {
    "inn_dus7eglngvry": "页面「工作地点：全国」，未单列深圳；云迹科技总部在北京，属全国多地岗，深圳是否常年有需求页面未标注",
    "inn_qwp4k76mlrim": "JD 含「系统部署标准化…交付支持」「客户现场部署、实施或技术支持经验」，按交付/部署归入应用工程师类",
    "inn_hszxpawzyero": "JD 含「人形机器人相关应用功能的开发、调试及真机部署」，按应用开发归入应用工程师类",
    "inn_k1pckmm0yjrh": "深圳科创学院孵化团队「亚睿特机器人」岗位；任职要求写明 2 年及以上相关工作经验",
    "inn_08bb1o0o5lhd": "公司为脑机接口/AI 可穿戴硬件团队（机器人相邻赛道），岗位为硬件方向产品经理；页面未标注机器人，归入产品经理类需注意",
}


def build():
    det = load_details()
    lists = load_lists()
    records, evidence = [], []

    def add(uuid, family):
        d = det.get(uuid)
        if not d:
            print("!! missing detail", uuid)
            return
        l = lists.get(uuid, {})
        head = parse_head(d.get("head"))
        title = (d.get("page_title") or "").split("实习招聘-")[0].strip().rstrip("-").strip()
        body = d.get("body") or ""
        reqs = get_requirements(body)
        salary = head["salary"]
        if salary in ("薪资面议", "面议"):
            salary = None
        terms = []
        if head["days_per_week"]:
            terms.append(head["days_per_week"])
        if head["months"]:
            terms.append("实习%d个月" % head["months"])
        grad = get_graduation_limit(body)
        notes = NOTES.get(uuid)
        extra = []
        if family == "其他":
            extra.append("机器人行业其他实习岗位（对照用）")
        if not grad:
            extra.append("页面未标注毕业时间/在校身份限制")
        if extra:
            notes = "；".join(([notes] if notes else []) + extra)

        rec = {
            "source": "实习僧(shixiseng.com)",
            "source_url": "https://www.shixiseng.com/intern/%s" % uuid,
            "company": l.get("cname"),
            "job_title": title,
            "city": head["city"] or l.get("city"),
            "job_family": family,
            "requirements": reqs,
            "experience_threshold": get_experience(body),
            "graduation_limit": grad,
            "education": head["degree"] or l.get("degree"),
            "internship_terms": ",".join(terms) if terms else None,
            "salary": salary,
            "evidence": re.sub(r"\s+", " ", body.replace("\x01", " ")).strip()[:900],
            "collected_at": NOW,
            "notes": notes,
        }
        records.append(rec)
        evidence.append("\n".join([
            "## %s | %s | %s" % (rec["company"], rec["job_title"], family),
            "",
            "- URL: %s" % rec["source_url"],
            "- 采集时间(UTC): %s" % NOW,
            "- 页面标题: %s" % (d.get("page_title") or ""),
            "- 头部概览: %s" % re.sub(r"\s+", " ", (d.get("head") or "").replace("\x01", " | "))[-700:],
            "- 截止日期: %s" % (d.get("deadline") or "页面未标注"),
            "- 工作地点: %s" % (d.get("workplace") or "页面未标注"),
            "",
            "```",
            re.sub(r"\s+", " ", body.replace("\x01", " ")).strip()[:2600],
            "```", "",
        ]))

    for uuid, fam in CORE:
        add(uuid, fam)
    for uuid in OTHER:
        add(uuid, "其他")

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(records, open(os.path.join(ROOT, "data/sxs_jobs.json"), "w",
                            encoding="utf-8"), ensure_ascii=False, indent=1)
    hdr = ("# 深圳·机器人行业·实习岗位 采集证据（实习僧 shixiseng.com）\n\n"
           "采集时间(UTC): %s\n\n"
           "说明：以下均为页面正文原文摘录，便于逐条复核。字段缺失处标注「页面未标注」。\n\n"
           % NOW)
    open(os.path.join(ROOT, "data/sxs_evidence.md"), "w",
         encoding="utf-8").write(hdr + "\n".join(evidence))
    print("records:", len(records))
    for r in records:
        print(" -", r["job_family"], "|", r["company"], "|", r["job_title"], "|",
              r["city"], "|", r["salary"], "|", r["internship_terms"])


if __name__ == "__main__":
    build()

