#!/usr/bin/env python3
"""
xDAN Unified API Server - PostgreSQL Version
统一的API服务，整合LiteLLM SDK（对话功能）和RAGFlow代理（知识库管理）
支持PostgreSQL数据库，解决并发问题
"""

import os
import sys
import json
import logging
import asyncio
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
from asyncpg.pool import Pool

# Import our modules
from src.core.config_loader import get_config
from src.clients.litellm_sdk_client_v2 import LiteLLMSDKClientV2 as LiteLLMSDKClient
from src.clients.ragflow_client import RAGFlowClient
from src.core.s3_framework import S3FrameworkAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()
ragflow_config = config.get_ragflow_config()
service_config = config.get_service_config()

# PostgreSQL configuration
PG_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "xdan_chat_db"),
    "user": os.getenv("POSTGRES_USER", "xdan_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "xdan_password"),
}

# Global database pool
db_pool: Optional[Pool] = None

# ==================== Database Setup ====================

async def init_database():
    """Initialize PostgreSQL database tables"""
    conn = await asyncpg.connect(**PG_CONFIG)
    
    try:
        # Create tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                description TEXT,
                dataset_ids JSONB DEFAULT '[]'::jsonb,
                llm_config JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        ''')
        
        logger.info("Database tables initialized successfully")
        
    finally:
        await conn.close()

# ==================== Pydantic Models ====================

class ChatCreateRequest(BaseModel):
    name: str = Field(..., description="聊天名称")
    dataset_ids: List[str] = Field(default=[], description="关联的数据集ID列表")
    description: Optional[str] = Field(None, description="聊天描述")
    llm_config: Optional[Dict[str, Any]] = Field(default={
        "model_name": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 2000
    })

class ChatMessageRequest(BaseModel):
    content: str = Field(..., description="消息内容")
    stream: bool = Field(default=False, description="是否流式返回")
    use_s3_rag: bool = Field(default=True, description="是否使用S3框架RAG（false时使用传统LLM）")
    rag_config: Optional[Dict[str, Any]] = Field(default=None, description="S3框架配置参数")

class RetrievalRequest(BaseModel):
    question: str = Field(..., description="检索问题")
    dataset_ids: List[str] = Field(..., description="要检索的数据集ID列表")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.1)

class S3ChatRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    dataset_ids: List[str] = Field(..., description="要检索的数据集ID列表")
    chat_id: Optional[str] = Field(None, description="对话ID（可选，用于保存历史）")
    max_rounds: int = Field(default=3, ge=1, le=5, description="最大搜索轮数")
    top_k: int = Field(default=10, ge=1, le=20, description="每轮检索数量")
    stream: bool = Field(default=False, description="是否流式返回")
    save_history: bool = Field(default=True, description="是否保存对话历史")

class DatasetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    embedding_model: str = "BAAI/bge-m3@SILICONFLOW"
    chunk_method: str = "naive"
    parser_config: Dict[str, Any] = Field(default={
        "chunk_token_num": 512,
        "delimiter": "\\n"
    })

# ==================== Application Setup ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting xDAN Unified API Server (PostgreSQL)...")
    
    # Initialize database
    await init_database()
    
    # Create connection pool
    global db_pool
    db_pool = await asyncpg.create_pool(**PG_CONFIG, min_size=10, max_size=20)
    logger.info("PostgreSQL connection pool created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down xDAN Unified API Server...")
    if db_pool:
        await db_pool.close()
        logger.info("PostgreSQL connection pool closed")

app = FastAPI(
    title="xDAN Rag Copilot API Service (PostgreSQL)",
    version="1.0.0",
    description="统一的API服务，整合LiteLLM对话和RAGFlow知识库管理，使用PostgreSQL存储",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Dependencies ====================

def get_litellm_client():
    """Get LiteLLM SDK client"""
    return LiteLLMSDKClient()

def get_ragflow_client():
    """Get RAGFlow client"""
    return RAGFlowClient(
        api_url=ragflow_config.get('api_url'),
        api_key=ragflow_config.get('api_key')
    )

def get_s3_agent():
    """Get S3 Framework Agent"""
    ragflow_client = get_ragflow_client()
    litellm_client = get_litellm_client()
    return S3FrameworkAgent(ragflow_client, litellm_client)

async def get_db() -> asyncpg.Connection:
    """Get database connection from pool"""
    async with db_pool.acquire() as connection:
        yield connection

# ==================== Helper Functions ====================

async def get_chat_info(chat_id: str, conn: asyncpg.Connection) -> Optional[Dict]:
    """Get chat information from database"""
    row = await conn.fetchrow(
        "SELECT * FROM chats WHERE id = $1", 
        uuid.UUID(chat_id)
    )
    
    if row:
        # Parse JSON fields from database
        dataset_ids = row["dataset_ids"] if isinstance(row["dataset_ids"], list) else json.loads(row["dataset_ids"])
        llm_config = row["llm_config"] if isinstance(row["llm_config"], dict) else json.loads(row["llm_config"])
        
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "dataset_ids": dataset_ids,
            "llm_config": llm_config,
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat()
        }
    return None

async def save_message(chat_id: str, role: str, content: str, conn: asyncpg.Connection, metadata: Dict = None) -> str:
    """Save message to database"""
    # Convert metadata dict to JSON string for PostgreSQL JSONB
    metadata_json = json.dumps(metadata or {})
    message_id = await conn.fetchval(
        """INSERT INTO messages (chat_id, role, content, metadata) 
           VALUES ($1, $2, $3, $4::jsonb) RETURNING id""",
        uuid.UUID(chat_id), role, content, metadata_json
    )
    return str(message_id)

def format_sse_message(data: Any) -> str:
    """Format message for SSE"""
    if isinstance(data, dict):
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    else:
        return f"data: {data}\n\n"

async def execute_s3_rag_workflow(question: str, dataset_ids: List[str], s3_agent: S3FrameworkAgent, stream: bool = False) -> tuple[str, dict]:
    """Execute complete S3 RAG workflow and return answer with detailed retrieval info"""
    if not dataset_ids:
        return question, {"workflow_type": "direct", "reason": "no_datasets"}
    
    try:
        logger.info(f"Starting S3 workflow for question: {question[:50]}...")
        
        # Execute S3 workflow
        if stream:
            # For streaming, we need to handle it differently
            workflow_result = {}
            full_answer = ""
            async for chunk in s3_agent.execute_s3_workflow(
                question=question,
                dataset_ids=dataset_ids,
                max_rounds=3,
                top_k=10,
                stream=True
            ):
                if isinstance(chunk, str):
                    full_answer += chunk
                    yield chunk
                else:
                    workflow_result = chunk
            
            # Get the final workflow result for reference data
            if not workflow_result:
                workflow_result = await s3_agent.execute_s3_workflow(
                    question=question,
                    dataset_ids=dataset_ids,
                    max_rounds=3,
                    top_k=10,
                    stream=False
                )
        else:
            workflow_result = await s3_agent.execute_s3_workflow(
                question=question,
                dataset_ids=dataset_ids,
                max_rounds=3,
                top_k=10,
                stream=False
            )
            full_answer = workflow_result.get("final_answer", "")
        
        # Build comprehensive reference data
        reference_data = {
            "workflow_type": "s3_framework",
            "workflow_completed": workflow_result.get("workflow_completed", False),
            "total_rounds": len(workflow_result.get("rounds", [])),
            "search_rounds": [],
            "selected_documents": workflow_result.get("selected_documents", []),
            "execution_time": {
                "start_time": workflow_result.get("start_time"),
                "end_time": workflow_result.get("end_time")
            }
        }
        
        # Extract detailed search round information
        for round_info in workflow_result.get("rounds", []):
            round_data = {
                "round": round_info.get("round"),
                "search_query": round_info.get("search_query"),
                "search_results_count": round_info.get("search_results_count"),
                "agent_decision": {
                    "search_complete": round_info.get("decision", {}).get("search_complete"),
                    "important_docs": round_info.get("decision", {}).get("important_docs", []),
                    "thinking": round_info.get("decision", {}).get("thinking"),
                    "next_query": round_info.get("decision", {}).get("next_query")
                },
                "timestamp": round_info.get("timestamp")
            }
            reference_data["search_rounds"].append(round_data)
        
        # Add document details with IDs and content
        detailed_docs = []
        for i, doc in enumerate(workflow_result.get("selected_documents", [])):
            detailed_docs.append({
                "id": doc.get("id", f"doc_{i+1}"),
                "content": doc.get("content", doc.get("content_ltks", "")),
                "document_name": doc.get("document_name", "Unknown"),
                "similarity": doc.get("similarity", 0),
                "dataset_id": doc.get("dataset_id", ""),
                "chunk_index": i + 1
            })
        
        reference_data["selected_documents"] = detailed_docs
        reference_data["total_selected_docs"] = len(detailed_docs)
        
        logger.info(f"S3 workflow completed: {reference_data['total_rounds']} rounds, {reference_data['total_selected_docs']} docs selected")
        
        return full_answer, reference_data
        
    except Exception as e:
        logger.error(f"S3 workflow failed: {e}")
        # Fallback to simple RAG
        return question, {
            "workflow_type": "fallback",
            "error": str(e),
            "fallback_reason": "s3_workflow_failed"
        }

# ==================== Chat Management Endpoints ====================

@app.post("/api/v1/chats")
async def create_chat(
    request: ChatCreateRequest,
    conn: asyncpg.Connection = Depends(get_db)
):
    """创建新的对话"""
    chat_id = await conn.fetchval(
        """INSERT INTO chats (name, description, dataset_ids, llm_config) 
           VALUES ($1, $2, $3::jsonb, $4::jsonb) RETURNING id""",
        request.name,
        request.description,
        json.dumps(request.dataset_ids),
        json.dumps(request.llm_config)
    )
    
    # Fetch the created chat
    chat = await get_chat_info(str(chat_id), conn)
    
    return {
        "code": 0,
        "data": chat
    }

@app.get("/api/v1/chats")
async def list_chats(
    page: int = 1,
    page_size: int = 20,
    conn: asyncpg.Connection = Depends(get_db)
):
    """获取对话列表"""
    offset = (page - 1) * page_size
    
    # Get total count
    total = await conn.fetchval("SELECT COUNT(*) FROM chats")
    
    # Get chats
    rows = await conn.fetch(
        """SELECT * FROM chats 
           ORDER BY created_at DESC 
           LIMIT $1 OFFSET $2""",
        page_size, offset
    )
    
    chats = []
    for row in rows:
        chats.append({
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "dataset_ids": row["dataset_ids"],
            "llm_config": row["llm_config"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat()
        })
    
    return {
        "code": 0,
        "data": chats,
        "meta": {
            "page": page,
            "size": page_size,
            "total": total,
            "has_next": offset + page_size < total,
            "has_prev": page > 1
        }
    }

@app.post("/api/v1/chats/{chat_id}/completions")
async def chat_completion(
    chat_id: str,
    request: ChatMessageRequest,
    conn: asyncpg.Connection = Depends(get_db),
    litellm_client: LiteLLMSDKClient = Depends(get_litellm_client),
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """发送消息并获取AI回复（支持SSE流式响应）"""
    # Get chat info
    chat_info = await get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Save user message
    await save_message(chat_id, "user", request.content, conn)
    
    # Get chat history
    rows = await conn.fetch(
        """SELECT role, content FROM messages 
           WHERE chat_id = $1 
           ORDER BY created_at 
           LIMIT 10""",
        uuid.UUID(chat_id)
    )
    
    # Build messages
    messages = []
    for row in rows[:-1]:  # Exclude the last message we just saved
        messages.append({
            "role": row["role"],
            "content": row["content"]
        })
    
    # 如果有数据集且启用S3-RAG，使用S3框架；否则使用传统LLM
    if chat_info["dataset_ids"] and request.use_s3_rag:
        # 使用S3框架处理RAG对话
        logger.info(f"Using S3 framework for chat {chat_id} with datasets: {chat_info['dataset_ids']}")
        
        # 从rag_config获取配置或使用默认值
        rag_config = request.rag_config or {}
        max_rounds = rag_config.get("max_rounds", 3)
        top_k = rag_config.get("top_k", 10)
        
        # 直接使用S3框架的完整逻辑
        s3_agent = get_s3_agent()
        
        if request.stream:
            # S3流式响应
            async def generate_s3_sse():
                try:
                    # 发送初始消息
                    yield format_sse_message({
                        "code": 0,
                        "message": "Starting S3 RAG workflow...",
                        "data": {
                            "answer": "",
                            "reference": {"workflow_type": "s3_framework", "status": "starting"},
                            "session_id": chat_id
                        }
                    })
                    
                    # 执行S3工作流并获取流式结果
                    workflow_result = None
                    answer_content = ""
                    
                    async for chunk in s3_agent.execute_s3_workflow(
                        question=request.content,
                        dataset_ids=chat_info["dataset_ids"],
                        max_rounds=max_rounds,
                        top_k=top_k,
                        stream=True
                    ):
                        if isinstance(chunk, str):
                            # 答案内容流
                            answer_content += chunk
                            yield format_sse_message({
                                "code": 0,
                                "message": "",
                                "data": {
                                    "answer": answer_content,
                                    "reference": {"workflow_type": "s3_framework", "status": "generating"},
                                    "session_id": chat_id
                                }
                            })
                        elif isinstance(chunk, dict):
                            workflow_result = chunk
                    
                    # 获取完整的工作流结果（如果流式没有返回）
                    if not workflow_result:
                        try:
                            async for result in s3_agent.execute_s3_workflow(
                                question=request.content,
                                dataset_ids=chat_info["dataset_ids"],
                                max_rounds=max_rounds,
                                top_k=top_k,
                                stream=False
                            ):
                                workflow_result = result
                                break
                        except Exception as e:
                            logger.error(f"S3 workflow failed: {e}")
                            workflow_result = {}
                    
                    final_answer = workflow_result.get("final_answer", answer_content)
                    
                    # 如果S3工作流失败，创建基本的参考数据
                    if not workflow_result or not workflow_result.get("final_answer"):
                        logger.warning("S3 workflow_result is empty, creating fallback reference data")
                        reference_data = {
                            "workflow_type": "s3_framework",
                            "workflow_completed": False,
                            "total_rounds": max_rounds,
                            "search_rounds": [
                                {
                                    "round": 1,
                                    "search_query": request.content,
                                    "agent_decision": {"thinking": "执行S3框架搜索", "search_complete": True}
                                }
                            ],
                            "selected_documents": [],
                            "total_selected_docs": 0,
                            "status": "completed_with_fallback",
                            "config": {
                                "max_rounds": max_rounds,
                                "top_k": top_k,
                                "dataset_ids": chat_info["dataset_ids"]
                            }
                        }
                    else:
                        reference_data = build_s3_reference_data(workflow_result)
                    
                    # 发送最终结果
                    yield format_sse_message({
                        "code": 0,
                        "message": "S3 workflow completed",
                        "data": {
                            "answer": final_answer,
                            "reference": reference_data,
                            "session_id": chat_id
                        }
                    })
                    
                    # 保存AI回复
                    await save_message(chat_id, "assistant", final_answer, conn, metadata=reference_data)
                    
                    # 结束消息
                    yield format_sse_message({
                        "code": 0,
                        "message": "",
                        "data": True
                    })
                    
                except Exception as e:
                    logger.error(f"S3 streaming error in chat: {e}")
                    yield format_sse_message({
                        "code": 500,
                        "message": str(e),
                        "data": None
                    })
            
            return StreamingResponse(
                generate_s3_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        else:
            # S3非流式响应 - 使用真正的S3框架
            try:
                workflow_result = None
                async for result in s3_agent.execute_s3_workflow(
                    question=request.content,
                    dataset_ids=chat_info["dataset_ids"],
                    max_rounds=max_rounds,
                    top_k=top_k,
                    stream=False
                ):
                    workflow_result = result
                    break
                
                final_answer = workflow_result.get("final_answer", "")
                
                # 如果S3工作流失败或返回空结果，创建基本的参考数据
                if not workflow_result or not final_answer:
                    logger.warning("S3 Non-streaming workflow_result is empty, creating fallback reference data")
                    reference_data = {
                        "workflow_type": "s3_framework",
                        "workflow_completed": False,
                        "total_rounds": max_rounds,
                        "search_rounds": [
                            {
                                "round": 1,
                                "search_query": request.content,
                                "agent_decision": {"thinking": "执行S3框架搜索", "search_complete": True}
                            }
                        ],
                        "selected_documents": [],
                        "total_selected_docs": 0,
                        "status": "completed_with_fallback",
                        "config": {
                            "max_rounds": max_rounds,
                            "top_k": top_k,
                            "dataset_ids": chat_info["dataset_ids"]
                        }
                    }
                    # 如果没有答案，至少返回一个基本回答
                    if not final_answer:
                        final_answer = "抱歉，S3框架处理出现问题，无法生成完整回答。"
                else:
                    reference_data = build_s3_reference_data(workflow_result)
                
                # 保存AI回复
                await save_message(chat_id, "assistant", final_answer, conn, metadata=reference_data)
                
                return {
                    "code": 0,
                    "data": {
                        "answer": final_answer,
                        "reference": reference_data,
                        "session_id": chat_id
                    }
                }
                
            except Exception as e:
                logger.error(f"S3 workflow error in chat: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    else:
        # 无数据集或未启用S3-RAG时使用传统LLM对话
        if not chat_info["dataset_ids"]:
            logger.info(f"Using direct LLM for chat {chat_id} (no datasets)")
            reason = "no_datasets"
        else:
            logger.info(f"Using direct LLM for chat {chat_id} (S3-RAG disabled)")
            reason = "s3_rag_disabled"
        
        # Get chat history for context
        messages = []
        for row in rows[:-1]:  # Exclude the last message we just saved
            messages.append({
                "role": row["role"],
                "content": row["content"]
            })
        messages.append({"role": "user", "content": request.content})
        
        reference_data = {"workflow_type": "direct", "reason": reason}
        llm_config = chat_info.get("llm_config", {})
        
        # 传统LLM对话流程
        litellm_client = get_litellm_client()
        
        if request.stream:
            # Streaming response
            async def generate_sse():
            try:
                # Send initial message
                yield format_sse_message({
                    "code": 0,
                    "message": "",
                    "data": {
                        "answer": "",
                        "reference": reference_data,
                        "session_id": chat_id
                    }
                })
                
                # Get streaming response from LiteLLM
                full_response = ""
                async for chunk in await litellm_client.chat_completion(
                    messages=messages,
                    model=llm_config.get("model_name", "deepseek-chat"),
                    temperature=llm_config.get("temperature", 0.7),
                    max_tokens=llm_config.get("max_tokens", 2000),
                    stream=True,
                    use_case="generation"
                ):
                    if chunk:
                        # Handle LiteLLM streaming response object
                        content = ""
                        if hasattr(chunk, 'choices') and chunk.choices:
                            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                                content = chunk.choices[0].delta.content or ""
                        elif isinstance(chunk, dict):
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        
                        if content:
                            full_response += content
                            yield format_sse_message({
                                "code": 0,
                                "message": "",
                                "data": {
                                    "answer": full_response,
                                    "reference": reference_data,
                                    "session_id": chat_id
                                }
                            })
                
                # Save assistant response
                await save_message(chat_id, "assistant", full_response, conn)
                
                # Send completion message
                yield format_sse_message({
                    "code": 0,
                    "message": "",
                    "data": True
                })
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield format_sse_message({
                    "code": 500,
                    "message": str(e),
                    "data": None
                })
        
            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response for direct LLM
            try:
            response = await litellm_client.chat_completion(
                messages=messages,
                model=llm_config.get("model_name", "deepseek-chat"),
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 2000),
                stream=False,
                use_case="generation"
            )
            
            # Debug logging
            logger.info(f"LiteLLM response type: {type(response)}")
            logger.info(f"LiteLLM response attributes: {dir(response) if hasattr(response, '__dict__') else 'No attributes'}")
            
            # Handle LiteLLM response object
            if hasattr(response, 'choices') and response.choices:
                answer = response.choices[0].message.content
            elif isinstance(response, dict):
                answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                # Fallback - try to extract text from string response
                logger.warning(f"Unexpected response type: {type(response)}, content: {str(response)[:200]}")
                answer = str(response)
            
            # Save assistant response
            await save_message(chat_id, "assistant", answer, conn)
            
            return {
                "code": 0,
                "data": {
                    "answer": answer,
                    "reference": reference_data,
                    "session_id": chat_id
                }
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Chat completion error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    page: int = 1,
    page_size: int = 20,
    conn: asyncpg.Connection = Depends(get_db)
):
    """获取对话历史"""
    # Check if chat exists
    chat_info = await get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    offset = (page - 1) * page_size
    
    # Get total count
    total = await conn.fetchval(
        "SELECT COUNT(*) FROM messages WHERE chat_id = $1",
        uuid.UUID(chat_id)
    )
    
    # Get messages
    rows = await conn.fetch(
        """SELECT * FROM messages 
           WHERE chat_id = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        uuid.UUID(chat_id), page_size, offset
    )
    
    messages = []
    for row in rows:
        messages.append({
            "id": str(row["id"]),
            "role": row["role"],
            "content": row["content"],
            "metadata": row["metadata"],
            "created_at": row["created_at"].isoformat()
        })
    
    # Reverse to get chronological order
    messages.reverse()
    
    return {
        "code": 0,
        "data": messages,
        "meta": {
            "page": page,
            "size": page_size,
            "total": total,
            "has_next": offset + page_size < total,
            "has_prev": page > 1
        }
    }

@app.delete("/api/v1/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """删除对话"""
    # Check if chat exists
    chat_info = await get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete chat (messages will be cascade deleted)
    await conn.execute("DELETE FROM chats WHERE id = $1", uuid.UUID(chat_id))
    
    return {
        "code": 0,
        "message": "Chat deleted successfully"
    }

# ==================== RAGFlow Proxy Endpoints ====================

@app.get("/api/v1/datasets")
async def list_datasets(
    page: int = 1,
    page_size: int = 12,
    name: Optional[str] = None,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """获取知识库列表 - 代理到RAGFlow"""
    try:
        result = ragflow_client.list_datasets(
            page=page,
            page_size=page_size,
            name=name
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets")
async def create_dataset(
    request: DatasetCreateRequest,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """创建知识库 - 代理到RAGFlow"""
    try:
        result = ragflow_client.create_dataset(
            name=request.name,
            description=request.description,
            embedding_model=request.embedding_model,
            chunk_method=request.chunk_method,
            parser_config=request.parser_config
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/datasets/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    request: Dict[str, Any],
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """更新知识库 - 代理到RAGFlow"""
    try:
        result = ragflow_client.update_dataset(dataset_id, **request)
        return result
    except Exception as e:
        logger.error(f"Failed to update dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """删除知识库 - 代理到RAGFlow"""
    try:
        result = ragflow_client.delete_datasets([dataset_id])
        return result
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets/{dataset_id}/documents")
async def upload_documents(
    dataset_id: str,
    file: UploadFile = File(...),
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """上传文档到知识库 - 代理到RAGFlow"""
    try:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Upload to RAGFlow
            result = ragflow_client.upload_documents(dataset_id, [tmp_file_path])
            return result
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents")
async def list_documents(
    dataset_id: str,
    page: int = 1,
    page_size: int = 20,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """获取文档列表 - 代理到RAGFlow"""
    try:
        result = ragflow_client.list_documents(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_id}/documents/{document_id}")
async def delete_document(
    dataset_id: str,
    document_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """删除文档 - 代理到RAGFlow"""
    try:
        result = ragflow_client.delete_documents(dataset_id, [document_id])
        return result
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/retrieval")
async def retrieval(
    request: RetrievalRequest,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """知识库检索 - 代理到RAGFlow"""
    try:
        result = ragflow_client.retrieve_chunks(
            question=request.question,
            dataset_ids=request.dataset_ids,
            page=request.page,
            page_size=request.page_size,
            similarity_threshold=request.similarity_threshold
        )
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/stream")
async def search_stream(
    request: Dict[str, str]
):
    """
    搜索流式接口 - 展示search model执行过程
    前端期望的接口，显示智能搜索的完整决策流程
    """
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # 使用默认数据集
        dataset_ids = ["7e8d9e924cde11f0afc90242ac140006"]
        
        async def generate_search_sse():
            try:
                # 1. 搜索开始事件
                yield format_sse_message({
                    "event_type": "search_start",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "question": question,
                        "dataset_ids": dataset_ids
                    }
                })
                
                # 2. 执行S3工作流
                s3_agent = get_s3_agent()
                workflow_result = await s3_agent.execute_s3_workflow(
                    question=question,
                    dataset_ids=dataset_ids,
                    max_rounds=3,
                    top_k=10,
                    stream=False
                )
                
                # 3. 发送搜索轮次事件
                for round_info in workflow_result.get("rounds", []):
                    yield format_sse_message({
                        "event_type": "search_round",
                        "timestamp": round_info.get("timestamp", datetime.now().isoformat()),
                        "data": {
                            "round": round_info.get("round"),
                            "search_query": round_info.get("search_query"),
                            "search_results_count": round_info.get("search_results_count"),
                            "agent_decision": round_info.get("decision", {})
                        }
                    })
                
                # 4. 发送搜索结果汇总
                selected_docs = workflow_result.get("selected_documents", [])
                if selected_docs:
                    yield format_sse_message({
                        "event_type": "sources_gathered",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "sources_gathered": [{
                                "label": doc.get("document_name", "Unknown"),
                                "content": doc.get("content", "")[:200] + "...",
                                "similarity": doc.get("similarity", 0)
                            } for doc in selected_docs]
                        }
                    })
                
                # 5. 发送最终答案事件
                yield format_sse_message({
                    "event_type": "answer_generated",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "answer": workflow_result.get("final_answer", ""),
                        "workflow_completed": workflow_result.get("workflow_completed", False)
                    }
                })
                
                # 6. 完成事件
                yield format_sse_message({
                    "event_type": "complete",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                })
                
                # 7. 结束标记
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Search stream error: {e}")
                yield format_sse_message({
                    "event_type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"error": str(e)}
                })
        
        return StreamingResponse(
            generate_search_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Search stream initialization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/s3-chat")
async def s3_chat(
    request: S3ChatRequest,
    conn: asyncpg.Connection = Depends(get_db)
):
    """
    S3框架对话接口 - 完整的Search-Select-Synthesize流程
    返回详细的搜索过程和召回内容
    """
    try:
        s3_agent = get_s3_agent()
        
        # 保存用户问题
        if request.save_history and request.chat_id:
            await save_message(request.chat_id, "user", request.question, conn)
        
        if request.stream:
            # 流式响应
            async def generate_s3_sse():
                try:
                    workflow_result = None
                    answer_content = ""
                    
                    # 发送初始消息
                    yield format_sse_message({
                        "code": 0,
                        "message": "Starting S3 workflow...",
                        "data": {
                            "type": "workflow_start",
                            "question": request.question,
                            "dataset_ids": request.dataset_ids,
                            "max_rounds": request.max_rounds
                        }
                    })
                    
                    # 执行S3工作流
                    async for chunk in s3_agent.execute_s3_workflow(
                        question=request.question,
                        dataset_ids=request.dataset_ids,
                        max_rounds=request.max_rounds,
                        top_k=request.top_k,
                        stream=True
                    ):
                        if isinstance(chunk, str):
                            # 答案内容流
                            answer_content += chunk
                            yield format_sse_message({
                                "code": 0,
                                "message": "",
                                "data": {
                                    "type": "answer_chunk",
                                    "content": chunk,
                                    "full_answer": answer_content
                                }
                            })
                        elif isinstance(chunk, dict):
                            # 工作流结果
                            workflow_result = chunk
                    
                    # 获取完整的工作流结果（非流式）
                    if not workflow_result:
                        workflow_result = await s3_agent.execute_s3_workflow(
                            question=request.question,
                            dataset_ids=request.dataset_ids,
                            max_rounds=request.max_rounds,
                            top_k=request.top_k,
                            stream=False
                        )
                    
                    # 构建详细的参考信息
                    reference_data = build_s3_reference_data(workflow_result)
                    
                    # 发送最终结果
                    yield format_sse_message({
                        "code": 0,
                        "message": "S3 workflow completed",
                        "data": {
                            "type": "final_result",
                            "answer": workflow_result.get("final_answer", answer_content),
                            "reference": reference_data,
                            "session_id": request.chat_id or "s3_session"
                        }
                    })
                    
                    # 保存AI回复
                    if request.save_history and request.chat_id:
                        await save_message(
                            request.chat_id, 
                            "assistant", 
                            workflow_result.get("final_answer", answer_content), 
                            conn,
                            metadata=reference_data
                        )
                    
                    # 结束消息
                    yield format_sse_message({
                        "code": 0,
                        "message": "",
                        "data": True
                    })
                    
                except Exception as e:
                    logger.error(f"S3 streaming error: {e}")
                    yield format_sse_message({
                        "code": 500,
                        "message": str(e),
                        "data": None
                    })
            
            return StreamingResponse(
                generate_s3_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        else:
            # 非流式响应
            workflow_result = await s3_agent.execute_s3_workflow(
                question=request.question,
                dataset_ids=request.dataset_ids,
                max_rounds=request.max_rounds,
                top_k=request.top_k,
                stream=False
            )
            
            # 构建详细的参考信息
            reference_data = build_s3_reference_data(workflow_result)
            
            # 保存AI回复
            if request.save_history and request.chat_id:
                await save_message(
                    request.chat_id, 
                    "assistant", 
                    workflow_result.get("final_answer", ""), 
                    conn,
                    metadata=reference_data
                )
            
            return {
                "code": 0,
                "data": {
                    "answer": workflow_result.get("final_answer", ""),
                    "reference": reference_data,
                    "session_id": request.chat_id or "s3_session",
                    "workflow_completed": workflow_result.get("workflow_completed", False)
                }
            }
            
    except Exception as e:
        logger.error(f"S3 chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def build_s3_reference_data(workflow_result: Dict[str, Any]) -> Dict[str, Any]:
    """构建详细的S3参考数据"""
    
    # 如果workflow_result为空或None，返回基本的reference结构
    if not workflow_result:
        logger.warning("workflow_result is empty, returning basic reference data")
        return {
            "workflow_type": "s3_framework",
            "workflow_completed": False,
            "total_rounds": 0,
            "search_rounds": [],
            "selected_documents": [],
            "execution_time": {
                "start_time": None,
                "end_time": None
            },
            "error": "workflow_result_empty"
        }
    
    reference_data = {
        "workflow_type": "s3_framework",
        "workflow_completed": workflow_result.get("workflow_completed", False),
        "total_rounds": len(workflow_result.get("rounds", [])),
        "search_rounds": [],
        "selected_documents": [],
        "execution_time": {
            "start_time": workflow_result.get("start_time"),
            "end_time": workflow_result.get("end_time")
        }
    }
    
    # 提取详细的搜索轮次信息
    for round_info in workflow_result.get("rounds", []):
        round_data = {
            "round": round_info.get("round"),
            "search_query": round_info.get("search_query"),
            "search_results_count": round_info.get("search_results_count"),
            "agent_decision": {
                "search_complete": round_info.get("decision", {}).get("search_complete"),
                "important_docs": round_info.get("decision", {}).get("important_docs", []),
                "thinking": round_info.get("decision", {}).get("thinking"),
                "next_query": round_info.get("decision", {}).get("next_query")
            },
            "timestamp": round_info.get("timestamp")
        }
        reference_data["search_rounds"].append(round_data)
    
    # 添加文档详情（包含ID和内容）
    detailed_docs = []
    for i, doc in enumerate(workflow_result.get("selected_documents", [])):
        detailed_docs.append({
            "id": doc.get("id", f"doc_{i+1}"),
            "content": doc.get("content", doc.get("content_ltks", "")),
            "document_name": doc.get("document_name", "Unknown"),
            "similarity": doc.get("similarity", 0),
            "dataset_id": doc.get("dataset_id", ""),
            "chunk_index": i + 1
        })
    
    reference_data["selected_documents"] = detailed_docs
    reference_data["total_selected_docs"] = len(detailed_docs)
    
    return reference_data

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    # Check database connection
    db_status = "unhealthy"
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "xDAN Rag Copilot API Service",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "xDAN Rag Copilot API Service (PostgreSQL)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    port = service_config.get('api_proxy_port', 8050)
    
    logger.info(f"Starting xDAN Unified API Server (PostgreSQL) on port {port}")
    logger.info(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
    logger.info(f"RAGFlow API: {ragflow_config.get('api_url')}")
    logger.info(f"Documentation available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )