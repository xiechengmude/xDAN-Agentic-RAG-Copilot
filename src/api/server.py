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

from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form, Header, status
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
# PostgreSQL is handled by database module

# 新的导入
from src.core.database import DatabaseManager, get_database, DatabaseAdapter
from src.core.langfuse_client import LangfuseObservabilityClient, create_s3_tracker

# Import our modules
from src.core.config_loader import get_config
from src.clients.litellm_client import LiteLLMSDKClientV2 as LiteLLMSDKClient
from src.clients.ragflow_client import RAGFlowClient
from src.services.s3_service import S3Service

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

# ==================== Global Instances ====================

# 全局数据库和Langfuse实例
from src.core.database import db_manager
from src.core.langfuse_client import langfuse_client

# 初始化标志
_initialized = False

# ==================== Response Models ====================

class ApiResponse(BaseModel):
    """统一的API响应格式"""
    code: int = Field(0, description="状态码，0表示成功")
    message: str = Field("Success", description="响应消息")
    data: Any = Field(None, description="响应数据")
    meta: Optional[Dict[str, Any]] = Field(None, description="元数据，如分页信息")

class ApiError(BaseModel):
    """错误响应格式"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    data: Any = Field(None, description="错误详情")

# ==================== Authentication ====================

# 默认API密钥
DEFAULT_API_KEY = "xDAN-RAG-Service-Demo-Key"
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API密钥"""
    token = credentials.credentials
    # 检查是否为默认密钥或配置的密钥
    valid_keys = [DEFAULT_API_KEY]
    
    # 从环境变量或配置文件中获取额外的API密钥
    if hasattr(config, 'api_keys') and config.api_keys:
        valid_keys.extend(config.api_keys)
    
    if token not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# ==================== Error Code Mapping ====================

# RAGFlow错误码到HTTP状态码的映射
ERROR_CODE_MAPPING = {
    # 成功
    0: 200,
    
    # 客户端错误 (4xx)
    100: 403,  # 权限错误
    101: 404,  # 资源不存在（无效的UUID）
    102: 404,  # 文档未找到
    103: 400,  # 参数错误
    104: 400,  # 无效的请求格式
    105: 400,  # 缺少必需参数
    106: 400,  # 参数值无效
    107: 409,  # 资源冲突（如重复创建）
    108: 422,  # 无法处理的实体
    109: 429,  # 请求过多
    
    # 服务器错误 (5xx)
    200: 500,  # 服务器内部错误
    201: 502,  # 上游服务错误
    202: 503,  # 服务不可用
    203: 504,  # 网关超时
    
    # 业务逻辑错误 (4xx)
    300: 400,  # 业务逻辑错误
    301: 400,  # 操作不允许
    302: 400,  # 状态不正确
    303: 400,  # 资源已存在
    304: 400,  # 资源正在使用中
    305: 400,  # 超出限制
}

def get_http_status_from_ragflow_code(code: int) -> int:
    """根据RAGFlow错误码获取对应的HTTP状态码"""
    return ERROR_CODE_MAPPING.get(code, 400)  # 默认返回400

# ==================== Response Helpers ====================

def success_response(data: Any = None, message: str = "Success", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    """创建成功响应"""
    return {
        "code": 0,
        "message": message,
        "data": data,
        "meta": meta
    }

def error_response(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }

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

class ChatUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="对话名称")
    description: Optional[str] = Field(None, description="对话描述")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM配置")

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

# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 初始化和清理"""
    global _initialized, s3_service
    
    if not _initialized:
        logger.info("初始化数据库和Langfuse...")
        
        # 初始化数据库
        await db_manager.initialize()
        
        # 初始化Langfuse
        langfuse_client.initialize()
        
        # Initialize S3 service
        try:
            logger.info("[S3_TRACE] Starting S3 service initialization...")
            from src.services.service_factory import get_default_service
            
            # 使用工厂模式创建S3服务
            s3_service = get_default_service()
            logger.info(f"[S3_TRACE] S3 service initialized: {s3_service}")
            logger.info(f"[S3_TRACE] S3 service type: {type(s3_service)}")
            logger.info("S3 service initialized successfully using factory pattern")
            
        except Exception as e:
            logger.error(f"[S3_TRACE] Failed to initialize S3 service: {e}")
            logger.error(f"[S3_TRACE] Exception type: {type(e)}", exc_info=True)
            s3_service = None
        
        _initialized = True
        logger.info("数据库和Langfuse初始化完成")
    
    yield
    
    # 清理
    logger.info("正在关闭服务...")
    await db_manager.close()
    langfuse_client.shutdown()
    logger.info("服务已关闭")

