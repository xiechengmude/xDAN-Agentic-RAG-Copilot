#!/usr/bin/env python3
"""
测试搜索过程记录功能
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service_v2 import EnhancedS3RAGServiceV2
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

def format_search_history(history: list) -> str:
    """格式化搜索历史为易读的文本"""
    output = []
    
    for entry in history:
        output.append(f"\n{'='*60}")
        output.append(f"轮次 {entry['round']} - {entry['type']}")
        output.append(f"时间: {entry['timestamp']}")
        output.append(f"耗时: {entry.get('duration', 0):.2f}秒")
        
        if entry['type'] == 'initial_search':
            output.append(f"查询: {entry['query']}")
            output.append(f"检索到 {entry['results']['count']} 个文档")
            for doc in entry['results']['documents'][:3]:  # 只显示前3个
                output.append(f"  - 文档{doc['id']}: 相似度={doc['similarity']:.3f}")
                output.append(f"    {doc['content_preview']}")
        
        elif entry['type'] == 'agent_decision':
            decision = entry['agent_decision']
            output.append(f"\nSearch Model 思考过程:")
            output.append(f"{decision['thinking']}")
            output.append(f"\n决策: {'完成搜索' if decision['search_complete'] else '继续搜索'}")
            if decision['new_query']:
                output.append(f"新查询: {decision['new_query']}")
            if decision['important_docs']:
                output.append(f"选中文档: {decision['important_docs']}")
        
        elif entry['type'] == 'iterative_search':
            output.append(f"查询: {entry['query']}")
            output.append(f"检索到 {entry['results']['count']} 个文档")
            for doc in entry['results']['documents'][:3]:
                output.append(f"  - 文档{doc['id']}: 相似度={doc['similarity']:.3f}")
        
        elif entry['type'] == 'error':
            output.append(f"错误: {entry['error']}")
    
    return "\n".join(output)

def test_questions_with_recording():
    """测试问题并记录详细搜索过程"""
    
    # 测试问题集
    test_questions = [
        {
            "id": 1,
            "question": "什么是智信平台？它主要有哪些功能？",
            "difficulty": "简单"
        },
        {
            "id": 17,
            "question": "请你推测当还款状态是'申请失败'时，如果系统收到了机构的还款成功/失败通知，系统会如何处理？",
            "difficulty": "复杂"
        },
        {
            "id": 10,
            "question": "如果机构不支持用户的银行卡类型，授信时会发生什么？",
            "difficulty": "中等"
        }
    ]
    
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
    
    # 初始化增强版S3服务
    s3_service = EnhancedS3RAGServiceV2(
        ragflow_client=ragflow_client,
        search_llm_client=search_llm_client,
        generator_llm_client=generator_llm_client
    )
    
    print(f"\n配置信息:")
    print(f"- Search Model: {S3_SEARCH_MODEL_NAME}")
    print(f"- Generator Model: {S3_GENERATOR_MODEL_NAME}")
    print(f"- Dataset ID: {DEFAULT_DATASET_ID}")
    print("="*80)
    
    results = []
    
    for q in test_questions:
        print(f"\n\n{'#'*80}")
        print(f"测试问题 {q['id']}: {q['question']}")
        print(f"难度: {q['difficulty']}")
        print("#"*80)
        
        try:
            # 执行搜索过程
            search_result = s3_service.s3_search_process_with_history(
                question=q['question'],
                dataset_ids=[DEFAULT_DATASET_ID],
                max_rounds=5,
                top_k=10,
                similarity_threshold=0.3
            )
            
            # 打印搜索历史
            print("\n搜索过程详情:")
            print(format_search_history(search_result['search_history']))
            
            # 生成答案
            print("\n生成最终答案...")
            answer = s3_service.synthesize_answer(
                question=q['question'],
                selected_docs=search_result['selected_documents']
            )
            
            # 汇总结果
            result = {
                "question_id": q['id'],
                "question": q['question'],
                "difficulty": q['difficulty'],
                "search_rounds": search_result['search_rounds'],
                "total_documents_retrieved": search_result['total_documents_retrieved'],
                "selected_documents_count": len(search_result['selected_documents']),
                "total_search_time": search_result['total_search_time'],
                "search_history": search_result['search_history'],
                "answer": answer,
                "status": "success"
            }
            
            print(f"\n总结:")
            print(f"- 搜索轮数: {search_result['search_rounds']}")
            print(f"- 总检索文档数: {search_result['total_documents_retrieved']}")
            print(f"- 选中文档数: {len(search_result['selected_documents'])}")
            print(f"- 搜索总耗时: {search_result['total_search_time']:.2f}秒")
            print(f"\n答案预览: {answer[:200]}...")
            
        except Exception as e:
            print(f"\n错误: {e}")
            result = {
                "question_id": q['id'],
                "question": q['question'],
                "difficulty": q['difficulty'],
                "error": str(e),
                "status": "failed"
            }
        
        results.append(result)
    
    # 保存详细结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"search_process_recording_{timestamp}.json"
    
    report = {
        "test_name": "搜索过程记录测试",
        "timestamp": timestamp,
        "configuration": {
            "search_model": S3_SEARCH_MODEL_NAME,
            "generator_model": S3_GENERATOR_MODEL_NAME,
            "dataset_id": DEFAULT_DATASET_ID
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n详细结果已保存到: {output_file}")
    
    # 分析搜索模式
    print("\n搜索模式分析:")
    for result in results:
        if result['status'] == 'success':
            print(f"\n问题 {result['question_id']} ({result['difficulty']}):")
            print(f"  搜索轮数: {result['search_rounds']}")
            
            # 统计每种类型的操作
            search_history = result['search_history']
            decision_count = sum(1 for h in search_history if h['type'] == 'agent_decision')
            search_count = sum(1 for h in search_history if 'search' in h['type'])
            
            print(f"  决策次数: {decision_count}")
            print(f"  搜索次数: {search_count}")
            
            # 显示搜索查询演化
            queries = []
            for h in search_history:
                if h['type'] == 'initial_search':
                    queries.append(h['query'])
                elif h['type'] == 'iterative_search':
                    queries.append(h['query'])
            
            if len(queries) > 1:
                print("  查询演化:")
                for i, q in enumerate(queries):
                    print(f"    {i+1}. {q[:80]}...")

if __name__ == "__main__":
    test_questions_with_recording()