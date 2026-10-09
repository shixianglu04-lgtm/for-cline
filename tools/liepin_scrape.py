#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猎聘 (liepin.com) 岗位采集器 —— 已实测可直接 curl 抓取(SSR):
  搜索页(SEO): https://www.liepin.com/city-<slug>/zhaopin/pn<page>/?key=<关键词>   (40 条/页)
  详情页(SEO): https://www.liepin.com/job/<jobId>.shtml
  详情页(另一种ID空间): https://www.liepin.com/lptjob/<jobId>/
详情页含: 职位介绍/岗位职责/任职要求/加分项/截止日期/招聘人数/更新日期/薪资/城市/实习时长/学历/学生可投

用法:
  python3 liepin_scrape.py search "机器人 实习" --city sz --pages 3 --out data/liepin_robot.json
  python3 liepin_scrape.py detail 1980960323 85442155
"""
import re, sys, json, html, os, time, argparse, subprocess, urllib.parse, hashlib

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CACHE = os.environ.get("LIEPIN_CACHE", "/tmp/liepin_cache")
os.makedirs(CACHE, exist_ok=True)


def fetch(url, tag):
    key = hashlib.md5(url.encode()).hexdigest()[:12]
    path = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z_.-]", "_", tag)[:80] + "_" + key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 3000:
        return open(path, encoding="utf-8", errors="ignore").read()
    for _ in range(3):
        p = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        if len(p.stdout) > 3000:
            open(path, "w", encoding="utf-8").write(p.stdout)
            return p.stdout
        time.sleep(2)
    return ""


def seg(h):
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h)
    h = re.sub(r"<[^>]+>", "\x01", h)
    h = html.unescape(h)
    return re.sub(r"[\x01\s]+", "|", h)


def parse_search(h):
    out = []
    for blk in re.split(r'<li>\s*<div class="job-list-item"', h)[1:]:
        blk = blk.split("<li>")[0]
        rec = {}
        m = re.search(r'href="https://www\.liepin\.com/(?:a|job)/(\d+)\.shtml"', blk)
        if not m:
            continue
        rec["job_id"] = m.group(1)
        rec["source_url"] = "https://www.liepin.com/job/%s.shtml" % m.group(1)
        m = re.search(r'<div title="([^"]*)" class="ellipsis-1">', blk)
        if m:
            rec["job_title"] = html.unescape(m.group(1))
        m = re.search(r'<div class="job-dq-box">\s*<span class="dq-bracket">.*?</span>\s*<span[^>]*>([^<]*)</span>', blk, re.S)
        if m:
            rec["city_area"] = html.unescape(m.group(1)).strip()
        m = re.search(r'<span class="job-salary">([^<]*)</span>', blk)
        if m:
            rec["salary"] = html.unescape(m.group(1)).strip()
        labels = [html.unescape(x).strip() for x in
                  re.findall(r'<span class="labels-tag"[^>]*>([^<]*)</span>', blk)]
        if labels:
            rec["labels"] = labels
            for l in labels:
                if l in ("经验不限", "应届生", "1年以内", "1-3年"):
                    rec["experience"] = l
                elif l in ("学历不限", "统招本科", "本科", "硕士", "博士", "大专", "高中"):
                    rec["education"] = l
                elif l in ("实习", "全职", "兼职"):
                    rec["job_kind"] = l
        m = re.search(r'<span class="company-name ellipsis-1">([^<]*)</span>', blk)
        if m:
            rec["company"] = html.unescape(m.group(1)).strip()
        m = re.search(r'<div class="company-tags-box ellipsis-1">(.*?)</div>', blk, re.S)
        if m:
            tags = [html.unescape(x).strip() for x in re.findall(r'<span>([^<]*)</span>', m.group(1))]
            tags = [t for t in tags if t]
            if tags:
                rec["company_tags"] = tags
                for t in tags:
                    if t.endswith("人"):
                        rec["company_scale"] = t
                    elif t in ("A轮", "B轮", "C轮", "D轮", "天使轮", "不需要融资", "已上市",
                               "战略投资", "未融资", "IPO上市"):
                        rec["company_stage"] = t
                    elif not rec.get("industry"):
                        rec["industry"] = t
        m = re.search(r'<div class="recruiter-name ellipsis-1"\s*>([^<]*)</div>', blk)
        if m:
            rec["recruiter"] = html.unescape(m.group(1)).strip()
        out.append(rec)
    seen, res = set(), []
    for r in out:
        if r["job_id"] in seen:
            continue
        seen.add(r["job_id"])
        res.append(r)
    return res


def parse_detail(h, job_id, url):
    rec = {"job_id": job_id, "source_url": url}
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    if m:
        rec["page_title"] = html.unescape(m.group(1)).strip()
    t = seg(h)
    i = t.find("职位介绍")
    j = t.find("猎聘温馨提示")
    body = t[i:j] if i >= 0 else t[:6000]
    rec["body"] = body.strip("|")[:6000]
    head = t[:i] if i > 0 else t[:2000]
    rec["head"] = head[-1200:]
    for pat, field in ((r"截止日期：([0-9年月日-]+)", "deadline"),
                       (r"招聘人数：([^|]+)", "headcount"),
                       (r"职位地址：([^|]+)", "address"),
                       (r"企业行业：([^|]+)", "industry"),
                       (r"人数规模：([^|]+)", "scale"),
                       (r"数据来源：([^|]+)", "data_source")):
        mm = re.search(pat, t)
        if mm:
            rec[field] = mm.group(1).strip()
    return rec


def cmd_search(a):
    recs = []
    start = getattr(a, "start", 0)
    for page in range(start, start + a.pages):
        url = ("https://www.liepin.com/city-%s/zhaopin/pn%d/?key=%s"
               % (a.city, page, urllib.parse.quote(a.keyword)))
        h = fetch(url, "search_%s_%s_%d" % (a.keyword, a.city, page))
        rs = parse_search(h)
        for r in rs:
            r["keyword"] = a.keyword
            r["search_url"] = url
        print("page %d -> %d" % (page, len(rs)), file=sys.stderr)
        recs += rs
        time.sleep(1.2)
    if a.out:
        json.dump(recs, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(recs, ensure_ascii=False, indent=1))


def cmd_detail(a):
    out = []
    for jid in a.job_ids:
        url = "https://www.liepin.com/job/%s.shtml" % jid
        h = fetch(url, "detail_%s" % jid)
        for alt in ("https://www.liepin.com/a/%s.shtml" % jid,
                    "https://www.liepin.com/lptjob/%s/" % jid):
            if len(h) > 20000 and "职位介绍" in h:
                break
            url, h = alt, fetch(alt, "detail_alt_%s" % jid)
        out.append(parse_detail(h, jid, url))
        time.sleep(1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("keyword")
    s.add_argument("--city", default="sz")
    s.add_argument("--pages", type=int, default=1)
    s.add_argument("--start", type=int, default=0)
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_search)
    d = sub.add_parser("detail")
    d.add_argument("job_ids", nargs="+")
    d.set_defaults(func=cmd_detail)
    a = ap.parse_args()
    a.func(a)
