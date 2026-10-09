#!/bin/bash
# BOSS直聘 公开读取代理探测 (r.jina.ai / codetabs / allorigins / corsproxy ...)
# 用法: bash tools/boss_proxy_probe.sh > data/boss_proxy_probe.log 2>&1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TARGET='https://www.zhipin.com/web/geek/job?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600'
TARGET_ENC='https%3A%2F%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjob%3Fquery%3D%25E6%259C%25BA%25E5%2599%25A8%25E4%25BA%25BA%26city%3D101280600'
OUT=/tmp/boss_proxy
mkdir -p "$OUT"

pp () {  # $1=tag $2=url
  local tag="$1" url="$2" f="$OUT/$tag.body" code
  code=$(curl -s -o "$f" -w '%{http_code}' --max-time 35 -A "$UA" --compressed "$url")
  local sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  echo "===== [$tag] HTTP=$code size=$sz"
  echo "URL: $url"
  echo "BODY(first 500): $(head -c 500 "$f" | tr -d '\n')"
  echo
}

echo "########## BOSS 代理探测 $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"

pp jina_search "https://r.jina.ai/$TARGET"
pp jina_home   "https://r.jina.ai/https://www.zhipin.com/"
pp codetabs    "https://api.codetabs.com/v1/proxy?quest=$TARGET_ENC"
pp allorigins  "https://api.allorigins.win/raw?url=$TARGET_ENC"
pp corsproxy   "https://corsproxy.io/?$TARGET_ENC"
pp thingproxy  "https://thingproxy.freeboard.io/fetch/$TARGET"
pp whateverorigin "http://www.whateverorigin.org/get?url=$TARGET_ENC"
pp textise     "https://r.jina.ai/https://m.zhipin.com/"

echo "########## done ##########"
