"""
SSE (Server-Sent Events) 端点的单元测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import time

from src.api.sse_endpoints import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)


class TestSSEEndpoints:
    """SSE 端点测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_ragflow_client(self):
        """模拟 RAGFlow 客户端"""
        mock = Mock()
        return mock
    
    @pytest.mark.asyncio
    async def test_document_status_stream_success(self, mock_ragflow_client):
        """测试文档状态流成功场景"""
        # 模拟文档状态变化
        status_sequence = [
            {
                "id": "doc123",
                "status": "PARSING",
                "progress": 0.0,
                "progress_msg": "开始解析"
            },
            {
                "id": "doc123",
                "status": "PARSING",
                "progress": 0.5,
                "progress_msg": "解析中..."
            },
            {
                "id": "doc123",
                "status": "PARSE_SUCCESS",
                "progress": 1.0,
                "progress_msg": "解析完成"
            }
        ]
        
        # 设置 mock 返回值
        mock_ragflow_client.get_document_status = Mock(side_effect=status_sequence)
        
        # 使用依赖注入覆盖
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/doc123/status/stream",
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # 解析 SSE 响应
            events = []
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    events.append(data)
            
            # 验证事件序列
            assert len(events) >= 3
            assert events[0]["type"] == "status"
            assert events[0]["progress"] == 0.0
            assert events[-1]["type"] == "complete"
            assert events[-1]["success"] is True
    
    @pytest.mark.asyncio
    async def test_document_status_stream_not_found(self, mock_ragflow_client):
        """测试文档不存在的场景"""
        mock_ragflow_client.get_document_status = Mock(return_value=None)
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/notfound/status/stream",
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            
            # 解析错误事件
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    assert data["type"] == "error"
                    assert data["error"] == "Document not found"
                    break
    
    @pytest.mark.asyncio
    async def test_batch_document_status_stream(self, mock_ragflow_client):
        """测试批量文档状态流"""
        # 模拟文档列表响应
        docs_response = {
            "code": 0,
            "data": [
                {
                    "id": "doc1",
                    "status": "PARSING",
                    "progress": 0.3,
                    "progress_msg": "解析中"
                },
                {
                    "id": "doc2",
                    "status": "PARSE_SUCCESS",
                    "progress": 1.0,
                    "progress_msg": "完成"
                }
            ]
        }
        
        mock_ragflow_client.list_documents = Mock(return_value=docs_response)
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/status/stream?doc_ids=doc1,doc2",
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            
            events = []
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    events.append(data)
            
            # 验证批量状态事件
            batch_events = [e for e in events if e["type"] == "batch_status"]
            assert len(batch_events) > 0
            
            # 验证完成事件
            complete_events = [e for e in events if e["type"] == "batch_complete"]
            assert len(complete_events) == 1
    
    @pytest.mark.asyncio
    async def test_chat_stream_with_dataset(self, mock_ragflow_client):
        """测试带知识库的聊天流"""
        # 模拟检索结果
        retrieval_result = {
            "code": 0,
            "data": {
                "chunks": [
                    {
                        "content": "相关内容1",
                        "document_name": "文档1.pdf"
                    },
                    {
                        "content": "相关内容2",
                        "document_name": "文档2.pdf"
                    }
                ]
            }
        }
        
        # 模拟聊天流响应
        class MockStreamResponse:
            def iter_lines(self):
                yield b'data: {"choices": [{"delta": {"content": "你好"}}]}'
                yield b'data: {"choices": [{"delta": {"content": "，有什么"}}]}'
                yield b'data: {"choices": [{"delta": {"content": "可以帮助你"}}]}'
                yield b'data: [DONE]'
        
        mock_ragflow_client.retrieve_chunks = Mock(return_value=retrieval_result)
        mock_ragflow_client.create_chat_completion = Mock(return_value=MockStreamResponse())
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        request_data = {
            "messages": [{"role": "user", "content": "你好"}],
            "dataset_id": "dataset123"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/chats/chat123/stream",
                json=request_data,
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            
            # 验证检索被调用
            mock_ragflow_client.retrieve_chunks.assert_called_once()
            
            # 解析聊天事件
            messages = []
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data["type"] == "message":
                        messages.append(data["content"])
            
            # 验证消息内容
            full_message = "".join(messages)
            assert "你好" in full_message
            assert "可以帮助你" in full_message


class TestSSEClientIntegration:
    """SSE 客户端集成测试"""
    
    @pytest.mark.asyncio
    async def test_sse_connection_timeout(self):
        """测试 SSE 连接超时处理"""
        # 创建一个慢速端点
        @router.get("/test/slow-stream")
        async def slow_stream():
            async def generate():
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                await asyncio.sleep(10)  # 长时间等待
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
            from fastapi.responses import StreamingResponse
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        
        async with AsyncClient(app=app, base_url="http://test", timeout=1.0) as ac:
            with pytest.raises(Exception):  # 应该超时
                await ac.get("/test/slow-stream")
    
    @pytest.mark.asyncio
    async def test_sse_error_handling(self, mock_ragflow_client):
        """测试 SSE 错误处理"""
        # 模拟异常
        mock_ragflow_client.get_document_status = Mock(side_effect=Exception("API Error"))
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/doc123/status/stream",
                headers={"Accept": "text/event-stream"}
            )
            
            # 应该返回错误事件
            assert response.status_code == 200
            
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    assert data["type"] == "error"
                    assert "API Error" in data["error"]
                    break


