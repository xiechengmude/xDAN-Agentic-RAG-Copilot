#!/bin/bash

# API接口测试运行脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 默认配置
BASE_URL="${BASE_URL:-http://localhost:8025}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}🧪 xDAN RAG API 接口测试${NC}"
echo "================================"
echo "服务器地址: $BASE_URL"
echo ""

# 检查服务是否运行
echo -n "检查API服务状态... "
if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务正常${NC}"
else
    echo -e "${RED}❌ 服务未响应${NC}"
    echo ""
    echo "请确保API服务正在运行:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./deploy/local_start.sh start"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# 安装必要的依赖
echo ""
echo "检查Python依赖..."
pip install -q requests

# 运行测试
echo ""
echo "开始运行接口测试..."
echo "================================"
echo ""

cd "$SCRIPT_DIR"
python test_all_apis.py --base-url "$BASE_URL" "$@"

# 显示最新的测试报告位置
LATEST_REPORT=$(ls -t api_test_report_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_REPORT" ]; then
    echo ""
    echo -e "${GREEN}📊 查看测试报告:${NC}"
    echo "  cat tests/$LATEST_REPORT"
    echo ""
    echo "或使用Python美化输出:"
    echo "  python -m json.tool tests/$LATEST_REPORT"
fi