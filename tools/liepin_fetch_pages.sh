#!/bin/bash
# 逐个抓取猎聘岗位详情页(慢速, 避免触发限流), 保存原始 HTML 到 /tmp/lp_pages/
UA="Mozilla/5.0"
mkdir -p /tmp/lp_pages
IDS="1983736211 1981765709 1982685401 1985854639 1983379517 1985150549 1985874955 1985874941 1985458281 1981347583 1981943833 1984502141 1975047127 1985485575 1980960323 1984368725 1981859669 1981859679 1984022451 1984362641 1985850441 1983542087 1975390477 1983122411 1983013921 1985634031 1984900033 1979607823"
for id in $IDS; do
  f="/tmp/lp_pages/$id.html"
  if [ -s "$f" ] && [ $(stat -c%s "$f") -gt 20000 ] && ! grep -q "我们找遍了所有地方" "$f"; then
    echo "$id cached $(stat -c%s "$f")"; continue
  fi
  curl -s --max-time 30 -A "$UA" -o "$f" "https://www.liepin.com/job/$id.shtml"
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  if [ "$sz" -lt 20000 ] || grep -q "我们找遍了所有地方" "$f"; then
    sleep 12
    curl -s --max-time 30 -A "$UA" -o "$f" "https://www.liepin.com/job/$id.shtml"
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  fi
  echo "$id -> $sz"
  sleep 5
done
echo done
