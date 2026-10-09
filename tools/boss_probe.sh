#!/bin/bash
# BOSS直聘 直连入口探测: 记录 HTTP 码 + 响应片段
# 用法: bash tools/boss_probe.sh > data/boss_probe.log 2>&1
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
CJ=/tmp/boss_cookies.txt
OUT=/tmp/boss_probe
mkdir -p "$OUT"

probe () {  # $1=tag  $2=url  $3=extra curl args...
  local tag="$1"; local url="$2"; shift 2
  local f="$OUT/$tag.body"
  local code
  code=$(curl -s -o "$f" -w '%{http_code}' --max-time 25 \
        -A "$UA" --compressed \
        -H 'Accept: application/json, text/plain, */*' \
        -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
        -H 'sec-ch-ua: "Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"' \
        -H 'sec-ch-ua-mobile: ?0' -H 'sec-ch-ua-platform: "Windows"' \
        -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' \
        "$@" "$url")
  local sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  echo "===== [$tag] HTTP=$code size=$sz"
  echo "URL: $url"
  echo "BODY(first 400): $(head -c 400 "$f" | tr -d '\n')"
  echo
}

echo "########## BOSS直聘 直连探测 $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"

# 1. 首页 (先拿 cookie)
echo "----- step: 首页取 cookie -----"
curl -s -o "$OUT/home.body" -w 'HTTP=%{http_code}\n' --max-time 25 -A "$UA" --compressed \
     -c "$CJ" 'https://www.zhipin.com/' 
echo "home size=$(stat -c%s "$OUT/home.body")"
echo "cookies:"; cat "$CJ" 2>/dev/null | grep -v '^#' | head -20
echo

# 2. PC 搜索页
probe pc_search 'https://www.zhipin.com/web/geek/job?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600' \
      -b "$CJ" -H 'Referer: https://www.zhipin.com/'

# 3. PC 搜索 API (zpgeek)
probe wapi_search 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json?scene=1&query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600&page=1&pageSize=30' \
      -b "$CJ" -H 'Referer: https://www.zhipin.com/web/geek/job?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600' \
      -H 'X-Requested-With: XMLHttpRequest'

# 4. mobile API
probe mobile_search 'https://www.zhipin.com/wapi/zpgeek/mobile/search/joblist.json?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600&page=1' \
      -b "$CJ" -H 'Referer: https://m.zhipin.com/'

# 5. m.zhipin.com
probe m_home 'https://m.zhipin.com/' -b "$CJ"

# 6. SEO 岗位详情页 (随便一个 id, 观察是否 WAF)
probe job_detail 'https://www.zhipin.com/job_detail/' -b "$CJ" -H 'Referer: https://www.zhipin.com/'

# 7. 公司页
probe gongsi 'https://www.zhipin.com/gongsi/' -b "$CJ" -H 'Referer: https://www.zhipin.com/'

# 8. api.zhipin.com
probe api_domain 'https://api.zhipin.com/' -b "$CJ"

# 9. 小程序 webview 风格接口
probe wx_mini 'https://www.zhipin.com/wapi/zpgeek/miniprogram/search/joblist.json?query=%E6%9C%BA%E5%99%A8%E4%BA%BA&city=101280600' \
      -b "$CJ" -H 'Referer: https://servicewechat.com/wx9e5cd6c6a1cd3f46/'

echo "########## done ##########"
