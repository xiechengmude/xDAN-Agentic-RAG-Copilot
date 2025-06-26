#!/usr/bin/env python3
"""
PostgreSQL数据库初始化脚本
用于初始化xDAN RAG Service的数据库表结构
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config_loader import ConfigLoader

async def init_database():
    """初始化PostgreSQL数据库"""
    # 加载配置
    config_loader = ConfigLoader()
    db_config = config_loader.get('database', {})
    pg_config = db_config.get('postgresql', {})
    
    # 获取连接参数
    host = pg_config.get('host', 'localhost')
    port = pg_config.get('port', 5432)
    database = pg_config.get('database', 'xdan_rag_service')
    username = pg_config.get('username', 'postgres')
    password = pg_config.get('password', 'postgres')
    
    print(f"🔧 连接到PostgreSQL数据库: {host}:{port}/{database}")
    
    try:
        # 创建连接
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        print("✅ 数据库连接成功")
        
        # 读取SQL脚本
        sql_path = Path(__file__).parent / "init_db.sql"
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 直接执行创建表的语句
        print("🏗️  创建数据库表...")
        
        # 创建chats表
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(500) NOT NULL,
                description TEXT,
                dataset_ids JSONB DEFAULT '[]'::jsonb,
                llm_config JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建chats表")
        
        # 创建messages表
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(255) NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建messages表")
        
        # 创建s3_workflow_traces表
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS s3_workflow_traces (
                id VARCHAR(255) PRIMARY KEY,
                chat_id VARCHAR(255) NOT NULL,
                user_question TEXT NOT NULL,
                search_rounds INTEGER DEFAULT 0,
                total_documents INTEGER DEFAULT 0,
                final_answer TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE
            )
        ''')
        print("✅ 创建s3_workflow_traces表")
        
        # 创建langfuse_sessions表
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS langfuse_sessions (
                chat_id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                trace_id VARCHAR(255),
                user_id VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建langfuse_sessions表")
        
        # 创建索引
        print("\n📇 创建索引...")
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_dataset_ids ON chats USING GIN (dataset_ids)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_chat_id ON s3_workflow_traces(chat_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_created_at ON s3_workflow_traces(created_at)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_langfuse_sessions_session_id ON langfuse_sessions(session_id)')
        print("✅ 所有索引创建完成")
        
        # 创建触发器
        print("\n⚙️  创建触发器...")
        await conn.execute('''
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        ''')
        
        await conn.execute('''
            DROP TRIGGER IF EXISTS update_chats_updated_at ON chats
        ''')
        
        await conn.execute('''
            CREATE TRIGGER update_chats_updated_at 
                BEFORE UPDATE ON chats 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column()
        ''')
        print("✅ 触发器创建完成")
        
        # 验证表创建
        print("\n🔍 验证数据库结构...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            AND table_name IN ('chats', 'messages', 's3_workflow_traces', 'langfuse_sessions')
            ORDER BY table_name;
        """)
        
        print("\n📊 已创建的表:")
        for row in tables:
            print(f"  - {row['table_name']}")
        
        if len(tables) == 4:
            print("\n✅ 所有表已成功创建！")
        else:
            print(f"\n⚠️  警告: 预期4个表，实际创建了{len(tables)}个表")
        
        # 关闭连接
        await conn.close()
        
        print("\n🎉 PostgreSQL数据库初始化完成！")
        print(f"连接字符串: postgresql://{username}:****@{host}:{port}/{database}")
        
    except asyncpg.exceptions.InvalidCatalogNameError:
        print(f"\n❌ 错误: 数据库 '{database}' 不存在")
        print("请先创建数据库:")
        print(f"  CREATE DATABASE {database};")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database())