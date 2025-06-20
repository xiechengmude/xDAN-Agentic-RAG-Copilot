#!/usr/bin/env python3
"""
RAGFlowSDKWrapper 单元测试
测试官方SDK封装功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper


class TestRAGFlowSDKWrapper(unittest.TestCase):
    """RAGFlowSDKWrapper的单元测试"""
    
    def setUp(self):
        """测试初始化"""
        self.api_url = "http://test.api.com:7080"
        self.api_key = "test-api-key"
        
        # Mock RAGFlow SDK
        self.mock_ragflow_patcher = patch('ragflow_sdk_wrapper.RAGFlow')
        self.mock_ragflow_class = self.mock_ragflow_patcher.start()
        self.mock_ragflow_instance = Mock()
        self.mock_ragflow_class.return_value = self.mock_ragflow_instance
        
        # 设置SDK可用
        with patch('ragflow_sdk_wrapper.SDK_AVAILABLE', True):
            self.wrapper = RAGFlowSDKWrapper(api_url=self.api_url, api_key=self.api_key)
    
    def tearDown(self):
        """清理测试"""
        self.mock_ragflow_patcher.stop()
    
    # ==================== 初始化测试 ====================
    
    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""
        # 验证SDK初始化参数
        expected_base_url = "http://test.api.com:9380"  # 7080 -> 9380
        self.mock_ragflow_class.assert_called_with(
            api_key=self.api_key,
            base_url=expected_base_url
        )
    
    def test_init_with_env_vars(self):
        """测试使用环境变量初始化"""
        with patch.dict(os.environ, {
            'RAGFLOW_API_URL': 'http://env.api.com:7080',
            'RAGFLOW_API_KEY': 'env-api-key'
        }):
            with patch('ragflow_sdk_wrapper.RAGFlow') as mock_ragflow:
                with patch('ragflow_sdk_wrapper.SDK_AVAILABLE', True):
                    wrapper = RAGFlowSDKWrapper()
                    mock_ragflow.assert_called_with(
                        api_key='env-api-key',
                        base_url='http://env.api.com:9380'
                    )
    
    def test_init_without_sdk(self):
        """测试SDK不可用时的初始化"""
        with patch('ragflow_sdk_wrapper.SDK_AVAILABLE', False):
            with self.assertRaises(ImportError):
                RAGFlowSDKWrapper(api_url=self.api_url, api_key=self.api_key)
    
    # ==================== 数据集管理测试 ====================
    
    def test_list_datasets_success(self):
        """测试成功列出数据集"""
        # Mock数据集对象
        mock_dataset1 = Mock()
        mock_dataset1.id = "dataset1"
        mock_dataset1.name = "Dataset 1"
        mock_dataset1.description = "Test dataset 1"
        mock_dataset1.created_at = "2024-01-01"
        mock_dataset1.updated_at = "2024-01-02"
        
        mock_dataset2 = Mock()
        mock_dataset2.id = "dataset2"
        mock_dataset2.name = "Dataset 2"
        mock_dataset2.description = "Test dataset 2"
        mock_dataset2.created_at = "2024-01-03"
        mock_dataset2.updated_at = "2024-01-04"
        
        self.mock_ragflow_instance.list_datasets.return_value = [mock_dataset1, mock_dataset2]
        
        result = self.wrapper.list_datasets(page=1, page_size=10)
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(len(result['data']), 2)
        self.assertEqual(result['data'][0]['id'], "dataset1")
        self.assertEqual(result['data'][1]['name'], "Dataset 2")
    
    def test_list_datasets_empty(self):
        """测试列出空数据集"""
        self.mock_ragflow_instance.list_datasets.return_value = []
        
        result = self.wrapper.list_datasets()
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data'], [])
    
    def test_list_datasets_error(self):
        """测试列出数据集时出错"""
        self.mock_ragflow_instance.list_datasets.side_effect = Exception("API Error")
        
        result = self.wrapper.list_datasets()
        
        self.assertEqual(result['code'], 500)
        self.assertIn("API Error", result['message'])
    
    def test_create_dataset_success(self):
        """测试成功创建数据集"""
        mock_dataset = Mock()
        mock_dataset.id = "new_dataset"
        mock_dataset.name = "New Dataset"
        mock_dataset.description = "Created dataset"
        mock_dataset.created_at = "2024-01-05"
        mock_dataset.updated_at = "2024-01-05"
        
        self.mock_ragflow_instance.create_dataset.return_value = mock_dataset
        
        result = self.wrapper.create_dataset(name="New Dataset", description="Created dataset")
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['id'], "new_dataset")
        self.assertEqual(result['data']['name'], "New Dataset")
    
    def test_delete_datasets_by_ids(self):
        """测试按ID删除数据集"""
        self.mock_ragflow_instance.delete_dataset.return_value = None
        
        result = self.wrapper.delete_datasets(ids=["dataset1", "dataset2"])
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(self.mock_ragflow_instance.delete_dataset.call_count, 2)
    
    def test_delete_all_datasets(self):
        """测试删除所有数据集"""
        mock_dataset = Mock()
        mock_dataset.delete.return_value = None
        self.mock_ragflow_instance.list_datasets.return_value = [mock_dataset, mock_dataset]
        
        result = self.wrapper.delete_datasets()
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(mock_dataset.delete.call_count, 2)
    
    # ==================== 检索功能测试 ====================
    
    def test_retrieve_chunks_success(self):
        """测试成功检索文本块"""
        # Mock chunk对象
        mock_chunk1 = Mock()
        mock_chunk1.id = "chunk1"
        mock_chunk1.content = "Test content 1"
        mock_chunk1.document_id = "doc1"
        mock_chunk1.dataset_id = "dataset1"
        mock_chunk1.similarity = 0.95
        
        mock_chunk2 = Mock()
        mock_chunk2.id = "chunk2"
        mock_chunk2.content = "Test content 2"
        mock_chunk2.document_id = "doc2"
        mock_chunk2.dataset_id = "dataset1"
        mock_chunk2.similarity = 0.85
        
        # 使用generator模拟retrieve返回
        def mock_retrieve(**kwargs):
            yield mock_chunk1
            yield mock_chunk2
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="test query",
            dataset_ids=["dataset1"],
            top_k=5,
            similarity_threshold=0.8
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(len(result['data']['chunks']), 2)
        self.assertEqual(result['data']['chunks'][0]['content'], "Test content 1")
        self.assertEqual(result['data']['chunks'][1]['similarity'], 0.85)
    
    def test_retrieve_chunks_empty(self):
        """测试检索结果为空"""
        def mock_retrieve(**kwargs):
            return
            yield  # 空generator
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(question="test query")
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['chunks'], [])
        self.assertEqual(result['data']['total'], 0)
    
    # ==================== Agent管理测试 ====================
    
    def test_list_agents_success(self):
        """测试成功列出Agent"""
        mock_agent1 = Mock()
        mock_agent1.id = "agent1"
        mock_agent1.name = "Agent 1"
        mock_agent1.description = "Test agent 1"
        mock_agent1.created_at = "2024-01-01"
        mock_agent1.updated_at = "2024-01-02"
        
        self.mock_ragflow_instance.list_agents.return_value = [mock_agent1]
        
        result = self.wrapper.list_agents()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], "agent1")
        self.assertEqual(result[0]['name'], "Agent 1")
    
    def test_get_agent_success(self):
        """测试成功获取指定Agent"""
        mock_agent = Mock()
        mock_agent.id = "agent1"
        mock_agent.name = "Test Agent"
        mock_agent.description = "Test description"
        mock_agent.created_at = "2024-01-01"
        mock_agent.updated_at = "2024-01-02"
        
        self.mock_ragflow_instance.list_agents.return_value = [mock_agent]
        
        result = self.wrapper.get_agent("agent1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], "agent1")
        self.assertEqual(result['name'], "Test Agent")
    
    def test_get_agent_not_found(self):
        """测试获取不存在的Agent"""
        self.mock_ragflow_instance.list_agents.return_value = []
        
        result = self.wrapper.get_agent("nonexistent")
        
        self.assertIsNone(result)
    
    def test_create_agent_success(self):
        """测试成功创建Agent"""
        mock_agent = Mock()
        mock_agent.id = "new_agent"
        mock_agent.name = "New Agent"
        mock_agent.description = "Created agent"
        mock_agent.created_at = "2024-01-05"
        mock_agent.updated_at = "2024-01-05"
        
        self.mock_ragflow_instance.create_agent.return_value = mock_agent
        
        result = self.wrapper.create_agent(name="New Agent", description="Created agent")
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['id'], "new_agent")
        self.assertEqual(result['data']['name'], "New Agent")
    
    # ==================== Session管理测试 ====================
    
    def test_create_session_success(self):
        """测试成功创建Session"""
        mock_agent = Mock()
        mock_session = Mock()
        mock_session.id = "session1"
        mock_session.created_at = "2024-01-05"
        
        mock_agent.create_session.return_value = mock_session
        self.mock_ragflow_instance.list_agents.return_value = [mock_agent]
        
        result = self.wrapper.create_session("agent1")
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['session_id'], "session1")
        self.assertEqual(result['data']['agent_id'], "agent1")
    
    def test_create_session_agent_not_found(self):
        """测试为不存在的Agent创建Session"""
        self.mock_ragflow_instance.list_agents.return_value = []
        
        result = self.wrapper.create_session("nonexistent")
        
        self.assertEqual(result['code'], 404)
        self.assertIn("not found", result['message'])
    
    def test_session_ask_success(self):
        """测试成功进行Session对话"""
        mock_agent = Mock()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.content = "This is the answer"
        
        mock_session.ask.return_value = mock_response
        mock_agent.create_session.return_value = mock_session
        self.mock_ragflow_instance.list_agents.return_value = [mock_agent]
        
        result = self.wrapper.session_ask("agent1", "What is the question?", stream=False)
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['content'], "This is the answer")
    
    def test_session_ask_stream(self):
        """测试流式Session对话"""
        mock_agent = Mock()
        mock_session = Mock()
        
        # Mock流式响应
        def mock_stream_response():
            yield Mock(content="Part 1")
            yield Mock(content="Part 2")
        
        mock_session.ask.return_value = mock_stream_response()
        mock_agent.create_session.return_value = mock_session
        self.mock_ragflow_instance.list_agents.return_value = [mock_agent]
        
        result_gen = self.wrapper.session_ask("agent1", "Question?", stream=True)
        results = list(result_gen)
        
        self.assertEqual(len(results), 2)
    
    # ==================== 辅助方法测试 ====================
    
    def test_dataset_to_dict(self):
        """测试Dataset对象转字典"""
        mock_dataset = Mock()
        mock_dataset.id = "test_id"
        mock_dataset.name = "Test Name"
        mock_dataset.description = "Test Description"
        mock_dataset.created_at = "2024-01-01"
        mock_dataset.updated_at = "2024-01-02"
        
        result = self.wrapper._dataset_to_dict(mock_dataset)
        
        self.assertEqual(result['id'], "test_id")
        self.assertEqual(result['name'], "Test Name")
        self.assertEqual(result['description'], "Test Description")
    
    def test_agent_to_dict(self):
        """测试Agent对象转字典"""
        mock_agent = Mock()
        mock_agent.id = "agent_id"
        mock_agent.name = "Agent Name"
        mock_agent.description = "Agent Description"
        mock_agent.created_at = "2024-01-01"
        mock_agent.updated_at = "2024-01-02"
        
        result = self.wrapper._agent_to_dict(mock_agent)
        
        self.assertEqual(result['id'], "agent_id")
        self.assertEqual(result['name'], "Agent Name")
        self.assertEqual(result['description'], "Agent Description")
    
    def test_chunk_to_dict(self):
        """测试Chunk对象转字典"""
        mock_chunk = Mock()
        mock_chunk.id = "chunk_id"
        mock_chunk.content = "Chunk content"
        mock_chunk.document_id = "doc_id"
        mock_chunk.dataset_id = "dataset_id"
        mock_chunk.similarity = 0.95
        
        result = self.wrapper._chunk_to_dict(mock_chunk)
        
        self.assertEqual(result['id'], "chunk_id")
        self.assertEqual(result['content'], "Chunk content")
        self.assertEqual(result['similarity'], 0.95)
    
    def test_get_rag_flow_instance(self):
        """测试获取原始RAGFlow实例"""
        instance = self.wrapper.get_rag_flow_instance()
        self.assertEqual(instance, self.mock_ragflow_instance)


if __name__ == '__main__':
    unittest.main()