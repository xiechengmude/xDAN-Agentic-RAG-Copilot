#!/bin/bash
# FlashSearch API 接口调用示例
# 包含所有API端点的完整调用例子

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# API配置
API_HOST=${API_HOST:-"localhost"}
API_PORT=${API_PORT:-"8050"}
API_BASE="http://${API_HOST}:${API_PORT}"

echo -e "${BLUE}=================================================${NC}"
echo -e "${CYAN}🚀 FlashSearch API 接口调用示例${NC}"
echo -e "${CYAN}📡 API地址: $API_BASE${NC}"
echo -e "${BLUE}=================================================${NC}"

# 函数：运行示例并显示结果
run_example() {
    local name=$1
    local cmd=$2
    echo -e "\n${YELLOW}▶ $name${NC}"
    echo -e "${PURPLE}命令:${NC}"
    echo "$cmd"
    echo -e "${GREEN}响应:${NC}"
    eval "$cmd"
    echo -e "${BLUE}------------------------------------------------${NC}"
}

# 1. 健康检查
echo -e "\n${CYAN}📋 1. 基础信息接口${NC}"

run_example "健康检查" \
"curl -s '$API_BASE/health' | python3 -m json.tool"

run_example "获取统计信息" \
"curl -s '$API_BASE/stats' | python3 -m json.tool"

run_example "获取可用搜索模式" \
"curl -s '$API_BASE/modes' | python3 -m json.tool"

# 2. 同步搜索
echo -e "\n${CYAN}📋 2. 同步搜索接口${NC}"

run_example "Fast模式搜索（快速）" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"2024年人工智能最新进展\",
    \"mode\": \"fast\"
  }' | python3 -m json.tool | head -50"

run_example "Normal模式搜索（标准）" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"量子计算在金融领域的应用案例\",
    \"mode\": \"normal\",
    \"domain\": \"finance\"
  }' | python3 -m json.tool | head -50"

run_example "Deep模式搜索（深度）" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"深度分析：区块链技术在供应链管理中的优势和挑战\",
    \"mode\": \"deep\",
    \"domain\": \"tech\",
    \"enable_langfuse\": true
  }' | python3 -m json.tool | head -50"

# 3. 异步搜索
echo -e "\n${CYAN}📋 3. 异步搜索接口${NC}"

run_example "提交异步搜索任务" \
"curl -s -X POST '$API_BASE/search/async' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"新能源汽车产业链深度研究报告\",
    \"mode\": \"deep\",
    \"domain\": \"academic\"
  }' | python3 -m json.tool"

# 4. SSE流式搜索
echo -e "\n${CYAN}📋 4. SSE流式搜索接口${NC}"

echo -e "${YELLOW}▶ SSE流式搜索示例${NC}"
echo -e "${PURPLE}命令:${NC}"
echo "curl -N -X POST '$API_BASE/search/stream' \\
  -H 'Content-Type: application/json' \\
  -H 'Accept: text/event-stream' \\
  -d '{
    \"query\": \"实时流式搜索测试：最新科技动态\",
    \"mode\": \"fast\"
  }' --no-buffer"

echo -e "${GREEN}说明:${NC} SSE接口会实时推送事件流，包括进度更新和分块答案"
echo -e "${BLUE}------------------------------------------------${NC}"

# 5. 验证接口
echo -e "\n${CYAN}📋 5. 查询验证接口${NC}"

run_example "验证有效查询" \
"curl -s -X POST '$API_BASE/validate' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"什么是机器学习？\"
  }' | python3 -m json.tool"

run_example "验证无效查询（太短）" \
"curl -s -X POST '$API_BASE/validate' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"AI\"
  }' | python3 -m json.tool"

# 6. 领域搜索示例
echo -e "\n${CYAN}📋 6. 不同领域搜索示例${NC}"

# 新闻领域
run_example "新闻领域搜索" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"今日最新科技新闻\",
    \"mode\": \"fast\",
    \"domain\": \"news\"
  }' | python3 -m json.tool | head -30"

