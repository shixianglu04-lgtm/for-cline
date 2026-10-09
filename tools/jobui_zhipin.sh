#!/bin/bash
# 职友集 机器人相关关键词 + --resolve, 目标是找 original_domain=zhipin.com 的岗位
cd /workspace
mkdir -p data/jobui_zp
KW=("机器人应用工程师" "机器人技术支持" "机器人产品经理" "机器人解决方案" \
    "机器人交付" "机器人调试" "机器人售后" "机器人售前" "机器人FAE" \
    "机器人实施" "机器人服务工程师" "机器人应用开发" "具身智能" "人形机器人" \
    "机械臂" "AGV" "无人机" "外骨骼" "智能硬件产品经理" "机器人客户成功")
for k in "${KW[@]}"; do
  out="data/jobui_zp/${k}.json"
  if [ -s "$out" ]; then echo "skip $k"; continue; fi
  python3 tools/jobui_scrape.py "$k" 深圳 --pages 1 --resolve --out "$out" >/dev/null 2>&1
  echo "$k -> $(jq 'length' "$out" 2>/dev/null) (zhipin: $(jq '[.[]|select(.original_domain=="zhipin.com")]|length' "$out" 2>/dev/null))"
  sleep 1.5
done
echo done
