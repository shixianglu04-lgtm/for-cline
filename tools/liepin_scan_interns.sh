#!/bin/bash
# 猎聘: 抓取深圳"实习"关键词的列表页(pn0..pn9, 40条/页), 用于发现机器人行业实习岗位
cd /workspace
mkdir -p data/liepin_scan
for p in $(seq 0 9); do
  out="data/liepin_scan/pn${p}.json"
  if [ -s "$out" ]; then echo "skip pn$p"; continue; fi
  python3 tools/liepin_scrape.py search "实习" --city sz --start $p --pages 1 --out "$out" >/dev/null 2>&1
  echo "pn$p -> $(jq 'length' "$out" 2>/dev/null)"
  sleep 1
 done
echo done
