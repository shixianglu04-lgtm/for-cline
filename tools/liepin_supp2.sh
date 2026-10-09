#!/bin/bash
# 猎聘 第三批补充关键词 (更贴近"实习")
cd /workspace
mkdir -p data/liepin_supp2
KW=("机器人实习生" "智能硬件产品实习" "硬件产品经理实习" "产品实习生" \
    "技术支持工程师实习生" "解决方案工程师实习" "机器人服务工程师实习" \
    "机器人交付工程师" "机器人调试工程师" "机器人售后工程师" "机器人售前工程师" \
    "机器人应用实习生" "机器人产品实习生" "机器人技术支持工程师" "FAE实习生" \
    "应用工程师实习生" "现场应用实习生" "客户成功实习生" "交付工程师实习生" "调试工程师实习生")
for k in "${KW[@]}"; do
  out="data/liepin_supp2/${k}.json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  python3 tools/liepin_scrape.py search "$k" --city sz --pages 1 --out "$out" >/dev/null 2>&1
  echo "$k -> $(jq 'length' "$out" 2>/dev/null)"
  sleep 1.2
done
echo done
