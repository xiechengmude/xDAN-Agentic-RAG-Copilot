#!/usr/bin/env python3
"""
pytest配置文件
提供测试fixtures和通用配置
适配重构后的新架构
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# ==================== Mock数据 ====================

@pytest.fixture
def mock_chunks():
    """提供mock的检索chunks数据"""
    return [
        {
            'id': 'chunk1',
            'content': 'Python is a high-level, interpreted programming language.',
            'document_id': 'doc1',
            'dataset_id': 'dataset1',
            'similarity': 0.95,
            'metadata': {
                'source': 'python_tutorial.pdf',
                'page': 1
            }
        },
        {
            'id': 'chunk2',
            'content': 'Python emphasizes code readability and uses significant whitespace.',
            'document_id': 'doc1',
            'dataset_id': 'dataset1',
            'similarity': 0.92,
            'metadata': {
                'source': 'python_tutorial.pdf',
                'page': 2
            }
        },
        {
            'id': 'chunk3',
            'content': 'Python supports multiple programming paradigms including procedural, object-oriented, and functional.',
            'document_id': 'doc2',
            'dataset_id': 'dataset1',
            'similarity': 0.88,
            'metadata': {
                'source': 'python_features.pdf',
                'page': 5
            }
        }
    ]


@pytest.fixture
def mock_datasets():
    """提供mock的数据集数据"""
    return [
        {
            'id': 'dataset1',
            'name': 'Python Documentation',
            'description': 'Official Python programming documentation',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-15T00:00:00Z',
            'document_count': 150,
            'chunk_count': 3000
        },
        {
            'id': 'dataset2',
            'name': 'Machine Learning Papers',
            'description': 'Collection of ML research papers',
            'created_at': '2024-01-10T00:00:00Z',
            'updated_at': '2024-01-20T00:00:00Z',
            'document_count': 500,
            'chunk_count': 15000
        }
    ]


@pytest.fixture
def mock_agents():
    """提供mock的Agent数据"""
    return [
        {
            'id': 'agent1',
            'name': 'Python Expert',
            'description': 'Agent specialized in Python programming questions',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-10T00:00:00Z',
            'model': 'gpt-4',
            'system_prompt': 'You are a Python programming expert.'
        },
        {
            'id': 'agent2',
            'name': 'ML Assistant',
            'description': 'Agent for machine learning topics',
            'created_at': '2024-01-05T00:00:00Z',
            'updated_at': '2024-01-15T00:00:00Z',
            'model': 'claude-3',
            'system_prompt': 'You are a machine learning specialist.'
        }
    ]


@pytest.fixture
def mock_sessions():
    """提供mock的Session数据"""
    return [
        {
            'id': 'session1',
            'agent_id': 'agent1',
            'user_id': 'user123',
            'created_at': '2024-01-20T10:00:00Z',
            'updated_at': '2024-01-20T10:30:00Z',
            'message_count': 5,
            'status': 'active'
        },
        {
            'id': 'session2',
            'agent_id': 'agent2',
            'user_id': 'user456',
            'created_at': '2024-01-20T11:00:00Z',
            'updated_at': '2024-01-20T11:15:00Z',
            'message_count': 3,
            'status': 'active'
        }
    ]


# ==================== Mock服务 ====================

@pytest.fixture
def mock_litellm_client():
    """提供mock的LiteLLMSDKClientV2实例"""
    mock_client = AsyncMock()
    
    # 默认聊天完成响应
    mock_client.chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": "Mock LLM response"
            }
        }]
    }
    
    # 流式响应
    async def mock_stream():
        yield {"choices": [{"delta": {"content": "Part 1"}}]}
        yield {"choices": [{"delta": {"content": "Part 2"}}]}
        yield {"choices": [{"delta": {"content": "Part 3"}}]}
    
    mock_client.chat_completion_stream = mock_stream
    
    return mock_client


@pytest.fixture
def mock_llm_client():
    """提供mock的LLMClient实例"""
    mock_llm = Mock()
    
    # 默认返回值
    mock_llm.chat_completion.return_value = "Mock LLM response"
    
    # 流式响应
    def mock_stream():
        yield "Part 1"
        yield "Part 2"
        yield "Part 3"
    
    mock_llm.chat_completion_stream = mock_stream
    
    return mock_llm


@pytest.fixture
def mock_ragflow_client():
    """提供mock的RAGFlowClient实例（HTTP模式）"""
    mock_client = Mock()
    
    # 设置默认返回值
    mock_client.list_datasets.return_value = {
        'code': 0,
        'data': []
    }
    
    mock_client.retrieve_chunks.return_value = {
        'code': 0,
        'data': {
            'chunks': [],
            'total': 0
        }
    }
    
    mock_client.create_dataset.return_value = {
        'code': 0,
        'data': {
            'id': 'new_dataset',
            'name': 'Test Dataset'
        }
    }
    
    return mock_client


# ==================== 测试环境配置 ====================

@pytest.fixture
def test_env_vars(monkeypatch):
    """设置测试环境变量"""
    env_vars = {
        'RAGFLOW_API_URL': 'http://test.ragflow.com:7080',
        'RAGFLOW_API_KEY': 'test-api-key-123',
        'LLM_API_URL': 'http://test.llm.com/v1',
        'LLM_MODEL_NAME': 'test-model',
        'DEFAULT_DATASET_ID': 'test-dataset-id'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def s3_system_prompt():
    """提供S3系统提示词"""
    return """You are a search copilot for the generation model. Based on a user's query and initial searched results, you will first determine if the searched results are enough to produce an answer.

