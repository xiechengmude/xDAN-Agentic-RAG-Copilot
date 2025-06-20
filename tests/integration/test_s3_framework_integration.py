#!/usr/bin/env python3
"""
S3框架集成测试
测试S3框架与RAGFlow SDK的完整集成流程
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import asyncio
import json

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.services.enhanced_s3_rag_service import (
    EnhancedS3RAGService, EnhancedS3RAGRequest, EnhancedS3RAGResponse,
    get_enhanced_s3_rag_service, enhanced_s3_rag_ask
)
from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient


class TestS3FrameworkIntegration(unittest.TestCase):
    """S3框架的集成测试"""
    
    def setUp(self):
        """测试初始化"""
        # Mock依赖
        self.mock_ragflow_sdk = Mock(spec=RAGFlowSDKWrapper)
        self.mock_llm_client = Mock(spec=LLMClient)
        
        # 创建服务实例
        self.service = EnhancedS3RAGService(self.mock_ragflow_sdk, self.mock_llm_client)
        self.service.is_sdk_mode = True
        
        # 设置默认mock返回值
        self.setup_default_mocks()
    
    def setup_default_mocks(self):
        """设置默认的mock返回值"""
        # Mock检索结果
        self.default_chunks = [
            {
                'id': 'chunk1',
                'content': 'Python is a high-level programming language.',
                'document_id': 'doc1',
                'dataset_id': 'dataset1',
                'similarity': 0.95
            },
            {
                'id': 'chunk2',
                'content': 'Python supports multiple programming paradigms.',
                'document_id': 'doc2',
                'dataset_id': 'dataset1',
                'similarity': 0.90
            },
            {
                'id': 'chunk3',
                'content': 'Python has a large standard library.',
                'document_id': 'doc3',
                'dataset_id': 'dataset1',
                'similarity': 0.85
            }
        ]
        
        self.mock_ragflow_sdk.retrieve_chunks.return_value = {
            'code': 0,
            'data': {
                'chunks': self.default_chunks,
                'total': len(self.default_chunks)
            }
        }
        
        # Mock LLM响应
        self.mock_llm_client.chat_completion.return_value = """
        <think>I have found relevant information about Python programming language.</think>
        <important_info>[1, 2]</important_info>
        <search_complete>True</search_complete>
        """
    
    # ==================== 完整S3流程测试 ====================
    
    def test_complete_s3_flow_single_round(self):
        """测试单轮S3完整流程"""
        question = "What is Python?"
        dataset_ids = ["dataset1"]
        
        # 执行S3流程
        result = self.service.s3_search_process(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            top_k=5,
            similarity_threshold=0.8
        )
        
        # 验证结果
        self.assertEqual(result['question'], question)
        self.assertEqual(result['search_rounds'], 1)
        self.assertEqual(len(result['selected_documents']), 2)  # Agent选择了2个文档
        
        # 验证选中的文档
        selected_contents = [doc['content'] for doc in result['selected_documents']]
        self.assertIn('Python is a high-level programming language.', selected_contents)
        self.assertIn('Python supports multiple programming paradigms.', selected_contents)
        
        # 验证最终上下文
        self.assertIn('文档 1:', result['final_context'])
        self.assertIn('文档 2:', result['final_context'])
        
        # 验证API调用
        self.mock_ragflow_sdk.retrieve_chunks.assert_called_once()
        self.mock_llm_client.chat_completion.assert_called_once()
    
    def test_complete_s3_flow_multiple_rounds(self):
        """测试多轮S3完整流程"""
        question = "Explain Python's advanced features"
        
        # 设置多轮响应
        llm_responses = [
            # 第一轮：需要更多信息
            """<think>I need more specific information about advanced features.</think>
            <query>{"question": "Python decorators metaclasses generators"}</query>
            <important_info>[1]</important_info>
            <search_complete>False</search_complete>""",
            
            # 第二轮：信息充足
            """<think>Now I have comprehensive information.</think>
            <important_info>[1, 3, 4]</important_info>
            <search_complete>True</search_complete>"""
        ]
        
        self.mock_llm_client.chat_completion.side_effect = llm_responses
        
        # 第二轮搜索结果
        second_round_chunks = [
            {
                'id': 'chunk4',
                'content': 'Decorators are a powerful feature in Python.',
                'document_id': 'doc4',
                'dataset_id': 'dataset1',
                'similarity': 0.93
            },
            {
                'id': 'chunk5',
                'content': 'Metaclasses control class creation in Python.',
                'document_id': 'doc5',
                'dataset_id': 'dataset1',
                'similarity': 0.88
            }
        ]
        
        # 设置不同的检索结果
        self.mock_ragflow_sdk.retrieve_chunks.side_effect = [
            {
                'code': 0,
                'data': {'chunks': self.default_chunks, 'total': 3}
            },
            {
                'code': 0,
                'data': {'chunks': second_round_chunks, 'total': 2}
            }
        ]
        
        # 执行S3流程
        result = self.service.s3_search_process(
            question=question,
            dataset_ids=["dataset1"],
            max_rounds=5
        )
        
        # 验证结果
        self.assertEqual(result['search_rounds'], 2)
        self.assertEqual(len(result['selected_documents']), 3)  # 最多3个文档
        
        # 验证进行了两轮搜索
        self.assertEqual(self.mock_ragflow_sdk.retrieve_chunks.call_count, 2)
        self.assertEqual(self.mock_llm_client.chat_completion.call_count, 2)
        
        # 验证搜索过程记录
        search_process = result['search_process']
        self.assertGreaterEqual(len(search_process), 3)  # 至少3个步骤
        
        # 验证第二轮搜索使用了新查询
        second_search_call = self.mock_ragflow_sdk.retrieve_chunks.call_args_list[1]
        self.assertIn('decorators', second_search_call[1]['question'].lower())
    
    # ==================== Agent集成测试 ====================
    
    def test_agent_s3_conversation_integration(self):
        """测试Agent与S3框架的集成"""
        agent_id = "test_agent_123"
        question = "What are Python's key features?"
        
        # Mock session创建
        self.mock_ragflow_sdk.create_session.return_value = {
            'code': 0,
            'data': {'session_id': 'session_456'}
        }
        
        # Mock agent回答
        self.mock_ragflow_sdk.session_ask.return_value = {
            'code': 0,
            'data': {'content': 'Python has many key features including simplicity and readability.'}
        }
        
        # 执行Agent S3对话
        result = self.service.agent_s3_conversation(
            agent_id=agent_id,
            question=question,
            dataset_ids=["dataset1"]
        )
        
        # 验证结果
        self.assertEqual(result['answer'], 'Python has many key features including simplicity and readability.')
        self.assertEqual(result['agent_info']['agent_id'], agent_id)
        self.assertEqual(result['session_info']['session_id'], 'session_456')
        
        # 验证API调用顺序
        self.mock_ragflow_sdk.create_session.assert_called_once_with(agent_id)
        
        # 验证session_ask被调用，并包含了S3搜索的上下文
        session_ask_call = self.mock_ragflow_sdk.session_ask.call_args
        self.assertIn('基于以下上下文回答问题', session_ask_call[1]['question'])
        self.assertIn(question, session_ask_call[1]['question'])
    
    def test_agent_conversation_with_existing_session(self):
        """测试使用现有Session的Agent对话"""
        agent_id = "test_agent"
        session_id = "existing_session_789"
        question = "Tell me more about Python"
        
        # Mock agent回答
        self.mock_ragflow_sdk.session_ask.return_value = {
            'code': 0,
            'data': {'content': 'Continuing our conversation about Python...'}
        }
        
        # 执行Agent S3对话
        result = self.service.agent_s3_conversation(
            agent_id=agent_id,
            question=question,
            session_id=session_id,
            dataset_ids=["dataset1"]
        )
        
        # 验证没有创建新session
        self.mock_ragflow_sdk.create_session.assert_not_called()
        
        # 验证使用了提供的session_id
        self.assertEqual(result['session_info']['session_id'], session_id)
    
    def test_agent_conversation_fallback_to_llm(self):
        """测试Agent失败时回退到LLM"""
        agent_id = "test_agent"
        question = "What is Python?"
        
        # Mock session创建成功
        self.mock_ragflow_sdk.create_session.return_value = {
            'code': 0,
            'data': {'session_id': 'session_123'}
        }
        
        # Mock agent调用失败
        self.mock_ragflow_sdk.session_ask.return_value = {
            'code': 500,
            'message': 'Agent service unavailable'
        }
        
        # 设置synthesize_answer的mock
        with patch.object(self.service, 'synthesize_answer') as mock_synthesize:
            mock_synthesize.return_value = "Fallback answer from LLM"
            
            result = self.service.agent_s3_conversation(
                agent_id=agent_id,
                question=question,
                dataset_ids=["dataset1"]
            )
            
            # 验证使用了fallback
            self.assertEqual(result['answer'], "Fallback answer from LLM")
            mock_synthesize.assert_called_once()
    
    # ==================== 错误处理和边界情况测试 ====================
    
    def test_s3_process_no_results(self):
        """测试无搜索结果的S3流程"""
        # Mock空检索结果
        self.mock_ragflow_sdk.retrieve_chunks.return_value = {
            'code': 0,
            'data': {'chunks': [], 'total': 0}
        }
        
        result = self.service.s3_search_process(
            question="Nonexistent topic",
            dataset_ids=["dataset1"]
        )
        
        # 验证结果
        self.assertEqual(result['search_rounds'], 0)
        self.assertEqual(result['selected_documents'], [])
        self.assertEqual(result['final_context'], "未找到相关信息")
    
    def test_s3_process_search_failure(self):
        """测试搜索失败的S3流程"""
        # Mock检索失败
        self.mock_ragflow_sdk.retrieve_chunks.return_value = {
            'code': 500,
            'message': 'Search service error'
        }
        
        with patch.object(self.service, 'search_step') as mock_search_step:
            mock_search_step.return_value = ([], False)
            
            result = self.service.s3_search_process(
                question="Test question",
                dataset_ids=["dataset1"]
            )
            
            # 验证返回了错误状态
            self.assertEqual(result['search_rounds'], 0)
            self.assertEqual(result['final_context'], "未找到相关信息")
    
    def test_s3_process_max_rounds_limit(self):
        """测试达到最大搜索轮数限制"""
        # 设置Agent总是要求更多搜索
        self.mock_llm_client.chat_completion.return_value = """
        <think>I need more information</think>
        <query>{"question": "more details"}</query>
        <search_complete>False</search_complete>
        """
        
        # 执行S3流程，设置较小的max_rounds
        result = self.service.s3_search_process(
            question="Complex topic",
            dataset_ids=["dataset1"],
            max_rounds=2
        )
        
        # 验证只进行了2轮搜索
        self.assertEqual(result['search_rounds'], 2)
        self.assertEqual(self.mock_llm_client.chat_completion.call_count, 2)
    
    def test_s3_process_llm_error_handling(self):
        """测试LLM错误处理"""
        # 第一次调用成功，第二次失败
        self.mock_llm_client.chat_completion.side_effect = [
            """<query>{"question": "more info"}</query>
            <search_complete>False</search_complete>""",
            Exception("LLM service error")
        ]
        
        result = self.service.s3_search_process(
            question="Test question",
            dataset_ids=["dataset1"],
            max_rounds=3
        )
        
        # 验证在错误后停止
        self.assertEqual(self.mock_llm_client.chat_completion.call_count, 2)
        self.assertGreater(result['search_rounds'], 0)
    
    # ==================== 答案合成集成测试 ====================
    
    def test_synthesize_answer_integration(self):
        """测试答案合成的完整流程"""
        question = "What makes Python popular?"
        selected_docs = [
            {'content': 'Python is known for its simplicity and readability.'},
            {'content': 'Python has a vast ecosystem of libraries.'},
            {'content': 'Python is used in data science, web development, and AI.'}
        ]
        
        # Mock LLM生成答案
        self.mock_llm_client.chat_completion.return_value = (
            "Python's popularity stems from its simplicity, readability, "
            "extensive library ecosystem, and versatility across domains "
            "like data science, web development, and AI."
        )
        
        answer = self.service.synthesize_answer(
            question=question,
            selected_docs=selected_docs,
            temperature=0.7,
            max_tokens=200
        )
        
        # 验证答案
        self.assertIn("simplicity", answer)
        self.assertIn("library ecosystem", answer)
        
        # 验证LLM调用参数
        call_args = self.mock_llm_client.chat_completion.call_args
        prompt = call_args[1]['messages'][0]['content']
        
        # 验证prompt包含了所有文档内容
        for doc in selected_docs:
            self.assertIn(doc['content'], prompt)
        self.assertIn(question, prompt)
    
    # ==================== 流式响应测试 ====================
    
    def test_agent_conversation_stream_mode(self):
        """测试Agent对话的流式模式"""
        agent_id = "test_agent"
        question = "Stream test"
        
        # Mock流式响应
        def mock_stream_response():
            yield {'content': 'Part 1 '}
            yield {'content': 'Part 2 '}
            yield {'content': 'Part 3'}
        
        self.mock_ragflow_sdk.create_session.return_value = {
            'code': 0,
            'data': {'session_id': 'stream_session'}
        }
        
        # 注意：实际实现中session_ask的stream模式需要特殊处理
        # 这里简化测试
        with patch.object(self.service, 's3_search_process') as mock_s3:
            mock_s3.return_value = {
                'question': question,
                'search_rounds': 1,
                'selected_documents': [],
                'search_process': [],
                'final_context': 'Context',
                'model_info': {'model': 'test', 'mode': 'SDK'}
            }
            
            # 测试流式处理（注意：实际实现可能需要异步）
            result = self.service.agent_s3_conversation(
                agent_id=agent_id,
                question=question,
                dataset_ids=["dataset1"]
            )
            
            # 基本验证
            self.assertIn('agent_info', result)
            self.assertIn('session_info', result)


class TestS3FrameworkEndToEnd(unittest.TestCase):
    """S3框架的端到端测试"""
    
    def setUp(self):
        """测试初始化"""
        # 创建完整的mock环境
        self.setup_mocks()
    
    def setup_mocks(self):
        """设置所有必要的mocks"""
        # Mock环境变量
        self.env_patcher = patch.dict(os.environ, {
            'RAGFLOW_API_URL': 'http://test.api.com:7080',
            'RAGFLOW_API_KEY': 'test-key',
            'LLM_API_URL': 'http://llm.api.com',
            'LLM_MODEL_NAME': 'test-model',
            'DEFAULT_DATASET_ID': 'default-dataset'
        })
        self.env_patcher.start()
        
        # Mock SDK可用性
        self.sdk_patcher = patch('enhanced_s3_rag_service.SDK_AVAILABLE', True)
        self.sdk_patcher.start()
        
        # Mock RAGFlowSDKWrapper
        self.ragflow_patcher = patch('enhanced_s3_rag_service.RAGFlowSDKWrapper')
        self.mock_ragflow_class = self.ragflow_patcher.start()
        self.mock_ragflow_instance = Mock()
        self.mock_ragflow_class.return_value = self.mock_ragflow_instance
        
        # Mock LLMClient
        self.llm_patcher = patch('enhanced_s3_rag_service.LLMClient')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm_instance = Mock()
        self.mock_llm_class.return_value = self.mock_llm_instance
    
    def tearDown(self):
        """清理测试"""
        self.env_patcher.stop()
        self.sdk_patcher.stop()
        self.ragflow_patcher.stop()
        self.llm_patcher.stop()
    
    def test_enhanced_s3_rag_ask_endpoint(self):
        """测试enhanced_s3_rag_ask API端点"""
        # 创建请求
        request = EnhancedS3RAGRequest(
            question="What is machine learning?",
            dataset_ids=["ml-dataset"],
            use_sdk=True,
            max_search_rounds=2,
            top_k=10,
            similarity_threshold=0.75,
            temperature=0.8,
            max_tokens=500,
            stream=False
        )
        
        # 设置mock返回值
        self.mock_ragflow_instance.retrieve_chunks.return_value = {
            'code': 0,
            'data': {
                'chunks': [
                    {
                        'content': 'Machine learning is a subset of AI.',
                        'similarity': 0.95
                    }
                ],
                'total': 1
            }
        }
        
        self.mock_llm_instance.chat_completion.side_effect = [
            """<important_info>[1]</important_info>
            <search_complete>True</search_complete>""",
            "Machine learning is a powerful technology..."
        ]
        
        # 获取服务并调用
        service = get_enhanced_s3_rag_service(
            self.mock_ragflow_instance,
            self.mock_llm_instance
        )
        
        # 模拟API调用
        try:
            # 执行S3流程
            search_result = service.s3_search_process(
                question=request.question,
                dataset_ids=request.dataset_ids,
                max_rounds=request.max_search_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            
            # 合成答案
            answer = service.synthesize_answer(
                question=request.question,
                selected_docs=search_result['selected_documents'],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            result_dict = {**search_result, 'answer': answer}
            response = EnhancedS3RAGResponse(**result_dict)
            
            # 验证响应
            self.assertEqual(response.question, "What is machine learning?")
            self.assertEqual(response.answer, "Machine learning is a powerful technology...")
            self.assertGreater(response.search_rounds, 0)
            
        except Exception as e:
            self.fail(f"API endpoint test failed: {str(e)}")


if __name__ == '__main__':
    unittest.main()