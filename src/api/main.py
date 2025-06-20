"""
主API应用 - 包含搜索过程可视化API
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import asyncio
from typing import Dict, Any
import logging

# 导入搜索过程API - 修复导入
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.search_process_api import (
    stream_search_process, 
    complete_search_process,
    get_event_types,
    SearchRequest,
    EventType,
    SearchEvent
)

# 导入现有的API端点
from src.api.routes import router

logger = logging.getLogger(__name__)

# 创建主应用
app = FastAPI(
    title="RAGFlow Enhanced API",
    description="支持搜索过程可视化的增强RAG API",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（前端示例）
app.mount("/demo", StaticFiles(directory="examples/frontend", html=True), name="demo")

# 包含现有路由
app.include_router(router, prefix="/api/v1", tags=["RAG Operations"])

# 包含搜索过程API路由
app.post("/api/v2/search/stream", tags=["Search Visualization"])(stream_search_process)
app.post("/api/v2/search/complete", tags=["Search Visualization"])(complete_search_process)
app.get("/api/v2/search/event-types", tags=["Search Visualization"])(get_event_types)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

@app.websocket("/ws/search/{client_id}")
async def websocket_search(websocket: WebSocket, client_id: str):
    """
    WebSocket端点 - 实时搜索过程流
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 接收搜索请求
            data = await websocket.receive_json()
            
            if data.get("action") == "search":
                # 获取搜索参数
                request = SearchRequest(**data.get("params", {}))
                
                # 导入必要的服务
                from src.api.search_process_api import get_streaming_service
                service = get_streaming_service()
                
                # 定义WebSocket事件回调
                async def ws_event_callback(event: SearchEvent):
                    await manager.send_json(client_id, {
                        "type": "event",
                        "event": event.dict()
                    })
                
                # 设置事件回调
                service.set_event_callback(ws_event_callback)
                
                try:
                    # 执行搜索
                    search_result = await service.s3_search_process_streaming(
                        question=request.question,
                        dataset_ids=request.dataset_ids or [],
                        max_rounds=request.max_rounds,
                        top_k=request.top_k,
                        similarity_threshold=request.similarity_threshold
                    )
                    
                    # 生成答案
                    if search_result.get('selected_documents'):
                        await manager.send_json(client_id, {
                            "type": "event",
                            "event": {
                                "event_type": EventType.ANSWER_GENERATION_START,
                                "data": {"message": "正在生成答案..."}
                            }
                        })
                        
                        answer = service.synthesize_answer(
                            question=request.question,
                            selected_docs=search_result['selected_documents']
                        )
                        
                        await manager.send_json(client_id, {
                            "type": "event",
                            "event": {
                                "event_type": EventType.ANSWER_GENERATED,
                                "data": {"answer": answer}
                            }
                        })
                    
                    # 发送完成信号
                    await manager.send_json(client_id, {
                        "type": "complete",
                        "summary": {
                            "total_rounds": search_result.get('search_rounds', 0),
                            "total_documents": search_result.get('total_documents_retrieved', 0),
                            "selected_documents": len(search_result.get('selected_documents', [])),
                            "search_time": search_result.get('search_time', 0)
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Search error: {e}")
                    await manager.send_json(client_id, {
                        "type": "error",
                        "error": str(e)
                    })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "RAGFlow Enhanced API",
        "version": "2.0.0",
        "endpoints": {
            "v1": {
                "rag": "/api/v1/rag",
                "datasets": "/api/v1/datasets",
                "documents": "/api/v1/documents",
                "health": "/api/v1/health"
            },
            "v2": {
                "search_stream": "/api/v2/search/stream",
                "search_complete": "/api/v2/search/complete",
                "event_types": "/api/v2/search/event-types",
                "websocket": "/ws/search/{client_id}"
            },
            "demo": "/demo"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "ragflow-enhanced-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )