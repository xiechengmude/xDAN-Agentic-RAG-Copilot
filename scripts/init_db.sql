-- PostgreSQL初始化脚本
-- xDAN RAG Service数据库架构

-- 创建数据库（如果需要）
-- CREATE DATABASE xdan_rag_service;

-- 切换到数据库
-- \c xdan_rag_service;

-- 创建chats表 - 存储对话会话信息
CREATE TABLE IF NOT EXISTS chats (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    dataset_ids JSONB DEFAULT '[]'::jsonb,
    llm_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建messages表 - 存储对话消息
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建s3_workflow_traces表 - 存储S3框架工作流追踪
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
);

-- 创建langfuse_sessions表 - 存储Langfuse会话映射
CREATE TABLE IF NOT EXISTS langfuse_sessions (
    chat_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    trace_id VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_dataset_ids ON chats USING GIN (dataset_ids);
CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_chat_id ON s3_workflow_traces(chat_id);
CREATE INDEX IF NOT EXISTS idx_s3_workflow_traces_created_at ON s3_workflow_traces(created_at);
CREATE INDEX IF NOT EXISTS idx_langfuse_sessions_session_id ON langfuse_sessions(session_id);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为chats表添加更新时间触发器
DROP TRIGGER IF EXISTS update_chats_updated_at ON chats;
CREATE TRIGGER update_chats_updated_at 
    BEFORE UPDATE ON chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 添加注释
COMMENT ON TABLE chats IS '对话会话表，存储用户创建的对话信息';
COMMENT ON TABLE messages IS '消息表，存储对话中的所有消息';
COMMENT ON TABLE s3_workflow_traces IS 'S3框架工作流追踪表，记录每次S3搜索的详细信息';
COMMENT ON TABLE langfuse_sessions IS 'Langfuse会话映射表，关联本地chat_id和Langfuse session_id';

COMMENT ON COLUMN chats.dataset_ids IS '关联的知识库ID列表（JSON数组）';
COMMENT ON COLUMN chats.llm_config IS 'LLM配置信息（JSON对象）';
COMMENT ON COLUMN messages.role IS '消息角色：user（用户）、assistant（助手）、system（系统）';
COMMENT ON COLUMN messages.metadata IS '消息元数据，如引用文档、相似度分数等';
COMMENT ON COLUMN s3_workflow_traces.search_rounds IS 'S3框架执行的搜索轮数';
COMMENT ON COLUMN s3_workflow_traces.total_documents IS '检索到的文档总数';

-- 初始化数据（可选）
-- INSERT INTO chats (id, name, description) VALUES 
-- ('demo-chat-001', '演示对话', '用于演示的测试对话');