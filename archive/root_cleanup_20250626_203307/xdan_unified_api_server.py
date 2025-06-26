#!/usr/bin/env python3
"""
xDAN Unified API Server
统一的API服务，整合LiteLLM SDK（对话功能）和RAGFlow代理（知识库管理）
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
# import httpx  # Not needed, using requests from ragflow_client
import sqlite3
from sqlite3 import Row

# Import our modules
from src.core.config_loader import get_config
from src.clients.litellm_sdk_client_v2 import LiteLLMSDKClientV2 as LiteLLMSDKClient
from src.clients.ragflow_client import RAGFlowClient
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService

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

# ==================== Database Setup ====================

def init_database():
    """Initialize SQLite database for chat history"""
    conn = sqlite3.connect('chat_history.db')
    conn.row_factory = Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            dataset_ids TEXT,
            llm_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    ''')
    
    conn.commit()
    conn.close()

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

class RetrievalRequest(BaseModel):
    question: str = Field(..., description="检索问题")
    dataset_ids: List[str] = Field(..., description="要检索的数据集ID列表")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.1)

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

# Global S3 service instance
s3_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global s3_service
    
    # Startup
    logger.info("Starting xDAN Unified API Server...")
    init_database()
    
    # Initialize S3 service
    try:
        # 尝试使用SDK初始化RAGFlow客户端
        from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper, SDK_AVAILABLE
        
        if SDK_AVAILABLE:
            logger.info("Using RAGFlow SDK for S3 service")
            ragflow_client = RAGFlowSDKWrapper(
                api_url=ragflow_config.get('api_url'),
                api_key=ragflow_config.get('api_key')
            )
        else:
            logger.info("SDK not available, using HTTP client for S3 service")
            ragflow_client = RAGFlowClient(
                api_url=ragflow_config.get('api_url'),
                api_key=ragflow_config.get('api_key')
            )
        
        # 获取S3框架配置
        model_config = config.get_model_config()
        s3_config = model_config.get('s3_framework', {})
        
        # 创建统一的LiteLLM客户端用于Search和Generator
        # LiteLLM会根据use_case和model自动路由到正确的模型
        search_llm_client = LiteLLMSDKClient()
        generator_llm_client = LiteLLMSDKClient()
        
        # 初始化S3服务
        s3_service = EnhancedS3RAGService(
            ragflow_client=ragflow_client,
            search_llm_client=search_llm_client,
            generator_llm_client=generator_llm_client
        )
        logger.info("S3 RAG service initialized successfully with LiteLLM for all LLM operations")
        
    except Exception as e:
        logger.error(f"Failed to initialize S3 service: {e}")
        s3_service = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down xDAN Unified API Server...")

app = FastAPI(
    title="xDAN Rag Copilot API Service",
    version="1.0.0",
    description="统一的API服务，整合LiteLLM对话和RAGFlow知识库管理",
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

def get_db():
    """Get database connection with thread safety"""
    # SQLite在FastAPI中需要特殊处理，因为默认不支持多线程
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    conn.row_factory = Row
    try:
        yield conn
    finally:
        conn.close()

def get_s3_service():
    """Get S3 RAG service instance"""
    if s3_service is None:
        raise HTTPException(status_code=503, detail="S3 service not available")
    return s3_service

# ==================== Helper Functions ====================

def get_chat_info(chat_id: str, conn: sqlite3.Connection) -> Optional[Dict]:
    """Get chat information from database"""
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT * FROM chats WHERE id = ?", 
        (chat_id,)
    ).fetchone()
    
    if result:
        return {
            "id": result["id"],
            "name": result["name"],
            "description": result["description"],
            "dataset_ids": json.loads(result["dataset_ids"]) if result["dataset_ids"] else [],
            "llm_config": json.loads(result["llm_config"]) if result["llm_config"] else {},
            "created_at": result["created_at"],
            "updated_at": result["updated_at"]
        }
    return None

def save_message(chat_id: str, role: str, content: str, conn: sqlite3.Connection, metadata: Dict = None):
    """Save message to database"""
    message_id = str(uuid.uuid4())
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO messages (id, chat_id, role, content, metadata) 
           VALUES (?, ?, ?, ?, ?)""",
        (message_id, chat_id, role, content, json.dumps(metadata) if metadata else None)
    )
    conn.commit()
    return message_id

