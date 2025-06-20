#!/usr/bin/env python3
"""
测试单个问题
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

def test_single_question():
    """测试单个问题"""
    # 初始化客户端
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
    
    # 初始化S3服务
    s3_service = EnhancedS3RAGService(
        ragflow_client=ragflow_client,
        search_llm_client=search_llm_client,
        generator_llm_client=generator_llm_client
    )
    
    # 测试问题
    question = "什么是智信平台？"
    
    print(f"测试问题: {question}")
    print(f"Search Model: {S3_SEARCH_MODEL_NAME}")
    print(f"Generator Model: {S3_GENERATOR_MODEL_NAME}")
    print("-" * 60)
    
    # 执行S3搜索流程
    result = s3_service.s3_search_process(
        question=question,
        dataset_ids=[DEFAULT_DATASET_ID],
        max_rounds=2,
        top_k=5,
        similarity_threshold=0.3
    )
    
    print(f"搜索轮数: {result['search_rounds']}")
    print(f"选中文档数: {len(result['selected_documents'])}")
    
    # 生成答案
    answer = s3_service.synthesize_answer(
        question=question,
        selected_docs=result['selected_documents'],
        temperature=0.7,
        max_tokens=500
    )
    
    print(f"\n答案: {answer}")

if __name__ == "__main__":
    test_single_question()