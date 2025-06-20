"""
SSE 前后端集成测试
测试实际的 SSE 通信流程
"""

import pytest
import asyncio
import json
import threading
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
import uvicorn
import requests
from typing import List, Dict, Any

from api import app, ragflow_client
from src.clients.ragflow_client import RAGFlowClient


class TestSSEIntegration:
    """SSE 集成测试"""
    
    @pytest.fixture
    def test_server(self):
        """启动测试服务器"""
        # 使用线程运行服务器
        server_thread = threading.Thread(
            target=uvicorn.run,
            args=(app,),
            kwargs={
                "host": "127.0.0.1",
                "port": 8002,
                "log_level": "error"
            },
            daemon=True
        )
        server_thread.start()
        
        # 等待服务器启动
        time.sleep(1)
        
        yield "http://127.0.0.1:8002"
        
        # 测试结束后服务器会自动关闭（daemon线程）
    
    def test_document_status_sse_flow(self, test_server, monkeypatch):
        """测试完整的文档状态 SSE 流程"""
        # 模拟文档状态序列
        status_sequence = [
            {
                "id": "test_doc",
                "name": "test.pdf",
                "status": "1",  # PARSING
                "progress": 0.0,
                "progress_msg": "开始解析"
            },
            {
                "id": "test_doc",
                "name": "test.pdf",
                "status": "1",
                "progress": 0.3,
                "progress_msg": "解析中..."
            },
            {
                "id": "test_doc",
                "name": "test.pdf",
                "status": "1",
                "progress": 0.7,
                "progress_msg": "即将完成..."
            },
            {
                "id": "test_doc",
                "name": "test.pdf",
                "status": "2",  # PARSE_SUCCESS
                "progress": 1.0,
                "progress_msg": "解析完成"
            }
        ]
        
        # 创建状态迭代器
        status_iter = iter(status_sequence)
        
        # Mock get_document_status
        def mock_get_status(dataset_id, doc_id):
            try:
                return next(status_iter)
            except StopIteration:
                return status_sequence[-1]  # 返回最后的状态
        
        monkeypatch.setattr(ragflow_client, "get_document_status", mock_get_status)
        
        # 发起 SSE 请求
        url = f"{test_server}/api/v1/datasets/test_dataset/documents/test_doc/status/stream"
        
        events = []
        with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # 读取事件流
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        events.append(data)
                        
                        # 如果收到完成事件，停止读取
                        if data.get("type") == "complete":
                            break
        
        # 验证事件序列
        assert len(events) >= 4  # 至少应该有3个状态更新 + 1个完成事件
        
        # 验证进度递增
        progress_events = [e for e in events if e.get("type") == "status"]
        progress_values = [e.get("progress", 0) for e in progress_events]
        assert progress_values == sorted(progress_values)  # 进度应该递增
        
        # 验证完成事件
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0].get("success") is True
    
    def test_batch_document_status_sse(self, test_server, monkeypatch):
        """测试批量文档状态 SSE"""
        # 模拟文档列表响应
        call_count = 0
        
        def mock_list_documents(dataset_id, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # 第一次调用：部分文档完成
                return {
                    "code": 0,
                    "data": [
                        {
                            "id": "doc1",
                            "status": "1",  # PARSING
                            "progress": 0.5,
                            "progress_msg": "解析中"
                        },
                        {
                            "id": "doc2",
                            "status": "2",  # PARSE_SUCCESS
                            "progress": 1.0,
                            "progress_msg": "完成"
                        }
                    ]
                }
            else:
                # 后续调用：所有文档完成
                return {
                    "code": 0,
                    "data": [
                        {
                            "id": "doc1",
                            "status": "2",  # PARSE_SUCCESS
                            "progress": 1.0,
                            "progress_msg": "完成"
                        },
                        {
                            "id": "doc2",
                            "status": "2",  # PARSE_SUCCESS
                            "progress": 1.0,
                            "progress_msg": "完成"
                        }
                    ]
                }
        
        monkeypatch.setattr(ragflow_client, "list_documents", mock_list_documents)
        
        # 发起批量 SSE 请求
        url = f"{test_server}/api/v1/datasets/test_dataset/documents/status/stream?doc_ids=doc1,doc2"
        
        events = []
        with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        events.append(data)
                        
                        if data.get("type") == "batch_complete":
                            break
        
        # 验证批量状态事件
        status_events = [e for e in events if e.get("type") == "batch_status"]
        assert len(status_events) >= 2  # 至少应该有两个状态更新
        
        # 验证完成事件
        complete_events = [e for e in events if e.get("type") == "batch_complete"]
        assert len(complete_events) == 1
        assert "doc1" in complete_events[0].get("summary", {})
        assert "doc2" in complete_events[0].get("summary", {})
    
    def test_chat_stream_sse(self, test_server, monkeypatch):
        """测试聊天流 SSE"""
        # 模拟检索结果
        def mock_retrieve(question, dataset_ids, **kwargs):
            return {
                "code": 0,
                "data": {
                    "chunks": [
                        {
                            "content": "测试知识内容",
                            "document_name": "test.pdf",
                            "score": 0.9
                        }
                    ]
                }
            }
        
        # 模拟聊天响应流
        class MockChatResponse:
            def iter_lines(self):
                messages = [
                    b'data: {"choices": [{"delta": {"content": "基于"}}]}',
                    b'data: {"choices": [{"delta": {"content": "知识库"}}]}',
                    b'data: {"choices": [{"delta": {"content": "的"}}]}',
                    b'data: {"choices": [{"delta": {"content": "回答"}}]}',
                    b'data: [DONE]'
                ]
                for msg in messages:
                    yield msg
        
        def mock_create_chat(chat_id, messages, stream=False):
            if stream:
                return MockChatResponse()
            return {"choices": [{"message": {"content": "基于知识库的回答"}}]}
        
        monkeypatch.setattr(ragflow_client, "retrieve_chunks", mock_retrieve)
        monkeypatch.setattr(ragflow_client, "create_chat_completion", mock_create_chat)
        
        # 发起聊天流请求
        url = f"{test_server}/api/v1/chats/test_chat/stream"
        request_data = {
            "messages": [{"role": "user", "content": "测试问题"}],
            "dataset_id": "test_dataset"
        }
        
        events = []
        response = requests.post(
            url,
            json=request_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        assert response.status_code == 200
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    events.append(data)
                    
                    if data.get("done"):
                        break
        
        # 验证消息事件
        message_events = [e for e in events if e.get("type") == "message"]
        assert len(message_events) >= 4  # 至少4个消息片段
        
        # 组合完整消息
        full_message = "".join(e.get("content", "") for e in message_events)
        assert "基于知识库的回答" in full_message
        
        # 验证最后一个事件标记为完成
        assert events[-1].get("done") is True
    
    def test_sse_error_handling(self, test_server, monkeypatch):
        """测试 SSE 错误处理"""
        # 模拟异常
        def mock_error(*args, **kwargs):
            raise Exception("模拟的 API 错误")
        
        monkeypatch.setattr(ragflow_client, "get_document_status", mock_error)
        
        # 发起请求
        url = f"{test_server}/api/v1/datasets/test_dataset/documents/error_doc/status/stream"
        
        events = []
        with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}) as response:
            assert response.status_code == 200
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        events.append(data)
                        break  # 收到错误事件后停止
        
        # 验证错误事件
        assert len(events) == 1
        assert events[0].get("type") == "error"
        assert "模拟的 API 错误" in events[0].get("error", "")
    
    def test_sse_concurrent_connections(self, test_server, monkeypatch):
        """测试并发 SSE 连接"""
        # 模拟不同的文档状态
        doc_status = {
            "doc1": {"id": "doc1", "status": "1", "progress": 0.3},
            "doc2": {"id": "doc2", "status": "1", "progress": 0.5},
            "doc3": {"id": "doc3", "status": "2", "progress": 1.0}
        }
        
        def mock_get_status(dataset_id, doc_id):
            return doc_status.get(doc_id, {"id": doc_id, "status": "0", "progress": 0})
        
        monkeypatch.setattr(ragflow_client, "get_document_status", mock_get_status)
        
        # 并发请求
        import concurrent.futures
        
        def fetch_sse(doc_id):
            url = f"{test_server}/api/v1/datasets/test_dataset/documents/{doc_id}/status/stream"
            events = []
            
            with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}) as response:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = json.loads(line_str[6:])
                            events.append(data)
                            
                            # 收到一定数量的事件后停止
                            if len(events) >= 2:
                                break
            
            return doc_id, events
        
        # 使用线程池并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(fetch_sse, doc_id)
                for doc_id in ["doc1", "doc2", "doc3"]
            ]
            
            results = {}
            for future in concurrent.futures.as_completed(futures):
                doc_id, events = future.result()
                results[doc_id] = events
        
        # 验证每个文档都收到了事件
        assert len(results) == 3
        for doc_id, events in results.items():
            assert len(events) >= 1
            # 验证事件包含正确的文档ID
            status_events = [e for e in events if e.get("doc_id") == doc_id]
            assert len(status_events) >= 1


