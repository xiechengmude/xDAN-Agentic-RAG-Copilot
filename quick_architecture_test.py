#!/usr/bin/env python3
"""
快速架构决策测试 - 基于prompt分析不需要实际搜索
评估Agent vs SearchModel的职责划分
"""

import json
import logging
import sys
import os
import asyncio
import yaml
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
for logger in ['httpx', 'openai', 'LiteLLM', 'urllib3', 'firecrawl']:
    logging.getLogger(logger).setLevel(logging.WARNING)

class QuickArchitectureTest:
    def __init__(self):
        self.client = EnhancedLiteLLMClient()
        
    async def test_prompt_comparison(self):
        """对比Agent和SearchModel在决策质量上的差异"""
        
        print("🏛️ 快速架构决策测试")
        print("目标: 基于prompt质量评估Agent是否应该接管SearchModel")
        print("="*80)
        
        # 测试场景
        test_scenario = {
            "question": "分析苹果公司2024年的财务表现和市场竞争地位",
            "mock_search_results": [
                {
                    "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240930.htm",
                    "title": "Apple Inc. - Form 10-K - Annual Report 2024",
                    "snippet": "Apple Inc. annual report for fiscal year 2024, including financial statements, revenue, and business overview"
                },
                {
                    "url": "https://www.apple.com/newsroom/2024/11/apple-reports-fourth-quarter-results/",
                    "title": "Apple Reports Fourth Quarter 2024 Results",
                    "snippet": "Apple today announced financial results for its fiscal 2024 fourth quarter. Revenue up 6% year over year"
                },
                {
                    "url": "https://www.idc.com/getdoc.jsp?containerId=prUS52032024",
                    "title": "IDC Smartphone Market Share Report Q4 2024",
                    "snippet": "Global smartphone market share analysis for Q4 2024, including Apple's position"
                },
                {
                    "url": "https://www.statista.com/statistics/apple-financial-performance-2024/",
                    "title": "Apple Inc. - Financial Performance Statistics 2024",
                    "snippet": "Comprehensive statistics on Apple's financial performance in 2024"
                }
            ]
        }
        
        print(f"测试场景: {test_scenario['question']}")
        print(f"模拟搜索结果: {len(test_scenario['mock_search_results'])}个")
        
        # 测试1: 当前SearchModel决策
        print(f"\n{'='*50}")
        print("🔄 测试1: SearchModel决策能力")
        print(f"{'='*50}")
        
        searchmodel_result = await self._test_searchmodel_decision(test_scenario)
        
        # 测试2: 统一Agent决策
        print(f"\n{'='*50}")
        print("🔄 测试2: 统一Agent决策能力")
        print(f"{'='*50}")
        
        unified_agent_result = await self._test_unified_agent_decision(test_scenario)
        
        # 对比分析
        self._compare_decision_quality(searchmodel_result, unified_agent_result)
        
    async def _test_searchmodel_decision(self, scenario: Dict) -> Dict:
        """测试SearchModel的决策能力"""
        
        # 加载SearchModel prompt
        try:
            with open('prompts/deepsearch/versions/v1.2.1/searchmodel_system.txt', 'r', encoding='utf-8') as f:
                searchmodel_prompt = f.read()
        except:
            print("⚠️ SearchModel prompt未找到")
            return {"error": "prompt not found"}
        
        # 构造决策请求
        decision_request = f"""
问题: {scenario['question']}

搜索结果:
"""
        for i, result in enumerate(scenario['mock_search_results'], 1):
            decision_request += f"{i}. {result['title']}\n"
            decision_request += f"   URL: {result['url']}\n"
            decision_request += f"   摘要: {result['snippet']}\n\n"
        
        decision_request += """
请按照你的系统prompt格式，分析这些搜索结果并做出决策。
"""
        
        start_time = datetime.now()
        
        try:
            response = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": searchmodel_prompt},
                    {"role": "user", "content": decision_request}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # 分析决策质量
            quality_score = self._analyze_decision_quality(response_text)
            
            result = {
                "architecture": "searchmodel",
                "response": response_text,
                "quality_score": quality_score,
                "response_time": (datetime.now() - start_time).total_seconds(),
                "success": True
            }
            
            print(f"SearchModel决策:")
            print(f"  响应时间: {result['response_time']:.1f}s")
            print(f"  质量分数: {quality_score*100:.1f}%")
            print(f"  响应长度: {len(response_text)}字符")
            
            return result
            
        except Exception as e:
            print(f"❌ SearchModel测试失败: {e}")
            return {"error": str(e), "architecture": "searchmodel"}
    
    async def _test_unified_agent_decision(self, scenario: Dict) -> Dict:
        """测试统一Agent的决策能力"""
        
        # 加载统一Agent prompt
        try:
            with open('prompts/deepsearch/versions/v1.2.1/unified_agent_system.txt', 'r', encoding='utf-8') as f:
                unified_prompt = f.read()
        except:
            print("⚠️ 统一Agent prompt未找到")
            return {"error": "prompt not found"}
        
        # 构造决策请求
        decision_request = f"""
问题: {scenario['question']}

搜索结果:
"""
        for i, result in enumerate(scenario['mock_search_results'], 1):
            decision_request += f"{i}. {result['title']}\n"
            decision_request += f"   URL: {result['url']}\n"
            decision_request += f"   摘要: {result['snippet']}\n\n"
        
        decision_request += """
请按照你的系统prompt格式，分析这些搜索结果并做出决策。
"""
        
        start_time = datetime.now()
        
        try:
            response = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": unified_prompt},
                    {"role": "user", "content": decision_request}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # 分析决策质量
            quality_score = self._analyze_decision_quality(response_text)
            
            result = {
                "architecture": "unified_agent",
                "response": response_text,
                "quality_score": quality_score,
                "response_time": (datetime.now() - start_time).total_seconds(),
                "success": True
            }
            
            print(f"统一Agent决策:")
            print(f"  响应时间: {result['response_time']:.1f}s")
            print(f"  质量分数: {quality_score*100:.1f}%")
            print(f"  响应长度: {len(response_text)}字符")
            
            return result
            
        except Exception as e:
            print(f"❌ 统一Agent测试失败: {e}")
            return {"error": str(e), "architecture": "unified_agent"}
    
    def _analyze_decision_quality(self, response: str) -> float:
        """分析决策质量"""
        score = 0.0
        
        # 思考过程质量 (40%)
        if '<thinking>' in response and '</thinking>' in response:
            thinking_content = response.split('<thinking>')[1].split('</thinking>')[0]
            thinking_indicators = [
                '分析' in thinking_content or 'analysis' in thinking_content.lower(),
                '评估' in thinking_content or 'evaluate' in thinking_content.lower(),
                'URL' in thinking_content,
                len(thinking_content) > 200,  # 足够详细
                '质量' in thinking_content or 'quality' in thinking_content.lower()
            ]
            score += sum(thinking_indicators) / len(thinking_indicators) * 0.4
        
        # 格式规范性 (30%)
        format_indicators = [
            '<search_complete>' in response,
            '<important_urls>' in response,
            '<next_query>' in response or 'search_complete>true' in response,
            '</thinking>' in response
        ]
        score += sum(format_indicators) / len(format_indicators) * 0.3
        
        # 内容深度 (30%)
        depth_indicators = [
            '权威' in response or 'authority' in response.lower(),
            '相关' in response or 'relevant' in response.lower(),
            '缺口' in response or 'gap' in response.lower(),
            len(response) > 500,  # 足够详细的分析
            '策略' in response or 'strategy' in response.lower()
        ]
        score += sum(depth_indicators) / len(depth_indicators) * 0.3
        
        return min(score, 1.0)
    
    def _compare_decision_quality(self, searchmodel_result: Dict, unified_result: Dict):
        """对比决策质量"""
        
        print(f"\n{'='*80}")
        print("📊 架构决策质量对比")
        print(f"{'='*80}")
        
        if searchmodel_result.get('error') or unified_result.get('error'):
            print("❌ 测试出现错误，无法完成对比")
            return
        
        # 质量对比
        searchmodel_quality = searchmodel_result.get('quality_score', 0) * 100
        unified_quality = unified_result.get('quality_score', 0) * 100
        
        print(f"🧠 决策质量对比:")
        print(f"  SearchModel质量: {searchmodel_quality:.1f}%")
        print(f"  统一Agent质量: {unified_quality:.1f}%")
        
        quality_diff = unified_quality - searchmodel_quality
        print(f"  质量差异: {quality_diff:+.1f}%")
        
        # 性能对比
        searchmodel_time = searchmodel_result.get('response_time', 0)
        unified_time = unified_result.get('response_time', 0)
        
        print(f"\n⚡ 响应时间对比:")
        print(f"  SearchModel响应时间: {searchmodel_time:.1f}s")
        print(f"  统一Agent响应时间: {unified_time:.1f}s")
        
        if searchmodel_time > 0:
            time_improvement = (searchmodel_time - unified_time) / searchmodel_time * 100
            print(f"  时间改进: {time_improvement:+.1f}%")
        
        # 架构复杂度分析
        print(f"\n🏗️ 架构复杂度评估:")
        print(f"  当前架构:")
        print(f"    - 需要维护Agent + SearchModel两套prompt")
        print(f"    - 需要处理Agent→SearchModel的上下文传递")
        print(f"    - 调试时需要分析两个决策点")
        print(f"    - 每轮需要2次LLM调用")
        
        print(f"  统一Agent架构:")
        print(f"    - 只需维护一套综合prompt")
        print(f"    - 内部决策一致性更好")
        print(f"    - 调试时只需分析一个决策点")
        print(f"    - 每轮只需1次LLM调用")
        
        # 最终建议
        print(f"\n🎯 架构决策建议:")
        
        # 计算综合分数
        quality_weight = 0.6
        performance_weight = 0.4
        
        unified_score = (
            (unified_quality / 100) * quality_weight +
            (1 if unified_time <= searchmodel_time else 0) * performance_weight
        )
        
        searchmodel_score = (
            (searchmodel_quality / 100) * quality_weight +
            (1 if searchmodel_time <= unified_time else 0) * performance_weight
        )
        
        if unified_score > searchmodel_score:
            print("✅ 强烈建议采用统一Agent架构")
            print("理由:")
            print("  • 决策质量更高，思考过程更连贯")
            print("  • 架构简化，降低维护成本")
            print("  • 减少LLM调用，提升性能和成本效益")
            print("  • 消除双Agent间的上下文传递问题")
        else:
            print("⚠️ 建议保持当前双Agent架构")
            print("理由:")
            print("  • SearchModel专业化决策质量更高")
            print("  • 职责分离更清晰")
        
        # 保存对比报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "searchmodel_result": searchmodel_result,
            "unified_agent_result": unified_result,
            "quality_comparison": {
                "searchmodel_quality": searchmodel_quality,
                "unified_quality": unified_quality,
                "quality_improvement": quality_diff
            },
            "performance_comparison": {
                "searchmodel_time": searchmodel_time,
                "unified_time": unified_time,
                "time_improvement": time_improvement if searchmodel_time > 0 else 0
            },
            "recommendation": "unified_agent" if unified_score > searchmodel_score else "searchmodel"
        }
        
        report_file = f"quick_architecture_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细对比报告已保存: {report_file}")

async def main():
    tester = QuickArchitectureTest()
    await tester.test_prompt_comparison()

if __name__ == "__main__":
    asyncio.run(main())