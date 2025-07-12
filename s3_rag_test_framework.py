#!/usr/bin/env python3
"""
S3 架构 RAG 服务完整测试框架
从客户需求和关注角度设计的多维度评估体系
"""
import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)

from src.services.s3_service import S3Service
from src.core.config_loader import ConfigLoader
from src.core.langfuse_client import langfuse_client

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class S3RAGTestFramework:
    """S3 RAG 服务测试框架"""
    
    def __init__(self):
        self.test_results = []
        self.langfuse_traces = []
        self.setup_services()
    
    def setup_services(self):
        """初始化服务"""
        # 初始化 Langfuse
        langfuse_client.initialize()
        
        # 初始化 S3 服务
        config_loader = ConfigLoader()
        config = {
            'ragflow_api_url': config_loader.get('ragflow.api_url'),
            'ragflow_api_key': config_loader.get('ragflow.api_key'),
            'default_dataset_id': config_loader.get('ragflow.default_dataset_id')
        }
        self.s3_service = S3Service(config)
    
    async def run_comprehensive_test(self):
        """运行完整的 RAG 测试"""
        print("🚀 S3 RAG 服务完整测试框架")
        print("=" * 80)
        print("测试维度：检索质量、生成质量、智能体决策、性能、稳定性、用户体验、业务适配")
        print("=" * 80)
        
        # 定义测试用例集
        test_cases = self.get_test_cases()
        
        for category, cases in test_cases.items():
            print(f"\n📋 {category} 测试")
            print("-" * 60)
            
            for i, case in enumerate(cases, 1):
                print(f"\n测试 {category}-{i}: {case['name']}")
                result = await self.execute_test_case(case, f"{category}-{i}")
                self.test_results.append(result)
                
                # 简要显示结果
                self.display_brief_result(result)
                
                # 等待数据同步
                await asyncio.sleep(1)
        
        # 生成完整测试报告
        self.generate_test_report()
    
    def get_test_cases(self) -> Dict[str, List[Dict]]:
        """获取测试用例集"""
        return {
            "1. 检索质量维度": [
                {
                    "name": "召回准确性测试",
                    "question": "智信平台中的ice-crp系统主要负责什么功能？",
                    "expected_keywords": ["ice-crp", "路由系统", "授信路由", "借款路由"],
                    "test_type": "retrieval_precision",
                    "evaluation_focus": "检索到的文档是否与问题高度相关"
                },
                {
                    "name": "召回全面性测试",
                    "question": "智信平台的完整授信流程包括哪些步骤？",
                    "expected_keywords": ["授信路由", "填写信息", "绑定银行卡", "人脸验证", "机构交互", "授信结果查询"],
                    "test_type": "retrieval_recall",
                    "evaluation_focus": "是否检索到授信流程的所有关键环节"
                },
                {
                    "name": "相关性排序测试",
                    "question": "什么是撞库？在智信系统中的作用是什么？",
                    "expected_keywords": ["撞库", "md5值", "机构判断", "其他APP申请"],
                    "test_type": "relevance_ranking",
                    "evaluation_focus": "最相关的文档是否排在前面"
                }
            ],
            
            "2. 生成质量维度": [
                {
                    "name": "答案正确性测试",
                    "question": "智信平台有几种扣款模式？分别是什么？",
                    "expected_answer_points": [
                        "两种扣款模式",
                        "机构绑卡扣款模式",
                        "辅助扣款模式"
                    ],
                    "test_type": "answer_correctness",
                    "evaluation_focus": "答案是否准确回答问题核心要点"
                },
                {
                    "name": "答案完整性测试",
                    "question": "请详细说明智信平台的还款处理流程。",
                    "expected_coverage": [
                        "还款提交机构流程",
                        "机构扣款",
                        "还款查询流程", 
                        "还款通知流程",
                        "还款补处理流程"
                    ],
                    "test_type": "answer_completeness",
                    "evaluation_focus": "答案是否涵盖还款流程的所有重要环节"
                },
                {
                    "name": "术语准确性测试",
                    "question": "ice-pfs-app、ice-partner-app、ice-gws-app在系统中的作用分别是什么？",
                    "expected_technical_terms": [
                        "ice-pfs-app: 产品流程系统",
                        "ice-partner-app: 机构配置",
                        "ice-gws-app: 机构交互"
                    ],
                    "test_type": "terminology_accuracy",
                    "evaluation_focus": "技术术语使用是否准确"
                }
            ],
            
            "3. 智能体决策维度": [
                {
                    "name": "信息充分性判断测试",
                    "question": "奇富借条是什么？",
                    "test_type": "agent_sufficiency",
                    "evaluation_focus": "Agent是否能正确判断信息是否充足",
                    "expected_behavior": "应该1-2轮即可找到充分信息"
                },
                {
                    "name": "迭代搜索策略测试",
                    "question": "智信系统中用户从申请到放款的完整流程是怎样的？",
                    "test_type": "iterative_search",
                    "evaluation_focus": "Agent是否能通过多轮搜索逐步完善信息",
                    "expected_behavior": "应该进行2-3轮搜索获取完整流程信息"
                },
                {
                    "name": "文档选择准确性测试",
                    "question": "智信Z模式和辅助模式有什么区别？",
                    "test_type": "document_selection",
                    "evaluation_focus": "Agent选择的重要文档是否最相关",
                    "expected_behavior": "选择的文档应该包含模式对比信息"
                }
            ],
            
            "4. 性能维度": [
                {
                    "name": "响应时间测试",
                    "question": "智信贷款平台是什么？",
                    "test_type": "response_time",
                    "evaluation_focus": "端到端响应时间是否在可接受范围",
                    "performance_threshold": 30  # 秒
                },
                {
                    "name": "复杂问题处理效率",
                    "question": "请详细分析智信平台授信、借款、还款三个主要流程的系统交互机制。",
                    "test_type": "complex_processing",
                    "evaluation_focus": "处理复杂问题的效率和质量平衡"
                }
            ],
            
            "5. 稳定性维度": [
                {
                    "name": "边界情况处理",
                    "question": "xyz123系统是什么？",  # 不存在的系统
                    "test_type": "boundary_handling",
                    "evaluation_focus": "对不存在信息的处理是否合理"
                },
                {
                    "name": "一致性测试",
                    "question": "智信贷款平台的主要功能是什么？",  # 重复测试
                    "test_type": "consistency",
                    "evaluation_focus": "多次询问相同问题的答案一致性"
                }
            ],
            
            "6. 用户体验维度": [
                {
                    "name": "可解释性测试",
                    "question": "ice-core-app系统的核心职责是什么？",
                    "test_type": "explainability",
                    "evaluation_focus": "答案是否包含清晰的逻辑和引用"
                },
                {
                    "name": "信息来源透明度",
                    "question": "智信平台的借款试算是怎么工作的？",
                    "test_type": "source_transparency",
                    "evaluation_focus": "是否能清楚标识信息来源"
                }
            ]
        }
    
    async def execute_test_case(self, test_case: Dict, test_id: str) -> Dict:
        """执行单个测试用例"""
        chat_id = f"s3-test-{test_id}-{datetime.now().strftime('%H%M%S')}"
        
        # 创建 Langfuse 追踪
        session_id = langfuse_client.create_session(chat_id, "rag-tester")
        trace_id = langfuse_client.start_trace(
            name=f"S3 RAG Test - {test_case['name']}",
            session_id=session_id,
            metadata={
                "test_type": test_case.get('test_type', 'unknown'),
                "test_id": test_id,
                "evaluation_focus": test_case.get('evaluation_focus', '')
            },
            tags=["s3-rag-test", test_case.get('test_type', 'general')]
        )
        
        # 执行测试
        start_time = time.time()
        try:
            result_data = {}
            async for chunk in self.s3_service.ask(
                question=test_case['question'],
                max_rounds=3,
                stream=False
            ):
                if isinstance(chunk, dict):
                    result_data.update(chunk)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 分析结果
            analysis = self.analyze_test_result(test_case, result_data, execution_time, trace_id)
            
            return {
                "test_id": test_id,
                "test_name": test_case['name'],
                "test_type": test_case.get('test_type', 'unknown'),
                "question": test_case['question'],
                "answer": result_data.get('answer', ''),
                "execution_time": execution_time,
                "metadata": result_data.get('metadata', {}),
                "langfuse_trace": trace_id,
                "langfuse_session": session_id,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "test_id": test_id,
                "test_name": test_case['name'],
                "test_type": test_case.get('test_type', 'unknown'),
                "question": test_case['question'],
                "error": str(e),
                "execution_time": time.time() - start_time,
                "langfuse_trace": trace_id,
                "analysis": {"overall_score": 0, "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_test_result(self, test_case: Dict, result_data: Dict, execution_time: float, trace_id: str) -> Dict:
        """分析测试结果"""
        answer = result_data.get('answer', '')
        metadata = result_data.get('metadata', {})
        
        analysis = {
            "overall_score": 0,
            "detailed_scores": {},
            "observations": [],
            "recommendations": []
        }
        
        # 基于测试类型进行专项分析
        test_type = test_case.get('test_type', 'general')
        
        if test_type in ['retrieval_precision', 'retrieval_recall', 'relevance_ranking']:
            analysis.update(self.analyze_retrieval_quality(test_case, result_data))
        elif test_type in ['answer_correctness', 'answer_completeness', 'terminology_accuracy']:
            analysis.update(self.analyze_generation_quality(test_case, result_data))
        elif test_type in ['agent_sufficiency', 'iterative_search', 'document_selection']:
            analysis.update(self.analyze_agent_decisions(test_case, result_data))
        elif test_type in ['response_time', 'complex_processing']:
            analysis.update(self.analyze_performance(test_case, result_data, execution_time))
        elif test_type in ['boundary_handling', 'consistency']:
            analysis.update(self.analyze_stability(test_case, result_data))
        elif test_type in ['explainability', 'source_transparency']:
            analysis.update(self.analyze_user_experience(test_case, result_data))
        
        # 记录评分到 Langfuse
        try:
            langfuse_client.log_user_feedback(
                trace_id=trace_id,
                feedback_type="rating",
                score=analysis['overall_score'],
                comment=f"测试类型: {test_type}, 综合评分: {analysis['overall_score']:.2f}"
            )
        except Exception as e:
            logger.warning(f"Langfuse 评分记录失败: {e}")
        
        return analysis
    
    def analyze_retrieval_quality(self, test_case: Dict, result_data: Dict) -> Dict:
        """分析检索质量"""
        answer = result_data.get('answer', '')
        metadata = result_data.get('metadata', {})
        
        # 关键词覆盖率分析
        expected_keywords = test_case.get('expected_keywords', [])
        found_keywords = [kw for kw in expected_keywords if kw in answer]
        keyword_coverage = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
        
        # 文档数量分析
        docs_used = metadata.get('documents_used', 0)
        search_rounds = metadata.get('search_rounds', 0)
        
        score = min(1.0, keyword_coverage * 0.7 + (0.3 if docs_used > 0 else 0))
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "keyword_coverage": keyword_coverage,
                "document_utilization": 1.0 if docs_used > 0 else 0,
                "search_efficiency": max(0, 1.0 - (search_rounds - 1) * 0.2)
            },
            "observations": [
                f"关键词覆盖率: {keyword_coverage:.1%} ({len(found_keywords)}/{len(expected_keywords)})",
                f"找到关键词: {', '.join(found_keywords)}",
                f"使用文档数: {docs_used}",
                f"搜索轮数: {search_rounds}"
            ]
        }
    
    def analyze_generation_quality(self, test_case: Dict, result_data: Dict) -> Dict:
        """分析生成质量"""
        answer = result_data.get('answer', '')
        
        # 答案长度和完整性
        answer_length = len(answer)
        has_substantive_content = answer_length > 50 and answer.strip() != ""
        
        # 要点覆盖分析
        expected_points = test_case.get('expected_answer_points', [])
        expected_coverage = test_case.get('expected_coverage', [])
        expected_terms = test_case.get('expected_technical_terms', [])
        
        coverage_score = 0
        if expected_points:
            covered_points = sum(1 for point in expected_points if any(keyword in answer for keyword in point.split()))
            coverage_score = covered_points / len(expected_points)
        elif expected_coverage:
            covered_items = sum(1 for item in expected_coverage if item in answer)
            coverage_score = covered_items / len(expected_coverage)
        elif expected_terms:
            covered_terms = sum(1 for term in expected_terms if term.split(':')[0] in answer)
            coverage_score = covered_terms / len(expected_terms)
        
        score = (0.3 if has_substantive_content else 0) + coverage_score * 0.7
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "content_substantiveness": 1.0 if has_substantive_content else 0,
                "coverage_completeness": coverage_score,
                "answer_length_adequacy": min(1.0, answer_length / 200)
            },
            "observations": [
                f"答案长度: {answer_length} 字符",
                f"内容充实性: {'是' if has_substantive_content else '否'}",
                f"要点覆盖率: {coverage_score:.1%}"
            ]
        }
    
    def analyze_agent_decisions(self, test_case: Dict, result_data: Dict) -> Dict:
        """分析智能体决策质量"""
        metadata = result_data.get('metadata', {})
        search_rounds = metadata.get('search_rounds', 0)
        docs_used = metadata.get('documents_used', 0)
        
        # 搜索轮次合理性
        expected_behavior = test_case.get('expected_behavior', '')
        rounds_reasonable = True
        if "1-2轮" in expected_behavior and search_rounds > 2:
            rounds_reasonable = False
        elif "2-3轮" in expected_behavior and (search_rounds < 2 or search_rounds > 3):
            rounds_reasonable = False
        
        # 信息收集效率
        efficiency_score = min(1.0, docs_used / max(1, search_rounds)) if search_rounds > 0 else 0
        
        score = (0.4 if rounds_reasonable else 0.1) + efficiency_score * 0.6
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "search_rounds_reasonableness": 1.0 if rounds_reasonable else 0.2,
                "information_gathering_efficiency": efficiency_score,
                "decision_appropriateness": 0.8 if docs_used > 0 else 0.2
            },
            "observations": [
                f"搜索轮数: {search_rounds} (预期: {expected_behavior})",
                f"文档收集: {docs_used} 个",
                f"轮次合理性: {'是' if rounds_reasonable else '否'}",
                f"收集效率: {efficiency_score:.2f}"
            ]
        }
    
    def analyze_performance(self, test_case: Dict, result_data: Dict, execution_time: float) -> Dict:
        """分析性能表现"""
        threshold = test_case.get('performance_threshold', 30)
        time_acceptable = execution_time <= threshold
        
        # 时间效率评分
        time_score = max(0, 1.0 - (execution_time - threshold) / threshold) if execution_time > threshold else 1.0
        
        # 内容质量评分（简化）
        answer = result_data.get('answer', '')
        quality_score = min(1.0, len(answer) / 100) if answer else 0
        
        score = time_score * 0.6 + quality_score * 0.4
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "response_time_efficiency": time_score,
                "quality_under_time_constraint": quality_score
            },
            "observations": [
                f"响应时间: {execution_time:.1f}秒 (阈值: {threshold}秒)",
                f"时间达标: {'是' if time_acceptable else '否'}",
                f"答案长度: {len(answer)} 字符"
            ]
        }
    
    def analyze_stability(self, test_case: Dict, result_data: Dict) -> Dict:
        """分析稳定性表现"""
        answer = result_data.get('answer', '')
        
        # 错误处理能力
        if "xyz123" in test_case['question']:  # 边界情况
            if "不知道" in answer or "没有找到" in answer or "无法" in answer:
                boundary_score = 1.0  # 正确处理了不存在的信息
            elif answer.strip() == "":
                boundary_score = 0.5  # 无回答，但没有胡编
            else:
                boundary_score = 0.1  # 可能产生了幻觉
        else:
            boundary_score = 1.0 if answer else 0
        
        score = boundary_score
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "boundary_case_handling": boundary_score,
                "error_graceful_degradation": 1.0 if answer or "error" not in result_data else 0
            },
            "observations": [
                f"边界处理: {boundary_score:.1f}",
                f"答案内容: {answer[:100]}..." if answer else "无答案"
            ]
        }
    
    def analyze_user_experience(self, test_case: Dict, result_data: Dict) -> Dict:
        """分析用户体验"""
        answer = result_data.get('answer', '')
        metadata = result_data.get('metadata', {})
        
        # 可解释性评分
        has_clear_structure = any(marker in answer for marker in ['：', ':', '1.', '2.', '首先', '其次'])
        has_logical_flow = len(answer) > 100 and has_clear_structure
        
        explainability_score = (0.5 if has_clear_structure else 0) + (0.5 if has_logical_flow else 0)
        
        score = explainability_score
        
        return {
            "overall_score": score,
            "detailed_scores": {
                "structural_clarity": 1.0 if has_clear_structure else 0,
                "logical_coherence": 1.0 if has_logical_flow else 0
            },
            "observations": [
                f"结构清晰性: {'是' if has_clear_structure else '否'}",
                f"逻辑连贯性: {'是' if has_logical_flow else '否'}",
                f"答案组织: {'良好' if explainability_score > 0.7 else '一般' if explainability_score > 0.3 else '待改进'}"
            ]
        }
    
    def display_brief_result(self, result: Dict):
        """显示简要测试结果"""
        score = result['analysis']['overall_score']
        status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
        
        print(f"  {status} 评分: {score:.2f} | 耗时: {result['execution_time']:.1f}s")
        
        # 显示关键观察
        observations = result['analysis'].get('observations', [])
        for obs in observations[:2]:  # 只显示前2个关键观察
            print(f"    └─ {obs}")
    
    def generate_test_report(self):
        """生成完整测试报告"""
        print(f"\n{'='*80}")
        print("📊 S3 RAG 服务完整测试报告")
        print("="*80)
        
        # 保存报告到文件
        report_data = {
            "test_summary": self.generate_summary_stats(),
            "detailed_results": self.test_results,
            "langfuse_info": {
                "host": os.getenv('LANGFUSE_HOST'),
                "total_traces": len(self.test_results)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        report_file = f"s3_rag_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # 显示总结
        self.display_summary_report()
        
        print(f"\n📄 详细报告已保存: {report_file}")
        print(f"🔗 Langfuse 追踪: {os.getenv('LANGFUSE_HOST')}")
        print("="*80)
    
    def generate_summary_stats(self) -> Dict:
        """生成总结统计"""
        if not self.test_results:
            return {}
        
        successful_tests = [r for r in self.test_results if 'error' not in r]
        
        avg_score = sum(r['analysis']['overall_score'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        # 按维度分组统计
        dimension_stats = {}
        for result in successful_tests:
            test_type = result['test_type']
            if test_type not in dimension_stats:
                dimension_stats[test_type] = []
            dimension_stats[test_type].append(result['analysis']['overall_score'])
        
        dimension_averages = {
            dim: sum(scores) / len(scores) for dim, scores in dimension_stats.items()
        }
        
        return {
            "total_tests": len(self.test_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(self.test_results) - len(successful_tests),
            "average_score": avg_score,
            "average_response_time": avg_time,
            "dimension_scores": dimension_averages,
            "high_performing_tests": len([r for r in successful_tests if r['analysis']['overall_score'] > 0.8]),
            "low_performing_tests": len([r for r in successful_tests if r['analysis']['overall_score'] < 0.5])
        }
    
    def display_summary_report(self):
        """显示总结报告"""
        stats = self.generate_summary_stats()
        
        print(f"\n📈 整体表现")
        print(f"  总测试数: {stats['total_tests']}")
        print(f"  成功率: {stats['successful_tests']}/{stats['total_tests']} ({stats['successful_tests']/stats['total_tests']:.1%})")
        print(f"  平均评分: {stats['average_score']:.2f}/1.00")
        print(f"  平均响应时间: {stats['average_response_time']:.1f}秒")
        
        print(f"\n📊 各维度评分")
        for dim, score in stats['dimension_scores'].items():
            status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
            print(f"  {status} {dim}: {score:.2f}")
        
        print(f"\n🎯 性能分布")
        print(f"  优秀 (>0.8): {stats['high_performing_tests']} 项")
        print(f"  待改进 (<0.5): {stats['low_performing_tests']} 项")

async def main():
    """主函数"""
    test_framework = S3RAGTestFramework()
    await test_framework.run_comprehensive_test()
    
    # 关闭 Langfuse 连接
    langfuse_client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())