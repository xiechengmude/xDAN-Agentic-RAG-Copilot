#!/usr/bin/env python3
"""
搜索可视化演示服务器 - 简化版
"""

from fastapi import FastAPI
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

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service_v2_fixed import EnhancedS3RAGServiceV2
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

app = FastAPI(title="搜索过程可视化演示")

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

# HTML演示页面
DEMO_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能体搜索过程可视化</title>
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
        .timeline { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-height: 600px; overflow-y: auto; }
        .event { padding: 15px; margin-bottom: 10px; border-left: 4px solid #007bff; background: #f8f9fa; border-radius: 4px; opacity: 0; animation: fadeIn 0.5s ease-in forwards; }
        .event-header { font-weight: bold; color: #333; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; }
        .event-time { font-size: 12px; color: #999; }
        .event-content { color: #666; font-size: 14px; margin-top: 5px; }
        .event.search_start { border-left-color: #28a745; }
        .event.documents_retrieved { border-left-color: #ffc107; }
        .event.agent_thinking { border-left-color: #6f42c1; }
        .event.agent_decision { border-left-color: #fd7e14; }
        .event.answer_generated { border-left-color: #28a745; }
        .event.search_complete { border-left-color: #20c997; }
        .event.complete { border-left-color: #6c757d; }
        .loading { text-align: center; padding: 20px; color: #666; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .documents-list { margin-top: 10px; }
        .document-item { background: white; border: 1px solid #e9ecef; border-radius: 4px; margin-bottom: 8px; }
        .document-header { padding: 10px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .document-header:hover { background: #e9ecef; }
        .document-title { font-weight: 500; color: #495057; }
        .document-meta { font-size: 12px; color: #6c757d; }
        .document-content { padding: 10px; display: none; background: #fdfdfe; max-height: 300px; overflow-y: auto; }
        .document-content.expanded { display: block; }
        .document-content pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; font-family: inherit; font-size: 13px; line-height: 1.4; }
        .collapse-icon { transition: transform 0.2s; }
        .collapse-icon.expanded { transform: rotate(90deg); }
        
        .thinking-content { background: #f8f4ff; border: 1px solid #e1d4ff; border-radius: 4px; padding: 10px; margin-top: 8px; font-style: italic; }
        .answer-content { background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 4px; padding: 15px; margin-top: 8px; line-height: 1.6; }
        .answer-content h3, .answer-content h4 { color: #1e40af; margin: 10px 0 5px 0; }
        .answer-content ul, .answer-content ol { margin: 10px 0; padding-left: 20px; }
        .answer-content li { margin: 5px 0; }
        
        .progress-indicator { width: 20px; height: 20px; border: 2px solid #e9ecef; border-top: 2px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin-left: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .typing-indicator { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 智能体搜索过程可视化</h1>
        <div class="search-section">
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
        let eventSource = null;
        
        function startSearch() {
            const question = document.getElementById('questionInput').value;
            if (!question.trim()) {
                alert('请输入问题');
                return;
            }
            
            document.getElementById('timeline').innerHTML = '<div class="loading">正在连接服务器...</div>';
            document.getElementById('searchBtn').disabled = true;
            
            if (eventSource) {
                eventSource.close();
            }
            
            // 创建请求体
            const requestBody = {
                question: question,
                max_rounds: 3,
                top_k: 10,
                similarity_threshold: 0.3
            };
            
            // 使用fetch发送POST请求并获取流
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
            });
        }
        
        function addEvent(event) {
            const timeline = document.getElementById('timeline');
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event ' + event.event_type;
            
            const eventHeader = document.createElement('div');
            eventHeader.className = 'event-header';
            
            const headerLeft = document.createElement('div');
            headerLeft.textContent = getEventTypeName(event.event_type);
            
            const headerRight = document.createElement('div');
            headerRight.className = 'event-time';
            headerRight.textContent = new Date(event.timestamp).toLocaleTimeString();
            
            // 添加进度指示器（如果需要）
            if (isProcessingEvent(event.event_type)) {
                const progressIndicator = document.createElement('div');
                progressIndicator.className = 'progress-indicator';
                headerRight.appendChild(progressIndicator);
            }
            
            eventHeader.appendChild(headerLeft);
            eventHeader.appendChild(headerRight);
            
            const eventContent = document.createElement('div');
            eventContent.className = 'event-content';
            
            // 根据事件类型生成内容
            if (event.event_type === 'documents_retrieved') {
                eventContent.appendChild(createDocumentsContent(event));
            } else if (event.event_type === 'agent_decision') {
                eventContent.appendChild(createAgentDecisionContent(event));
            } else if (event.event_type === 'answer_generated') {
                eventContent.appendChild(createAnswerContent(event));
            } else {
                eventContent.innerHTML = getEventSummary(event);
            }
            
            eventDiv.appendChild(eventHeader);
            eventDiv.appendChild(eventContent);
            
            timeline.appendChild(eventDiv);
            
            // 平滑滚动到底部
            setTimeout(() => {
                timeline.scrollTo({
                    top: timeline.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        }
        
        function isProcessingEvent(eventType) {
            return ['agent_thinking', 'answer_generation_start'].includes(eventType);
        }
        
        function createDocumentsContent(event) {
            const container = document.createElement('div');
            
            const summary = document.createElement('div');
            summary.textContent = `检索到 ${event.data.count} 个文档`;
            container.appendChild(summary);
            
            // 如果有文档详情，显示文档列表
            if (event.data.documents && event.data.documents.length > 0) {
                const docsList = document.createElement('div');
                docsList.className = 'documents-list';
                
                event.data.documents.forEach((doc, index) => {
                    const docItem = createDocumentItem(doc, index);
                    docsList.appendChild(docItem);
                });
                
                container.appendChild(docsList);
            }
            
            return container;
        }
        
        function createDocumentItem(doc, index) {
            const docItem = document.createElement('div');
            docItem.className = 'document-item';
            
            const docHeader = document.createElement('div');
            docHeader.className = 'document-header';
            docHeader.onclick = () => toggleDocumentContent(docItem);
            
            const docTitle = document.createElement('div');
            docTitle.className = 'document-title';
            docTitle.textContent = `文档 ${doc.id || index + 1}`;
            
            const docMeta = document.createElement('div');
            docMeta.className = 'document-meta';
            docMeta.innerHTML = `
                <span>相似度: ${(doc.similarity || 0).toFixed(3)}</span>
                <span class="collapse-icon">▶</span>
            `;
            
            docHeader.appendChild(docTitle);
            docHeader.appendChild(docMeta);
            
            const docContent = document.createElement('div');
            docContent.className = 'document-content';
            
            const contentPre = document.createElement('pre');
            contentPre.textContent = doc.content_preview || doc.content || '暂无内容';
            docContent.appendChild(contentPre);
            
            docItem.appendChild(docHeader);
            docItem.appendChild(docContent);
            
            return docItem;
        }
        
        function toggleDocumentContent(docItem) {
            const content = docItem.querySelector('.document-content');
            const icon = docItem.querySelector('.collapse-icon');
            
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
            icon.textContent = content.classList.contains('expanded') ? '▼' : '▶';
        }
        
        function createAgentDecisionContent(event) {
            const container = document.createElement('div');
            
            if (event.data.thinking) {
                const thinkingDiv = document.createElement('div');
                thinkingDiv.className = 'thinking-content';
                thinkingDiv.innerHTML = `<strong>思考过程:</strong><br>${event.data.thinking}`;
                container.appendChild(thinkingDiv);
            }
            
            if (event.data.decision) {
                const decisionDiv = document.createElement('div');
                decisionDiv.innerHTML = `<strong>决策结果:</strong> ${event.data.decision}`;
                decisionDiv.style.marginTop = '8px';
                container.appendChild(decisionDiv);
            }
            
            return container;
        }
        
        function createAnswerContent(event) {
            const container = document.createElement('div');
            
            if (event.data.answer) {
                const answerDiv = document.createElement('div');
                answerDiv.className = 'answer-content';
                
                // 解析markdown格式的答案
                let formattedAnswer = event.data.answer
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*?)\n/g, '<h3>$1</h3>')
                    .replace(/## (.*?)\n/g, '<h3>$1</h3>')
                    .replace(/# (.*?)\n/g, '<h3>$1</h3>')
                    .replace(/- (.*?)$/gm, '<li>$1</li>')
                    .replace(/^\d+\. (.*?)$/gm, '<li>$1</li>')
                    .replace(/\n/g, '<br>');
                
                // 包装列表项
                formattedAnswer = formattedAnswer.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
                
                answerDiv.innerHTML = formattedAnswer;
                container.appendChild(answerDiv);
            }
            
            return container;
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
                    return event.data.answer ? event.data.answer.substring(0, 200) + '...' : '';
                default:
                    return JSON.stringify(event.data);
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def home():
    """返回演示页面"""
    return HTMLResponse(content=DEMO_HTML)

@app.post("/api/search/stream")
async def stream_search(request: SearchRequest):
    """流式搜索API"""
    async def generate():
        # 初始化服务
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
        
        service = EnhancedS3RAGServiceV2(
            ragflow_client=ragflow_client,
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
                        'count': history_item.get('results', {}).get('count', 0),
                        'documents': history_item.get('results', {}).get('documents', [])
                    }
                
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.2)  # 增加延迟以便观察流式效果
            
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动搜索过程可视化演示服务...")
    print("📍 访问地址: http://localhost:8050")
    print("\n按 Ctrl+C 停止服务\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8050)