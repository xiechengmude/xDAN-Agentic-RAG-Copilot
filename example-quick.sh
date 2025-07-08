#!/bin/bash
# FlashSearch API 快速测试示例
# 精简版API调用示例，快速验证各个接口

# API配置
HOST=${1:-"localhost"}
PORT=${2:-"${FLASHSEARCH_PORT:-8060}"}
API="http://$HOST:$PORT"

echo "🚀 FlashSearch API 快速测试"
echo "📡 API地址: $API"
echo "================================"

# 1. 健康检查
echo -e "\n1️⃣ 健康检查"
curl -s "$API/health" | python3 -m json.tool

# 2. 同步搜索 (Fast模式)
echo -e "\n2️⃣ 同步搜索 (Fast模式)"
curl -s -X POST "$API/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？", "mode": "fast"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'成功: {d[\"success\"]}, 答案长度: {len(d.get(\"answer\",\"\"))}字符, 耗时: {d.get(\"stats\",{}).get(\"response_time\",\"N/A\")}秒')"

# 3. 异步搜索
echo -e "\n3️⃣ 异步搜索"
curl -s -X POST "$API/search/async" \
  -H "Content-Type: application/json" \
  -d '{"query": "量子计算应用", "mode": "normal"}' \
  | python3 -m json.tool

# 4. SSE流式搜索 (5秒演示)
echo -e "\n4️⃣ SSE流式搜索 (5秒演示)"
timeout 5 curl -N -X POST "$API/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"query": "流式搜索测试", "mode": "fast"}' \
  --no-buffer 2>/dev/null | grep "^data:" | head -5

# 5. 查询验证
echo -e "\n5️⃣ 查询验证"
curl -s -X POST "$API/validate" \
  -H "Content-Type: application/json" \
  -d '{"query": "区块链技术"}' \
  | python3 -m json.tool

echo -e "\n✅ 快速测试完成！"