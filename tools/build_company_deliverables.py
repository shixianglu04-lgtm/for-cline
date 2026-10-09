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
            'experience_threshold': pick_sentences(req, r'经验|年以[上下]|熟悉|具备') or None,
            'graduation_limit': pick_sentences(body, r'届|在校|在读|实习期|实习时间|每周|个月|学历'),
            'education': education(req),
            'internship_terms': pick_sentences(body, r'实习期|实习时间|每周|个月|天/周|持续'),
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
            'city': '深圳市' + ('（%s）' % '、'.join([x for x in locs if x])) if locs else '深圳市',
            'job_family': family(title),
            'requirements': [x.strip() for x in re.split(r'[\n；;]', desc) if len(x.strip()) > 5][:12],
            'experience_threshold': pick_sentences(desc, r'经验|年以[上下]') or None,
            'graduation_limit': pick_sentences(desc, r'届|在校|在读|实习期|实习时间|每周|个月') or None,
            'education': education(desc),
            'internship_terms': pick_sentences(desc, r'实习期|实习时间|每周|个月|天/周|持续') or None,
            'salary': None,
            'evidence': ('职位名称：%s；工作地：%s；职位描述：%s' % (title, '、'.join([x for x in locs if x]), desc[:600])).strip(),
            'collected_at': NOW,
            'notes': '工作地来自 MokaHR 职位 JSON 的 locations 字段；薪资页面未标注。',
        }
        records.append(rec)

json.dump(records, open(os.path.join(OUT, 'company_jobs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('records', len(records))
from collections import Counter
print(Counter(r['job_family'] for r in records))
print(Counter(r['company'] for r in records))
