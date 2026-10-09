#!/bin/bash
# 职友集关键词矩阵采集: 深圳 + 实习 + 三类岗位关键词
cd /workspace
mkdir -p data/jobui
KW=("应用工程师" "现场应用" "FAE" "应用开发" "解决方案" "技术支持" "售前" "售后" "产品经理" "产品助理" "产品策划" "交付工程师" "调试工程师" "机器人" "具身智能" "机械臂" "AGV" "无人驾驶")
for k in "${KW[@]}"; do
  out="data/jobui/$(echo "$k" | tr -d ' ').json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  echo "== $k"
  python3 tools/jobui_scrape.py "$k" 深圳 --pages 2 --out "$out" >/dev/null 2>&1
  jq 'length' "$out" 2>/dev/null
  sleep 2
done
echo done
