#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北森 zhiye.com 招聘门户 —— 实习(intern)频道采集器
实测可用接口: POST https://<tenant>.zhiye.com/api/Jobad/GetJobAdPageList
  body: {"PageIndex":1,"PageSize":20}   Referer: https://<tenant>.zhiye.com/intern/jobs
返回字段含 JobAdName / Duty(岗位职责) / Require(任职要求) / LocNames 等。

用法: python3 beisen_intern.py <tenant> <out.json>
"""
import sys, json, time, urllib.request

UA = "Mozilla/5.0"


def post(url, body, referer):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"User-Agent": UA, "Content-Type": "application/json",
                                          "Accept": "application/json", "Referer": referer})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def main():
    tenant, out = sys.argv[1], sys.argv[2]
    base = "https://%s.zhiye.com" % tenant
    url = base + "/api/Jobad/GetJobAdPageList"
    ref = base + "/intern/jobs"
    jobs, page = [], 1
    while page <= 20:
        j = post(url, {"PageIndex": page, "PageSize": 20}, ref)
        d = j.get("Data") or []
        jobs += d
        total = j.get("Count") or len(jobs)
        print("[%s] page %d got %d / total %s" % (tenant, page, len(d), total), file=sys.stderr)
        if not d or len(jobs) >= total:
            break
        page += 1
        time.sleep(0.6)
    json.dump({"tenant": tenant, "api": url, "channel": "intern",
               "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "total": len(jobs), "jobs": jobs},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved %d -> %s" % (len(jobs), out), file=sys.stderr)


if __name__ == "__main__":
    main()
