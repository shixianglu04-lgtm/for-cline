#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量抓取猎聘岗位详情, 输出 data/liepin_detail/details.json"""
import json, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from liepin_scrape import fetch, parse_detail

MARK = "职位介绍"

IDS = [
    # 产品经理方向
    "1983736211",  # 越疆科技 产品助理实习生(机器人\机器狗)
    "1981765709",  # 自变量机器人 产品经理实习生(A230145)
    "1982685401",  # 自变量机器人 GTM产品经理实习生(A61372)
    "1985854639",  # 奥比中光 硬件产品助理实习生
    "1983379517",  # 极萃创新 产品经理实习生
    # 技术支持方向
    "1985150549",  # 越疆科技 海外技术支持实习生(意大利语)
    "1985874955",  # 拓竹科技 海外技术支持实习生(多语种)
    "1985874941",  # 拓竹科技 社交媒体技术支持实习生
    "1985458281",  # 清智元视 售后实习生
    "1981347583",  # 思必驰 硬件售后实习生
    "1981943833",  # 星火数控 技术支持工程师实习生
    "1984502141",  # 理邦仪器 技术支持实习生-深圳
    "1975047127",  # 特利秀科技 售前技术支持实习生
    "1985485575",  # 微众信科 AI实习生(售前技术支持)
    # 应用/交付方向
    "1980960323",  # 数字华夏 机器人交付实习生
    "1984368725",  # 道通科技 解决方案SA岗位实习生
    "1981859669",  # 点聚 解决方案实习生
    "1981859679",  # 点聚 售前实习生
    "1984022451",  # 华钦科技 交付经理实习生
    "1984362641",  # 工匠行 大模型应用工程师实习生
    # 机器人行业算法/其他实习(用于对照)
    "1985850441", "1983542087", "1975390477", "1983122411", "1983013921",
]


def main():
    out = []
    for jid in IDS:
        url = "https://www.liepin.com/job/%s.shtml" % jid
        h = fetch(url, "detail_%s" % jid)
        for alt in ("https://www.liepin.com/a/%s.shtml" % jid,
                    "https://www.liepin.com/lptjob/%s/" % jid):
            if len(h) > 20000 and MARK in h:
                break
            url, h = alt, fetch(alt, "detail_alt_%s" % jid)
        r = parse_detail(h, jid, url)
        r["fetch_ok"] = len(h) > 20000 and MARK in h
        out.append(r)
        print(jid, r["fetch_ok"], (r.get("page_title") or "")[:60], flush=True)
        time.sleep(1.5)
    json.dump(out, open("/workspace/data/liepin_detail/details.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