# ==================== FastAPI App ====================

app = FastAPI(
    title="xDAN Unified API Server",
    description="统一的API服务，整合S3框架、RAGFlow和Langfuse可观察性",
    version="2.0.0",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Exception Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.status_code,
            message=exc.detail,
            data=None
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=error_response(
            code=500,
            message="Internal server error",
            data=str(exc) if app.debug else None
        )
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

async def get_db():
    """Get PostgreSQL database adapter"""
    return await get_database()

def get_s3_service():
    """Get S3 RAG service instance"""
    if s3_service is None:
        raise HTTPException(status_code=503, detail="S3 service not available")
    return s3_service

# ==================== Helper Functions ====================

async def get_chat_info(chat_id: str, db: DatabaseAdapter) -> Optional[Dict]:
    """Get chat information from database"""
    chat = await db.get_chat(chat_id)
    if chat:
        return {
            "id": chat["id"],
            "name": chat["name"],
            "description": chat["description"],
            "dataset_ids": chat["dataset_ids"],
            "llm_config": chat["llm_config"],
            "created_at": chat["created_at"],
            "updated_at": chat.get("updated_at", chat["created_at"])
        }
    return None

async def save_message(chat_id: str, role: str, content: str, db: DatabaseAdapter, metadata: Dict = None):
    """Save message to database"""
    message_id = await db.save_message(chat_id, role, content, metadata)
    return message_id

def format_sse_message(data: Any) -> str:
    """Format message for SSE"""
    if isinstance(data, dict):
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    else:
        return f"data: {data}\n\n"

async def enhance_with_s3_framework(question: str, dataset_ids: List[str], s3_service: S3Service) -> Dict[str, Any]:
    """Enhance question with S3 framework (Search-Select-Synthesize)"""
    logger.info(f"[S3_TRACE] enhance_with_s3_framework called")
    logger.info(f"[S3_TRACE] - Question: {question[:100]}...")
    logger.info(f"[S3_TRACE] - Dataset IDs: {dataset_ids}")
    logger.info(f"[S3_TRACE] - S3 service type: {type(s3_service)}")
    
    if not dataset_ids:
        logger.warning(f"[S3_TRACE] No dataset IDs provided, returning empty result")
        return {"enhanced_question": question, "selected_documents": [], "search_process": []}
    
    try:
        # 使用S3服务执行问答
        logger.info(f"[S3_TRACE] Calling s3_service.ask()")
        logger.info(f"[S3_TRACE] S3 ask parameters:")
        logger.info(f"[S3_TRACE] - question: {question}")
        logger.info(f"[S3_TRACE] - dataset_ids: {dataset_ids}")
        logger.info(f"[S3_TRACE] - max_rounds: 3")
        logger.info(f"[S3_TRACE] - stream: False")
        
        s3_result = None
        async for result in s3_service.ask(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            logger.info(f"[S3_TRACE] Received result from s3_service.ask")
            logger.info(f"[S3_TRACE] Result keys: {list(result.keys()) if result else 'None'}")
            s3_result = result
            break  # 非流式模式，只取第一个结果
        
        if s3_result and s3_result.get('workflow_completed'):
            # S3工作流已完成，提取搜索结果
            logger.info(f"[S3_TRACE] S3 workflow completed successfully")
            logger.info(f"[S3_TRACE] - Result keys: {list(s3_result.keys())}")
            
            selected_docs = s3_result.get('selected_documents', [])
            rounds = s3_result.get('rounds', [])
            search_rounds = len(rounds)
            logger.info(f"[S3_TRACE] - Selected documents: {len(selected_docs)}")
            logger.info(f"[S3_TRACE] - Search rounds: {search_rounds}")
            
            # 构建搜索过程信息
            search_process = []
            for i, round_info in enumerate(rounds, 1):
                query = round_info.get('search_query', 'N/A')
                count = round_info.get('search_results_count', 0)
                search_process.append(f"轮次{i}: 查询'{query}' -> 找到{count}个文档")
            
            logger.info(f"[S3_TRACE] - Search process steps: {len(search_process)}")
            
            if selected_docs:
                context = "\n\n".join([
                    f"参考资料{i+1} (相似度: {doc.get('similarity', 0):.2f}): {doc.get('content', '')}"
                    for i, doc in enumerate(selected_docs)
                ])
                
                enhanced_question = f"""基于以下经过智能筛选的参考资料回答问题：

{context}

用户问题：{question}

请提供准确、完整的回答，并在适当的地方引用参考资料编号。"""
                
                return {
                    "enhanced_question": enhanced_question,
                    "selected_documents": selected_docs,
                    "search_process": search_process,
                    "search_rounds": search_rounds
                }
        
        logger.warning(f"[S3_TRACE] No workflow info in S3 result")
        logger.warning(f"[S3_TRACE] S3 result: {s3_result}")
        logger.warning(f"S3框架未找到相关文档: {question}")
        return {
            "enhanced_question": question,
            "selected_documents": [],
            "search_process": []
        }
        
    except Exception as e:
        logger.error(f"[S3_TRACE] Exception in enhance_with_s3_framework: {e}")
        logger.error(f"[S3_TRACE] Exception type: {type(e)}")
        logger.error(f"[S3_TRACE] Full traceback:", exc_info=True)
        logger.error(f"S3 framework enhancement failed: {e}")
        # 如果S3框架失败，返回原始问题
        return {"enhanced_question": question, "selected_documents": [], "search_process": []}

# ==================== Chat Management Endpoints ====================

@app.post("/api/v1/chats", response_model=ApiResponse)
async def create_chat(
    request: ChatCreateRequest,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """创建新的对话"""
    try:
        chat_data = {
            "id": str(uuid.uuid4()),
            "name": request.name,
            "description": request.description,
            "dataset_ids": request.dataset_ids,
            "llm_config": request.llm_config or {}
        }
        
        chat_id = await db.create_chat(chat_data)
        
        # 创建Langfuse会话
        if langfuse_client.enabled:
            langfuse_client.create_session(chat_id)
        
        return success_response(data={
            "id": chat_id,
            "name": request.name,
            "description": request.description,
            "dataset_ids": request.dataset_ids,
            "llm": request.llm_config,
            "create_date": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat")

@app.get("/api/v1/chats", response_model=ApiResponse)
async def list_chats(
    page: int = 1,
    page_size: int = 20,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """获取对话列表"""
    try:
        result = await db.list_chats(page=page, page_size=page_size)
        
        # 转换格式以匹配API响应
        chats = []
        for chat in result["chats"]:
            chats.append({
                "id": chat["id"],
                "name": chat["name"],
                "description": chat["description"],
                "dataset_ids": chat["dataset_ids"],
                "llm": chat["llm_config"],
                "create_date": chat["created_at"]
            })
        
        return success_response(data={
            "chats": chats,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        })
    except Exception as e:
        logger.error(f"Failed to list chats: {e}")
        raise HTTPException(status_code=500, detail="Failed to list chats")

@app.get("/api/v1/chats/{chat_id}", response_model=ApiResponse)
async def get_chat(
    chat_id: str,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """获取单个对话详情"""
    try:
        chat_info = await get_chat_info(chat_id, db)
        if not chat_info:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return success_response(data={
            "id": chat_info["id"],
            "name": chat_info["name"],
            "description": chat_info["description"],
            "dataset_ids": chat_info["dataset_ids"],
            "llm": chat_info["llm_config"],
            "create_date": chat_info["created_at"],
            "update_date": chat_info["updated_at"]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat")

@app.put("/api/v1/chats/{chat_id}", response_model=ApiResponse)
async def update_chat(
    chat_id: str,
    request: ChatUpdateRequest,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """更新对话信息"""
    try:
        # 检查对话是否存在
        chat_info = await get_chat_info(chat_id, db)
        if not chat_info:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        # 准备更新数据
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.llm_config is not None:
            update_data["llm_config"] = request.llm_config
            
        # 执行更新
        success = await db.update_chat(chat_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update chat")
        
        # 返回更新后的对话信息
        updated_chat = await get_chat_info(chat_id, db)
        return success_response(data={
            "id": updated_chat["id"],
            "name": updated_chat["name"],
            "description": updated_chat["description"],
            "dataset_ids": updated_chat["dataset_ids"],
            "llm": updated_chat["llm_config"],
            "update_date": updated_chat["updated_at"]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to update chat")

@app.post("/api/v1/chats/{chat_id}/completions", response_model=ApiResponse)
async def chat_completion(
    chat_id: str,
    request: ChatMessageRequest,
    db: DatabaseAdapter = Depends(get_database),
    litellm_client: LiteLLMSDKClient = Depends(get_litellm_client),
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """发送消息并获取AI回复（支持SSE流式响应）"""
    logger.info(f"[S3_TRACE] Chat completion started for chat_id: {chat_id}")
    logger.info(f"[S3_TRACE] Request content: {request.content[:100]}...")
    
    # Get chat info
    chat_info = await get_chat_info(chat_id, db)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    logger.info(f"[S3_TRACE] Chat info retrieved: dataset_ids={chat_info.get('dataset_ids')}")
    
    # Save user message
    await save_message(chat_id, "user", request.content, db)
    
    # Get chat history
    messages_result = await db.get_messages(chat_id, page=1, page_size=10)
    
    # Build messages
    messages = []
    for msg in messages_result["messages"]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Enhance with S3 framework if datasets are associated
    s3_result = {"enhanced_question": request.content, "selected_documents": [], "search_process": []}
    
    logger.info(f"[S3_TRACE] Checking S3 conditions:")
    logger.info(f"[S3_TRACE] - Has dataset_ids: {bool(chat_info['dataset_ids'])}")
    logger.info(f"[S3_TRACE] - Dataset IDs: {chat_info['dataset_ids']}")
    logger.info(f"[S3_TRACE] - S3 service exists: {s3_service is not None}")
    logger.info(f"[S3_TRACE] - S3 service instance: {s3_service}")
    
    if chat_info["dataset_ids"] and s3_service:
        logger.info(f"[S3_TRACE] S3 enhancement conditions met, calling enhance_with_s3_framework")
        try:
            s3_result = await enhance_with_s3_framework(
                request.content,
                chat_info["dataset_ids"],
                s3_service
            )
            logger.info(f"[S3_TRACE] S3 enhancement completed")
            logger.info(f"[S3_TRACE] - Documents found: {len(s3_result.get('selected_documents', []))}")
            logger.info(f"[S3_TRACE] - Search rounds: {s3_result.get('search_rounds', 0)}")
            logger.info(f"[S3_TRACE] - Has search process: {bool(s3_result.get('search_process'))}")
        except Exception as e:
            logger.error(f"[S3_TRACE] S3 framework enhancement failed: {e}", exc_info=True)
            # 如果S3增强失败，使用原始问题
    else:
        logger.warning(f"[S3_TRACE] S3 enhancement skipped - conditions not met")
            
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
                stream_generator = await litellm_client.chat_completion(
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
                            # 返回增量内容，而不是累加的完整内容
                            yield format_sse_message({
                                "code": 0,
                                "message": "",
                                "data": {
                                    "answer_delta": content,  # 只返回当前增量
                                    "reference": {
                                        "total": len(s3_result.get("selected_documents", [])),
                                        "chunks": s3_result.get("selected_documents", [])
                                    },
                                    "session_id": chat_id
                                }
                            })
                
                # Save assistant response with metadata
                await save_message(chat_id, "assistant", full_response, db, {
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
            await save_message(chat_id, "assistant", answer, db, {
                "s3_search_rounds": s3_result.get("search_rounds", 0),
                "s3_documents_found": len(s3_result.get("selected_documents", []))
            })
            
            return success_response(data={
                "answer": answer,
                "reference": {
                    "total": len(s3_result.get("selected_documents", [])),
                    "chunks": s3_result.get("selected_documents", []),
                    "search_rounds": s3_result.get("search_rounds", 0),
                    "search_process": s3_result.get("search_process", [])
                },
                "session_id": chat_id
            })
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chats/{chat_id}/messages", response_model=ApiResponse)
async def get_chat_messages(
    chat_id: str,
    page: int = 1,
    page_size: int = 20,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """获取对话历史"""
    # Check if chat exists
    chat_info = await get_chat_info(chat_id, db)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        result = await db.get_messages(chat_id, page=page, page_size=page_size)
        
        return success_response(data={
            "messages": result["messages"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"]
        })
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

@app.delete("/api/v1/chats/{chat_id}", response_model=ApiResponse)
async def delete_chat(
    chat_id: str,
    db: DatabaseAdapter = Depends(get_database),
    api_key: str = Depends(verify_api_key)
):
    """删除对话"""
    # Check if chat exists
    chat_info = await get_chat_info(chat_id, db)
    if not chat_info:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        # Delete chat (messages will be cascade deleted)
        success = await db.delete_chat(chat_id)
        if success:
            return success_response(message="Chat deleted successfully")
        else:
            raise HTTPException(status_code=404, detail="Chat not found")
    except Exception as e:
        logger.error(f"Failed to delete chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat")

# ==================== RAGFlow Proxy Endpoints ====================

@app.get("/api/v1/datasets", response_model=ApiResponse)
async def list_datasets(
    page: int = 1,
    page_size: int = 12,
    name: Optional[str] = None,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """获取知识库列表 - 代理到RAGFlow"""
    try:
        result = ragflow_client.list_datasets(
            page=page,
            page_size=page_size,
            name=name
        )
        # RAGFlow已经返回{code, data}格式，如果成功直接返回
        if result.get("code") == 0:
            return success_response(
                data=result.get("data"),
                message=result.get("message", "Success")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code, 
                detail=result.get("message", "RAGFlow API error")
            )
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets", response_model=ApiResponse)
async def create_dataset(
    request: DatasetCreateRequest,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
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
        if result.get("code") == 0:
            return success_response(
                data=result.get("data"),
                message=result.get("message", "Dataset created successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code, 
                detail=result.get("message", "Failed to create dataset")
            )
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/datasets/{dataset_id}", response_model=ApiResponse)
async def update_dataset(
    dataset_id: str,
    request: Dict[str, Any],
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """更新知识库 - 代理到RAGFlow"""
    try:
        result = ragflow_client.update_dataset(dataset_id, **request)
        if result.get("code") == 0:
            return success_response(
                data=result.get("data"),
                message=result.get("message", "Dataset updated successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to update dataset")
            )
    except Exception as e:
        logger.error(f"Failed to update dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_id}", response_model=ApiResponse)
async def delete_dataset(
    dataset_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """删除知识库 - 代理到RAGFlow"""
    try:
        result = ragflow_client.delete_datasets([dataset_id])
        if result.get("code") == 0:
            return success_response(
                message=result.get("message", "Dataset deleted successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to delete dataset")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets", response_model=ApiResponse)
async def batch_delete_datasets(
    request: Dict[str, List[str]],
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """批量删除知识库 - 代理到RAGFlow"""
    try:
        dataset_ids = request.get("ids", [])
        if not dataset_ids:
            raise HTTPException(status_code=400, detail="Missing 'ids' field")
        
        result = ragflow_client.delete_datasets(dataset_ids)
        if result.get("code") == 0:
            return success_response(
                message=result.get("message", "Datasets deleted successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to delete datasets")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch delete datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets/{dataset_id}/documents", response_model=ApiResponse)
async def upload_documents(
    dataset_id: str,
    file: UploadFile = File(...),
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
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
            if result.get("code") == 0:
                return success_response(
                    data=result.get("data"),
                    message=result.get("message", "Document uploaded successfully")
                )
            else:
                # 根据错误码返回合适的HTTP状态码
                error_code = result.get("code", -1)
                status_code = get_http_status_from_ragflow_code(error_code)
                
                raise HTTPException(
                    status_code=status_code,
                    detail=result.get("message", "Failed to upload document")
                )
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents", response_model=ApiResponse)
async def list_documents(
    dataset_id: str,
    page: int = 1,
    page_size: int = 20,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """获取文档列表 - 代理到RAGFlow"""
    try:
        result = ragflow_client.list_documents(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size
        )
        if result.get("code") == 0:
            return success_response(
                data=result.get("data"),
                message=result.get("message", "Success")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to list documents")
            )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/datasets/{dataset_id}/documents/{document_id}", response_model=ApiResponse)
async def delete_document(
    dataset_id: str,
    document_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """删除文档 - 代理到RAGFlow"""
    try:
        result = ragflow_client.delete_documents(dataset_id, [document_id])
        if result.get("code") == 0:
            return success_response(
                message=result.get("message", "Document deleted successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to delete document")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets/{dataset_id}/documents/parse", response_model=ApiResponse)
async def parse_documents(
    dataset_id: str,
    request: Dict[str, List[str]],
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """解析文档 - 代理到RAGFlow"""
    try:
        document_ids = request.get("document_ids", [])
        if not document_ids:
            raise HTTPException(status_code=400, detail="Missing 'document_ids' field")
        
        # RAGFlow doesn't have a direct parse endpoint, return success
        # In practice, documents are parsed automatically after upload
        return success_response(
            message="Document parsing initiated",
            data={"document_ids": document_ids}
        )
    except Exception as e:
        logger.error(f"Failed to parse documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/retrieve", response_model=ApiResponse)
async def retrieve(
    request: RetrievalRequest,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
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
        if result.get("code") == 0:
            return success_response(
                data=result.get("data"),
                message=result.get("message", "Retrieval successful")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Retrieval failed")
            )
    except Exception as e:
        logger.error(f"Failed to retrieve: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Additional Document Management Endpoints ====================

@app.delete("/api/v1/datasets/{dataset_id}/documents", response_model=ApiResponse)
async def batch_delete_documents(
    dataset_id: str,
    request: Dict[str, List[str]],
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """批量删除文档 - 代理到RAGFlow"""
    try:
        document_ids = request.get("ids", [])
        if not document_ids:
            raise HTTPException(status_code=400, detail="Missing 'ids' field")
        
        result = ragflow_client.delete_documents(dataset_id, document_ids)
        if result.get("code") == 0:
            return success_response(
                message=result.get("message", "Documents deleted successfully")
            )
        else:
            # 根据错误码返回合适的HTTP状态码
            error_code = result.get("code", -1)
            status_code = get_http_status_from_ragflow_code(error_code)
            
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Failed to delete documents")
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to batch delete documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents/{document_id}")
async def get_document_content(
    dataset_id: str,
    document_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """获取文档内容 - 代理到RAGFlow"""
    try:
        content = ragflow_client.get_document_content(dataset_id, document_id)
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        logger.error(f"Failed to get document content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/datasets/{dataset_id}/documents/{document_id}/download")
async def download_document(
    dataset_id: str,
    document_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """下载文档 - 代理到RAGFlow"""
    try:
        content = ragflow_client.download_document(dataset_id, document_id)
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename=document_{document_id}"}
        )
    except Exception as e:
        logger.error(f"Failed to download document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Reference Document Endpoints ====================

@app.get("/api/v1/documents/reference/{document_id}", response_model=ApiResponse)
async def get_reference_document(
    document_id: str,
    dataset_id: str,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """获取引用文档详情 - 用于用户查看模型回答的引用来源"""
    try:
        # 先获取文档列表确认文档存在
        doc_list_result = ragflow_client.list_documents(dataset_id, page=1, page_size=100)
        
        if doc_list_result.get("code") != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to access dataset: {doc_list_result.get('message', 'Unknown error')}"
            )
        
        # 查找匹配的文档
        docs = doc_list_result.get("data", {}).get("docs", [])
        target_doc = None
        for doc in docs:
            if doc.get("id") == document_id:
                target_doc = doc
                break
        
        if not target_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found in dataset {dataset_id}"
            )
        
        # 获取文档内容
        try:
            content = ragflow_client.get_document_content(dataset_id, document_id)
        except Exception as content_error:
            # 如果无法获取文档内容，至少返回基本信息
            logger.warning(f"Could not fetch document content: {content_error}")
            content = f"[文档内容暂时无法获取] - {str(content_error)}"
        
        return success_response(data={
            "document_id": document_id,
            "document_name": target_doc.get("name", "Unknown"),
            "dataset_id": dataset_id,
            "content": content,
            "metadata": {
                "size": target_doc.get("size", 0),
                "type": target_doc.get("type", "unknown"),
                "status": target_doc.get("run", "unknown"),
                "upload_time": target_doc.get("create_time", "unknown"),
                "token_count": target_doc.get("token_num", 0)
            }
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reference document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ReferenceDocumentRequest(BaseModel):
    references: List[Dict[str, Any]] = Field(..., description="引用文档列表")

@app.post("/api/v1/documents/reference/batch", response_model=ApiResponse)
async def get_reference_documents_batch(
    request: ReferenceDocumentRequest,
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    api_key: str = Depends(verify_api_key)
):
    """批量获取引用文档详情"""
    try:
        documents = []
        total_found = 0
        
        for ref in request.references:
            document_id = ref.get("document_id")
            dataset_id = ref.get("dataset_id")
            
            if not document_id or not dataset_id:
                continue
                
            try:
                # 复用单个文档获取逻辑
                doc_response = await get_reference_document(document_id, dataset_id, ragflow_client, api_key)
                if doc_response.get("code") == 0:
                    doc_data = doc_response.get("data", {})
                    documents.append({
                        "document_id": doc_data.get("document_id"),
                        "document_name": doc_data.get("document_name"),
                        "content": doc_data.get("content", "")[:1000] + "..." if len(doc_data.get("content", "")) > 1000 else doc_data.get("content", ""),  # 截取前1000字符
                        "metadata": doc_data.get("metadata", {}),
                        "similarity": ref.get("similarity", 0.0)  # 从请求中获取相似度
                    })
                    total_found += 1
            except Exception as e:
                logger.warning(f"Failed to get document {document_id}: {e}")
                continue
        
        return success_response(data={
            "documents": documents,
            "total_found": total_found,
            "total_requested": len(request.references)
        })
            
    except Exception as e:
        logger.error(f"Failed to get reference documents batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查S3服务状态
        s3_status = True
        ragflow_status = True
        litellm_status = True
        
        if s3_service:
            health_check_result = await s3_service.health_check()
            s3_status = health_check_result.get('s3_framework', True)
            ragflow_status = health_check_result.get('ragflow', True)
            litellm_status = health_check_result.get('litellm', True)
        
        return JSONResponse(
            status_code=200,
            content=success_response(data={
                "status": "healthy",
                "service": "xDAN Rag Copilot API Service",
                "version": "2.0.0",
                "components": {
                    "s3_framework": s3_status,
                    "ragflow": ragflow_status,
                    "litellm": litellm_status
                },
                "timestamp": datetime.now().isoformat()
            })
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content=error_response(
                code=503,
                message="Service unhealthy",
                data={"error": str(e)}
            )
        )

@app.get("/", response_model=ApiResponse)
async def root():
    """根路径"""
    return JSONResponse(
        status_code=200,
        content=success_response(data={
            "service": "xDAN Rag Copilot API Service",
            "version": "2.0.0",
            "description": "统一的API服务，整合S3框架和RAGFlow知识库管理",
            "features": [
                "S3智能问答框架",
                "知识库管理",
                "实时流式对话",
                "统一LLM路由"
            ],
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "api": "/api/v1"
            }
        })
    )


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    port = service_config.get('api_proxy_port', 8050)
    
    logger.info(f"Starting xDAN Unified API Server on port {port}")
    logger.info(f"RAGFlow API: {ragflow_config.get('api_url')}")
    logger.info(f"PostgreSQL: localhost:5432/xdan_rag_service")
    logger.info(f"Langfuse: https://agentops.xdan.ai")
    logger.info(f"Documentation available at: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )