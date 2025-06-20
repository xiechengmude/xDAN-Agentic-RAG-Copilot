#!/usr/bin/env python3
"""
智信问题测试脚本
使用增强版S3 RAG服务测试智信平台相关问题
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper, SDK_AVAILABLE
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService
from src.clients.llm_client import LLMClient

# 测试问题列表
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "什么是智信平台？它主要有哪些功能？",
        "difficulty": "简单",
        "expected_topics": ["智信贷款平台", "奇富借条", "连接用户和机构", "推荐机构", "流量", "分润"]
    },
    {
        "id": 2,
        "question": "在智信平台有哪些类型的机构，他们的模式是怎么样的？有什么区别？",
        "difficulty": "简单",
        "expected_topics": ["机构绑卡扣款模式", "辅助扣款模式", "绑卡", "扣款"]
    },
    {
        "id": 3,
        "question": "智信平台上主要有哪些系统，用一句话分别介绍每个系统主要负责什么？",
        "difficulty": "简单",
        "expected_topics": ["ice-crp", "ics-pfs-app", "ice-partner-app", "ice-gws-app", "ice-gws-web", "ice-core-app"]
    },
    {
        "id": 4,
        "question": "一个用户想在智信平台上借款，需要经过哪些主体流程？",
        "difficulty": "中等",
        "expected_topics": ["授信路由", "用户申请", "授信机构交互", "绑定银行卡", "借款申请"]
    },
    {
        "id": 5,
        "question": "授信路由流程中，是怎么判断出机构满足授信条件的？",
        "difficulty": "简单",
        "expected_topics": ["维护时间", "授信上限", "银行卡", "撞库"]
    }
]

class ZhixinQuestionTester:
    """智信问题测试器"""
    
    def __init__(self):
        """初始化测试器"""
        # 从环境变量或使用默认值
        self.ragflow_api_url = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        self.ragflow_api_key = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")
        self.default_dataset_id = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")
        
        # 导入S3模型配置
        from config.settings import (
            S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
            S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
        )
        
        self.search_model_name = S3_SEARCH_MODEL_NAME
        self.search_model_url = S3_SEARCH_MODEL_URL
        self.search_api_key = S3_SEARCH_API_KEY
        self.generator_model_name = S3_GENERATOR_MODEL_NAME
        self.generator_model_url = S3_GENERATOR_MODEL_URL
        self.generator_api_key = S3_GENERATOR_API_KEY
        
        # 初始化客户端
        self.setup_clients()
        
        # 测试结果
        self.test_results = []
    
    def setup_clients(self):
        """设置客户端"""
        try:
            # 尝试使用SDK模式
            if SDK_AVAILABLE:
                print("使用RAGFlow SDK模式")
                self.ragflow_client = RAGFlowSDKWrapper(
                    api_url=self.ragflow_api_url,
                    api_key=self.ragflow_api_key
                )
            else:
                print("SDK不可用，使用HTTP客户端模式")
                from src.clients.ragflow_client import RAGFlowClient
                self.ragflow_client = RAGFlowClient(
                    api_url=self.ragflow_api_url,
                    api_key=self.ragflow_api_key
                )
            
            # 初始化LLM客户端（用于搜索和生成）
            # 使用独立的搜索和生成模型
            self.search_llm_client = LLMClient(
                base_url=self.search_model_url,
                api_key=self.search_api_key,
                model_name=self.search_model_name
            )
            self.generator_llm_client = LLMClient(
                base_url=self.generator_model_url,
                api_key=self.generator_api_key,
                model_name=self.generator_model_name
            )
            
            # 初始化S3服务
            self.s3_service = EnhancedS3RAGService(
                ragflow_client=self.ragflow_client,
                search_llm_client=self.search_llm_client,
                generator_llm_client=self.generator_llm_client
            )
            
            print(f"客户端初始化成功")
            print(f"RAGFlow API: {self.ragflow_api_url}")
            print(f"Search Model: {self.search_model_name} ({self.search_model_url})")
            print(f"Generator Model: {self.generator_model_name} ({self.generator_model_url})")
            print(f"默认数据集: {self.default_dataset_id}")
            print("-" * 80)
            
        except Exception as e:
            print(f"客户端初始化失败: {e}")
            raise
    
    def test_question(self, question_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个问题"""
        print(f"\n测试问题 {question_info['id']}: {question_info['question']}")
        print(f"难度: {question_info['difficulty']}")
        print("-" * 60)
        
        start_time = datetime.now()
        
        try:
            # 执行S3搜索流程
            search_result = self.s3_service.s3_search_process(
                question=question_info['question'],
                dataset_ids=[self.default_dataset_id],
                max_rounds=3,
                top_k=10,
                similarity_threshold=0.3  # 降低阈值以获得更多结果
            )
            
            # 生成答案
            answer = self.s3_service.synthesize_answer(
                question=question_info['question'],
                selected_docs=search_result['selected_documents'],
                temperature=0.7,
                max_tokens=1000
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 评估答案质量
            score = self.evaluate_answer(answer, question_info['expected_topics'])
            
            result = {
                'question_id': question_info['id'],
                'question': question_info['question'],
                'difficulty': question_info['difficulty'],
                'answer': answer,
                'search_rounds': search_result['search_rounds'],
                'selected_documents': len(search_result['selected_documents']),
                'duration': duration,
                'score': score,
                'status': 'success'
            }
            
            # 打印结果摘要
            print(f"✓ 搜索轮数: {search_result['search_rounds']}")
            print(f"✓ 选中文档: {len(search_result['selected_documents'])} 个")
            print(f"✓ 耗时: {duration:.2f} 秒")
            print(f"✓ 质量得分: {score:.2f}/1.0")
            print(f"\n答案预览:")
            print(answer[:200] + "..." if len(answer) > 200 else answer)
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'question_id': question_info['id'],
                'question': question_info['question'],
                'difficulty': question_info['difficulty'],
                'answer': None,
                'error': str(e),
                'duration': duration,
                'status': 'failed'
            }
            
            print(f"✗ 测试失败: {e}")
        
        return result
    
    def evaluate_answer(self, answer: str, expected_topics: List[str]) -> float:
        """评估答案质量（简单的关键词匹配）"""
        if not answer:
            return 0.0
        
        answer_lower = answer.lower()
        matched = 0
        
        for topic in expected_topics:
            if topic.lower() in answer_lower:
                matched += 1
        
        return matched / len(expected_topics) if expected_topics else 1.0
    
    def run_tests(self, question_ids: List[int] = None):
        """运行测试"""
        print("=" * 80)
        print("开始智信问题测试")
        print("=" * 80)
        
        # 选择要测试的问题
        if question_ids:
            questions_to_test = [q for q in TEST_QUESTIONS if q['id'] in question_ids]
        else:
            questions_to_test = TEST_QUESTIONS[:5]  # 默认测试前5个问题
        
        # 逐个测试问题
        for question_info in questions_to_test:
            result = self.test_question(question_info)
            self.test_results.append(result)
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("测试报告")
        print("=" * 80)
        
        total_questions = len(self.test_results)
        successful = sum(1 for r in self.test_results if r['status'] == 'success')
        failed = total_questions - successful
        
        print(f"\n总计测试: {total_questions} 个问题")
        print(f"成功: {successful} 个")
        print(f"失败: {failed} 个")
        
        if successful > 0:
            avg_duration = sum(r['duration'] for r in self.test_results if r['status'] == 'success') / successful
            avg_score = sum(r.get('score', 0) for r in self.test_results if r['status'] == 'success') / successful
            avg_rounds = sum(r.get('search_rounds', 0) for r in self.test_results if r['status'] == 'success') / successful
            
            print(f"\n平均耗时: {avg_duration:.2f} 秒")
            print(f"平均质量得分: {avg_score:.2f}/1.0")
            print(f"平均搜索轮数: {avg_rounds:.1f}")
        
        # 保存详细结果
        self.save_results()
    
    def save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_zhixin_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': timestamp,
                'configuration': {
                    'ragflow_api': self.ragflow_api_url,
                    'llm_model': self.llm_model_name,
                    'dataset_id': self.default_dataset_id
                },
                'results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细结果已保存到: {filename}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试智信平台相关问题')
    parser.add_argument('--questions', type=int, nargs='+', 
                       help='指定要测试的问题ID（例如：--questions 1 2 3）')
    parser.add_argument('--all', action='store_true', 
                       help='测试所有问题（共21个）')
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = ZhixinQuestionTester()
    
    # 运行测试
    if args.all:
        # 如果要测试所有问题，需要扩展TEST_QUESTIONS列表
        print("注意：当前只配置了前5个问题，测试前5个...")
        tester.run_tests()
    elif args.questions:
        tester.run_tests(args.questions)
    else:
        # 默认测试前5个问题
        tester.run_tests()


if __name__ == "__main__":
    main()