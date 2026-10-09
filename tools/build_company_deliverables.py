#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总 T2 采集结果 -> /workspace/data/company_jobs.json / company_evidence.md / company_channels.md
数据来源：北森 zhiye.com 门户 API、MokaHR 官网 API（均为官方招聘系统）。"""
import json, re, os, time, html

TMP = '/workspace/tmp'
OUT = '/workspace/data'
NOW = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

FAM = [
    ('产品经理', r'产品经理|产品助理|产品策划|AI产品|产品实习生'),
    ('应用工程师', r'应用工程师|现场应用|应用开发|解决方案|部署|交付|调试|实施|FAE'),
    ('技术支持', r'技术支持|售前|售后|客户成功|技术运维|运维|服务工程师'),
]

def family(title):
    for name, pat in FAM:
        if re.search(pat, title):
            return name
    return '其他'

def clean(t):
    if not t:
        return ''
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = t.replace('\r', '\n')
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n+', '\n', t)
    return t.strip()

def pick_sentences(text, pat, limit=260):
    """从原文中截取包含关键词的原句（不改写）。"""
    if not text:
        return None
    parts = re.split(r'[\n。；;]', text)
    hits = [p.strip() for p in parts if p.strip() and re.search(pat, p)]
    if not hits:
        return None
    s = '；'.join(hits)[:limit]
    return s

def education(text):
    if not text:
        return None
    m = re.findall(r'(博士|硕士|本科|大专|专科|中专|高中)[^，。；\n]{0,12}学历|学历[^，。；\n]{0,6}(博士|硕士|本科|大专|专科)|(博士|硕士|本科|大专|专科)(在读|及以上|以上)', text)
    if m:
        return pick_sentences(text, r'博士|硕士|本科|大专|专科|学历', 160)
    return None

records = []
evidence_sections = []
channels = []

# ---------------- 北森 zhiye.com ----------------
BS = [
    ('ubtrobot', 'https://ubtrobot.zhiye.com', '优必选科技 UBTECH', '北森-优必选招聘门户'),
    ('dobot', 'https://dobot.zhiye.com', '越疆科技 Dobot', '北森-越疆招聘门户'),
    ('paxini', 'https://paxini.zhiye.com', '帕西尼感知科技 Paxini', '北森-帕西尼招聘门户'),
    ('pudutech', 'https://pudutech.zhiye.com', '普渡科技 Pudu Robotics', '北森-普渡招聘门户'),
    ('hairobotics', 'https://hairobotics.zhiye.com', '海柔创新 HAI ROBOTICS', '北森-海柔招聘门户'),
    ('inovance', 'https://inovance.zhiye.com', '汇川技术 Inovance', '北森-汇川招聘门户'),
    ('narwal', 'https://careers.narwal.com', '云鲸智能 Narwal', '北森-云鲸招聘门户'),
]
for org, base, comp, src in BS:
    f = os.path.join(TMP, 'bs_sz_%s.json' % org)
    if not os.path.exists(f):
        continue
    d = json.load(open(f, encoding='utf-8'))
    seen = set()
    for j in d['jobs']:
        title = j.get('JobAdName') or ''
        if not re.search(r'实习|Intern', title):
            continue
        if title in seen:
            continue
        seen.add(title)
        jid = j.get('JobAdId')
        duty = clean(j.get('Duty'))
        req = clean(j.get('Require'))
        body = (duty + '\n' + req).strip()
        url = '%s/intern/detail?jobAdId=%s' % (base, jid)
        rec = {
            'source': src,
            'source_url': url,
            'company': comp,
            'job_title': title,
            'city': '深圳市',
            'job_family': family(title),
            'requirements': [x.strip() for x in re.split(r'[\n；;]', req) if len(x.strip()) > 3][:12],
            'experience_threshold': pick_sentences(req, r'经验|年以[上下]|年限|实习经历') or None,
            'graduation_limit': pick_sentences(body, r'届|在校|在读|实习期|实习时间|每周|天/周|个月'),
            'education': education(req),
            'internship_terms': pick_sentences(body, r'实习期|实习时间|每周|天/周|实习[0-9]|[0-9]个月'),
            'salary': j.get('Salary'),
            'evidence': ('职位名称：%s；职责：%s；任职要求：%s' % (title, duty[:300], req[:400])).strip(),
            'collected_at': NOW,
            'notes': '城市由招聘门户「深圳市(4403)」地区筛选得出（官方API LocId=4403 过滤），岗位列表未单列工作地字段；salary 门户未公开（字段为 null）。',
        }
        records.append(rec)

# ---------------- Moka ----------------
MK = [
    ('moka_robosense_intern', 'https://app.mokahr.com/social-recruitment/robosense/118867?locale=zh-CN',
     '速腾聚创 RoboSense', 'MokaHR-速腾聚创实习生招聘官网'),
    ('dji_intern', 'https://apply.careers.dji.com/social-recruitment/dji/168240?locale=zh-CN',
     '大疆创新 DJI', 'MokaHR-大疆实习生招聘官网'),
]
for f, site, comp, src in MK:
    p = os.path.join(TMP, f + '.json')
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding='utf-8'))
    for j in d['jobs']:
        title = j.get('title') or ''
        if not re.search(r'实习|Intern', title):
            continue
        locs = [l.get('cityName') for l in (j.get('locations') or [])]
        if not any(('深圳' in (x or '')) or ('南山' in (x or '')) or ('广东' in (x or '')) for x in locs):
            continue
        desc = clean(j.get('jobDescription'))
        req = pick_sentences(desc, r'要求|任职|学历|专业|经验|熟悉|优先') or ''
        url = site.split('?')[0] + '#/job/' + str(j.get('id'))
        rec = {
            'source': src,
            'source_url': url,
            'company': comp,
            'job_title': title,
            'city': ('深圳市（南山区）' if any('南山' in (x or '') for x in locs) else '深圳市'),
            'job_family': family(title),
            'requirements': [x.strip() for x in re.split(r'[\n；;]', desc) if len(x.strip()) > 5][:12],
            'experience_threshold': pick_sentences(desc, r'经验|年以[上下]|年限') or None,
            'graduation_limit': pick_sentences(desc, r'届|在校|在读|实习期|实习时间|每周|天/周|[0-9]个月') or None,
            'education': education(desc),
            'internship_terms': pick_sentences(desc, r'实习期|实习时间|每周|天/周|[0-9]个月') or None,
            'salary': None,
            'evidence': ('职位名称：%s；工作地：%s；职位描述：%s' % (title, '、'.join([x for x in locs if x]), desc[:600])).strip(),
            'collected_at': NOW,
            'notes': '工作地来自 MokaHR 职位 JSON 的 locations 字段（该岗位同时开放：%s）；薪资页面未标注。' % ('、'.join([x for x in locs if x])),
        }
        records.append(rec)

json.dump(records, open(os.path.join(OUT, 'company_jobs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('records', len(records))
from collections import Counter
print(Counter(r['job_family'] for r in records))
print(Counter(r['company'] for r in records))

# ---------------- company_evidence.md ----------------
lines = ['# 企业官网/官方招聘系统 · 深圳机器人实习岗位证据（T2）',
         '',
         '采集时间(UTC)：%s' % NOW,
         '说明：每条记录的 source_url 为官方招聘系统岗位页（北森门户为 SPA 深链 `/intern/detail?jobAdId=`；MokaHR 为 `#/job/<id>`）。',
         'evidence 字段为页面/官方接口返回的原文摘录，未做改写。',
         '']
for i, r in enumerate(records, 1):
    lines.append('## %d. %s — %s' % (i, r['company'], r['job_title']))
    lines.append('')
    lines.append('- 岗位类别：%s' % r['job_family'])
    lines.append('- 城市：%s' % r['city'])
    lines.append('- 来源系统：%s' % r['source'])
    lines.append('- 链接：%s' % r['source_url'])
    lines.append('- 采集时间(UTC)：%s' % r['collected_at'])
    lines.append('- 学历：%s' % (r['education'] or '页面未标注'))
    lines.append('- 经验门槛：%s' % (r['experience_threshold'] or '页面未标注'))
    lines.append('- 毕业时间限制/在校生·实习时长：%s' % (r['graduation_limit'] or '页面未标注'))
    lines.append('- 实习时长/出勤：%s' % (r['internship_terms'] or '页面未标注'))
    lines.append('- 薪资：%s' % (r['salary'] or '页面未标注'))
    lines.append('')
    lines.append('关键原文：')
    lines.append('')
    lines.append('```')
    lines.append(r['evidence'][:1200])
    lines.append('```')
    lines.append('')
open(os.path.join(OUT, 'company_evidence.md'), 'w', encoding='utf-8').write('\n'.join(lines))

# ---------------- company_channels.md ----------------
CH = [
 ('大疆 DJI（实习生招聘官网）', 'https://apply.careers.dji.com/social-recruitment/dji/168240', '200(API)', '是', 'MokaHR：POST /api/outer/ats-apply/website/jobs/v2（AES-128-CBC 解密，IV=页面 aesIv）。实习生站在招 4 个岗位，无三类岗位'),
 ('大疆 DJI（校招/社招）', 'https://apply.careers.dji.com/campus-recruitment/dji/143359 ; /social-recruitment/dji/170070', '200(API)', '是', 'MokaHR 同上；校招 140 条、社招 504 条，标题含“实习”者 0 条（正式校招/社招）'),
 ('优必选 UBTECH', 'https://ubtrobot.zhiye.com', '200', '是', '北森：POST /api/Jobad/GetJobAdPageList（LocId=4403 深圳过滤）；深圳在招实习 10 个（含产品实习生/AI产品实习生）'),
 ('越疆科技 Dobot', 'https://dobot.zhiye.com', '200', '是', '北森 同上；深圳在招实习 6 个，均为市场/采购/商务/财务/设计，无三类岗位'),
 ('帕西尼感知 Paxini', 'https://paxini.zhiye.com', '200', '是', '北森 同上；深圳在招实习 1 个（招聘实习生）'),
 ('普渡科技 Pudu Robotics', 'https://pudutech.zhiye.com', '200', '是', '北森 同上；深圳在招实习 4 个（含“部署优化实习生”=应用工程师类）'),
 ('海柔创新 HAI ROBOTICS', 'https://hairobotics.zhiye.com', '200', '是', '北森 同上；深圳在招 119 条中标题含“实习”者 0 条 —— 已查，无实习岗'),
 ('汇川技术 Inovance', 'https://inovance.zhiye.com', '200', '是', '北森 同上；深圳在招 42 条中标题含“实习”者 0 条 —— 已查，无实习岗'),
 ('云鲸智能 Narwal', 'https://careers.narwal.com', '200', '是', '北森（企业自定义域名，stcms.beisen.com 资源）；深圳在招实习 1 个（招聘实习生）'),
 ('速腾聚创 RoboSense（实习生招聘）', 'https://app.mokahr.com/social-recruitment/robosense/118867', '200(API)', '是', 'MokaHR 同上；在招实习 19 个，含“产品经理—实习生（深圳南山）”'),
 ('速腾聚创 RoboSense（官网入口）', 'https://www.robosense.cn/about/joinus', '200', '是', '官网列出 校园招聘/社会招聘/实习生招聘 三个 MokaHR 入口'),
 ('星尘智能 Astribot', 'https://app.mokahr.com/campus-recruitment/astribot/144862 ; /social-recruitment/astribot/144861', '200(API)', '是', 'MokaHR 同上；官网列实习岗“具身智能算法实习生/营销实习生”，但 jobs/v2 列表未返回实习岗（疑 hireMode 过滤），需职位短链 /su/xxx'),
 ('大族激光 Han’s Laser', 'https://app.mokahr.com/social-recruitment/hanslaser/46382', '200(API)', '是', 'MokaHR 同上；36 条社招岗位中标题含“实习”者 0 条'),
 ('逐际动力 LimX Dynamics', 'https://career.limxdynamics.com/index', '200', '否', '飞书招聘(atsx)：/api/v1/search/job/posts 需 `_signature`（JS 混淆的签名函数），无签名 POST 返回 405，GET 返回 SPA；页面明文含“实习岗”栏目'),
 ('众擎机器人 EngineAI', 'https://dx3a2bminsq.jobs.feishu.cn/index', '-', '否', '飞书招聘(jobs.feishu.cn)，同逐际动力的签名机制，本次未攻克'),
 ('影石 Insta360', 'https://www.insta360.com/cn/careers', '403', '否', 'Cloudflare 人机验证（响应标题 "Just a moment..."），curl 无法取得内容'),
 ('奥比中光 Orbbec', 'https://www.orbbec.com.cn/', '200', '否', '官网无招聘入口（JS 站），未发现 ATS 链接；orbbec.zhiye.com 不存在'),
 ('乐聚机器人 Leju', 'https://www.lejurobot.com/', '200', '否', '官网 sitemap(zh/en) 无招聘页；leju.zhiye.com 不存在'),
 ('优艾智合 Youibot', 'https://www.youibot.com/', '200', '否', '站点返回“正在安全检测中”WAF 拦截；youibot.zhiye.com 不存在'),
 ('智平方 AI² Robotics', 'https://ai2robotics.com/joinus/', '200', '否', 'WordPress 招聘页仅公司介绍，无岗位列表/ATS 链接'),
 ('海柔创新官网', 'https://www.hairobotics.com/join-us', '200', '部分', '官网 Careers 仅列社招岗位（售后工程师/现场应用工程师等，非实习）'),
 ('Bing 搜索', 'https://www.bing.com/search?q=...', '200', '否', '返回与查询无关的结果（数据中心 IP 被降级），RSS 输出同样无效，无法用于站点发现'),
 ('深圳市科创学院 AIRS', 'https://www.szairs.org/ ; https://www.airs.org.cn/', 'DNS失败', '否', '域名无法解析'),
]
lines = ['# 通道实测结论表（T2：企业官网/官方招聘系统）', '',
         '采集时间(UTC)：%s' % NOW, '',
         '| 公司/站点 | URL | HTTP码 | 是否可抓 | 接口/结论 |',
         '| --- | --- | --- | --- | --- |']
for c in CH:
    lines.append('| %s | %s | %s | %s | %s |' % c)
lines += ['', '## 三类岗位（应用工程师/技术支持/产品经理）实习 HC 结论', '',
          '- 优必选 UBTECH：产品经理类 2 个（AI产品实习生、产品实习生）；应用工程师类 0；技术支持类 0（官网“技术支持工程师”为正式岗，非实习）。',
          '- 普渡科技 Pudu：应用工程师类 1 个（部署优化实习生）；产品经理类 0（官网“软件产品经理/解决方案工程师”为正式岗，非实习）。',
          '- 速腾聚创 RoboSense：产品经理类 1 个（产品经理—实习生，深圳南山）；应用工程师类 0；技术支持类 0。',
          '- 技术支持类实习：上述所有官方通道（大疆/优必选/越疆/普渡/云鲸/海柔/汇川/速腾/大族/星尘）均未发现“技术支持/售前/售后/客户成功/运维”字样的实习岗 —— 已查，无。',
          '',
          '## 已知限制',
          '- 北森 API `GetJobAdPageList` 单页上限 15 条，且部分门户返回条数少于门户显示 Count（如优必选 100/115、云鲸 50/65），可能有少量岗位未取全。',
          '- MokaHR 岗位列表接口对部分站点（如星尘智能）不返回实习岗，实习岗仅在职位短链 /su/xxx 中，需逐个解析。',
          '- 飞书招聘（逐际动力、众擎）接口带 `_signature` 反爬签名，本次未能破解。',
          ]
open(os.path.join(OUT, 'company_channels.md'), 'w', encoding='utf-8').write('\n'.join(lines))
print('written md')

