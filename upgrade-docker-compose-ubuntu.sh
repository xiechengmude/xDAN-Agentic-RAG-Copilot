#!/bin/bash

# Ubuntu 系统升级 Docker Compose 到 V2 的脚本

echo "=== Ubuntu 升级 Docker Compose V2 指南 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}方法 1: 使用 Docker 官方仓库安装（推荐）${NC}"
echo "==========================================="
cat << 'EOF'
# 1. 更新包索引
sudo apt-get update

# 2. 安装 Docker Compose 插件
sudo apt-get install docker-compose-plugin -y

# 3. 验证安装
docker compose version

# 4. 创建兼容性链接（可选，让 docker-compose 命令也能用）
sudo ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

EOF

echo -e "${YELLOW}方法 2: 手动下载安装${NC}"
echo "===================="
cat << 'EOF'
# 1. 删除旧版本
sudo apt-get remove docker-compose -y
sudo rm /usr/local/bin/docker-compose

# 2. 下载最新版本（替换版本号为最新）
DOCKER_COMPOSE_VERSION="v2.24.1"
sudo curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose

# 3. 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 4. 创建软链接到 Docker CLI 插件目录
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo ln -s /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose

# 5. 验证安装
docker-compose version
docker compose version

EOF

echo -e "${YELLOW}方法 3: 使用 Docker 官方安装脚本（最简单）${NC}"
echo "========================================="
cat << 'EOF'
# 1. 确保 Docker 仓库已配置
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release -y

# 2. 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 3. 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. 更新包索引并安装
sudo apt-get update
sudo apt-get install docker-compose-plugin -y

# 5. 验证
docker compose version

EOF

echo -e "${GREEN}升级后的使用方法：${NC}"
echo "=================="
cat << 'EOF'
# 新命令格式（推荐）
docker compose up -d
docker compose down
docker compose logs -f

# 如果创建了兼容性链接，旧命令也能用
docker-compose up -d
docker-compose down

# 检查版本
docker compose version    # 应该显示 v2.x.x
docker-compose version    # 如果有链接，也显示 v2.x.x

EOF

echo -e "${GREEN}常见问题解决：${NC}"
echo "=============="
cat << 'EOF'
# 如果遇到权限问题
sudo usermod -aG docker $USER
newgrp docker

# 如果找不到 docker compose 命令
export PATH=$PATH:/usr/libexec/docker/cli-plugins

# 完全卸载旧版本
sudo apt-get purge docker-compose
sudo pip3 uninstall docker-compose

# 检查安装位置
which docker-compose
which docker

EOF

echo -e "${RED}注意事项：${NC}"
echo "=========="
echo "1. Docker Compose V2 使用 'docker compose' 而不是 'docker-compose'"
echo "2. 大部分命令兼容，但有细微差异"
echo "3. 建议使用新的命令格式"
echo ""
echo "立即执行升级："
echo "sudo apt-get update && sudo apt-get install docker-compose-plugin -y"