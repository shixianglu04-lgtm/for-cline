#!/usr/bin/env python3
# 北森 zhiye.com 招聘门户采集器
# 用法: python3 tools/beisen_scrape.py <org> <out.json>
#   org 例: ubtrobot  (即 https://ubtrobot.zhiye.com)
import sys, json, urllib.request, time
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
def post(url, body, referer):
    data=json.dumps(body).encode()
    req=urllib.request.Request(url, data=data, method='POST', headers={
        'User-Agent':UA,'Content-Type':'application/json','Accept':'application/json',
        'Origin':referer.rsplit('/',1)[0] if referer.endswith('/') else '/'.join(referer.split('/')[:3]),
        'Referer':referer})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8','ignore'))
def main():
    org=sys.argv[1]; out=sys.argv[2]; loc=sys.argv[3] if len(sys.argv)>3 else ''
    base=org if org.startswith('http') else f'https://{org}.zhiye.com'
    url=base+'/api/Jobad/GetJobAdPageList'
    ref=base+'/campus/jobs'
    all_j=[]; page=1
    while True:
        body={'PageIndex':page,'PageSize':15}
        if loc: body['LocId']=loc
        j=post(url, body, ref)
        d=j.get('Data') or []
        all_j.extend(d)
        total=j.get('Count') or len(all_j)
        print(f'[{org}] page {page} got {len(d)} count {total}', file=sys.stderr)
        if not d or len(all_j)>=total: break
        page+=1
        if page>40: break
        time.sleep(0.4)
    json.dump({'org':org,'locId':loc,'base':base,'api':url,'collected_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'total':len(all_j),'jobs':all_j}, open(out,'w'), ensure_ascii=False, indent=1)
    print(f'[{org}] saved {len(all_j)} -> {out}', file=sys.stderr)
main()