If the searched results are enough, you will use <search_complete>True</search_complete> to indicate that you have gathered enough information for the generation model to produce an answer.

If the searched results are not enough, you will go through a loop of <query> -> <information> -> <important_info> -> <search_complete> -> <query> (if not complete) ..., to help the generation model to generate a better answer with more relevant information searched.

You should show the search query between <query> and </query> in JSON format.
Based on the search query, we will return the top searched results between <information> and </information>. You need to put the doc ids of the important documents (up to 3 documents, within the current information window) between <important_info> and </important_info> (e.g., <important_info>[1, 4]</important_info>).

A search query MUST be followed by a <search_complete> tag if the search is not complete.
After reviewing the information, you must decide whether to continue searching with a new query or indicate that the search is complete. If you need more information, use <search_complete>False</search_complete> to indicate you want to continue searching with a better query. Otherwise, use <search_complete>True</search_complete> to terminate the search.

During the process, you can add reasoning process within <think></think> tag whenever you want. Note: Only the important information would be used for the generation model to produce an answer."""


# ==================== 测试辅助函数 ====================

@pytest.fixture
def create_mock_agent_response():
    """创建mock的Agent响应生成器"""
    def _create_response(think_content="", query=None, important_docs=None, search_complete=True):
        response_parts = []
        
        if think_content:
            response_parts.append(f"<think>{think_content}</think>")
        
        if query:
            response_parts.append(f'<query>{{"question": "{query}"}}</query>')
        
        if important_docs:
            docs_str = ", ".join(str(d) for d in important_docs)
            response_parts.append(f"<important_info>[{docs_str}]</important_info>")
        
        response_parts.append(f"<search_complete>{str(search_complete)}</search_complete>")
        
        return "\n".join(response_parts)
    
    return _create_response


@pytest.fixture
def create_mock_chunk():
    """创建mock chunk的工厂函数"""
    def _create_chunk(chunk_id, content, similarity=0.9, doc_id="doc1", dataset_id="dataset1"):
        return {
            'id': chunk_id,
            'content': content,
            'document_id': doc_id,
            'dataset_id': dataset_id,
            'similarity': similarity,
            'metadata': {
                'source': f'{doc_id}.pdf',
                'page': 1
            }
        }
    
    return _create_chunk


# ==================== pytest配置 ====================

def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """自动为测试添加标记"""
    for item in items:
        # 根据文件路径自动添加标记
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

# ==================== 新架构相关Fixtures ====================

@pytest.fixture
def mock_s3_framework():
    """提供mock的S3Framework实例"""
    from src.core.s3_framework import S3FrameworkAgent
    mock_framework = Mock(spec=S3FrameworkAgent)
    
    # Mock执行工作流
    async def mock_workflow(*args, **kwargs):
        yield {
            "workflow_info": {
                "search_rounds": 1,
                "selected_documents": [],
                "search_process": []
            },
            "final_answer": "Mock answer from S3 framework"
        }
    
    mock_framework.execute_s3_workflow = mock_workflow
    return mock_framework

@pytest.fixture
def mock_s3_service():
    """提供mock的S3Service实例"""
    from src.services.s3_service import S3Service
    mock_service = Mock(spec=S3Service)
    
    # Mock ask方法
    async def mock_ask(*args, **kwargs):
        yield {"final_answer": "Mock answer from S3 service"}
    
    mock_service.ask = mock_ask
    mock_service.health_check = AsyncMock(return_value={
        "ragflow": True,
        "litellm": True,
        "s3_framework": True
    })
    
    return mock_service

@pytest.fixture
def test_s3_config():
    """测试用S3配置"""
    return {
        'ragflow_api_url': 'http://test.ragflow.api',
        'ragflow_api_key': 'test_key',
        'default_dataset_id': 'test_dataset'
    }