#!/bin/bash

# 启动服务器（无代理版本）
# 用于测试环境，避免代理干扰

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}清除代理设置...${NC}"
# 清除所有代理环境变量
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
unset all_proxy
unset ALL_PROXY
unset no_proxy
unset NO_PROXY

echo -e "${GREEN}✅ 代理已清除${NC}"

# 调用原始启动脚本
echo -e "${BLUE}启动服务器...${NC}"
exec ./start_server.sh "$@"