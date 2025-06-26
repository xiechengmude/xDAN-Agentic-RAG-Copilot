-- PostgreSQL初始化脚本
-- 创建xDAN RAG Service数据库和优化配置

-- 设置PostgreSQL高并发优化参数
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 创建chats表
CREATE TABLE IF NOT EXISTS chats (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    dataset_ids JSONB DEFAULT '[]'::jsonb,
    llm_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建messages表
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建性能优化索引
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);

-- 创建复合索引用于分页查询
CREATE INDEX IF NOT EXISTS idx_messages_chat_id_created_at ON messages(chat_id, created_at DESC);

-- 创建GIN索引用于JSONB字段
CREATE INDEX IF NOT EXISTS idx_chats_dataset_ids_gin ON chats USING GIN (dataset_ids);
CREATE INDEX IF NOT EXISTS idx_messages_metadata_gin ON messages USING GIN (metadata);

-- 创建用于更新timestamp的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为chats表添加自动更新timestamp的触发器
CREATE TRIGGER update_chats_updated_at 
    BEFORE UPDATE ON chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建用于Langfuse集成的额外表 (可选)
CREATE TABLE IF NOT EXISTS langfuse_traces (
    id VARCHAR(255) PRIMARY KEY,
    chat_id VARCHAR(255) REFERENCES chats(id) ON DELETE CASCADE,
    trace_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    trace_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_langfuse_traces_chat_id ON langfuse_traces(chat_id);
CREATE INDEX IF NOT EXISTS idx_langfuse_traces_trace_id ON langfuse_traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_langfuse_traces_session_id ON langfuse_traces(session_id);

-- 插入示例数据
INSERT INTO chats (id, name, description, dataset_ids, llm_config) VALUES 
(
    'demo-chat-001', 
    'xDAN RAG Demo对话', 
    '演示S3框架和Langfuse集成的示例对话',
    '["7e8d9e924cde11f0afc90242ac140006"]'::jsonb,
    '{"model_name": "deepseek-chat", "temperature": 0.7, "max_tokens": 2000}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- 数据库统计信息和维护
ANALYZE;

-- 显示配置信息
SELECT 
    'PostgreSQL高并发数据库初始化完成' as status,
    version() as postgresql_version,
    current_database() as database_name,
    current_timestamp as initialized_at;