#!/usr/bin/env python3
"""
快速测试智信问题集（只测试前3个问题）
"""

import os
import sys
import json
import time
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

def main():
    """快速测试前3个问题"""
    print("快速测试智信问题集（前3个问题）")
    print("=" * 60)
    
    # 加载问题集
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/zhixin_questions.json"
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # 只测试前3个问题
    test_questions = questions_data["questions"][:3]
    
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
    
    results = []
    
    for i, question in enumerate(test_questions):
        print(f"\n问题 {i+1}/3: {question['question']}")
        print(f"难度: {question['difficulty']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # 搜索阶段
            print("执行搜索...")
            search_result = s3_service.s3_search_process(
                question=question["question"],
                dataset_ids=[DEFAULT_DATASET_ID],
                max_rounds=2,  # 减少搜索轮数以加快测试
                top_k=5,
                similarity_threshold=0.3
            )
            
            search_rounds = search_result.get("search_rounds", 0)
            selected_docs_count = len(search_result.get("selected_documents", []))
            
            print(f"搜索完成 - 轮数: {search_rounds}, 选中文档: {selected_docs_count}")
            
            # 生成答案
            print("生成答案...")
            answer = s3_service.synthesize_answer(
                question=question["question"],
                selected_docs=search_result.get("selected_documents", []),
                temperature=0.7,
                max_tokens=500
            )
            
            duration = time.time() - start_time
            
            result = {
                "question_id": question["id"],
                "question": question["question"],
                "answer": answer,
                "search_rounds": search_rounds,
                "selected_documents": selected_docs_count,
                "duration": round(duration, 2),
                "status": "success"
            }
            
            print(f"✓ 成功 - 耗时: {duration:.1f}秒")
            print(f"答案预览: {answer[:100]}...")
            
        except Exception as e:
            result = {
                "question_id": question["id"],
                "question": question["question"],
                "error": str(e),
                "duration": round(time.time() - start_time, 2),
                "status": "failed"
            }
            print(f"✗ 失败: {e}")
        
        results.append(result)
    
    # 保存快速测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results_zhixin_quick_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_type": "quick",
            "timestamp": timestamp,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n快速测试完成，结果保存到: {output_file}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"成功: {success_count}/3")

if __name__ == "__main__":
    main()