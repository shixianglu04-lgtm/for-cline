#!/bin/bash
# 猎聘 深圳 关键词矩阵 (注意: 关键词不要带空格, 否则 SEO 页不渲染职位卡片)
cd /workspace
mkdir -p data/liepin
KW=("机器人实习" "机器人技术支持" "机器人产品经理" "机器人应用工程师" "技术支持实习" "产品经理实习" "售前实习" "售后实习" "解决方案实习" "FAE实习" "交付实习" "调试实习" "应用工程师实习" "现场应用实习" "产品助理实习" "客户成功实习" "具身智能实习" "人形机器人实习" "机械臂实习" "AGV实习" "机器人售后服务" "机器人交付")
for k in "${KW[@]}"; do
  out="data/liepin/${k}.json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  python3 tools/liepin_scrape.py search "$k" --city sz --pages 1 --out "$out" >/dev/null 2>&1
  n=$(jq 'length' "$out" 2>/dev/null || echo 0)
  echo "$k -> $n"
  sleep 1.5
done
echo done
