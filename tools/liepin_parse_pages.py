#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 /tmp/lp_pages/*.html (已下载的猎聘详情页) -> data/liepin_detail/details.json"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from liepin_scrape import parse_detail, seg

out = []
for f in sorted(glob.glob("/tmp/lp_pages/*.html")):
    jid = os.path.basename(f).replace(".html", "")
    h = open(f, encoding="utf-8", errors="ignore").read()
    if len(h) < 20000 or "职位介绍" not in h:
        print("skip", jid, len(h), flush=True)
        continue
    r = parse_detail(h, jid, "https://www.liepin.com/job/%s.shtml" % jid)
    # 抓取列表头部的关键约束: 实习/天每周/月数/学历/学生可投
    t = seg(h)
    for pat, key in ((r"实习\|(\d)天/周\|(\d+)个月", "intern_cycle"),
                     (r"(学生可投)", "student_ok"),
                     (r"(\d+-\d+元/天|\d+-\d+k|面议)", "salary_head"),
                     (r"\|([^|]*?(?:区|新区|深圳))\|实习", "city_head")):
        import re
        m = re.search(pat, t)
        if m:
            r[key] = m.group(0) if not m.groups() else "|".join(m.groups())
    out.append(r)
    print(jid, r.get("page_title", "")[:60], flush=True)

json.dump(out, open("/workspace/data/liepin_detail/details.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("total", len(out))