# 辅助函数
def get_ragflow_client():
    """获取 RAGFlow 客户端的占位函数"""
    pass


@pytest.fixture
def mock_time():
    """模拟时间流逝"""
    with patch('time.time') as mock:
        start_time = time.time()
        mock.side_effect = lambda: start_time + mock.call_count
        yield mock


class TestSSEPerformance:
    """SSE 性能测试"""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self, mock_ragflow_client):
        """测试多个并发 SSE 流"""
        # 模拟多个文档
        def create_doc_status(doc_id, progress):
            return {
                "id": doc_id,
                "status": "PARSING" if progress < 1.0 else "PARSE_SUCCESS",
                "progress": progress
            }
        
        # 为每个文档创建不同的进度
        doc_progress = {"doc1": 0.0, "doc2": 0.0, "doc3": 0.0}
        
        def get_status(dataset_id, doc_id):
            progress = doc_progress.get(doc_id, 0.0)
            doc_progress[doc_id] = min(progress + 0.3, 1.0)
            return create_doc_status(doc_id, doc_progress[doc_id])
        
        mock_ragflow_client.get_document_status = Mock(side_effect=get_status)
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        # 并发请求多个流
        async with AsyncClient(app=app, base_url="http://test") as ac:
            tasks = []
            for doc_id in ["doc1", "doc2", "doc3"]:
                task = ac.get(
                    f"/api/v1/datasets/dataset123/documents/{doc_id}/status/stream",
                    headers={"Accept": "text/event-stream"}
                )
                tasks.append(task)
            
            # 等待所有流完成
            responses = await asyncio.gather(*tasks)
            
            # 验证所有响应
            for response in responses:
                assert response.status_code == 200
                assert "complete" in response.text


class TestSSEEdgeCases:
    """SSE 边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_document_list(self, mock_ragflow_client):
        """测试空文档列表"""
        mock_ragflow_client.list_documents = Mock(return_value={"code": 0, "data": []})
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/status/stream?doc_ids=doc1,doc2",
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            assert "batch_complete" in response.text
    
    @pytest.mark.asyncio
    async def test_malformed_chat_request(self, mock_ragflow_client):
        """测试格式错误的聊天请求"""
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        # 缺少 messages 字段
        request_data = {"dataset_id": "dataset123"}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/chats/chat123/stream",
                json=request_data,
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            
            # 应该返回错误事件
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data["type"] == "error":
                        assert "error" in data
                        break
    
    @pytest.mark.asyncio
    async def test_status_with_special_characters(self, mock_ragflow_client):
        """测试包含特殊字符的状态消息"""
        status_with_special = {
            "id": "doc123",
            "status": "PARSING",
            "progress": 0.5,
            "progress_msg": "解析中...包含特殊字符: \"引号\" \n换行 \t制表符"
        }
        
        mock_ragflow_client.get_document_status = Mock(return_value=status_with_special)
        
        app.dependency_overrides[get_ragflow_client] = lambda: mock_ragflow_client
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/datasets/dataset123/documents/doc123/status/stream",
                headers={"Accept": "text/event-stream"}
            )
            
            assert response.status_code == 200
            
            # 验证 JSON 正确编码
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])  # 应该能正确解析
                    if data["type"] == "status":
                        assert "引号" in data.get("progress_msg", "")
                        break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])