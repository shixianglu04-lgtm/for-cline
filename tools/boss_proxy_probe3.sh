#!/bin/bash
# BOSS 第三批代理探测 (allorigins/get, cors.lol, cors.workers, microlink, corsfix) + r.jina.ai 重试
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
T='https://www.zhipin.com/web/geek/job?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600'
TE='https%3A%2F%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjob%3Fquery%3D%25E6%259C%25BA%25E5%2599%25A8%25E4%25BA%25BA%26city%3D101280600'
OUT=/tmp/boss_proxy3; mkdir -p "$OUT"
pp () { local tag="$1" url="$2" f="$OUT/$tag.body" code
  code=$(curl -s -o "$f" -w '%{http_code}' --max-time 20 -A "$UA" --compressed "$url")
  echo "===== [$tag] HTTP=$code size=$(stat -c%s "$f" 2>/dev/null || echo 0)"
  echo "URL: $url"; echo "BODY(first 300): $(head -c 300 "$f" | tr -d '\n')"; echo; }
echo "########## BOSS 代理第三批 $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
pp allorigins_get "https://api.allorigins.win/get?url=$TE"
pp cors_lol      "https://api.cors.lol/?url=$TE"
pp cors_workers  "https://test.cors.workers.dev/?$T"
pp microlink     "https://api.microlink.io/?url=$TE"
pp corsfix       "https://proxy.corsfix.com/?$T"
pp jina_retry    "https://r.jina.ai/$T"
echo "########## done ##########"
