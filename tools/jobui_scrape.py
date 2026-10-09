#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职友集 (jobui.com) 实习岗位采集器
职友集聚合多平台(BOSS直聘/猎聘/实习僧/智联/51job...)岗位:
  - 列表页 SSR 明文: 岗位名 / 经验要求 / 学历 / 薪资 / 公司 / 行业 / 规模 / 更新日期
  - 详情页内嵌原始来源: data-domain + data-url (原始招聘平台链接)

用法:
  python3 jobui_scrape.py "机器人" 深圳 --pages 3 --resolve --out data/jobui_robot.json
"""
import re, sys, json, html, os, time, argparse, subprocess, urllib.parse, hashlib

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CACHE = os.environ.get("JOBUI_CACHE", "/tmp/jobui_cache")
os.makedirs(CACHE, exist_ok=True)


def fetch(url, tag):
    key = hashlib.md5(url.encode()).hexdigest()[:12]
    path = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z_.-]", "_", tag)[:90] + "_" + key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return open(path, encoding="utf-8", errors="ignore").read()
    for _ in range(3):
        p = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        if len(p.stdout) > 1000:
            open(path, "w", encoding="utf-8").write(p.stdout)
            return p.stdout
        time.sleep(2)
    return ""


def txt(h):
    h = re.sub(r"<[^>]+>", "\x01", h)
    h = html.unescape(h)
    return re.sub(r"[\x01\s]+", " ", h).strip()


def parse_list(h):
    """按 c-job-list 分块解析"""
    out = []
    for blk in re.split(r'<div class="c-job-list">', h)[1:]:
        rec = {}
        m = re.search(r'<a class="job-name" href="(/job/(\d+)/)"[^>]*>\s*<h3>(.*?)</h3>', blk, re.S)
        if not m:
            continue
        rec["jobui_url"] = "https://www.jobui.com" + m.group(1)
        rec["jobui_id"] = m.group(2)
        rec["job_title"] = txt(m.group(3))
        for field, key in (("工作经验要求", "experience"), ("学历要求", "education"),
                           ("工资", "salary")):
            mm = re.search(r'title="%s：([^"]*)"' % field, blk)
            if mm:
                rec[key] = mm.group(1)
        mm = re.search(r'<a class="job-company-name"[^>]*>([^<]*)</a>', blk)
        if mm:
            rec["company"] = txt(mm.group(1))
        mm = re.search(r'<span class="job-desc">\s*([\d.]+万人次浏览[^<]*)</span>', blk)
        if mm:
            parts = [p.strip() for p in txt(mm.group(1)).split("/") if p.strip()]
            rec["company_scale"] = parts[-1] if len(parts) > 1 else None
            rec["industry"] = parts[1] if len(parts) > 2 else None
        mm = re.search(r'<span class="job-desc fwb">([^<]*)</span>', blk)
        if mm:
            rec["company_intro"] = txt(mm.group(1))
        mm = re.search(r'<div class="job-add-date">([^<]*)</div>', blk)
        if mm:
            rec["updated"] = txt(mm.group(1))
        out.append(rec)
    seen, res = set(), []
    for r in out:
        if r["jobui_id"] in seen:
            continue
        seen.add(r["jobui_id"])
        res.append(r)
    return res


def resolve_source(jobui_url, jobui_id):
    """抓职友集详情页, 取出内嵌的原始来源域名与 URL"""
    h = fetch(jobui_url, "detail_" + jobui_id)
    md = re.search(r'data-domain="([^"]*)"', h)
    mu = re.search(r'data-url="([^"]*)"', h)
    return {"original_domain": md.group(1) if md else None,
            "original_url": html.unescape(mu.group(1)) if mu else None,
            "detail_ok": bool(mu)}


def cmd_search(a):
    allrec = []
    for page in range(1, a.pages + 1):
        url = ("https://www.jobui.com/jobs?jobKw=%s&cityKw=%s&jobType=%s&page=%d"
               % (urllib.parse.quote(a.keyword), urllib.parse.quote(a.city),
                  urllib.parse.quote(a.jobtype), page))
        h = fetch(url, "list_%s_%s_%d" % (a.keyword, a.city, page))
        recs = parse_list(h)
        print("page %d -> %d" % (page, len(recs)), file=sys.stderr)
        for r in recs:
            r["keyword"] = a.keyword
            r["search_city"] = a.city
            r["job_type_filter"] = a.jobtype
        allrec += recs
        time.sleep(1)
    if a.resolve:
        for r in allrec:
            r.update(resolve_source(r["jobui_url"], r["jobui_id"]))
            time.sleep(0.6)
    if a.out:
        json.dump(allrec, open(a.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(json.dumps(allrec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("city", nargs="?", default="深圳")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--jobtype", default="实习")
    ap.add_argument("--resolve", action="store_true", help="抓详情页解析原始来源URL")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cmd_search(a)