# 金融领域
run_example "金融领域搜索" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"苹果公司最新财报分析\",
    \"mode\": \"normal\",
    \"domain\": \"finance\"
  }' | python3 -m json.tool | head -30"

# 学术领域
run_example "学术领域搜索" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"深度学习在医疗影像诊断中的应用研究\",
    \"mode\": \"deep\",
    \"domain\": \"academic\"
  }' | python3 -m json.tool | head -30"

# 政策领域
run_example "政策领域搜索" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"2024年人工智能监管政策最新动态\",
    \"mode\": \"normal\",
    \"domain\": \"policy\"
  }' | python3 -m json.tool | head -30"

# 7. 高级用法
echo -e "\n${CYAN}📋 7. 高级用法示例${NC}"

# 带完整参数的搜索
run_example "完整参数搜索" \
"curl -s -X POST '$API_BASE/search' \
  -H 'Content-Type: application/json' \
  -d '{
    \"query\": \"ChatGPT对教育行业的影响分析\",
    \"mode\": \"deep\",
    \"domain\": \"academic\",
    \"enable_langfuse\": true
  }' | python3 -m json.tool | head -30"

# 8. SSE流式搜索完整示例
echo -e "\n${CYAN}📋 8. SSE流式搜索完整示例（限时10秒）${NC}"

echo -e "${YELLOW}▶ 实时流式搜索演示${NC}"
echo -e "${PURPLE}执行中...（最多显示10秒）${NC}"
timeout 10 curl -N -X POST "$API_BASE/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "query": "SSE流式搜索演示",
    "mode": "fast"
  }' --no-buffer 2>/dev/null | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        echo -e "${GREEN}[事件]${NC} $line"
    fi
done || echo -e "${YELLOW}流式演示结束（10秒超时）${NC}"

echo -e "${BLUE}------------------------------------------------${NC}"

# 9. 批量测试
echo -e "\n${CYAN}📋 9. 批量测试示例${NC}"

echo -e "${YELLOW}▶ 批量问题测试脚本${NC}"
cat << 'EOF'
#!/bin/bash
# 批量测试多个问题
questions=(
    "什么是深度学习？"
    "量子计算的基本原理"
    "区块链技术应用"
)

for q in "${questions[@]}"; do
    echo "搜索: $q"
    curl -s -X POST "$API_BASE/search" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$q\", \"mode\": \"fast\"}" \
        | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'答案长度: {len(d.get(\"answer\",\"\"))}字符')"
    sleep 2
done
EOF

echo -e "${BLUE}------------------------------------------------${NC}"

# 10. 性能测试
echo -e "\n${CYAN}📋 10. 性能测试示例${NC}"

echo -e "${YELLOW}▶ 响应时间测试${NC}"
echo -e "${PURPLE}命令:${NC}"
echo 'time curl -s -X POST "$API_BASE/search" \
  -H "Content-Type: application/json" \
  -d '"'"'{"query": "性能测试", "mode": "fast"}'"'"' \
  -o /dev/null -w "状态码: %{http_code}\n响应时间: %{time_total}s\n"'

# 总结
echo -e "\n${BLUE}=================================================${NC}"
echo -e "${GREEN}✨ API调用示例完成！${NC}"
echo -e "${BLUE}=================================================${NC}"

echo -e "\n${CYAN}📚 使用提示:${NC}"
echo -e "1. 设置API地址: ${YELLOW}export API_HOST=your-host API_PORT=your-port${NC}"
echo -e "2. Fast模式适合快速查询（约30-60秒）"
echo -e "3. Normal模式适合标准搜索（约60-120秒）"
echo -e "4. Deep模式适合深度分析（约120-180秒）"
echo -e "5. SSE流式接口支持实时进度更新"
echo -e "6. 异步接口适合长时间运行的搜索任务"

echo -e "\n${CYAN}🔗 更多信息:${NC}"
echo -e "- API文档: ${YELLOW}$API_BASE/docs${NC}"
echo -e "- 交互式文档: ${YELLOW}$API_BASE/redoc${NC}"
echo -e "- OpenAPI规范: ${YELLOW}$API_BASE/openapi.json${NC}"