def format_sse_message(data: Any) -> str:
    """Format message for SSE"""
    if isinstance(data, dict):
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    else:
        return f"data: {data}\n\n"

async def enhance_with_s3_framework(question: str, dataset_ids: List[str], s3_service: EnhancedS3RAGService) -> Dict[str, Any]:
    """Enhance question with S3 framework (Search-Select-Synthesize)"""
    if not dataset_ids:
        return {"enhanced_question": question, "selected_documents": [], "search_process": []}
    
    try:
        # 使用S3框架进行智能搜索和选择
        s3_result = s3_service.s3_search_process(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=3,  # 最多3轮迭代搜索
            top_k=10,      # 每轮检索10个文档
            similarity_threshold=0.1
        )
        
        # 构建增强的问题上下文
        if s3_result.get('selected_documents'):
            context = "\n\n".join([
                f"参考资料{i+1} (相似度: {doc.get('similarity', 0):.2f}): {doc.get('content', '')}"
                for i, doc in enumerate(s3_result['selected_documents'])
            ])
            
            enhanced_question = f"""基于以下经过智能筛选的参考资料回答问题：

{context}

用户问题：{question}

请提供准确、完整的回答，并在适当的地方引用参考资料编号。"""
            
            return {
                "enhanced_question": enhanced_question,
                "selected_documents": s3_result['selected_documents'],
                "search_process": s3_result['search_process'],
                "search_rounds": s3_result.get('search_rounds', 1)
            }
        else:
            logger.warning(f"S3框架未找到相关文档: {question}")
            return {
                "enhanced_question": question,
                "selected_documents": [],
                "search_process": s3_result.get('search_process', [])
            }
        
    except Exception as e:
        logger.error(f"S3 framework enhancement failed: {e}")
        # 如果S3框架失败，返回原始问题
        return {"enhanced_question": question, "selected_documents": [], "search_process": []}

# ==================== Chat Management Endpoints ====================

