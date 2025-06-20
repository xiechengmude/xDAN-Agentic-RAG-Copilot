#!/usr/bin/env python3
"""
综合测试智信问题集，记录Search Model和Generator Model的详细结果
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.llm_client import LLMClient
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

def extract_search_results(search_result: Dict[str, Any]) -> Dict[str, Any]:
    """从搜索结果中提取关键信息"""
    search_details = {
        "search_rounds": search_result.get("search_rounds", 0),
        "total_documents_retrieved": search_result.get("total_documents_retrieved", 0),
        "selected_documents_count": len(search_result.get("selected_documents", [])),
        "search_queries": [],
        "search_decisions": [],
        "selected_document_ids": []
    }
    
    # 提取搜索历史
    search_history = search_result.get("search_history", [])
    for round_data in search_history:
        if "query" in round_data:
            search_details["search_queries"].append(round_data["query"])
        if "agent_decision" in round_data:
            decision = {
                "round": round_data.get("round", 0),
                "search_complete": round_data["agent_decision"].get("search_complete", False),
                "reasoning": round_data["agent_decision"].get("reasoning", "")
            }
            search_details["search_decisions"].append(decision)
    
    # 提取选中的文档ID
    for doc in search_result.get("selected_documents", []):
        if isinstance(doc, dict) and "id" in doc:
            search_details["selected_document_ids"].append(doc["id"])
    
    return search_details

def test_single_question(s3_service: EnhancedS3RAGService, question_data: Dict[str, Any]) -> Dict[str, Any]:
    """测试单个问题"""
    print(f"\n测试问题 {question_data['id']}: {question_data['question']}")
    print(f"难度: {question_data['difficulty']}")
    print("-" * 80)
    
    start_time = time.time()
    result = {
        "question_id": question_data["id"],
        "question": question_data["question"],
        "difficulty": question_data["difficulty"],
        "expected_answer": question_data.get("expected_answer", ""),
        "reference_source": question_data.get("reference_source", ""),
        "topics": question_data.get("topics", [])
    }
    
    try:
        # Phase 1: S3 Search Process (使用Search Model)
        print("执行S3搜索流程...")
        search_start = time.time()
        
        search_result = s3_service.s3_search_process(
            question=question_data["question"],
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=3,
            top_k=10,
            similarity_threshold=0.3
        )
        
        search_duration = time.time() - search_start
        
        # 提取搜索结果详情
        search_model_results = extract_search_results(search_result)
        search_model_results["duration"] = round(search_duration, 2)
        search_model_results["model_name"] = S3_SEARCH_MODEL_NAME
        
        print(f"搜索完成 - 轮数: {search_model_results['search_rounds']}, "
              f"选中文档: {search_model_results['selected_documents_count']}")
        
        # Phase 2: Answer Generation (使用Generator Model)
        print("生成答案...")
        generation_start = time.time()
        
        answer = s3_service.synthesize_answer(
            question=question_data["question"],
            selected_docs=search_result.get("selected_documents", []),
            temperature=0.7,
            max_tokens=1000
        )
        
        generation_duration = time.time() - generation_start
        
        generator_model_results = {
            "model_name": S3_GENERATOR_MODEL_NAME,
            "answer": answer,
            "duration": round(generation_duration, 2),
            "input_documents_count": len(search_result.get("selected_documents", [])),
            "answer_length": len(answer)
        }
        
        # 总体结果
        total_duration = time.time() - start_time
        
        result.update({
            "status": "success",
            "total_duration": round(total_duration, 2),
            "search_model_results": search_model_results,
            "generator_model_results": generator_model_results,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✓ 完成 - 总耗时: {total_duration:.1f}秒")
        print(f"答案预览: {answer[:150]}...")
        
    except Exception as e:
        print(f"✗ 失败: {str(e)}")
        result.update({
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "total_duration": round(time.time() - start_time, 2),
            "timestamp": datetime.now().isoformat()
        })
    
    return result

def main():
    """主测试函数"""
    print("=" * 80)
    print("智信平台问题集综合测试")
    print("=" * 80)
    
    # 加载问题集
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/zhixin_questions.json"
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    print(f"加载了 {questions_data['total_questions']} 个问题")
    print(f"难度分布: {json.dumps(questions_data['difficulty_distribution'], ensure_ascii=False)}")
    
    # 初始化客户端
    print("\n初始化客户端...")
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
    
    print(f"\n配置信息:")
    print(f"- RAGFlow API: {RAGFLOW_API_URL}")
    print(f"- Search Model: {S3_SEARCH_MODEL_NAME}")
    print(f"- Generator Model: {S3_GENERATOR_MODEL_NAME}")
    print(f"- Dataset ID: {DEFAULT_DATASET_ID}")
    print("=" * 80)
    
    # 测试所有问题
    results = []
    start_time = time.time()
    
    # 可以限制测试数量进行快速测试
    # questions_to_test = questions_data["questions"][:3]  # 只测试前3个
    questions_to_test = questions_data["questions"]  # 测试所有问题
    
    for i, question in enumerate(questions_to_test):
        print(f"\n进度: {i+1}/{len(questions_to_test)}")
        result = test_single_question(s3_service, question)
        results.append(result)
        
        # 避免请求过快
        if i < len(questions_to_test) - 1:
            time.sleep(1)
    
    total_test_duration = time.time() - start_time
    
    # 生成测试报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 统计数据
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count
    
    if success_count > 0:
        avg_total_duration = sum(r["total_duration"] for r in results if r["status"] == "success") / success_count
        avg_search_duration = sum(r["search_model_results"]["duration"] for r in results if r["status"] == "success") / success_count
        avg_generation_duration = sum(r["generator_model_results"]["duration"] for r in results if r["status"] == "success") / success_count
        avg_search_rounds = sum(r["search_model_results"]["search_rounds"] for r in results if r["status"] == "success") / success_count
        avg_selected_docs = sum(r["search_model_results"]["selected_documents_count"] for r in results if r["status"] == "success") / success_count
    else:
        avg_total_duration = avg_search_duration = avg_generation_duration = avg_search_rounds = avg_selected_docs = 0
    
    report = {
        "test_name": "智信平台问题集综合测试",
        "test_time": timestamp,
        "total_test_duration": round(total_test_duration, 2),
        "configuration": {
            "ragflow_api": RAGFLOW_API_URL,
            "search_model": {
                "name": S3_SEARCH_MODEL_NAME,
                "url": S3_SEARCH_MODEL_URL
            },
            "generator_model": {
                "name": S3_GENERATOR_MODEL_NAME,
                "url": S3_GENERATOR_MODEL_URL
            },
            "dataset_id": DEFAULT_DATASET_ID
        },
        "summary": {
            "total_questions": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_count / len(results) * 100, 2) if results else 0,
            "average_total_duration": round(avg_total_duration, 2),
            "average_search_duration": round(avg_search_duration, 2),
            "average_generation_duration": round(avg_generation_duration, 2),
            "average_search_rounds": round(avg_search_rounds, 2),
            "average_selected_documents": round(avg_selected_docs, 2)
        },
        "results": results
    }
    
    # 保存结果
    output_filename = f"test_results_zhixin_comprehensive_{timestamp}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print(f"- 总问题数: {len(results)}")
    print(f"- 成功: {success_count}")
    print(f"- 失败: {failed_count}")
    print(f"- 成功率: {report['summary']['success_rate']}%")
    print(f"- 平均总耗时: {avg_total_duration:.1f}秒")
    print(f"- 平均搜索耗时: {avg_search_duration:.1f}秒")
    print(f"- 平均生成耗时: {avg_generation_duration:.1f}秒")
    print(f"- 平均搜索轮数: {avg_search_rounds:.1f}")
    print(f"- 结果已保存到: {output_filename}")
    print("=" * 80)

if __name__ == "__main__":
    main()