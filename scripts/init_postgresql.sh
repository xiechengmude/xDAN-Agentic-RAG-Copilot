#!/bin/bash

# PostgreSQL数据库初始化脚本
# 用于初始化xDAN RAG Service的PostgreSQL数据库

# 设置数据库连接参数
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-xdan_rag_service}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

echo "🔧 初始化PostgreSQL数据库..."
echo "数据库: $DB_HOST:$DB_PORT/$DB_NAME"

# 检查psql是否安装
if ! command -v psql &> /dev/null; then
    echo "❌ 错误: psql未安装。请安装PostgreSQL客户端工具。"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# 创建数据库（如果不存在）
echo "📦 创建数据库（如果不存在）..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true

# 执行初始化脚本
echo "🏗️  执行数据库初始化脚本..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < "$(dirname "$0")/init_db.sql"

if [ $? -eq 0 ]; then
    echo "✅ 数据库初始化成功！"
else
    echo "❌ 数据库初始化失败"
    exit 1
fi

# 验证表是否创建成功
echo "🔍 验证数据库结构..."
TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('chats', 'messages', 's3_workflow_traces', 'langfuse_sessions');")

if [ "$TABLES" -eq 4 ]; then
    echo "✅ 所有表已成功创建"
    echo ""
    echo "📊 数据库表："
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt public.*"
else
    echo "⚠️  警告: 某些表可能未创建成功"
fi

echo ""
echo "🎉 PostgreSQL数据库初始化完成！"
echo "连接字符串: postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"