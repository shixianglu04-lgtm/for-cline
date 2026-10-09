#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
牛客网 nowcoder.com 实习岗位采集器 (SSR window.__INITIAL_STATE__ 明文)
用法:
  python3 nc_scrape.py center                 # 实习广场默认页
  python3 nc_scrape.py center "机器人" 深圳    # 关键词 + 城市
  python3 nc_scrape.py detail <jobId>
说明: 页面为 Nuxt/Nuxt-like SSR, 岗位列表与岗位要求均明文内嵌于
      window.__INITIAL_STATE__; 无需登录。若查询页未 SSR 出列表,
      脚本会退化为抓默认页并本地过滤。
"""
import re, sys, json, time, argparse, subprocess, os, urllib.parse as up

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CACHE = os.environ.get("NC_CACHE", "/tmp/nc_cache")
os.makedirs(CACHE, exist_ok=True)


def fetch(url, tag):
    path = os.path.join(CACHE, re.sub(r"[^0-9A-Za-z_.-]", "_", tag)[:150] + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 3000:
        return open(path, encoding="utf-8", errors="ignore").read()
    for attempt in range(3):
        p = subprocess.run(["curl", "-s", "--max-time", "30", "-A", UA, url],
                           capture_output=True, text=True)
        d = p.stdout
        if len(d) > 3000:
            open(path, "w", encoding="utf-8").write(d)
            return d
        time.sleep(2 + attempt * 3)
    return ""


def extract_state(t):
    """用括号配对从 window.__INITIAL_STATE__= 提取完整 JSON 对象"""
    key = "window.__INITIAL_STATE__="
    i = t.find(key)
    if i < 0:
        return None
    s = t[i + len(key):]
    depth, instr, esc, start = 0, False, False, None
    for j, c in enumerate(s):
        if start is None:
            if c == "{":
                start = j
                depth = 1
            continue
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                raw = s[start:j + 1]
                try:
                    return json.loads(raw)
                except Exception:
                    return None
    return None


def jobs_from_state(state):
    ic = (state.get("store") or {}).get("interCenter") or {}
    out = []
    for it in ic.get("jobList") or []:
        d = it.get("data") or {}
        out.append(d)
    return ic, out


def cmd_center(args):
    base = "https://www.nowcoder.com/jobs/intern/center"
    params = {}
    if args.keyword:
        params["query"] = args.keyword
    if args.city:
        params["jobCity"] = args.city
    url = base + ("?" + up.urlencode(params) if params else "")
    h = fetch(url, "center_%s_%s" % (args.keyword, args.city))
    st = extract_state(h)
    if not st:
        print(json.dumps({"error": "no_state", "url": url}, ensure_ascii=False))
        return
    ic, jobs = jobs_from_state(st)
    res = {"url": url, "totalPage": ic.get("totalPage"),
           "conditions": ic.get("conditions"), "jobs": jobs}
    print(json.dumps(res, ensure_ascii=False, indent=1))


def cmd_detail(args):
    res = []
    for jid in args.jobIds:
        url = "https://www.nowcoder.com/job/center/%s" % jid
        h = fetch(url, "detail_" + jid)
        st = extract_state(h)
        rec = {"jobId": jid, "url": url}
        if st:
            jd = (st.get("store") or {}).get("jobDetail") or {}
            det = jd.get("detail") or {}
            rec["detail"] = det
            rec["company"] = (jd.get("jobCompany") or {}).get("companyName") \
                if isinstance(jd.get("jobCompany"), dict) else None
        res.append(rec)
        time.sleep(1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("center")
    c.add_argument("keyword", nargs="?", default=None)
    c.add_argument("city", nargs="?", default=None)
    c.set_defaults(func=cmd_center)
    d = sub.add_parser("detail")
    d.add_argument("jobIds", nargs="+")
    d.set_defaults(func=cmd_detail)
    a = ap.parse_args()
    a.func(a)
