#!/bin/bash
# 职友集: 按公司名检索深圳实习岗位 (覆盖机器人公司全部实习 HC)
cd /workspace
mkdir -p data/jobui_com
CO=("大疆" "优必选" "越疆" "普渡" "云鲸" "乐聚" "逐际动力" "众擎" "海柔创新" "库犸" "奥比中光" "影石" "速腾聚创" "优艾智合" "元化智能" "微创机器人" "越凡创新" "帕西尼" "睿尔曼" "深圳科创学院" "汇川技术" "雷赛智能" "大族激光" "云洲智能" "强脑科技" "智平方" "自变量机器人" "灵初智能" "跨维智能" "星尘智能" "未来机器人" "优乐赛" "镭神智能" "杉川机器人" "银星智能" "奇诺动力" "擎羽科技" "卓驭科技" "亮源新创" "安克创新" "速英科技" "易桉智能" "造梦科技" "灵动星核" "优地科技" "普渡机器人" "中兵智能创新研究院")
for c in "${CO[@]}"; do
  out="data/jobui_com/${c}.json"
  if [ -s "$out" ]; then echo "skip $c"; continue; fi
  python3 tools/jobui_scrape.py "$c" 深圳 --pages 1 --out "$out" >/dev/null 2>&1
  n=$(jq 'length' "$out" 2>/dev/null || echo 0)
  echo "$c -> $n"
  sleep 1.5
done
echo done
