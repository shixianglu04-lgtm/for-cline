# 通道实测结论表（T2：企业官网/官方招聘系统）

采集时间(UTC)：2026-10-09T08:56:56Z

| 公司/站点 | URL | HTTP码 | 是否可抓 | 接口/结论 |
| --- | --- | --- | --- | --- |
| 大疆 DJI（实习生招聘官网） | https://apply.careers.dji.com/social-recruitment/dji/168240 | 200(API) | 是 | MokaHR：POST /api/outer/ats-apply/website/jobs/v2（AES-128-CBC 解密，IV=页面 aesIv）。实习生站在招 4 个岗位，无三类岗位 |
| 大疆 DJI（校招/社招） | https://apply.careers.dji.com/campus-recruitment/dji/143359 ; /social-recruitment/dji/170070 | 200(API) | 是 | MokaHR 同上；校招 140 条、社招 504 条，标题含“实习”者 0 条（正式校招/社招） |
| 优必选 UBTECH | https://ubtrobot.zhiye.com | 200 | 是 | 北森：POST /api/Jobad/GetJobAdPageList（LocId=4403 深圳过滤）；深圳在招实习 10 个（含产品实习生/AI产品实习生） |
| 越疆科技 Dobot | https://dobot.zhiye.com | 200 | 是 | 北森 同上；深圳在招实习 6 个，均为市场/采购/商务/财务/设计，无三类岗位 |
| 帕西尼感知 Paxini | https://paxini.zhiye.com | 200 | 是 | 北森 同上；深圳在招实习 1 个（招聘实习生） |
| 普渡科技 Pudu Robotics | https://pudutech.zhiye.com | 200 | 是 | 北森 同上；深圳在招实习 4 个（含“部署优化实习生”=应用工程师类） |
| 海柔创新 HAI ROBOTICS | https://hairobotics.zhiye.com | 200 | 是 | 北森 同上；深圳在招 119 条中标题含“实习”者 0 条 —— 已查，无实习岗 |
| 汇川技术 Inovance | https://inovance.zhiye.com | 200 | 是 | 北森 同上；深圳在招 42 条中标题含“实习”者 0 条 —— 已查，无实习岗 |
| 云鲸智能 Narwal | https://careers.narwal.com | 200 | 是 | 北森（企业自定义域名，stcms.beisen.com 资源）；深圳在招实习 1 个（招聘实习生） |
| 速腾聚创 RoboSense（实习生招聘） | https://app.mokahr.com/social-recruitment/robosense/118867 | 200(API) | 是 | MokaHR 同上；在招实习 19 个，含“产品经理—实习生（深圳南山）” |
| 速腾聚创 RoboSense（官网入口） | https://www.robosense.cn/about/joinus | 200 | 是 | 官网列出 校园招聘/社会招聘/实习生招聘 三个 MokaHR 入口 |
| 星尘智能 Astribot | https://app.mokahr.com/campus-recruitment/astribot/144862 ; /social-recruitment/astribot/144861 | 200(API) | 是 | MokaHR 同上；官网列实习岗“具身智能算法实习生/营销实习生”，但 jobs/v2 列表未返回实习岗（疑 hireMode 过滤），需职位短链 /su/xxx |
| 大族激光 Han’s Laser | https://app.mokahr.com/social-recruitment/hanslaser/46382 | 200(API) | 是 | MokaHR 同上；36 条社招岗位中标题含“实习”者 0 条 |
| 逐际动力 LimX Dynamics | https://career.limxdynamics.com/index | 200 | 否 | 飞书招聘(atsx)：/api/v1/search/job/posts 需 `_signature`（JS 混淆的签名函数），无签名 POST 返回 405，GET 返回 SPA；页面明文含“实习岗”栏目 |
| 众擎机器人 EngineAI | https://dx3a2bminsq.jobs.feishu.cn/index | - | 否 | 飞书招聘(jobs.feishu.cn)，同逐际动力的签名机制，本次未攻克 |
| 影石 Insta360 | https://www.insta360.com/cn/careers | 403 | 否 | Cloudflare 人机验证（响应标题 "Just a moment..."），curl 无法取得内容 |
| 奥比中光 Orbbec | https://www.orbbec.com.cn/ | 200 | 否 | 官网无招聘入口（JS 站），未发现 ATS 链接；orbbec.zhiye.com 不存在 |
| 乐聚机器人 Leju | https://www.lejurobot.com/ | 200 | 否 | 官网 sitemap(zh/en) 无招聘页；leju.zhiye.com 不存在 |
| 优艾智合 Youibot | https://www.youibot.com/ | 200 | 否 | 站点返回“正在安全检测中”WAF 拦截；youibot.zhiye.com 不存在 |
| 智平方 AI² Robotics | https://ai2robotics.com/joinus/ | 200 | 否 | WordPress 招聘页仅公司介绍，无岗位列表/ATS 链接 |
| 海柔创新官网 | https://www.hairobotics.com/join-us | 200 | 部分 | 官网 Careers 仅列社招岗位（售后工程师/现场应用工程师等，非实习） |
| Bing 搜索 | https://www.bing.com/search?q=... | 200 | 否 | 返回与查询无关的结果（数据中心 IP 被降级），RSS 输出同样无效，无法用于站点发现 |
| 深圳市科创学院 AIRS | https://www.szairs.org/ ; https://www.airs.org.cn/ | DNS失败 | 否 | 域名无法解析 |

## 三类岗位（应用工程师/技术支持/产品经理）实习 HC 结论

- 优必选 UBTECH：产品经理类 2 个（AI产品实习生、产品实习生）；应用工程师类 0；技术支持类 0（官网“技术支持工程师”为正式岗，非实习）。
- 普渡科技 Pudu：应用工程师类 1 个（部署优化实习生）；产品经理类 0（官网“软件产品经理/解决方案工程师”为正式岗，非实习）。
- 速腾聚创 RoboSense：产品经理类 1 个（产品经理—实习生，深圳南山）；应用工程师类 0；技术支持类 0。
- 技术支持类实习：上述所有官方通道（大疆/优必选/越疆/普渡/云鲸/海柔/汇川/速腾/大族/星尘）均未发现“技术支持/售前/售后/客户成功/运维”字样的实习岗 —— 已查，无。

## 已知限制
- 北森 API `GetJobAdPageList` 单页上限 15 条，且部分门户返回条数少于门户显示 Count（如优必选 100/115、云鲸 50/65），可能有少量岗位未取全。
- MokaHR 岗位列表接口对部分站点（如星尘智能）不返回实习岗，实习岗仅在职位短链 /su/xxx 中，需逐个解析。
- 飞书招聘（逐际动力、众擎）接口带 `_signature` 反爬签名，本次未能破解。