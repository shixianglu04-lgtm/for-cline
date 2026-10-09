#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实习僧 (shixiseng.com) 实习岗位采集器
用法:
  python3 sxs_scrape.py search "机器人 应用工程师" 深圳 --pages 2 --out data/sxs_ae.json
  python3 sxs_scrape.py detail inn_5dleevhlxjxh

原理: 搜索页/详情页均为 Nuxt SSR, 直接 curl 即可拿到 HTML。
      详情页正文为明文 (仅列表页 job name 使用字体混淆, 详情页 <title> 明文可用)。
"""
import re, sys, json, html, time, argparse, subprocess, os, random

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CACHE = os.environ.get("SXS_CACHE", "/tmp/sxs_cache")
os.makedirs(CACHE, exist_ok=True)


def fetch(url, tag):
    path = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z_.-]", "_", tag)[:150] + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return open(path, encoding="utf-8", errors="ignore").read()
    for attempt in range(3):
        p = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        d = p.stdout
        if len(d) > 5000:
            open(path, "w", encoding="utf-8").write(d)
            return d
        time.sleep(2 + attempt * 3)
    return ""


def strip_tags(h):
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h)
    h = re.sub(r"<[^>]+>", "\x01", h)
    h = html.unescape(h)
    h = re.sub(r"[\x01\s]+", "\x01", h)
    return h.strip("\x01")


def parse_list(htmltext):
    """列表页: 解析 NUXT payload, 返回岗位元数据列表"""
    m = re.search(r"window\.__NUXT__=([\s\S]*?)</script>", htmltext)
    if not m:
        return []
    payload = m.group(1).strip().rstrip(";")
    js = ("const s=%s;const out=[];const seen=new Set();"
          "(function walk(o){if(o&&typeof o==='object'){"
          "if(o.uuid&&String(o.uuid).startsWith('inn')&&!seen.has(o.uuid)){seen.add(o.uuid);"
          "out.push({uuid:o.uuid,cname:o.cname,city:o.city,degree:o.degree,"
          "minsalary:o.minsalary,maxsalary:o.maxsalary,days_per_week:o.month_num,"
          "fte_type:o.ftype,industry:o.industry,i_tags:o.i_tags,c_tags:o.c_tags,"
          "deadline:o.refresh});}"
          "for(const k of Object.keys(o)) walk(o[k]);}})(s);console.log(JSON.stringify(out));"
          ) % payload
    tmp = "/tmp/_sxs_parse.js"
    open(tmp, "w", encoding="utf-8").write(js)
    p = subprocess.run(["node", tmp], capture_output=True, text=True)
    try:
        jobs = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return []
    for j in jobs:  # 数字型薪酬 -> 元/天
        for k in ("minsalary", "maxsalary"):
            if isinstance(j.get(k), str):
                j[k] = None
    return jobs


def parse_detail(htmltext, uuid):
    """详情页: 抽取标题/公司/职责/要求/时长等明文信息"""
    title = ""
    m = re.search(r"<title>(.*?)</title>", htmltext, re.S)
    if m:
        title = html.unescape(m.group(1)).strip()
    txt = strip_tags(htmltext)
    seg = txt
    i = seg.find("职位描述")
    if i > 0:
        seg = seg[i:]
    j = seg.find("公司简介")
    if j > 0:
        seg = seg[:j]
    # 头部概览: 薪资/城市/学历/天周/实习月数 出现在 "职位描述" 之前
    head = txt[:txt.find("职位描述")] if "职位描述" in txt else txt[:4000]
    head = head[-1500:]
    out = {"uuid": uuid, "url": "https://www.shixiseng.com/intern/%s" % uuid,
           "page_title": title, "head": head, "body": seg.strip("\x01 ")[:6000]}
    mt = re.search(r"([\u4e00-\u9fa5]{2,15}?)(?:实习)?招聘-([^<]*?)招聘", title)
    if mt:
        out["job_name_guess"] = mt.group(1)
        out["company_guess"] = mt.group(2)
    mc = re.search(r"截止日期：([0-9-]+)", seg)
    out["deadline"] = mc.group(1) if mc else None
    ms = re.search(r"工作地点：([^\x01]{2,80})", seg)
    out["workplace"] = ms.group(1) if ms else None
    return out


def cmd_search(args):
    city = args.city
    all_jobs = []
    import urllib.parse as up
    for page in range(1, args.pages + 1):
        url = ("https://www.shixiseng.com/interns?keyword=%s&city=%s&page=%d"
               % (up.quote(args.keyword), up.quote(city), page))
        h = fetch(url, "list_%s_%s_%d" % (args.keyword, city, page))
        jobs = parse_list(h)
        for j in jobs:
            j["keyword"] = args.keyword
            j["search_city"] = city
        all_jobs += jobs
        print("page %d -> %d jobs" % (page, len(jobs)), file=sys.stderr)
        time.sleep(1)
    seen, uniq = set(), []
    for j in all_jobs:
        if j["uuid"] in seen:
            continue
        seen.add(j["uuid"])
        uniq.append(j)
    if args.out:
        json.dump(uniq, open(args.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(json.dumps(uniq, ensure_ascii=False, indent=1))


def cmd_detail(args):
    res = []
    for uuid in args.uuids:
        h = fetch("https://www.shixiseng.com/intern/%s" % uuid, "detail_" + uuid)
        res.append(parse_detail(h, uuid))
        time.sleep(1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("keyword")
    s.add_argument("city", nargs="?", default="深圳")
    s.add_argument("--pages", type=int, default=1)
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_search)
    d = sub.add_parser("detail")
    d.add_argument("uuids", nargs="+")
    d.set_defaults(func=cmd_detail)
    a = ap.parse_args()
    a.func(a)
