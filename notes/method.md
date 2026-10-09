# 采集方法与渠道可用性实测记录

采集时间：2026-10-09（UTC）｜ 出口环境：数据中心 IP 沙箱（Linux + curl/python3/node/jq）
筛选口径：**深圳市 + 机器人/具身智能/智能硬件行业 + 实习（Intern）岗位**，岗位族限定
「应用工程师类（含 FAE/现场应用/交付/调试/解决方案）」「技术支持类（含售前/售后/客户成功）」「产品经理类（含产品助理/产品策划）」。

---

## 一、渠道可用性总表（实测结论）

| 渠道 | 结论 | 可用入口 | 备注 |
| --- | --- | --- | --- |
| **猎聘 liepin.com** | ✅ 可直接抓取（SSR 明文） | 列表：`https://www.liepin.com/city-sz/zhaopin/pn<页>/?key=<词>`（40 条/页）<br>详情：`https://www.liepin.com/job/<id>.shtml` | 关键词**不能带空格**；PC 搜索页 `www.liepin.com/zhaopin/?key=` 是 JS 空壳；`/lptjob/<id>/` 与 `/job/<id>.shtml` 是两个 ID 空间 |
| **实习僧 shixiseng.com** | ✅ 可直接抓取（Nuxt SSR 明文） | 列表：`/interns?keyword=<词>&city=深圳&page=N`<br>详情：`/intern/<uuid>` | 详情页含岗位职责/任职要求/投递要求/截止日期/工作地点；列表页岗位名有字体混淆，详情页明文 |
| **职友集 jobui.com** | ✅ 可直接抓取，且可反查原始平台 | 列表：`https://www.jobui.com/jobs?jobKw=<词>&cityKw=深圳&jobType=实习`<br>详情：`/job/<id>/` | 详情页内嵌 `data-domain` + `data-url` = 岗位**原始发布平台链接**（zhipin.com / liepin.com / zhaopin.com / shixiseng.com / beisen.com…） |
| **企业官网·北森（zhiye.com）** | ✅ 接口可抓 | `https://<tenant>.zhiye.com/...` 门户接口 | 越疆 dobot1.zhiye.com、普渡、优必选、海柔、帕西尼等；详见 `notes/company_channels.md` |
| **企业官网·MokaHR（mokahr.com）** | ⚠️ 视企业而定 | 门户页面 + 公开 JSON 接口 | 见 `notes/company_channels.md` |
| **BOSS直聘 zhipin.com** | ❌ 出口 IP 被 WAF 拦截 | — | 首页/搜索页/`wapi/zpgeek/search/joblist.json`/`m.zhipin.com` 全部返回 `{"code":37,"message":"您的环境存在异常"}` |
| **BOSS直聘·第三方读取代理** | ❌ 被策略拒绝 | r.jina.ai | 返回 `403 AbuseAlleviationError: Anonymous access to domain www.zhipin.com blocked until Fri Oct 09 2026 09:26:41 GMT` |
| **BOSS直聘·网页存档** | ❌ 无有效快照 | web.archive.org | 存档内容为 BOSS 自身的错误页 `{"code":4,"request too frequent}`；CDX API 返回 503 |
| **搜索引擎（Bing/百度/搜狗/DuckDuckGo）** | ❌ 本沙箱不可用 | — | Bing 返回与查询无关的结果（疑似共享出口缓存污染）；百度 302 跳验证；搜狗跳 antispider；DuckDuckGo 202 挑战页 |

> 结论：**猎聘、实习僧、职友集、企业官网（北森/MokaHR）** 构成本次调研的数据主干；
> **BOSS直聘**在本沙箱内被反爬拦截，只能用「职友集聚合索引」间接看到其岗位元数据，且无法打开原文，
> 已在表格中如实标注证据等级（不把二手索引当原文）。

## 二、采集脚本（可复现）

| 脚本 | 用途 |
| --- | --- |
| `tools/liepin_scrape.py` | 猎聘：`search` 抓列表、`detail` 抓岗位详情 |
| `tools/liepin_matrix.sh` / `liepin_scan_interns.sh` | 猎聘关键词矩阵 / 深圳"实习"全量列表扫描（pn0–pn9） |
| `tools/liepin_detail_batch.py` | 批量抓取候选岗位详情 |
| `tools/sxs_scrape.py` | 实习僧：`search` / `detail` |
| `tools/jobui_scrape.py` | 职友集：列表 + 原始来源反查（`--resolve`） |
| `tools/jobui_aggregate.py` / `liepin_aggregate.py` | 候选岗位归并、去重、岗位族归类 |

## 三、字段口径

- **岗位要求**：招聘页「任职要求/职位要求/岗位要求」原文要点（逐条摘录，不改写语义）。
- **经验门槛**：页面标注的工作经验要求；实习岗常见「不限经验」，也有明确要求项目/竞赛/实习经历者（如要求 2 年经验、要求 RoboMaster 参赛经历）。
- **毕业时间限制**：届别（如 27 届/27-28 应届生）、在读学历层次、可实习时长（如 ≥3 个月）、每周出勤（如 5 天/周）、投递截止日期。

## 四、局限与风险提示

1. 招聘信息随时更新/下线，表中数据为 2026-10-09 抓取快照，投递前请以官方页面为准。
2. BOSS直聘数据在本环境无法打开原文，相关条目以「聚合站索引」标注，未计入正式表格主表。
3. 部分岗位（如"全国"工作地、非机器人行业）在归并时被剔除，剔除标准见各聚合脚本中的过滤规则。