@app.post("/api/v1/chats")
async def create_chat(
    request: ChatCreateRequest,
    conn: sqlite3.Connection = Depends(get_db)
):
    """创建新的对话"""
    chat_id = str(uuid.uuid4())
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO chats (id, name, description, dataset_ids, llm_config) 
           VALUES (?, ?, ?, ?, ?)""",
        (
            chat_id,
            request.name,
            request.description,
            json.dumps(request.dataset_ids),
            json.dumps(request.llm_config)
        )
    )
    conn.commit()
    
    return {
        "code": 0,
        "data": {
            "id": chat_id,
            "name": request.name,
            "description": request.description,
            "dataset_ids": request.dataset_ids,
            "llm": request.llm_config,
            "create_date": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/chats")
async def list_chats(
    page: int = 1,
    page_size: int = 20,
    conn: sqlite3.Connection = Depends(get_db)
):
    """获取对话列表"""
    cursor = conn.cursor()
    offset = (page - 1) * page_size
    
    # Get total count
    total = cursor.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
    
    # Get chats
    results = cursor.execute(
        """SELECT * FROM chats 
           ORDER BY created_at DESC 
           LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()
    
    chats = []
    for row in results:
        chats.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "dataset_ids": json.loads(row["dataset_ids"]) if row["dataset_ids"] else [],
            "llm_config": json.loads(row["llm_config"]) if row["llm_config"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
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
    conn: sqlite3.Connection = Depends(get_db),
    litellm_client: LiteLLMSDKClient = Depends(get_litellm_client),
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client)
):
    """发送消息并获取AI回复（支持SSE流式响应）"""
    # Get chat info
    chat_info = get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Save user message
    save_message(chat_id, "user", request.content, conn)
    
    # Get chat history
    cursor = conn.cursor()
    history = cursor.execute(
        """SELECT role, content FROM messages 
           WHERE chat_id = ? 
           ORDER BY created_at 
           LIMIT 10""",
        (chat_id,)
    ).fetchall()
    
    # Build messages
    messages = []
    for msg in history[:-1]:  # Exclude the last message we just saved
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Enhance with S3 framework if datasets are associated
    s3_result = {"enhanced_question": request.content, "selected_documents": [], "search_process": []}
    
    if chat_info["dataset_ids"] and s3_service:
        try:
            s3_result = await enhance_with_s3_framework(
                request.content,
                chat_info["dataset_ids"],
                s3_service
            )
        except Exception as e:
            logger.error(f"S3 framework enhancement failed: {e}")
            # 如果S3增强失败，使用原始问题
            
    enhanced_question = s3_result["enhanced_question"]
    
    messages.append({
        "role": "user",
        "content": enhanced_question
    })
    
    # Get LLM response
    llm_config = chat_info.get("llm_config", {})
    
    if request.stream:
        # Streaming response
        async def generate_sse():
            try:
                # Send initial message with S3 search metadata
                yield format_sse_message({
                    "code": 0,
                    "message": "",
                    "data": {
                        "answer": "",
                        "reference": {
                            "total": len(s3_result.get("selected_documents", [])),
                            "chunks": s3_result.get("selected_documents", []),
                            "search_rounds": s3_result.get("search_rounds", 0),
                            "search_process": s3_result.get("search_process", [])
                        },
                        "session_id": chat_id
                    }
                })
                
                # Get streaming response from LiteLLM
                stream_generator = litellm_client.chat_completion(
                    messages=messages,
                    model=llm_config.get("model_name", "deepseek-chat"),
                    temperature=llm_config.get("temperature", 0.7),
                    max_tokens=llm_config.get("max_tokens", 2000),
                    stream=True,
                    use_case="generation"
                )
                
                full_response = ""
                async for chunk in stream_generator:
                    if chunk:
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            full_response += content
                            yield format_sse_message({
                                "code": 0,
                                "message": "",
                                "data": {
                                    "answer": full_response,
                                    "reference": {
                                        "total": len(s3_result.get("selected_documents", [])),
                                        "chunks": s3_result.get("selected_documents", [])
                                    },
                                    "session_id": chat_id
                                }
                            })
                
                # Save assistant response with metadata
                save_message(chat_id, "assistant", full_response, conn, {
                    "s3_search_rounds": s3_result.get("search_rounds", 0),
                    "s3_documents_found": len(s3_result.get("selected_documents", []))
                })
                
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
        # Non-streaming response
        try:
            response = await litellm_client.chat_completion(
                messages=messages,
                model=llm_config.get("model_name", "deepseek-chat"),
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 2000),
                stream=False,
                use_case="generation"
            )
            
            answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Save assistant response with metadata
            save_message(chat_id, "assistant", answer, conn, {
                "s3_search_rounds": s3_result.get("search_rounds", 0),
                "s3_documents_found": len(s3_result.get("selected_documents", []))
            })
            
            return {
                "code": 0,
                "data": {
                    "answer": answer,
                    "reference": {
                        "total": len(s3_result.get("selected_documents", [])),
                        "chunks": s3_result.get("selected_documents", []),
                        "search_rounds": s3_result.get("search_rounds", 0),
                        "search_process": s3_result.get("search_process", [])
                    },
                    "session_id": chat_id
                }
            }
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    page: int = 1,
    page_size: int = 20,
    conn: sqlite3.Connection = Depends(get_db)
):
    """获取对话历史"""
    # Check if chat exists
    chat_info = get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    cursor = conn.cursor()
    offset = (page - 1) * page_size
    
    # Get total count
    total = cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE chat_id = ?",
        (chat_id,)
    ).fetchone()[0]
    
    # Get messages
    results = cursor.execute(
        """SELECT * FROM messages 
           WHERE chat_id = ? 
           ORDER BY created_at DESC 
           LIMIT ? OFFSET ?""",
        (chat_id, page_size, offset)
    ).fetchall()
    
    messages = []
    for row in results:
        messages.append({
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "created_at": row["created_at"]
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
    conn: sqlite3.Connection = Depends(get_db)
):
    """删除对话"""
    cursor = conn.cursor()
    
    # Check if chat exists
    chat_info = get_chat_info(chat_id, conn)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete messages first
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    
    # Delete chat
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    
    conn.commit()
    
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

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "xDAN Rag Copilot API Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "xDAN Rag Copilot API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    port = service_config.get('api_proxy_port', 8050)
    
    logger.info(f"Starting xDAN Unified API Server on port {port}")
    logger.info(f"RAGFlow API: {ragflow_config.get('api_url')}")
    logger.info(f"Documentation available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )