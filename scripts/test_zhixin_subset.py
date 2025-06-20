#!/usr/bin/env python3
"""
测试智信问题子集
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

def test_subset():
    """测试问题子集"""
    # 初始化客户端
    print("初始化客户端...")
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
    
    print(f"Search Model: {S3_SEARCH_MODEL_NAME}")
    print(f"Generator Model: {S3_GENERATOR_MODEL_NAME}")
    print("=" * 60)
    
    # 只测试前3个问题
    questions = [
        {
            "id": 1,
            "question": "什么是智信平台？它主要有哪些功能？",
            "difficulty": "简单",
            "expected_topics": ["智信", "平台", "功能"]
        },
        {
            "id": 2,
            "question": "在智信平台有哪些类型的机构，他们的模式是怎么样的？有什么区别？",
            "difficulty": "简单",
            "expected_topics": ["机构类型", "绑卡扣款", "辅助扣款"]
        },
        {
            "id": 3,
            "question": "智信平台上主要有哪些系统，用一句话分别介绍每个系统主要负责什么？",
            "difficulty": "简单",
            "expected_topics": ["系统", "ice-crp", "ice-pfs", "ice-partner", "ice-gws", "ice-core"]
        }
    ]
    
    results = []
    
    for q in questions:
        print(f"\n测试问题 {q['id']}: {q['question']}")
        print("-" * 40)
        
        start_time = datetime.now()
        
        try:
            # 执行S3搜索流程（减少搜索轮数）
            search_result = s3_service.s3_search_process(
                question=q['question'],
                dataset_ids=[DEFAULT_DATASET_ID],
                max_rounds=2,  # 减少搜索轮数
                top_k=5,       # 减少返回数量
                similarity_threshold=0.3
            )
            
            # 生成答案
            answer = s3_service.synthesize_answer(
                question=q['question'],
                selected_docs=search_result['selected_documents'],
                temperature=0.7,
                max_tokens=500
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "question_id": q['id'],
                "question": q['question'],
                "difficulty": q['difficulty'],
                "answer": answer,
                "search_rounds": search_result['search_rounds'],
                "selected_documents": len(search_result['selected_documents']),
                "duration": round(duration, 2),
                "status": "success"
            }
            
            print(f"✓ 完成 - 耗时: {duration:.1f}秒")
            print(f"答案预览: {answer[:100]}...")
            
        except Exception as e:
            result = {
                "question_id": q['id'],
                "question": q['question'],
                "difficulty": q['difficulty'],
                "answer": None,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds(),
                "status": "failed"
            }
            print(f"✗ 失败: {e}")
        
        results.append(result)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_zhixin_subset_{timestamp}.json"
    
    report = {
        "test_time": timestamp,
        "configuration": {
            "ragflow_api": RAGFLOW_API_URL,
            "search_model": S3_SEARCH_MODEL_NAME,
            "generator_model": S3_GENERATOR_MODEL_NAME,
            "dataset_id": DEFAULT_DATASET_ID
        },
        "results": results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {filename}")
    
    # 打印总结
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n测试总结: {success_count}/{len(results)} 成功")

if __name__ == "__main__":
    test_subset()