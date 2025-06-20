#!/usr/bin/env python3
"""
测试配置文件
定义测试环境和配置
"""

import os
from typing import Dict, Any

# ==================== 测试环境配置 ====================

TEST_ENV = os.getenv('TEST_ENV', 'test')

# 测试环境变量
TEST_ENV_VARS = {
    'test': {
        'RAGFLOW_API_URL': 'http://test.ragflow.com:7080',
        'RAGFLOW_API_KEY': 'test-api-key',
        'LLM_API_URL': 'http://test.llm.com/v1',
        'LLM_MODEL_NAME': 'test-model',
        'DEFAULT_DATASET_ID': 'test-dataset-id'
    },
    'integration': {
        'RAGFLOW_API_URL': 'http://staging.ragflow.com:7080',
        'RAGFLOW_API_KEY': 'staging-api-key',
        'LLM_API_URL': 'http://staging.llm.com/v1',
        'LLM_MODEL_NAME': 'staging-model',
        'DEFAULT_DATASET_ID': 'staging-dataset-id'
    }
}

# ==================== 测试参数配置 ====================

# S3框架测试参数
S3_TEST_PARAMS = {
    'max_search_rounds': 3,
    'top_k': 5,
    'similarity_threshold': 0.8,
    'temperature': 0.7,
    'max_tokens': 1000
}

# Agent测试参数
AGENT_TEST_PARAMS = {
    'test_agent_id': 'test-agent-001',
    'test_agent_name': 'Test Agent',
    'test_session_id': 'test-session-001',
    'test_user_id': 'test-user-001'
}

# 检索测试参数
RETRIEVE_TEST_PARAMS = {
    'test_questions': [
        'What is Python?',
        'Explain machine learning',
        'How does deep learning work?',
        'What are Python decorators?'
    ],
    'test_dataset_ids': ['dataset1', 'dataset2'],
    'test_document_ids': ['doc1', 'doc2', 'doc3']
}

# ==================== Mock数据配置 ====================

# Mock响应延迟（毫秒）
MOCK_RESPONSE_DELAYS = {
    'retrieve': 100,
    'llm_completion': 200,
    'agent_response': 150,
    'session_create': 50
}

# Mock错误率（0-1之间的概率）
MOCK_ERROR_RATES = {
    'retrieve': 0.0,  # 检索错误率
    'llm_completion': 0.0,  # LLM完成错误率
    'agent_response': 0.0,  # Agent响应错误率
    'session_create': 0.0  # Session创建错误率
}

# ==================== 测试超时配置 ====================

TEST_TIMEOUTS = {
    'unit_test': 5,  # 单元测试超时（秒）
    'integration_test': 30,  # 集成测试超时（秒）
    'api_call': 10,  # API调用超时（秒）
    'llm_response': 20  # LLM响应超时（秒）
}

# ==================== 测试数据路径 ====================

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# ==================== 测试标记配置 ====================

TEST_MARKERS = {
    'slow': 'marks test as slow running',
    'integration': 'marks test as integration test',
    'unit': 'marks test as unit test',
    'requires_sdk': 'marks test as requiring ragflow_sdk',
    'requires_llm': 'marks test as requiring LLM service',
    'skip_ci': 'marks test to skip in CI environment'
}

# ==================== 辅助函数 ====================

def get_test_env_vars() -> Dict[str, str]:
    """获取当前测试环境的环境变量"""
    return TEST_ENV_VARS.get(TEST_ENV, TEST_ENV_VARS['test'])


def should_mock_external_services() -> bool:
    """判断是否应该mock外部服务"""
    return TEST_ENV == 'test'


def get_mock_delay(service: str) -> int:
    """获取mock服务的响应延迟"""
    return MOCK_RESPONSE_DELAYS.get(service, 0)


def get_error_rate(service: str) -> float:
    """获取mock服务的错误率"""
    return MOCK_ERROR_RATES.get(service, 0.0)


# ==================== 测试验证配置 ====================

VALIDATION_RULES = {
    'chunk_content_min_length': 10,
    'chunk_content_max_length': 5000,
    'similarity_min': 0.0,
    'similarity_max': 1.0,
    'agent_name_max_length': 100,
    'session_id_pattern': r'^[a-zA-Z0-9-_]+$',
    'dataset_id_pattern': r'^[a-f0-9]{32}$'
}

# ==================== 性能基准配置 ====================

PERFORMANCE_BENCHMARKS = {
    'retrieve_chunks': {
        'max_time_ms': 500,
        'max_memory_mb': 100
    },
    's3_search_process': {
        'max_time_ms': 3000,
        'max_memory_mb': 200
    },
    'agent_conversation': {
        'max_time_ms': 5000,
        'max_memory_mb': 300
    }
}