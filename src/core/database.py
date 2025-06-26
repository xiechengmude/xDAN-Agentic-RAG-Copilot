#!/usr/bin/env python3
"""
PostgreSQL数据库层
提供高并发异步数据库支持，集成Langfuse可观察性
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from abc import ABC, abstractmethod

# PostgreSQL imports
try:
    import asyncpg
    from asyncpg import Pool
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None
    Pool = None
    raise ImportError("asyncpg is required for PostgreSQL support. Run: uv pip install asyncpg")

from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""
    
    @abstractmethod
    async def initialize(self):
        """初始化数据库连接和表结构"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    async def create_chat(self, chat_data: Dict[str, Any]) -> str:
        """创建对话"""
        pass
    
    @abstractmethod
    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """获取对话信息"""
        pass
    
    @abstractmethod
    async def update_chat(self, chat_id: str, updates: Dict[str, Any]) -> bool:
        """更新对话"""
        pass
    
    @abstractmethod
    async def delete_chat(self, chat_id: str) -> bool:
        """删除对话"""
        pass
    
    @abstractmethod
    async def list_chats(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取对话列表"""
        pass
    
    @abstractmethod
    async def save_message(self, chat_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """保存消息"""
        pass
    
    @abstractmethod
    async def get_messages(self, chat_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取消息列表"""
        pass


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL数据库适配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[Pool] = None
        
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL support. Install with: pip install asyncpg")
    
    async def _setup_connection(self, conn):
        """设置连接参数（高性能优化）"""
        # 设置会话级参数
        await conn.execute("SET jit = 'off'")  # 关闭JIT编译，减少延迟
        await conn.execute("SET statement_timeout = '30s'")
        await conn.execute("SET lock_timeout = '10s'")
        await conn.execute("SET idle_in_transaction_session_timeout = '60s'")
    
    async def _init_connection(self, conn):
        """初始化连接"""
        # 可以在这里添加更多初始化逻辑
        pass
    
    async def initialize(self):
        """初始化PostgreSQL连接池和表结构"""
        pg_config = self.config.get('postgresql', {})
        pool_config = pg_config.get('pool', {})
        
        # 构建连接字符串
        host = pg_config.get('host', 'localhost')
        port = pg_config.get('port', 5433)  # 修改默认端口为5433
        database = pg_config.get('database', 'xdan_rag_service')
        username = pg_config.get('username', 'ragflow_user')  # 修改默认用户名
        password = pg_config.get('password', 'ragflow123')  # 修改默认密码
        
        # 添加调试日志
        logger.info(f"数据库连接配置: host={host}, port={port}, database={database}, username={username}")
        logger.info(f"完整配置: {pg_config}")
        
        try:
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                min_size=pool_config.get('min_connections', 5),
                max_size=pool_config.get('max_connections', 20),
                command_timeout=pool_config.get('connection_timeout', 30),
                max_inactive_connection_lifetime=pool_config.get('idle_timeout', 600)
            )
            
            # 创建表结构
            await self._create_tables()
            logger.info(f"PostgreSQL连接池已初始化: {host}:{port}/{database}")
            
        except Exception as e:
            logger.error(f"PostgreSQL初始化失败: {e}")
            raise
    
    async def _create_tables(self):
        """创建表结构"""
        async with self.pool.acquire() as conn:
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
            
            # 创建messages表
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    chat_id VARCHAR(255) NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at)')
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL连接池已关闭")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                return result == 1
        except Exception as e:
            logger.error(f"PostgreSQL健康检查失败: {e}")
            return False
    
    async def create_chat(self, chat_data: Dict[str, Any]) -> str:
        """创建对话（使用事务）"""
        chat_id = chat_data['id']
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 使用事务确保数据一致性
                await conn.execute('''
                    INSERT INTO chats (id, name, description, dataset_ids, llm_config)
                    VALUES ($1, $2, $3, $4, $5)
                ''', 
                    chat_id,
                    chat_data['name'],
                    chat_data.get('description'),
                    json.dumps(chat_data.get('dataset_ids', [])),
                    json.dumps(chat_data.get('llm_config', {}))
                )
        return chat_id
    
    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """获取对话信息"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM chats WHERE id = $1', chat_id)
            if row:
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'dataset_ids': json.loads(row['dataset_ids']),
                    'llm_config': json.loads(row['llm_config']),
                    'created_at': row['created_at'].isoformat(),
                    'updated_at': row['updated_at'].isoformat()
                }
        return None
    
    async def update_chat(self, chat_id: str, updates: Dict[str, Any]) -> bool:
        """更新对话"""
        set_clauses = []
        values = []
        param_index = 1
        
        for key, value in updates.items():
            if key in ['name', 'description']:
                set_clauses.append(f"{key} = ${param_index}")
                values.append(value)
                param_index += 1
            elif key in ['dataset_ids', 'llm_config']:
                set_clauses.append(f"{key} = ${param_index}")
                values.append(json.dumps(value))
                param_index += 1
        
        set_clauses.append(f"updated_at = ${param_index}")
        values.append(datetime.now())
        values.append(chat_id)  # WHERE条件的参数
        
        query = f"UPDATE chats SET {', '.join(set_clauses)} WHERE id = ${param_index + 1}"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *values)
            return result.split()[-1] == '1'  # 检查是否更新了1行
    
    async def delete_chat(self, chat_id: str) -> bool:
        """删除对话（级联删除消息）"""
        async with self.pool.acquire() as conn:
            result = await conn.execute('DELETE FROM chats WHERE id = $1', chat_id)
            return result.split()[-1] == '1'
    
    async def list_chats(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取对话列表"""
        offset = (page - 1) * page_size
        
        async with self.pool.acquire() as conn:
            # 获取总数
            total = await conn.fetchval('SELECT COUNT(*) FROM chats')
            
            # 获取分页数据
            rows = await conn.fetch('''
                SELECT * FROM chats 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            ''', page_size, offset)
            
            chats = []
            for row in rows:
                chats.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'dataset_ids': json.loads(row['dataset_ids']),
                    'llm_config': json.loads(row['llm_config']),
                    'created_at': row['created_at'].isoformat(),
                    'updated_at': row['updated_at'].isoformat()
                })
            
            return {
                'chats': chats,
                'total': total,
                'page': page,
                'page_size': page_size,
                'has_next': offset + page_size < total,
                'has_prev': page > 1
            }
    
    async def save_message(self, chat_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """保存消息"""
        async with self.pool.acquire() as conn:
            message_id = await conn.fetchval('''
                INSERT INTO messages (chat_id, role, content, metadata)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            ''', 
                chat_id, 
                role, 
                content, 
                json.dumps(metadata or {})
            )
            return str(message_id)
    
    async def get_messages(self, chat_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取消息列表"""
        offset = (page - 1) * page_size
        
        async with self.pool.acquire() as conn:
            # 获取总数
            total = await conn.fetchval('SELECT COUNT(*) FROM messages WHERE chat_id = $1', chat_id)
            
            # 获取分页数据
            rows = await conn.fetch('''
                SELECT * FROM messages 
                WHERE chat_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3
            ''', chat_id, page_size, offset)
            
            messages = []
            for row in rows:
                messages.append({
                    'id': str(row['id']),
                    'role': row['role'],
                    'content': row['content'],
                    'metadata': json.loads(row['metadata']),
                    'created_at': row['created_at'].isoformat()
                })
            
            # 反转顺序以获得时间正序
            messages.reverse()
            
            return {
                'messages': messages,
                'total': total,
                'page': page,
                'page_size': page_size,
                'has_next': offset + page_size < total,
                'has_prev': page > 1
            }




class DatabaseManager:
    """PostgreSQL数据库管理器"""
    
    def __init__(self):
        self.adapter: Optional[PostgreSQLAdapter] = None
        from src.core.config_loader import get_config
        self.config_loader = get_config()
    
    async def initialize(self):
        """初始化PostgreSQL数据库适配器"""
        db_config = self.config_loader.get('database', {})
        
        if not ASYNCPG_AVAILABLE:
            raise RuntimeError("PostgreSQL支持不可用，请运行: uv pip install asyncpg")
        
        self.adapter = PostgreSQLAdapter(db_config)
        await self.adapter.initialize()
        logger.info("PostgreSQL数据库管理器已初始化")
    
    async def close(self):
        """关闭数据库连接"""
        if self.adapter:
            await self.adapter.close()
    
    def get_adapter(self) -> PostgreSQLAdapter:
        """获取PostgreSQL数据库适配器"""
        if not self.adapter:
            raise RuntimeError("数据库管理器未初始化")
        return self.adapter


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_database() -> DatabaseAdapter:
    """FastAPI依赖：获取数据库适配器"""
    return db_manager.get_adapter()