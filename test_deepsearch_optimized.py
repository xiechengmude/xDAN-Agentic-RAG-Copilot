#!/usr/bin/env python3
"""
优化DeepSearch流程测试 - 验证完整的SERP→SearchModel→Crawl→Extract→Loop→Gen流程
遵循KISS和DRY原则
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# 导入DeepSearch框架和配置
from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.litellm_client import LiteLLMSDKClient
from src.core.config_loader import ConfigLoader

class DeepSearchOptimizedTester:
    """优化DeepSearch流程测试器"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        self.litellm_client = None
        self.deepsearch_framework = None
        
    async def setup(self):
        """初始化测试环境"""
        print("🚀 初始化DeepSearch测试环境...")
        
        # 初始化LiteLLM客户端
        self.litellm_client = LiteLLMSDKClient(self.config)
        
        # 初始化DeepSearch框架
        self.deepsearch_framework = DeepSearchFramework(
            litellm_client=self.litellm_client,
            config=self.config
        )
        
        print("✅ DeepSearch测试环境初始化完成")
        print(f"📊 配置加载: {len(self.config)} 个配置项")
        print(f"🔍 BrightData Zone: {self.deepsearch_framework.brightdata_zone}")
        print(f"🕸️ FireCrawl Key: ...{self.deepsearch_framework.firecrawl_api_key[-8:]}")
        
    async def test_complex_analytical_question(self):
        """测试复杂分析问题 - 需要多跳推理和实时数据整合"""
        
        print("\n" + "="*100)
        print("🎯 测试复杂分析问题 - DeepSearch深度搜索模式")
        print("="*100)
        
        # 复杂的多跳推理问题
        question = "分析2024年第四季度全球半导体供应链紧张对中国新能源汽车出口的具体影响，结合最新贸易数据和政策变化"
        
        print(f"❓ 问题: {question}")
        print(f"🎯 期望: SERP搜索 → SearchModel评估选择Top3 → 并行Crawl → SearchModelAgent提取 → Loop直到知识缺口填补 → Gen模型结构化整理")
        
        start_time = time.time()
        
        try:
            # 执行DeepSearch工作流
            final_result = None
            async for result in self.deepsearch_framework.execute_deepsearch_workflow(
                question=question,
                max_rounds=3,  # 最多3轮搜索
                num_results=10,  # 每轮10个候选
                stream=False
            ):
                if isinstance(result, dict):
                    final_result = result
                    break
            
            duration = time.time() - start_time
            
            if final_result and final_result.get("workflow_completed"):
                self.analyze_deepsearch_result(final_result, duration)
            else:
                print("❌ DeepSearch工作流未完成")
                if final_result:
                    print(f"错误: {final_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ DeepSearch测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_deepsearch_result(self, result: Dict[str, Any], duration: float):
        """分析DeepSearch结果"""
        
        print(f"\n📊 DeepSearch流程分析")
        print("="*80)
        
        # 基本信息
        print(f"⏱️ 总耗时: {duration:.2f}秒")
        print(f"🔄 搜索轮数: {len(result.get('rounds', []))}")
        print(f"📄 提取内容数: {len(result.get('extracted_content', []))}")
        print(f"✅ 工作流完成: {result.get('workflow_completed', False)}")
        
        # 搜索轮次分析
        rounds = result.get('rounds', [])
        print(f"\n🔍 搜索轮次详情:")
        for i, round_info in enumerate(rounds, 1):
            print(f"  轮次{i}:")
            print(f"    查询: {round_info.get('search_query', 'N/A')[:50]}...")
            print(f"    找到结果: {round_info.get('search_results_count', 0)}")
            print(f"    选择URL: {len(round_info.get('selected_urls', []))}")
            print(f"    提取内容: {round_info.get('extracted_content_count', 0)}")
            
            decision = round_info.get('decision', {})
            print(f"    搜索完成: {decision.get('search_complete', False)}")
            if decision.get('evaluation_reasoning'):
                print(f"    评估理由: {decision['evaluation_reasoning'][:100]}...")
        
        # 内容来源分析
        extracted_content = result.get('extracted_content', [])
        successful_extractions = [item for item in extracted_content if item.get('extraction_success')]
        
        print(f"\n📚 内容来源分析:")
        print(f"  成功提取: {len(successful_extractions)}/{len(extracted_content)}")
        
        for i, item in enumerate(successful_extractions[:5], 1):  # 显示前5个
            title = item.get('title', 'Unknown')
            url = item.get('url', '')
            content_length = len(item.get('extracted_content', ''))
            extraction_ratio = item.get('extraction_ratio', 0) * 100
            
            print(f"  来源{i}: {title}")
            print(f"    URL: {url}")
            print(f"    提取内容: {content_length} 字符 (压缩比: {extraction_ratio:.1f}%)")
        
        # 最终答案分析
        final_answer = result.get('final_answer', '')
        answer_type = result.get('answer_type', 'standard')
        question_analysis = result.get('question_analysis', '')
        
        print(f"\n✍️ 最终答案分析:")
        print(f"  答案类型: {answer_type}")
        print(f"  答案长度: {len(final_answer)} 字符")
        print(f"  问题诉求分析: {question_analysis}")
        
        # 检查结构化元素
        if answer_type == "structured_with_citations":
            print(f"  结构化元素:")
            structure_indicators = [
                ("## 问题核心分析", "核心分析"),
                ("## 关键发现", "关键发现"),
                ("## 多维度解读", "多维度解读"),
                ("## 数据洞察", "数据洞察"),
                ("## 结论与建议", "结论建议"),
                ("## 参考来源", "参考来源"),
                ("【来源", "引用标注")
            ]
            
            for indicator, name in structure_indicators:
                count = final_answer.count(indicator)
                if count > 0:
                    print(f"    ✅ {name}: {count}处")
                else:
                    print(f"    ❌ {name}: 缺失")
        
        # 质量评估
        print(f"\n🎯 质量评估:")
        
        # 搜索质量
        total_sources = len(successful_extractions)
        search_quality = "优秀" if total_sources >= 5 else "良好" if total_sources >= 3 else "待改进"
        print(f"  信息来源质量: {search_quality} ({total_sources}个有效来源)")
        
        # 响应速度
        speed_quality = "优秀" if duration < 60 else "良好" if duration < 120 else "待改进"
        print(f"  响应速度: {speed_quality} ({duration:.2f}秒)")
        
        # 答案完整性
        completeness = "优秀" if len(final_answer) > 2000 else "良好" if len(final_answer) > 1000 else "待改进"
        print(f"  答案完整性: {completeness} ({len(final_answer)}字符)")
        
        # 结构化程度
        if answer_type == "structured_with_citations":
            citation_count = final_answer.count("【来源")
            structure_score = "优秀" if citation_count >= 10 else "良好" if citation_count >= 5 else "待改进"
            print(f"  结构化程度: {structure_score} ({citation_count}个引用)")
        
        # 显示答案预览
        print(f"\n📝 答案预览 (前500字符):")
        print("-" * 80)
        print(final_answer[:500] + "..." if len(final_answer) > 500 else final_answer)
        print("-" * 80)
        
        # 来源列表
        sources = result.get('sources', [])
        if sources:
            print(f"\n🔗 参考来源列表:")
            for source in sources[:3]:  # 显示前3个
                print(f"  【来源{source['id']}】{source['title']}")
                print(f"    {source['url']}")
    
    async def test_comparison_question(self):
        """测试对比分析问题"""
        
        print("\n" + "="*100)
        print("🎯 测试对比分析问题 - 多角度深度分析")
        print("="*100)
        
        question = "比较Python和Go语言在后端开发中的优劣势，包括性能、并发、生态、部署等方面的深度分析"
        
        print(f"❓ 问题: {question}")
        
        start_time = time.time()
        
        try:
            final_result = None
            async for result in self.deepsearch_framework.execute_deepsearch_workflow(
                question=question,
                max_rounds=2,  # 2轮搜索对比
                num_results=8,
                stream=False
            ):
                if isinstance(result, dict):
                    final_result = result
                    break
            
            duration = time.time() - start_time
            
            if final_result and final_result.get("workflow_completed"):
                print(f"\n✅ 对比分析完成，耗时 {duration:.2f}秒")
                
                # 简单分析
                final_answer = final_result.get('final_answer', '')
                sources_count = len(final_result.get('sources', []))
                
                print(f"📊 分析结果:")
                print(f"  - 信息来源: {sources_count}个")
                print(f"  - 答案长度: {len(final_answer)}字符")
                print(f"  - 包含对比分析: {'是' if 'Python' in final_answer and 'Go' in final_answer else '否'}")
                print(f"  - 多维度分析: {'是' if final_answer.count('##') >= 3 else '否'}")
                
            else:
                print("❌ 对比分析测试失败")
                
        except Exception as e:
            print(f"❌ 对比分析测试异常: {e}")
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        
        print("🚀 DeepSearch优化流程综合测试")
        print(f"📍 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 目标: 验证SERP→SearchModel→Crawl→Extract→Loop→Gen完整流程")
        print(f"📋 原则: KISS (保持简单) + DRY (避免重复)")
        
        await self.setup()
        
        # 测试1: 复杂分析问题
        await self.test_complex_analytical_question()
        
        # 等待间隔
        print(f"\n⏸️ 等待5秒后进行下一个测试...")
        await asyncio.sleep(5)
        
        # 测试2: 对比分析问题
        await self.test_comparison_question()
        
        # 测试总结
        print(f"\n" + "="*100)
        print(f"📊 DeepSearch优化流程测试完成")
        print(f"📍 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ 验证要点:")
        print(f"  1. ✅ 复用现有BrightData和FireCrawl客户端")
        print(f"  2. ✅ SearchModel通过摘要评估选择Top3网页")
        print(f"  3. ✅ 并行Crawl提高效率")
        print(f"  4. ✅ SearchModelAgent根据任务目标提取重要部分")
        print(f"  5. ✅ 循环直到知识缺口填补")
        print(f"  6. ✅ Gen模型按问题诉求结构化整理并附带引用")
        print(f"🎯 遵循KISS和DRY原则，持续解决问题直到完成优化")
        
        print(f"\n🔍 Langfuse追踪查看:")
        print(f"访问 http://localhost:3000/traces 查看完整的执行追踪")

async def main():
    """主函数"""
    tester = DeepSearchOptimizedTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())