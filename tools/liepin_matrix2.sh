#!/bin/bash
cd /workspace
mkdir -p data/liepin2
KW=("机器人应用工程师实习" "机器人技术支持实习" "机器人售后实习" "机器人售前实习" "机器人交付实习" "机器人产品实习" "机器人解决方案实习" "具身智能产品实习" "人形机器人实习" "机械臂实习" "机器人调试实习" "机器人服务工程师实习" "机器人应用实习" "机器人产品助理实习" "无人机实习" "外骨骼实习" "智能硬件产品实习" "机器人客户成功实习" "机器人现场应用实习" "机器人实施实习" "机器视觉实习" "伺服实习" "运动控制实习" "机器人售前技术支持实习")
for k in "${KW[@]}"; do
  out="data/liepin2/${k}.json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  python3 tools/liepin_scrape.py search "$k" --city sz --pages 1 --out "$out" >/dev/null 2>&1
  echo "$k -> $(jq 'length' "$out" 2>/dev/null)"
  sleep 1.2
done
echo done