class TestSSEPerformance:
    """SSE 性能测试"""
    
    def test_sse_memory_usage(self, test_server, monkeypatch):
        """测试长时间运行的 SSE 连接内存使用"""
        import psutil
        import os
        
        # 记录初始内存
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 模拟长时间运行的状态更新
        update_count = 0
        
        def mock_get_status(dataset_id, doc_id):
            nonlocal update_count
            update_count += 1
            
            # 模拟100次更新
            if update_count < 100:
                return {
                    "id": doc_id,
                    "status": "1",
                    "progress": update_count / 100.0,
                    "progress_msg": f"进度 {update_count}%"
                }
            else:
                return {
                    "id": doc_id,
                    "status": "2",
                    "progress": 1.0,
                    "progress_msg": "完成"
                }
        
        monkeypatch.setattr(ragflow_client, "get_document_status", mock_get_status)
        
        # 发起长时间 SSE 连接
        url = f"{test_server}/api/v1/datasets/test_dataset/documents/long_doc/status/stream"
        
        event_count = 0
        with requests.get(url, stream=True, headers={"Accept": "text/event-stream"}) as response:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        event_count += 1
                        
                        # 收到完成事件后停止
                        data = json.loads(line_str[6:])
                        if data.get("type") == "complete":
                            break
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 验证事件数量
        assert event_count >= 100  # 应该收到足够的事件
        
        # 验证内存增长在合理范围内（小于50MB）
        assert memory_increase < 50, f"内存增长过大: {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])