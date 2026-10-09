#!/bin/bash
# BOSS直聘 第二轮: SEO/移动端页面 + api.zhipin.com 端点探测
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
CJ=/tmp/boss_cookies.txt
OUT=/tmp/boss_probe2
mkdir -p "$OUT"

probe () {  # tag url extra...
  local tag="$1"; local url="$2"; shift 2
  local f="$OUT/$tag.body" code
  code=$(curl -s -o "$f" -w '%{http_code}' --max-time 25 -A "$UA" --compressed \
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
        -H 'Accept-Language: zh-CN,zh;q=0.9' -b "$CJ" "$@" "$url")
  local sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  echo "===== [$tag] HTTP=$code size=$sz"
  echo "URL: $url"
  echo "BODY(first 300): $(head -c 300 "$f" | tr -d '\n')"
  echo
}

echo "########## BOSS 第二轮探测 $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"

# SEO 城市/搜索页
probe www_shenzhen 'https://www.zhipin.com/shenzhen/'
probe www_seo_job  'https://www.zhipin.com/shenzhen/?query=%E6%9C%BA%E5%99%A8%E4%BA%BA'
probe m_shenzhen   'https://m.zhipin.com/shenzhen/'
probe m_seo_job    'https://m.zhipin.com/shenzhen/?query=%E6%9C%BA%E5%99%A8%E4%BA%BA'
probe m_search     'https://m.zhipin.com/job/?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600'

# api.zhipin.com 各端点
probe api_search   'https://api.zhipin.com/wapi/zpgeek/search/joblist.json?scene=1&query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600&page=1&pageSize=30' \
      -H 'Referer: https://www.zhipin.com/'
probe api_geek     'https://api.zhipin.com/wapi/zpgeek/mobile/search/joblist.json?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600' \
      -H 'Referer: https://m.zhipin.com/'

# BOSS 公开的 SEO sitemap / 静态接口
probe sitemap      'https://www.zhipin.com/sitemap.xml'
probe robots       'https://www.zhipin.com/robots.txt'
probe wapi_hot     'https://www.zhipin.com/wapi/zpgeek/search/joblist.json'
probe wapi_city    'https://www.zhipin.com/wapi/zpCommon/data/city.json'
probe wapi_industry 'https://www.zhipin.com/wapi/zpCommon/data/industry.json'
probe wapi_position 'https://www.zhipin.com/wapi/zpCommon/data/position.json'

# HTTP/2 强制
echo "----- HTTP/2 强制 (pc_search) -----"
curl -s --http2 -o "$OUT/pc_search_h2.body" -w 'HTTP=%{http_code} size=%{size_download}\n' --max-time 25 \
  -A "$UA" --compressed -b "$CJ" 'https://www.zhipin.com/web/geek/job?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600'
echo "body: $(head -c 200 "$OUT/pc_search_h2.body" | tr -d '\n')"

echo "########## done ##########"
