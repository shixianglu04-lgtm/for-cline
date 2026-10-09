#!/bin/bash
cd /workspace
mkdir -p data/liepin_com
CO=("越疆" "普渡" "云鲸" "乐聚" "逐际动力" "众擎" "海柔" "奥比中光" "影石" "优必选" "速腾聚创" "库犸" "星尘智能" "帕西尼" "优艾智合" "大疆" "越凡" "睿尔曼" "自变量" "数字华夏" "拓竹" "BrainCo" "强脑" "未来机器人" "杉川" "银星智能" "镭神" "戴盟" "智平方" "跨维" "灵初" "众为兴" "雷赛智能")
for c in "${CO[@]}"; do
  out="data/liepin_com/${c}.json"
  if [ -s "$out" ]; then echo "skip $c"; continue; fi
  python3 tools/liepin_scrape.py search "$c" --city sz --pages 1 --out "$out" >/dev/null 2>&1
  echo "$c -> $(jq 'length' "$out" 2>/dev/null)"
  sleep 2
done
echo done
