#!/usr/bin/env python3
"""
xDAN RAG Copilot 主服务器
提供智能搜索和对话服务
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import asyncio
import time
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.xdan_rag_client import XDANRagClient, APIError
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service_v2_fixed import EnhancedS3RAGServiceV2
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

app = FastAPI(title="xDAN RAG Copilot 搜索可视化演示")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class SearchRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    max_rounds: int = 3
    top_k: int = 10
    similarity_threshold: float = 0.3

class ChatRequest(BaseModel):
    question: str
    chat_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None

# HTML演示页面（更新版）
DEMO_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xDAN RAG Copilot - 智能搜索可视化</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 30px; text-align: center; }
        .search-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .search-input { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }
        button { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .mode-switch { margin-bottom: 15px; }
        .mode-switch label { margin-right: 20px; cursor: pointer; }
        .timeline { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-height: 600px; overflow-y: auto; }
        .event { padding: 15px; margin-bottom: 10px; border-left: 4px solid #007bff; background: #f8f9fa; border-radius: 4px; }
        .event-header { font-weight: bold; color: #333; margin-bottom: 5px; }
        .event-time { font-size: 12px; color: #999; }
        .event-content { color: #666; font-size: 14px; margin-top: 5px; }
        .event.search_start { border-left-color: #28a745; }
        .event.documents_retrieved { border-left-color: #ffc107; }
        .event.agent_thinking { border-left-color: #6f42c1; }
        .event.agent_decision { border-left-color: #fd7e14; }
        .event.answer_generated { border-left-color: #28a745; }
        .event.chat_created { border-left-color: #17a2b8; }
        .loading { text-align: center; padding: 20px; color: #666; }
        .answer-content { background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 15px; margin-top: 8px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; }
        .status-info { background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 4px; padding: 10px; margin-bottom: 15px; font-size: 14px; }
        .error-info { background: #ffebee; border: 1px solid #ef9a9a; border-radius: 4px; padding: 10px; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 xDAN RAG Copilot - 智能搜索可视化</h1>
        <div class="search-section">
            <div class="mode-switch">
                <label>
                    <input type="radio" name="mode" value="s3" checked> S3智能搜索模式
                </label>
                <label>
                    <input type="radio" name="mode" value="chat"> 对话模式
                </label>
            </div>
            <div id="statusInfo" class="status-info" style="display: none;"></div>
            <div id="errorInfo" class="error-info" style="display: none;"></div>
            <div class="search-input">
                <input type="text" id="questionInput" placeholder="请输入您的问题..." value="什么是智信平台？它主要有哪些功能？">
                <button id="searchBtn" onclick="startSearch()">开始搜索</button>
            </div>
        </div>
        <div class="timeline">
            <h3>搜索过程时间线</h3>
            <div id="timeline"></div>
        </div>
    </div>
    
    <script>
        let chatId = null;
        let eventSource = null;
        
        function showStatus(message, isError = false) {
            const statusEl = document.getElementById('statusInfo');
            const errorEl = document.getElementById('errorInfo');
            
            if (isError) {
                errorEl.textContent = message;
                errorEl.style.display = 'block';
                statusEl.style.display = 'none';
            } else {
                statusEl.textContent = message;
                statusEl.style.display = 'block';
                errorEl.style.display = 'none';
            }
        }
        
        function startSearch() {
            const question = document.getElementById('questionInput').value;
            if (!question.trim()) {
                alert('请输入问题');
                return;
            }
            
            const mode = document.querySelector('input[name="mode"]:checked').value;
            document.getElementById('timeline').innerHTML = '<div class="loading">正在连接服务器...</div>';
            document.getElementById('searchBtn').disabled = true;
            
            if (eventSource) {
                eventSource.close();
            }
            
            if (mode === 's3') {
                searchWithS3(question);
            } else {
                searchWithChat(question);
            }
        }
        
        function searchWithS3(question) {
            showStatus('使用S3智能搜索模式...');
            
            const requestBody = {
                question: question,
                max_rounds: 3,
                top_k: 10,
                similarity_threshold: 0.3
            };
            
            fetch('/api/search/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            }).then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                document.getElementById('timeline').innerHTML = '';
                
                const readStream = async () => {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') {
                                    document.getElementById('searchBtn').disabled = false;
                                    addEvent({
                                        event_type: 'complete',
                                        timestamp: new Date().toISOString(),
                                        data: { message: '搜索完成' }
                                    });
                                } else if (data) {
                                    try {
                                        const event = JSON.parse(data);
                                        addEvent(event);
                                    } catch (e) {
                                        console.error('解析错误:', e);
                                    }
                                }
                            }
                        }
                    }
                };
                
                readStream();
            }).catch(error => {
                console.error('请求错误:', error);
                document.getElementById('searchBtn').disabled = false;
                document.getElementById('timeline').innerHTML = '<div class="loading">连接错误，请重试</div>';
                showStatus('连接错误: ' + error.message, true);
            });
        }
        
        function searchWithChat(question) {
            showStatus('使用对话模式...');
            
            const requestBody = {
                question: question,
                chat_id: chatId
            };
            
            fetch('/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            }).then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                document.getElementById('timeline').innerHTML = '';
                
                const readStream = async () => {
                    let buffer = '';
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop(); // 保留未完成的行
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data) {
                                    try {
                                        const event = JSON.parse(data);
                                        if (event.chat_id && !chatId) {
                                            chatId = event.chat_id;
                                            showStatus(`对话已创建，ID: ${chatId}`);
                                        }
                                        addEvent(event);
                                    } catch (e) {
                                        console.error('解析错误:', e);
                                    }
                                }
                            }
                        }
                    }
                    document.getElementById('searchBtn').disabled = false;
                };
                
                readStream().catch(error => {
                    console.error('流读取错误:', error);
                    document.getElementById('searchBtn').disabled = false;
                    showStatus('流读取错误: ' + error.message, true);
                });
            }).catch(error => {
                console.error('请求错误:', error);
                document.getElementById('searchBtn').disabled = false;
                document.getElementById('timeline').innerHTML = '<div class="loading">连接错误，请重试</div>';
                showStatus('连接错误: ' + error.message, true);
            });
        }
        
        function addEvent(event) {
            const timeline = document.getElementById('timeline');
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event ' + event.event_type;
            
            const eventHeader = document.createElement('div');
            eventHeader.className = 'event-header';
            eventHeader.textContent = getEventTypeName(event.event_type);
            
            const eventTime = document.createElement('div');
            eventTime.className = 'event-time';
            eventTime.textContent = new Date(event.timestamp).toLocaleTimeString();
            
            const eventContent = document.createElement('div');
            eventContent.className = 'event-content';
            
            if (event.event_type === 'answer_generated' && event.data.answer) {
                const answerDiv = document.createElement('div');
                answerDiv.className = 'answer-content';
                answerDiv.textContent = event.data.answer;
                eventContent.appendChild(answerDiv);
            } else if (event.event_type === 'chat_response' && event.data.content) {
                const answerDiv = document.createElement('div');
                answerDiv.className = 'answer-content';
                answerDiv.textContent = event.data.content;
                eventContent.appendChild(answerDiv);
            } else {
                eventContent.textContent = getEventSummary(event);
            }
            
            eventDiv.appendChild(eventHeader);
            eventDiv.appendChild(eventTime);
            eventDiv.appendChild(eventContent);
            
            timeline.appendChild(eventDiv);
            timeline.scrollTop = timeline.scrollHeight;
        }
        
        function getEventTypeName(type) {
            const names = {
                'search_start': '🚀 搜索开始',
                'search_round_start': '🔍 开始新一轮搜索',
                'documents_retrieved': '📄 文档检索完成',
                'agent_thinking': '🤔 智能体思考中',
                'agent_decision': '💡 智能体决策',
                'new_query_generated': '✨ 生成新查询',
                'documents_selected': '✅ 选中文档',
                'search_complete': '🎯 搜索完成',
                'answer_generation_start': '✍️ 开始生成答案',
                'answer_generated': '📝 答案生成完成',
                'chat_created': '💬 对话创建成功',
                'chat_response': '💬 对话回复',
                'complete': '✅ 全部完成',
                'error': '❌ 错误'
            };
            return names[type] || type;
        }
        
        function getEventSummary(event) {
            if (!event.data) return '';
            
            switch (event.event_type) {
                case 'search_start':
                    return '问题: ' + event.data.question;
                case 'documents_retrieved':
                    return '检索到 ' + event.data.count + ' 个文档';
                case 'agent_decision':
                    return event.data.thinking || event.data.decision || '';
                case 'answer_generated':
                    return '✅ 答案已生成，请查看下方详细内容';
                case 'chat_created':
                    return '对话ID: ' + event.data.chat_id;
                case 'error':
                    return '错误: ' + event.data.message;
                default:
                    return JSON.stringify(event.data);
            }
        }
    </script>
</body>
</html>
"""

# 全局客户端实例
xdan_client = None
search_llm_client = None
generator_llm_client = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化客户端"""
    global xdan_client, search_llm_client, generator_llm_client
    
    try:
        # 初始化xDAN客户端
        xdan_client = XDANRagClient(
            api_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )
        
        # 初始化LLM客户端
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
        
        print("✅ 所有客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        raise

@app.get("/")
async def home():
    """返回演示页面"""
    return HTMLResponse(content=DEMO_HTML)

@app.post("/api/search/stream")
async def stream_search(request: SearchRequest):
    """S3智能搜索流式API"""
    async def generate():
        # 使用EnhancedS3RAGServiceV2进行搜索
        service = EnhancedS3RAGServiceV2(
            ragflow_client=xdan_client,
            search_llm_client=search_llm_client,
            generator_llm_client=generator_llm_client
        )
        
        # 发送开始事件
        yield f"data: {json.dumps({'event_type': 'search_start', 'timestamp': datetime.now().isoformat(), 'data': {'question': request.question}})}\n\n"
        
        try:
            # 执行搜索
            result = service.s3_search_process_with_history(
                question=request.question,
                dataset_ids=request.dataset_ids or [DEFAULT_DATASET_ID],
                max_rounds=request.max_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            
            # 发送搜索历史中的事件
            for history_item in result.get('search_history', []):
                event = {
                    'event_type': history_item['type'],
                    'timestamp': history_item.get('timestamp', datetime.now().isoformat()),
                    'round': history_item.get('round'),
                    'data': {}
                }
                
                if history_item['type'] == 'agent_decision':
                    event['data'] = {
                        'thinking': history_item.get('agent_decision', {}).get('thinking', ''),
                        'decision': '完成搜索' if history_item.get('agent_decision', {}).get('search_complete') else '继续搜索'
                    }
                elif history_item['type'] == 'initial_search' or history_item['type'] == 'iterative_search':
                    event['event_type'] = 'documents_retrieved'
                    event['data'] = {
                        'count': history_item.get('results', {}).get('count', 0)
                    }
                
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.1)
            
            # 生成答案
            if result.get('selected_documents'):
                yield f"data: {json.dumps({'event_type': 'answer_generation_start', 'timestamp': datetime.now().isoformat(), 'data': {'message': '正在生成答案...'}})}\n\n"
                
                answer = service.synthesize_answer(
                    question=request.question,
                    selected_docs=result['selected_documents']
                )
                
                yield f"data: {json.dumps({'event_type': 'answer_generated', 'timestamp': datetime.now().isoformat(), 'data': {'answer': answer}})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event_type': 'error', 'timestamp': datetime.now().isoformat(), 'data': {'message': str(e)}})}\n\n"
        
        # 发送完成信号
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest):
    """对话模式流式API"""
    async def generate():
        try:
            # 如果没有chat_id，创建新对话
            if not request.chat_id:
                chat_data = xdan_client.create_chat(
                    name=f"对话_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    dataset_ids=request.dataset_ids or [DEFAULT_DATASET_ID]
                )
                chat_id = chat_data['id']
                
                # 发送对话创建事件
                yield f"data: {json.dumps({'event_type': 'chat_created', 'timestamp': datetime.now().isoformat(), 'data': {'chat_id': chat_id}, 'chat_id': chat_id})}\n\n"
            else:
                chat_id = request.chat_id
            
            # 发送消息并获取流式响应
            response = xdan_client.send_message(chat_id, request.question, stream=True)
            
            # 处理流式响应
            for event_data in xdan_client.handle_sse_stream(response):
                event = {
                    'event_type': 'chat_response',
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'content': event_data.get('answer', ''),
                        'chat_id': chat_id
                    }
                }
                yield f"data: {json.dumps(event)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'event_type': 'complete', 'timestamp': datetime.now().isoformat(), 'data': {'message': '对话完成'}})}\n\n"
            
        except APIError as e:
            yield f"data: {json.dumps({'event_type': 'error', 'timestamp': datetime.now().isoformat(), 'data': {'message': f'API错误: {e.message}'}})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event_type': 'error', 'timestamp': datetime.now().isoformat(), 'data': {'message': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    try:
        # 测试API连接
        datasets = xdan_client.list_datasets(page_size=1)
        return {
            "status": "healthy",
            "api_connected": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "api_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    from src.utils.port_manager import ensure_port_free
    
    # 默认端口
    DEFAULT_PORT = 8050
    port = DEFAULT_PORT
    
    # 确保端口可用
    if not ensure_port_free(port, auto_kill=True):
        print(f"❌ 无法释放端口 {port}")
        # 尝试查找其他可用端口
        from src.utils.port_manager import PortManager
        new_port = PortManager.find_free_port(8050, 8100)
        if new_port:
            port = new_port
            print(f"✅ 使用备用端口: {port}")
        else:
            print("❌ 没有找到可用端口")
            exit(1)
    
    print("🚀 启动 xDAN RAG Copilot 主服务器...")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"📍 API文档: http://localhost:{port}/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)