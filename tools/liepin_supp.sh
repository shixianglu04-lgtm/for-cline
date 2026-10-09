#!/bin/bash
# 猎聘 补充关键词 (不与主协调者矩阵重复)
cd /workspace
mkdir -p data/liepin_supp
KW=("机器人客户成功" "机器人解决方案工程师" "机器人实施" "机器人售后技术支持" \
    "机器人售前技术支持" "机器人产品" "机器人应用" "机器人服务工程师" "机器人培训" \
    "外骨骼实习" "无人机实习" "无人驾驶实习" "激光雷达实习" "SLAM实习" "运动控制实习" \
    "机器人产品助理" "机器人客户支持" "机器人部署" "机器人应用开发" "机器人现场应用工程师")
for k in "${KW[@]}"; do
  out="data/liepin_supp/${k}.json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  python3 tools/liepin_scrape.py search "$k" --city sz --pages 1 --out "$out" >/dev/null 2>&1
  echo "$k -> $(jq 'length' "$out" 2>/dev/null)"
  sleep 1.2
done
echo done
