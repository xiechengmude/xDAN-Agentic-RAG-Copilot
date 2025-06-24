#!/usr/bin/env python3
"""
S3 RAG服务测试
测试S3框架的搜索、选择和合成功能
"""

import os
import sys
import json
import pytest
from typing import Dict, List
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

from src.services.enhanced_s3_rag_service_v2_fixed import EnhancedS3RAGServiceV2
from src.clients.xdan_rag_client import XDANRagClient
from src.clients.llm_client import LLMClient
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

class TestS3RAGService:
    """S3 RAG服务测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        # 初始化客户端
        cls.ragflow_client = XDANRagClient(
            api_url=RAGFLOW_API_URL,
            api_key=RAGFLOW_API_KEY
        )
        
        cls.search_llm = LLMClient(
            base_url=S3_SEARCH_MODEL_URL,
            api_key=S3_SEARCH_API_KEY,
            model_name=S3_SEARCH_MODEL_NAME
        )
        
        cls.generator_llm = LLMClient(
            base_url=S3_GENERATOR_MODEL_URL,
            api_key=S3_GENERATOR_API_KEY,
            model_name=S3_GENERATOR_MODEL_NAME
        )
        
        # 初始化S3服务
        cls.s3_service = EnhancedS3RAGServiceV2(
            ragflow_client=cls.ragflow_client,
            search_llm_client=cls.search_llm,
            generator_llm_client=cls.generator_llm
        )
    
    def test_01_format_search_results(self):
        """测试1: 搜索结果格式化"""
        # 模拟搜索结果
        mock_chunks = [
            {
                "id": "chunk1",
                "content": "RAGFlow is an open-source RAG engine.",
                "similarity": 0.95,
                "document_id": "doc1",
                "dataset_id": "dataset1"
            },
            {
                "id": "chunk2",
                "content": "It provides knowledge base management.",
                "similarity": 0.85,
                "document_id": "doc2",
                "dataset_id": "dataset1"
            }
        ]
        
        formatted_text, doc_mapping = self.s3_service.format_search_results(mock_chunks)
        
        assert isinstance(formatted_text, str)
        assert isinstance(doc_mapping, dict)
        assert len(doc_mapping) == 2
        assert "Document 1:" in formatted_text
        assert "Document 2:" in formatted_text
        
        print("✅ 搜索结果格式化测试成功")
        print(f"  格式化文本长度: {len(formatted_text)} 字符")
        print(f"  文档映射数量: {len(doc_mapping)}")
    
    def test_02_extract_search_decision(self):
        """测试2: 搜索决策提取"""
        # 测试继续搜索的响应
        continue_response = """
        <think>The current documents mention RAGFlow but don't explain its architecture.</think>
        <search_complete>false</search_complete>
        <query>{"question": "RAGFlow architecture and components"}</query>
        """
        
        decision = self.s3_service.extract_search_decision(continue_response)
        
        assert decision['search_complete'] is False
        assert decision['new_query'] == "RAGFlow architecture and components"
        assert "architecture" in decision['thinking']
        
        print("✅ 继续搜索决策提取成功")
        
        # 测试完成搜索的响应
        complete_response = """
        <think>Documents 1 and 3 contain comprehensive information about RAGFlow.</think>
        <search_complete>true</search_complete>
        <important_info>[1, 3, 5]</important_info>
        """
        
        decision = self.s3_service.extract_search_decision(complete_response)
        
        assert decision['search_complete'] is True
        assert decision['important_docs'] == [1, 3, 5]
        assert decision['new_query'] is None
        
        print("✅ 完成搜索决策提取成功")
    
    def test_03_search_step(self):
        """测试3: 单步搜索功能"""
        print("\n测试单步搜索...")
        
        chunks, success = self.s3_service.search_step(
            question="什么是RAGFlow？",
            dataset_ids=[DEFAULT_DATASET_ID],
            top_k=3,
            similarity_threshold=0.1
        )
        
        assert success is True
        assert isinstance(chunks, list)
        
        print(f"✅ 单步搜索成功，找到 {len(chunks)} 个文档片段")
        
        if chunks:
            print(f"  最相关片段相似度: {chunks[0].get('similarity', 'N/A')}")
    
    def test_04_s3_search_process(self):
        """测试4: 完整S3搜索流程"""
        print("\n测试完整S3搜索流程...")
        
        result = self.s3_service.s3_search_process_with_history(
            question="RAGFlow的主要功能有哪些？",
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=2,
            top_k=5,
            similarity_threshold=0.2
        )
        
        assert isinstance(result, dict)
        assert 'search_history' in result
        assert 'selected_documents' in result
        assert 'total_rounds' in result
        
        print(f"✅ S3搜索流程完成")
        print(f"  搜索轮数: {result['total_rounds']}")
        print(f"  历史记录数: {len(result['search_history'])}")
        print(f"  选中文档数: {len(result['selected_documents'])}")
        
        # 打印搜索历史
        for i, history in enumerate(result['search_history']):
            print(f"\n  第{i+1}条记录:")
            print(f"    类型: {history.get('type')}")
            print(f"    轮次: {history.get('round', 'N/A')}")
    
    def test_05_synthesize_answer(self):
        """测试5: 答案合成功能"""
        print("\n测试答案合成...")
        
        # 模拟选中的文档
        mock_selected_docs = [
            {
                "content": "RAGFlow is an open-source RAG engine based on deep document understanding.",
                "similarity": 0.95
            },
            {
                "content": "It offers a streamlined RAG workflow for businesses.",
                "similarity": 0.85
            }
        ]
        
        answer = self.s3_service.synthesize_answer(
            question="What is RAGFlow?",
            selected_docs=mock_selected_docs
        )
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        
        print(f"✅ 答案合成成功")
        print(f"  答案长度: {len(answer)} 字符")
        print(f"  答案预览: {answer[:100]}...")
    
    def test_06_empty_search_results(self):
        """测试6: 空搜索结果处理"""
        print("\n测试空搜索结果处理...")
        
        # 使用一个不太可能有结果的查询
        result = self.s3_service.s3_search_process_with_history(
            question="xyzabc123randomquery",
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=1,
            top_k=5,
            similarity_threshold=0.9  # 高阈值
        )
        
        print(f"✅ 空结果处理测试完成")
        print(f"  找到文档数: {len(result.get('selected_documents', []))}")
        
        # 即使没有找到文档，也应该有搜索历史
        assert 'search_history' in result
        assert len(result['search_history']) > 0
    
    def test_07_multi_round_search(self):
        """测试7: 多轮搜索"""
        print("\n测试多轮搜索...")
        
        result = self.s3_service.s3_search_process_with_history(
            question="RAGFlow的技术架构、核心组件和使用流程是什么？",
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=3,  # 允许最多3轮
            top_k=10,
            similarity_threshold=0.3
        )
        
        print(f"✅ 多轮搜索测试完成")
        print(f"  实际搜索轮数: {result['total_rounds']}")
        
        # 统计每轮的搜索类型
        search_types = {}
        for history in result['search_history']:
            search_type = history.get('type', 'unknown')
            search_types[search_type] = search_types.get(search_type, 0) + 1
        
        print(f"  搜索类型统计: {search_types}")
    
    def test_08_performance_metrics(self):
        """测试8: 性能指标"""
        import time
        
        print("\n测试性能指标...")
        
        start_time = time.time()
        
        result = self.s3_service.s3_search_process_with_history(
            question="介绍一下RAGFlow",
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=2,
            top_k=5,
            similarity_threshold=0.3
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"✅ 性能测试完成")
        print(f"  总耗时: {elapsed_time:.2f} 秒")
        print(f"  平均每轮耗时: {elapsed_time / result['total_rounds']:.2f} 秒")
        
        # 统计各阶段耗时（如果有时间戳的话）
        if result['search_history']:
            first_timestamp = result['search_history'][0].get('timestamp')
            last_timestamp = result['search_history'][-1].get('timestamp')
            print(f"  首次搜索时间: {first_timestamp}")
            print(f"  最后操作时间: {last_timestamp}")

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("S3 RAG服务测试")
    print("=" * 60)
    print(f"RAGFlow API: {RAGFLOW_API_URL}")
    print(f"Search Model: {S3_SEARCH_MODEL_NAME}")
    print(f"Generator Model: {S3_GENERATOR_MODEL_NAME}")
    print("=" * 60)
    
    # 使用pytest运行测试
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()