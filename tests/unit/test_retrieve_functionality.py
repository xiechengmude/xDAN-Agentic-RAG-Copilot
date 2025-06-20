#!/usr/bin/env python3
"""
检索功能单元测试
测试RAGFlow SDK的检索功能和相关方法
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper


class TestRetrieveFunctionality(unittest.TestCase):
    """检索功能的专项测试"""
    
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
    
    # ==================== 基础检索测试 ====================
    
    def test_retrieve_basic_query(self):
        """测试基础查询检索"""
        # Mock chunk数据
        mock_chunk = Mock()
        mock_chunk.id = "chunk1"
        mock_chunk.content = "Python is a programming language"
        mock_chunk.document_id = "doc1"
        mock_chunk.dataset_id = "dataset1"
        mock_chunk.similarity = 0.92
        
        def mock_retrieve(**kwargs):
            yield mock_chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="What is Python?",
            dataset_ids=["dataset1"],
            top_k=5,
            similarity_threshold=0.8
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(len(result['data']['chunks']), 1)
        self.assertEqual(result['data']['chunks'][0]['content'], "Python is a programming language")
        self.assertEqual(result['data']['chunks'][0]['similarity'], 0.92)
    
    def test_retrieve_multiple_chunks(self):
        """测试多个文本块检索"""
        # 创建多个mock chunks
        chunks_data = [
            {
                'id': f'chunk{i}',
                'content': f'Content {i}',
                'document_id': f'doc{i//2}',
                'dataset_id': 'dataset1',
                'similarity': 0.95 - i * 0.05
            }
            for i in range(5)
        ]
        
        mock_chunks = []
        for data in chunks_data:
            chunk = Mock()
            for key, value in data.items():
                setattr(chunk, key, value)
            mock_chunks.append(chunk)
        
        def mock_retrieve(**kwargs):
            for chunk in mock_chunks:
                yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="test query",
            dataset_ids=["dataset1"],
            top_k=10
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(len(result['data']['chunks']), 5)
        self.assertEqual(result['data']['total'], 5)
        
        # 验证相似度排序
        similarities = [chunk['similarity'] for chunk in result['data']['chunks']]
        self.assertEqual(similarities, [0.95, 0.9, 0.85, 0.8, 0.75])
    
    def test_retrieve_with_filters(self):
        """测试带过滤条件的检索"""
        # Mock检索调用
        retrieve_calls = []
        
        def mock_retrieve(**kwargs):
            retrieve_calls.append(kwargs)
            yield Mock(id="chunk1", content="Filtered content", similarity=0.88)
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="filter test",
            dataset_ids=["dataset1", "dataset2"],
            document_ids=["doc1", "doc2"],
            top_k=3,
            similarity_threshold=0.85
        )
        
        # 验证参数传递
        self.assertEqual(len(retrieve_calls), 1)
        call_params = retrieve_calls[0]
        self.assertEqual(call_params['dataset_ids'], ["dataset1", "dataset2"])
        self.assertEqual(call_params['document_ids'], ["doc1", "doc2"])
        self.assertEqual(call_params['top_k'], 3)
        self.assertEqual(call_params['similarity_threshold'], 0.85)
    
    def test_retrieve_empty_result(self):
        """测试空检索结果"""
        def mock_retrieve(**kwargs):
            return
            yield  # 空generator
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="no results query",
            dataset_ids=["empty_dataset"]
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['chunks'], [])
        self.assertEqual(result['data']['total'], 0)
    
    # ==================== 相似度阈值测试 ====================
    
    def test_similarity_threshold_filtering(self):
        """测试相似度阈值过滤"""
        # 创建不同相似度的chunks
        chunks_data = [
            {'similarity': 0.95, 'content': 'High similarity'},
            {'similarity': 0.85, 'content': 'Medium similarity'},
            {'similarity': 0.75, 'content': 'Low similarity'},
            {'similarity': 0.65, 'content': 'Very low similarity'}
        ]
        
        mock_chunks = []
        for i, data in enumerate(chunks_data):
            chunk = Mock()
            chunk.id = f'chunk{i}'
            chunk.content = data['content']
            chunk.similarity = data['similarity']
            chunk.document_id = f'doc{i}'
            chunk.dataset_id = 'dataset1'
            mock_chunks.append(chunk)
        
        # SDK应该在内部处理阈值过滤
        def mock_retrieve(**kwargs):
            threshold = kwargs.get('similarity_threshold', 0.0)
            for chunk in mock_chunks:
                if chunk.similarity >= threshold:
                    yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        # 测试不同阈值
        test_cases = [
            (0.9, 1),   # 只有一个chunk满足
            (0.8, 2),   # 两个chunks满足
            (0.7, 3),   # 三个chunks满足
            (0.6, 4),   # 所有chunks满足
        ]
        
        for threshold, expected_count in test_cases:
            result = self.wrapper.retrieve_chunks(
                question="threshold test",
                dataset_ids=["dataset1"],
                similarity_threshold=threshold
            )
            
            self.assertEqual(len(result['data']['chunks']), expected_count,
                           f"Failed for threshold {threshold}")
    
    # ==================== 多数据集检索测试 ====================
    
    def test_retrieve_from_multiple_datasets(self):
        """测试从多个数据集检索"""
        # 创建来自不同数据集的chunks
        datasets = ['dataset1', 'dataset2', 'dataset3']
        mock_chunks = []
        
        for i, dataset_id in enumerate(datasets):
            for j in range(2):  # 每个数据集2个chunks
                chunk = Mock()
                chunk.id = f'{dataset_id}_chunk{j}'
                chunk.content = f'Content from {dataset_id}'
                chunk.dataset_id = dataset_id
                chunk.document_id = f'{dataset_id}_doc{j}'
                chunk.similarity = 0.9 - (i * 0.1 + j * 0.05)
                mock_chunks.append(chunk)
        
        def mock_retrieve(**kwargs):
            requested_datasets = kwargs.get('dataset_ids', [])
            for chunk in mock_chunks:
                if chunk.dataset_id in requested_datasets:
                    yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        # 测试从特定数据集检索
        result = self.wrapper.retrieve_chunks(
            question="multi dataset test",
            dataset_ids=['dataset1', 'dataset3'],
            top_k=10
        )
        
        self.assertEqual(result['code'], 0)
        chunks = result['data']['chunks']
        
        # 验证只返回了指定数据集的chunks
        dataset_ids = set(chunk['dataset_id'] for chunk in chunks)
        self.assertEqual(dataset_ids, {'dataset1', 'dataset3'})
        self.assertEqual(len(chunks), 4)  # 每个数据集2个，共4个
    
    # ==================== 错误处理测试 ====================
    
    def test_retrieve_api_error(self):
        """测试API错误处理"""
        self.mock_ragflow_instance.retrieve.side_effect = Exception("API connection failed")
        
        result = self.wrapper.retrieve_chunks(
            question="error test",
            dataset_ids=["dataset1"]
        )
        
        self.assertEqual(result['code'], 500)
        self.assertIn("API connection failed", result['message'])
    
    def test_retrieve_with_invalid_params(self):
        """测试无效参数处理"""
        # 测试空问题
        result = self.wrapper.retrieve_chunks(
            question="",
            dataset_ids=["dataset1"]
        )
        
        # SDK应该处理空查询
        self.assertIn('code', result)
    
    # ==================== 特殊字符和编码测试 ====================
    
    def test_retrieve_with_special_characters(self):
        """测试包含特殊字符的检索"""
        special_content = "Python's \"hello world\" example: print('Hello, 世界!')"
        
        mock_chunk = Mock()
        mock_chunk.id = "special_chunk"
        mock_chunk.content = special_content
        mock_chunk.document_id = "doc1"
        mock_chunk.dataset_id = "dataset1"
        mock_chunk.similarity = 0.95
        
        def mock_retrieve(**kwargs):
            yield mock_chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="Python hello world 示例",
            dataset_ids=["dataset1"]
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data']['chunks'][0]['content'], special_content)
    
    # ==================== 分页和限制测试 ====================
    
    def test_retrieve_with_top_k_limit(self):
        """测试top_k限制"""
        # 创建10个chunks
        mock_chunks = []
        for i in range(10):
            chunk = Mock()
            chunk.id = f'chunk{i}'
            chunk.content = f'Content {i}'
            chunk.similarity = 0.99 - i * 0.01
            chunk.document_id = f'doc{i}'
            chunk.dataset_id = 'dataset1'
            mock_chunks.append(chunk)
        
        def mock_retrieve(**kwargs):
            top_k = kwargs.get('top_k', 5)
            for i, chunk in enumerate(mock_chunks):
                if i < top_k:
                    yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        # 测试不同的top_k值
        for top_k in [1, 3, 5, 20]:
            result = self.wrapper.retrieve_chunks(
                question="top k test",
                dataset_ids=["dataset1"],
                top_k=top_k
            )
            
            expected_count = min(top_k, 10)  # 最多10个chunks
            self.assertEqual(len(result['data']['chunks']), expected_count,
                           f"Failed for top_k={top_k}")
    
    # ==================== 性能相关测试 ====================
    
    def test_retrieve_large_result_set(self):
        """测试大量结果的检索"""
        # 创建100个chunks
        def mock_retrieve(**kwargs):
            for i in range(100):
                chunk = Mock()
                chunk.id = f'chunk{i}'
                chunk.content = f'Large dataset content {i}' * 10  # 较长的内容
                chunk.similarity = 0.99 - (i * 0.001)
                chunk.document_id = f'doc{i//10}'
                chunk.dataset_id = 'large_dataset'
                yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        result = self.wrapper.retrieve_chunks(
            question="large dataset test",
            dataset_ids=["large_dataset"],
            top_k=100
        )
        
        self.assertEqual(result['code'], 0)
        self.assertEqual(len(result['data']['chunks']), 100)
        self.assertEqual(result['data']['total'], 100)
    
    # ==================== 文档级别检索测试 ====================
    
    def test_retrieve_specific_documents(self):
        """测试特定文档的检索"""
        # 创建来自不同文档的chunks
        documents = ['doc1', 'doc2', 'doc3']
        mock_chunks = []
        
        for doc_id in documents:
            for i in range(3):  # 每个文档3个chunks
                chunk = Mock()
                chunk.id = f'{doc_id}_chunk{i}'
                chunk.content = f'Content from {doc_id} part {i}'
                chunk.document_id = doc_id
                chunk.dataset_id = 'dataset1'
                chunk.similarity = 0.9 - (i * 0.05)
                mock_chunks.append(chunk)
        
        def mock_retrieve(**kwargs):
            requested_docs = kwargs.get('document_ids', [])
            for chunk in mock_chunks:
                if not requested_docs or chunk.document_id in requested_docs:
                    yield chunk
        
        self.mock_ragflow_instance.retrieve = mock_retrieve
        
        # 测试检索特定文档
        result = self.wrapper.retrieve_chunks(
            question="document specific test",
            dataset_ids=["dataset1"],
            document_ids=["doc1", "doc3"]
        )
        
        chunks = result['data']['chunks']
        doc_ids = set(chunk['document_id'] for chunk in chunks)
        self.assertEqual(doc_ids, {'doc1', 'doc3'})
        self.assertEqual(len(chunks), 6)  # 2个文档，每个3个chunks


if __name__ == '__main__':
    unittest.main()