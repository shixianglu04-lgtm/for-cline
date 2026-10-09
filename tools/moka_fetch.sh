#!/bin/bash
# 用法: bash tools/moka_fetch.sh <siteUrl> <out.json>
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
URL="$1"; OUT="$2"
CK=$(mktemp)
curl -s -L -c "$CK" -b "$CK" --max-time 25 -A "$UA" "$URL" -o /workspace/tmp/_moka_page.html
IV=$(grep -oE '&quot;aesIv&quot;:&quot;[^&]+&quot;' /workspace/tmp/_moka_page.html | head -1 | sed 's/.*&quot;aesIv&quot;:&quot;//;s/&quot;//')
[ -z "$IV" ] && IV=$(grep -oE '"aesIv":"[^"]+"' /workspace/tmp/_moka_page.html | head -1 | sed 's/.*"aesIv":"//;s/"//')
echo "[fetch] iv=$IV page=$(wc -c < /workspace/tmp/_moka_page.html)"
MOKA_IV="$IV" node /workspace/tools/moka_scrape.js "$URL" "$OUT"
