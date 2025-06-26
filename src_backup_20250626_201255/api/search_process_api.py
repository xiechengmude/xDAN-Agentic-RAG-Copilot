"""
搜索过程API - 暴露智能体思考和搜索过程
支持实时流式返回和完整结果返回
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
import time
from datetime import datetime
from enum import Enum

from src.services.enhanced_s3_rag_service_v2 import EnhancedS3RAGServiceV2
from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

app = FastAPI(title="智能体搜索过程API", version="1.0.0")

# 事件类型枚举
class EventType(str, Enum):
    SEARCH_START = "search_start"
    SEARCH_ROUND_START = "search_round_start"
    DOCUMENTS_RETRIEVED = "documents_retrieved"
    AGENT_THINKING = "agent_thinking"
    AGENT_DECISION = "agent_decision"
    NEW_QUERY_GENERATED = "new_query_generated"
    DOCUMENTS_SELECTED = "documents_selected"
    SEARCH_COMPLETE = "search_complete"
    ANSWER_GENERATION_START = "answer_generation_start"
    ANSWER_GENERATED = "answer_generated"
    ERROR = "error"

# 请求模型
class SearchRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    max_rounds: int = 3
    top_k: int = 10
    similarity_threshold: float = 0.3
    stream: bool = True  # 是否使用流式返回

# 搜索事件模型
class SearchEvent(BaseModel):
    event_type: EventType
    timestamp: str
    round: Optional[int] = None
    data: Dict[str, Any]

# 增强的S3服务，支持事件回调
class StreamingEnhancedS3Service(EnhancedS3RAGServiceV2):
    """支持流式事件的增强S3服务"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callback = None
    
    def set_event_callback(self, callback):
        """设置事件回调函数"""
        self.event_callback = callback
    
    async def emit_event(self, event_type: EventType, data: Dict[str, Any], round: Optional[int] = None):
        """发送事件"""
        if self.event_callback:
            event = SearchEvent(
                event_type=event_type,
                timestamp=datetime.now().isoformat(),
                round=round,
                data=data
            )
            await self.event_callback(event)
    
    async def s3_search_process_streaming(self, question: str, dataset_ids: List[str], 
                                        max_rounds: int = 3, top_k: int = 5, 
                                        similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        带流式事件的S3搜索过程
        """
        # 发送搜索开始事件
        await self.emit_event(EventType.SEARCH_START, {
            "question": question,
            "config": {
                "max_rounds": max_rounds,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "search_model": S3_SEARCH_MODEL_NAME,
                "generator_model": S3_GENERATOR_MODEL_NAME
            }
        })
        
        search_history = []
        all_documents = {}
        selected_documents = []
        total_documents_retrieved = 0
        
        start_time = time.time()
        
        # 步骤1: 初始搜索
        await self.emit_event(EventType.SEARCH_ROUND_START, {
            "query": question,
            "round_type": "initial"
        }, round=1)
        
        initial_chunks, success = self.search_step(question, dataset_ids, top_k, similarity_threshold)
        
        if not success or not initial_chunks:
            await self.emit_event(EventType.ERROR, {
                "message": "初始搜索失败或无结果"
            })
            return {
                'question': question,
                'search_rounds': 0,
                'selected_documents': [],
                'error': "初始搜索失败"
            }
        
        # 发送文档检索结果
        await self.emit_event(EventType.DOCUMENTS_RETRIEVED, {
            "count": len(initial_chunks),
            "documents": [
                {
                    "id": i+1,
                    "similarity": chunk.get('similarity', 0.0),
                    "content_preview": chunk.get('content', '')[:200] + '...'
                }
                for i, chunk in enumerate(initial_chunks[:5])  # 只发送前5个预览
            ]
        }, round=1)
        
        initial_results, doc_mapping = self.format_search_results(initial_chunks, 1)
        all_documents.update(doc_mapping)
        total_documents_retrieved += len(initial_chunks)
        
        initial_prompt = f"""<question>
{question}
</question>
<information>
{initial_results}
</information>"""
        
        # 步骤2: 智能体决策和迭代搜索
        current_round = 1
        agent_input = S3_SYSTEM_PROMPT + initial_prompt
        
        while current_round <= max_rounds:
            try:
                # 发送智能体思考开始
                await self.emit_event(EventType.AGENT_THINKING, {
                    "message": "Search Model正在分析检索结果..."
                }, round=current_round)
                
                # 使用Search LLM进行决策
                messages = [{"role": "user", "content": agent_input}]
                llm_response = self.search_llm_client.chat_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )
                
                # 提取响应内容
                if isinstance(llm_response, dict):
                    agent_response = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                else:
                    agent_response = llm_response
                
                # 解析决策
                decision = self.extract_search_decision(agent_response)
                
                # 发送智能体决策事件
                await self.emit_event(EventType.AGENT_DECISION, {
                    "thinking": decision['thinking'],
                    "search_complete": decision['search_complete'],
                    "decision": "完成搜索" if decision['search_complete'] else "继续搜索"
                }, round=current_round)
                
                # 处理重要文档
                if decision['important_docs']:
                    for doc_id in decision['important_docs']:
                        if doc_id in all_documents and len(selected_documents) < 3:
                            selected_documents.append(all_documents[doc_id])
                    
                    await self.emit_event(EventType.DOCUMENTS_SELECTED, {
                        "selected_ids": decision['important_docs'],
                        "selected_count": len(selected_documents)
                    }, round=current_round)
                
                # 检查是否完成搜索
                if decision['search_complete']:
                    break
                
                # 生成新查询
                if decision['new_query']:
                    await self.emit_event(EventType.NEW_QUERY_GENERATED, {
                        "new_query": decision['new_query'],
                        "reason": "需要更多信息来完善答案"
                    }, round=current_round)
                    
                    # 执行新搜索
                    await self.emit_event(EventType.SEARCH_ROUND_START, {
                        "query": decision['new_query'],
                        "round_type": "iterative"
                    }, round=current_round+1)
                    
                    new_chunks, success = self.search_step(
                        decision['new_query'], 
                        dataset_ids, 
                        top_k, 
                        similarity_threshold
                    )
                    
                    if success and new_chunks:
                        await self.emit_event(EventType.DOCUMENTS_RETRIEVED, {
                            "count": len(new_chunks),
                            "documents": [
                                {
                                    "id": doc_id_start + i,
                                    "similarity": chunk.get('similarity', 0.0),
                                    "content_preview": chunk.get('content', '')[:200] + '...'
                                }
                                for i, chunk in enumerate(new_chunks[:5])
                            ]
                        }, round=current_round+1)
                        
                        doc_id_start = max(all_documents.keys()) + 1 if all_documents else 1
                        new_results, new_doc_mapping = self.format_search_results(new_chunks, doc_id_start)
                        all_documents.update(new_doc_mapping)
                        total_documents_retrieved += len(new_chunks)
                        
                        # 更新智能体输入
                        agent_input = f"{agent_input}\n\n<information>\n{new_results}\n</information>"
                
                current_round += 1
                
            except Exception as e:
                await self.emit_event(EventType.ERROR, {
                    "message": f"第{current_round}轮处理失败: {str(e)}"
                }, round=current_round)
                break
        
        # 如果没有选中的文档，使用前3个
        if not selected_documents and all_documents:
            selected_documents = list(all_documents.values())[:3]
        
        # 发送搜索完成事件
        await self.emit_event(EventType.SEARCH_COMPLETE, {
            "total_rounds": current_round,
            "total_documents": total_documents_retrieved,
            "selected_documents": len(selected_documents),
            "search_time": time.time() - start_time
        })
        
        return {
            'question': question,
            'search_rounds': current_round,
            'selected_documents': selected_documents,
            'total_documents_retrieved': total_documents_retrieved,
            'search_time': time.time() - start_time
        }

# 全局服务实例
streaming_service = None

def get_streaming_service():
    """获取流式服务实例"""
    global streaming_service
    if not streaming_service:
        ragflow_client = RAGFlowSDKWrapper(
            api_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )
        
        search_llm_client = LLMClient(
            base_url=S3_SEARCH_MODEL_URL,
            api_key=S3_SEARCH_API_KEY,
            model_name=S3_SEARCH_MODEL_NAME
        )
        
        generator_llm_client = LLMClient(
            base_url=S3_GENERATOR_MODEL_URL,
            api_key=S3_GENERATOR_API_KEY,
            model_name=S3_GENERATOR_MODEL_NAME
        )
        
        streaming_service = StreamingEnhancedS3Service(
            ragflow_client=ragflow_client,
            search_llm_client=search_llm_client,
            generator_llm_client=generator_llm_client
        )
    
    return streaming_service

@app.post("/api/search/stream")
async def stream_search_process(request: SearchRequest):
    """
    流式返回搜索过程
    使用Server-Sent Events (SSE)格式
    """
    service = get_streaming_service()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """生成SSE事件"""
        event_queue = asyncio.Queue()
        
        async def event_callback(event: SearchEvent):
            await event_queue.put(event)
        
        # 设置事件回调
        service.set_event_callback(event_callback)
        
        # 启动搜索任务
        search_task = asyncio.create_task(
            service.s3_search_process_streaming(
                question=request.question,
                dataset_ids=request.dataset_ids or [DEFAULT_DATASET_ID],
                max_rounds=request.max_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
        )
        
        # 持续发送事件直到搜索完成
        while not search_task.done() or not event_queue.empty():
            try:
                # 等待事件，超时检查任务是否完成
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield f"data: {event.json()}\n\n"
            except asyncio.TimeoutError:
                continue
        
        # 获取搜索结果
        search_result = await search_task
        
        # 生成答案
        if search_result.get('selected_documents'):
            yield f"data: {json.dumps({'event_type': EventType.ANSWER_GENERATION_START, 'timestamp': datetime.now().isoformat(), 'data': {'message': '正在生成答案...'}})}\n\n"
            
            answer = service.synthesize_answer(
                question=request.question,
                selected_docs=search_result['selected_documents']
            )
            
            yield f"data: {json.dumps({'event_type': EventType.ANSWER_GENERATED, 'timestamp': datetime.now().isoformat(), 'data': {'answer': answer}})}\n\n"
        
        # 发送结束信号
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )

@app.post("/api/search/complete")
async def complete_search_process(request: SearchRequest):
    """
    返回完整的搜索过程结果（非流式）
    """
    service = get_streaming_service()
    
    # 收集所有事件
    events = []
    
    async def event_collector(event: SearchEvent):
        events.append(event.dict())
    
    service.set_event_callback(event_collector)
    
    # 执行搜索
    search_result = await service.s3_search_process_streaming(
        question=request.question,
        dataset_ids=request.dataset_ids or [DEFAULT_DATASET_ID],
        max_rounds=request.max_rounds,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold
    )
    
    # 生成答案
    answer = None
    if search_result.get('selected_documents'):
        answer = service.synthesize_answer(
            question=request.question,
            selected_docs=search_result['selected_documents']
        )
    
    return {
        "question": request.question,
        "answer": answer,
        "search_summary": {
            "total_rounds": search_result.get('search_rounds', 0),
            "total_documents": search_result.get('total_documents_retrieved', 0),
            "selected_documents": len(search_result.get('selected_documents', [])),
            "search_time": search_result.get('search_time', 0)
        },
        "events": events
    }

@app.get("/api/search/event-types")
async def get_event_types():
    """获取所有事件类型说明"""
    return {
        "event_types": [
            {
                "type": event_type.value,
                "description": {
                    EventType.SEARCH_START: "搜索开始",
                    EventType.SEARCH_ROUND_START: "搜索轮次开始",
                    EventType.DOCUMENTS_RETRIEVED: "文档检索完成",
                    EventType.AGENT_THINKING: "智能体思考中",
                    EventType.AGENT_DECISION: "智能体做出决策",
                    EventType.NEW_QUERY_GENERATED: "生成新的搜索查询",
                    EventType.DOCUMENTS_SELECTED: "选中重要文档",
                    EventType.SEARCH_COMPLETE: "搜索过程完成",
                    EventType.ANSWER_GENERATION_START: "开始生成答案",
                    EventType.ANSWER_GENERATED: "答案生成完成",
                    EventType.ERROR: "发生错误"
                }.get(event_type, "")
            }
            for event_type in EventType
        ]
    }