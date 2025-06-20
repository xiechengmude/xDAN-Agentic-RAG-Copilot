#!/usr/bin/env python3
"""
Enhanced S3 RAG Service 单元测试
测试增强版S3服务的Agent和Session功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.enhanced_s3_rag_service import EnhancedS3RAGService, EnhancedS3RAGRequest, EnhancedS3RAGResponse


class TestEnhancedS3RAGService(unittest.TestCase):
    """EnhancedS3RAGService的单元测试"""
    
    def setUp(self):
        """测试初始化"""
        # Mock RAGFlow客户端（SDK模式）
        self.mock_ragflow_client = Mock()
        self.mock_ragflow_client.__class__.__name__ = 'RAGFlowSDKWrapper'
        
        # Mock LLM客户端
        self.mock_llm_client = Mock()
        
        # 创建服务实例
        self.service = EnhancedS3RAGService(self.mock_ragflow_client, self.mock_llm_client)
        
        # 设置为SDK模式
        self.service.is_sdk_mode = True
    
    # ==================== S3框架核心方法测试 ====================
    
    def test_format_search_results(self):
        """测试搜索结果格式化"""
        chunks = [
            {
                'content': 'This is content 1',
                'document_id': 'doc1',
                'dataset_id': 'dataset1',
                'similarity': 0.95
            },
            {
                'content': 'This is content 2',
                'document_id': 'doc2',
                'dataset_id': 'dataset1',
                'similarity': 0.85
            }
        ]
        
        formatted_text, doc_mapping = self.service.format_search_results(chunks)
        
        # 验证格式化文本
        self.assertIn("Document 1:", formatted_text)
        self.assertIn("Content: This is content 1", formatted_text)
        self.assertIn("Similarity: 0.95", formatted_text)
        
        # 验证文档映射
        self.assertEqual(len(doc_mapping), 2)
        self.assertEqual(doc_mapping[1]['content'], 'This is content 1')
        self.assertEqual(doc_mapping[2]['similarity'], 0.85)
    
    def test_format_search_results_empty(self):
        """测试空搜索结果格式化"""
        formatted_text, doc_mapping = self.service.format_search_results([])
        
        self.assertEqual(formatted_text, "No relevant documents found.")
        self.assertEqual(doc_mapping, {})
    
    def test_extract_search_query_json(self):
        """测试从Agent响应中提取JSON格式搜索查询"""
        agent_response = """
        <think>I need more information about Python</think>
        <query>{"question": "Python programming basics"}</query>
        <search_complete>False</search_complete>
        """
        
        query = self.service.extract_search_query(agent_response)
        self.assertEqual(query, "Python programming basics")
    
    def test_extract_search_query_plain(self):
        """测试从Agent响应中提取纯文本搜索查询"""
        agent_response = """
        <query>What is machine learning?</query>
        """
        
        query = self.service.extract_search_query(agent_response)
        self.assertEqual(query, "What is machine learning?")
    
    def test_extract_search_query_none(self):
        """测试无查询时的提取"""
        agent_response = "No query here"
        
        query = self.service.extract_search_query(agent_response)
        self.assertIsNone(query)
    
    def test_extract_important_docs(self):
        """测试提取重要文档ID"""
        agent_response = """
        <think>Documents 1 and 3 are most relevant</think>
        <important_info>[1, 3, 5]</important_info>
        """
        
        doc_ids = self.service.extract_important_docs(agent_response)
        self.assertEqual(doc_ids, [1, 3, 5])
    
    def test_extract_important_docs_empty(self):
        """测试提取空的重要文档ID"""
        agent_response = "<important_info>[]</important_info>"
        
        doc_ids = self.service.extract_important_docs(agent_response)
        self.assertEqual(doc_ids, [])
    
    def test_is_search_complete_true(self):
        """测试搜索完成判断 - True"""
        agent_response = "<search_complete>True</search_complete>"
        
        self.assertTrue(self.service.is_search_complete(agent_response))
    
    def test_is_search_complete_false(self):
        """测试搜索完成判断 - False"""
        agent_response = "<search_complete>False</search_complete>"
        
        self.assertFalse(self.service.is_search_complete(agent_response))
    
    # ==================== 增强搜索方法测试 ====================
    
    def test_search_step_sdk_success(self):
        """测试SDK模式下的搜索步骤成功"""
        self.mock_ragflow_client.retrieve_chunks.return_value = {
            'code': 0,
            'data': {
                'chunks': [
                    {'content': 'Test content', 'similarity': 0.9}
                ]
            }
        }
        
        chunks, success = self.service.search_step(
            "test query",
            ["dataset1"],
            top_k=5,
            similarity_threshold=0.8
        )
        
        self.assertTrue(success)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['content'], 'Test content')
    
    def test_search_step_sdk_failure(self):
        """测试SDK模式下的搜索步骤失败"""
        self.mock_ragflow_client.retrieve_chunks.return_value = {
            'code': 500,
            'message': 'API Error'
        }
        
        chunks, success = self.service.search_step("test query", ["dataset1"])
        
        self.assertFalse(success)
        self.assertEqual(chunks, [])
    
    def test_search_step_exception(self):
        """测试搜索步骤异常处理"""
        self.mock_ragflow_client.retrieve_chunks.side_effect = Exception("Network error")
        
        chunks, success = self.service.search_step("test query", ["dataset1"])
        
        self.assertFalse(success)
        self.assertEqual(chunks, [])
    
    # ==================== Agent和Session集成测试 ====================
    
    def test_agent_s3_conversation_new_session(self):
        """测试Agent S3对话 - 创建新Session"""
        # Mock create_session
        self.mock_ragflow_client.create_session.return_value = {
            'code': 0,
            'data': {'session_id': 'new_session_123'}
        }
        
        # Mock s3_search_process
        with patch.object(self.service, 's3_search_process') as mock_s3_search:
            mock_s3_search.return_value = {
                'question': 'test question',
                'search_rounds': 2,
                'selected_documents': [{'content': 'doc1'}],
                'search_process': [],
                'final_context': 'Final context',
                'model_info': {'model': 'test-model', 'mode': 'SDK'}
            }
            
            # Mock session_ask
            self.mock_ragflow_client.session_ask.return_value = {
                'code': 0,
                'data': {'content': 'Agent answer'}
            }
            
            result = self.service.agent_s3_conversation(
                agent_id='agent1',
                question='test question',
                dataset_ids=['dataset1']
            )
            
            # 验证结果
            self.assertEqual(result['answer'], 'Agent answer')
            self.assertEqual(result['agent_info']['agent_id'], 'agent1')
            self.assertEqual(result['session_info']['session_id'], 'new_session_123')
    
    def test_agent_s3_conversation_existing_session(self):
        """测试Agent S3对话 - 使用现有Session"""
        with patch.object(self.service, 's3_search_process') as mock_s3_search:
            mock_s3_search.return_value = {
                'question': 'test question',
                'search_rounds': 1,
                'selected_documents': [],
                'search_process': [],
                'final_context': 'Context',
                'model_info': {'model': 'test-model', 'mode': 'SDK'}
            }
            
            self.mock_ragflow_client.session_ask.return_value = {
                'code': 0,
                'data': {'content': 'Answer with session'}
            }
            
            result = self.service.agent_s3_conversation(
                agent_id='agent1',
                question='test question',
                session_id='existing_session_456'
            )
            
            # 验证没有创建新session
            self.mock_ragflow_client.create_session.assert_not_called()
            self.assertEqual(result['session_info']['session_id'], 'existing_session_456')
    
    def test_agent_s3_conversation_fallback(self):
        """测试Agent S3对话 - 失败时回退到LLM"""
        self.mock_ragflow_client.create_session.return_value = {
            'code': 0,
            'data': {'session_id': 'session1'}
        }
        
        with patch.object(self.service, 's3_search_process') as mock_s3_search:
            mock_s3_search.return_value = {
                'question': 'test question',
                'search_rounds': 1,
                'selected_documents': [{'content': 'doc1'}],
                'search_process': [],
                'final_context': 'Context',
                'model_info': {'model': 'test-model', 'mode': 'SDK'}
            }
            
            # Agent调用失败
            self.mock_ragflow_client.session_ask.return_value = {
                'code': 500,
                'message': 'Agent error'
            }
            
            with patch.object(self.service, 'synthesize_answer') as mock_synthesize:
                mock_synthesize.return_value = "Fallback answer"
                
                result = self.service.agent_s3_conversation(
                    agent_id='agent1',
                    question='test question'
                )
                
                # 验证使用了synthesize_answer作为回退
                mock_synthesize.assert_called_once()
                self.assertEqual(result['answer'], 'Fallback answer')
    
    def test_agent_s3_conversation_non_sdk_mode(self):
        """测试非SDK模式下的Agent对话"""
        self.service.is_sdk_mode = False
        
        with self.assertRaises(ValueError) as context:
            self.service.agent_s3_conversation('agent1', 'question')
        
        self.assertIn("Agent功能需要SDK模式", str(context.exception))
    
    # ==================== S3搜索流程测试 ====================
    
    def test_s3_search_process_complete(self):
        """测试完整的S3搜索流程"""
        # Mock初始搜索
        with patch.object(self.service, 'search_step') as mock_search:
            mock_search.return_value = ([
                {'content': 'Initial doc 1', 'similarity': 0.95},
                {'content': 'Initial doc 2', 'similarity': 0.85}
            ], True)
            
            # Mock LLM响应
            self.mock_llm_client.chat_completion.return_value = """
            <think>I have found relevant information</think>
            <important_info>[1, 2]</important_info>
            <search_complete>True</search_complete>
            """
            
            result = self.service.s3_search_process(
                question="test question",
                dataset_ids=["dataset1"],
                max_rounds=3
            )
            
            # 验证结果
            self.assertEqual(result['question'], 'test question')
            self.assertEqual(result['search_rounds'], 1)
            self.assertEqual(len(result['selected_documents']), 2)
            self.assertIn('Initial doc 1', result['final_context'])
    
    def test_s3_search_process_iterative(self):
        """测试迭代搜索流程"""
        # Mock搜索步骤
        search_results = [
            ([{'content': 'Initial doc', 'similarity': 0.9}], True),
            ([{'content': 'Second search doc', 'similarity': 0.95}], True)
        ]
        
        with patch.object(self.service, 'search_step') as mock_search:
            mock_search.side_effect = search_results
            
            # Mock LLM响应 - 第一次需要更多搜索
            llm_responses = [
                """<think>Need more info</think>
                <query>{"question": "more specific query"}</query>
                <search_complete>False</search_complete>""",
                """<think>Now I have enough</think>
                <important_info>[1, 3]</important_info>
                <search_complete>True</search_complete>"""
            ]
            
            self.mock_llm_client.chat_completion.side_effect = llm_responses
            
            result = self.service.s3_search_process(
                question="test question",
                dataset_ids=["dataset1"],
                max_rounds=3
            )
            
            # 验证进行了两轮搜索
            self.assertEqual(mock_search.call_count, 2)
            self.assertEqual(result['search_rounds'], 2)
    
    def test_s3_search_process_no_results(self):
        """测试无搜索结果的流程"""
        with patch.object(self.service, 'search_step') as mock_search:
            mock_search.return_value = ([], False)
            
            result = self.service.s3_search_process(
                question="test question",
                dataset_ids=["dataset1"]
            )
            
            self.assertEqual(result['search_rounds'], 0)
            self.assertEqual(result['selected_documents'], [])
            self.assertEqual(result['final_context'], "未找到相关信息")
    
    # ==================== 答案合成测试 ====================
    
    def test_synthesize_answer_success(self):
        """测试成功合成答案"""
        selected_docs = [
            {'content': 'Document 1 content'},
            {'content': 'Document 2 content'}
        ]
        
        self.mock_llm_client.chat_completion.return_value = "Synthesized answer"
        
        answer = self.service.synthesize_answer(
            question="test question",
            selected_docs=selected_docs,
            temperature=0.7,
            max_tokens=1000
        )
        
        self.assertEqual(answer, "Synthesized answer")
        
        # 验证LLM调用
        call_args = self.mock_llm_client.chat_completion.call_args
        messages = call_args[1]['messages']
        self.assertIn("Document 1 content", messages[0]['content'])
        self.assertIn("test question", messages[0]['content'])
    
    def test_synthesize_answer_no_docs(self):
        """测试无文档时的答案合成"""
        answer = self.service.synthesize_answer("test question", [])
        
        self.assertEqual(answer, "抱歉，没有找到相关信息来回答您的问题。")
        self.mock_llm_client.chat_completion.assert_not_called()
    
    def test_synthesize_answer_error(self):
        """测试答案合成错误处理"""
        selected_docs = [{'content': 'Test doc'}]
        self.mock_llm_client.chat_completion.side_effect = Exception("LLM Error")
        
        answer = self.service.synthesize_answer("test question", selected_docs)
        
        self.assertIn("生成答案时出现错误", answer)
        self.assertIn("LLM Error", answer)


class TestEnhancedS3RAGServiceHTTPMode(unittest.TestCase):
    """测试HTTP客户端模式"""
    
    def setUp(self):
        """测试初始化"""
        # Mock RAGFlow客户端（HTTP模式）
        self.mock_ragflow_client = Mock()
        self.mock_ragflow_client.__class__.__name__ = 'RAGFlowClient'
        
        # Mock LLM客户端
        self.mock_llm_client = Mock()
        
        # 创建服务实例
        self.service = EnhancedS3RAGService(self.mock_ragflow_client, self.mock_llm_client)
        
        # 设置为HTTP模式
        self.service.is_sdk_mode = False
    
    def test_search_step_http_mode(self):
        """测试HTTP模式下的搜索步骤"""
        self.mock_ragflow_client.retrieve_chunks.return_value = {
            'code': 0,
            'data': {
                'chunks': [
                    {'content': 'HTTP mode content', 'similarity': 0.88}
                ]
            }
        }
        
        chunks, success = self.service.search_step(
            "test query",
            ["dataset1"],
            top_k=10
        )
        
        self.assertTrue(success)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['content'], 'HTTP mode content')
    
    def test_agent_conversation_http_mode_error(self):
        """测试HTTP模式下Agent对话抛出错误"""
        with self.assertRaises(ValueError) as context:
            self.service.agent_s3_conversation('agent1', 'question')
        
        self.assertIn("Agent功能需要SDK模式", str(context.exception))


if __name__ == '__main__':
    unittest.main()