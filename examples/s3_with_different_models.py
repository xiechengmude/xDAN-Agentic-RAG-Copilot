#!/usr/bin/env python3
"""
使用不同的Search和Generator模型的S3 RAG示例
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService

# 加载环境变量
load_dotenv()

def main():
    """主函数"""
    # 从环境变量获取配置
    ragflow_api_url = os.getenv("RAGFLOW_API_URL")
    ragflow_api_key = os.getenv("RAGFLOW_API_KEY")
    dataset_id = os.getenv("DEFAULT_DATASET_ID")
    
    # 获取S3模型配置
    search_model_name = os.getenv("S3_SEARCH_MODEL_NAME")
    search_model_url = os.getenv("S3_SEARCH_MODEL_URL")
    generator_model_name = os.getenv("S3_GENERATOR_MODEL_NAME")
    generator_model_url = os.getenv("S3_GENERATOR_MODEL_URL")
    
    print("S3 RAG服务配置:")
    print(f"Search Model: {search_model_name}")
    print(f"Generator Model: {generator_model_name}")
    print("-" * 60)
    
    # 初始化RAGFlow客户端
    ragflow_client = RAGFlowSDKWrapper(
        api_url=ragflow_api_url,
        api_key=ragflow_api_key
    )
    
    # 创建独立的LLM客户端
    # 例如：可以使用不同的模型或不同的服务器
    search_llm_client = LLMClient(
        base_url=search_model_url,
        model_name=search_model_name
    )
    
    # 可以使用不同的生成模型
    # 例如：使用更大的模型进行最终答案生成
    generator_llm_client = LLMClient(
        base_url=generator_model_url,
        model_name=generator_model_name
    )
    
    # 初始化S3服务
    s3_service = EnhancedS3RAGService(
        ragflow_client=ragflow_client,
        search_llm_client=search_llm_client,
        generator_llm_client=generator_llm_client
    )
    
    # 测试问题
    test_questions = [
        "什么是智信平台？",
        "智信平台有哪些主要功能？",
        "用户如何在智信平台上借款？"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        print("-" * 40)
        
        # 执行S3搜索流程
        result = s3_service.s3_search_process(
            question=question,
            dataset_ids=[dataset_id],
            max_rounds=3,
            top_k=10,
            similarity_threshold=0.3
        )
        
        # 生成答案
        answer = s3_service.synthesize_answer(
            question=question,
            selected_docs=result['selected_documents'],
            temperature=0.7,
            max_tokens=500
        )
        
        print(f"搜索轮数: {result['search_rounds']}")
        print(f"选中文档数: {len(result['selected_documents'])}")
        print(f"使用的模型:")
        print(f"  - Search: {result['model_info']['search_model']}")
        print(f"  - Generator: {result['model_info']['generator_model']}")
        print(f"\n答案: {answer[:200]}...")

if __name__ == "__main__":
    main()