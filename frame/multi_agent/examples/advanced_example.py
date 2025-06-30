#!/usr/bin/env python3
"""
高级示例 - 演示复杂的多智能体协调和工作流
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from frame.multi_agent.core.coordinator import MultiAgentCoordinator
from frame.multi_agent.core.message import Message, MessageType, TaskMessage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AdvancedSearchCoordinator(MultiAgentCoordinator):
    """高级搜索协调器 - 支持自定义工作流"""
    
    def __init__(self, name: str = "AdvancedSearchCoordinator"):
        super().__init__(name)
        
        # 自定义工作流
        self.custom_workflows = {}
        
        # 结果缓存
        self.result_cache = {}
    
    async def execute_comparative_analysis(self, topic_a: str, topic_b: str) -> Dict[str, Any]:
        """执行对比分析工作流"""
        workflow_id = f"compare_{datetime.now().timestamp()}"
        
        try:
            self.logger.info(f"Starting comparative analysis: {topic_a} vs {topic_b}")
            
            # 并行搜索两个主题
            search_tasks = [
                self._execute_search_step(f"{topic_a} 详细分析", num_results=8),
                self._execute_search_step(f"{topic_b} 详细分析", num_results=8)
            ]
            
            search_results = await asyncio.gather(*search_tasks)
            search_a, search_b = search_results
            
            # 并行分析两个主题
            analysis_tasks = [
                self._execute_analysis_step(search_a, f"分析{topic_a}的特点"),
                self._execute_analysis_step(search_b, f"分析{topic_b}的特点")
            ]
            
            analysis_results = await asyncio.gather(*analysis_tasks)
            analysis_a, analysis_b = analysis_results
            
            # 执行对比综合
            comparison_task = TaskMessage(
                task_type="compare_sources",
                task_data={
                    "question": f"比较{topic_a}和{topic_b}",
                    "sources_info": [
                        {
                            "title": f"{topic_a}分析",
                            "content": str(analysis_a.get("analysis_result", {}))
                        },
                        {
                            "title": f"{topic_b}分析", 
                            "content": str(analysis_b.get("analysis_result", {}))
                        }
                    ]
                },
                sender=self.name,
                receiver="synthesis_agent"
            )
            
            comparison_result = await self._send_task_and_wait(comparison_task, timeout=60)
            
            return {
                "workflow_id": workflow_id,
                "topic_a": topic_a,
                "topic_b": topic_b,
                "search_results": {
                    "topic_a": search_a,
                    "topic_b": search_b
                },
                "analysis_results": {
                    "topic_a": analysis_a,
                    "topic_b": analysis_b
                },
                "comparison": comparison_result,
                "workflow_status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"Comparative analysis failed: {e}")
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_status": "failed"
            }
    
    async def execute_deep_research(self, research_topic: str, aspects: List[str]) -> Dict[str, Any]:
        """执行深度研究工作流"""
        workflow_id = f"research_{datetime.now().timestamp()}"
        
        try:
            self.logger.info(f"Starting deep research on: {research_topic}")
            
            # 为每个研究方面创建搜索任务
            search_tasks = []
            for aspect in aspects:
                query = f"{research_topic} {aspect}"
                search_tasks.append(self._execute_search_step(query, num_results=6))
            
            # 并行执行所有搜索
            search_results = await asyncio.gather(*search_tasks)
            
            # 分析每个方面
            analysis_tasks = []
            for i, aspect in enumerate(aspects):
                if i < len(search_results):
                    analysis_tasks.append(
                        self._execute_analysis_step(
                            search_results[i], 
                            f"分析{research_topic}在{aspect}方面的情况"
                        )
                    )
            
            analysis_results = await asyncio.gather(*analysis_tasks)
            
            # 综合所有研究结果
            synthesis_task = TaskMessage(
                task_type="final_answer",
                task_data={
                    "question": f"深度研究{research_topic}",
                    "collected_info": {
                        "research_aspects": aspects,
                        "total_sources": sum(len(sr.get("results", [])) for sr in search_results)
                    },
                    "search_results": [result for results in search_results for result in results.get("results", [])],
                    "analysis_results": {
                        f"aspect_{i}": result for i, result in enumerate(analysis_results)
                    }
                },
                sender=self.name,
                receiver="synthesis_agent"
            )
            
            synthesis_result = await self._send_task_and_wait(synthesis_task, timeout=90)
            
            return {
                "workflow_id": workflow_id,
                "research_topic": research_topic,
                "research_aspects": aspects,
                "aspect_results": {
                    aspects[i]: {
                        "search": search_results[i] if i < len(search_results) else {},
                        "analysis": analysis_results[i] if i < len(analysis_results) else {}
                    }
                    for i in range(len(aspects))
                },
                "synthesis": synthesis_result,
                "workflow_status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"Deep research failed: {e}")
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_status": "failed"
            }
    
    async def execute_trend_analysis(self, topic: str, time_periods: List[str]) -> Dict[str, Any]:
        """执行趋势分析工作流"""
        workflow_id = f"trend_{datetime.now().timestamp()}"
        
        try:
            self.logger.info(f"Starting trend analysis for: {topic}")
            
            # 为每个时间段创建搜索
            search_tasks = []
            for period in time_periods:
                query = f"{topic} {period} 发展 趋势"
                search_tasks.append(self._execute_search_step(query, num_results=5))
            
            search_results = await asyncio.gather(*search_tasks)
            
            # 分析每个时间段
            analysis_tasks = []
            for i, period in enumerate(time_periods):
                if i < len(search_results):
                    analysis_tasks.append(
                        self._execute_analysis_step(
                            search_results[i],
                            f"分析{topic}在{period}的发展状况"
                        )
                    )
            
            analysis_results = await asyncio.gather(*analysis_tasks)
            
            # 趋势对比分析
            trend_comparison_task = TaskMessage(
                task_type="compare_sources",
                task_data={
                    "question": f"{topic}的发展趋势对比",
                    "sources_info": [
                        {
                            "title": f"{period}时期",
                            "content": str(analysis_results[i].get("analysis_result", {}))
                        }
                        for i, period in enumerate(time_periods)
                        if i < len(analysis_results)
                    ]
                },
                sender=self.name,
                receiver="synthesis_agent"
            )
            
            trend_result = await self._send_task_and_wait(trend_comparison_task, timeout=60)
            
            return {
                "workflow_id": workflow_id,
                "topic": topic,
                "time_periods": time_periods,
                "period_analysis": {
                    time_periods[i]: {
                        "search": search_results[i] if i < len(search_results) else {},
                        "analysis": analysis_results[i] if i < len(analysis_results) else {}
                    }
                    for i in range(len(time_periods))
                },
                "trend_comparison": trend_result,
                "workflow_status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_status": "failed"
            }


async def comparative_analysis_demo():
    """对比分析演示"""
    print("🔍 高级对比分析演示")
    print("=" * 60)
    
    coordinator = AdvancedSearchCoordinator("comparative_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        # 执行对比分析
        result = await coordinator.execute_comparative_analysis(
            topic_a="React框架",
            topic_b="Vue.js框架"
        )
        
        if result.get("workflow_status") == "completed":
            print(f"\n✅ 对比分析完成!")
            print(f"主题A: {result['topic_a']}")
            print(f"主题B: {result['topic_b']}")
            
            # 显示搜索结果统计
            search_a_count = len(result["search_results"]["topic_a"].get("results", []))
            search_b_count = len(result["search_results"]["topic_b"].get("results", []))
            print(f"搜索结果: A={search_a_count}, B={search_b_count}")
            
            # 显示对比结果
            comparison = result.get("comparison", {}).get("synthesis_result", {})
            if comparison and "comparison" in comparison:
                print(f"\n📊 对比分析结果:")
                print("-" * 40)
                comp_text = comparison["comparison"]
                print(comp_text[:400] + "..." if len(comp_text) > 400 else comp_text)
        else:
            print(f"\n❌ 对比分析失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 对比分析演示失败: {e}")
    
    finally:
        await coordinator.stop()


async def deep_research_demo():
    """深度研究演示"""
    print("\n\n🔬 深度研究演示")
    print("=" * 60)
    
    coordinator = AdvancedSearchCoordinator("research_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        # 执行深度研究
        result = await coordinator.execute_deep_research(
            research_topic="人工智能",
            aspects=["技术发展", "应用领域", "未来趋势"]
        )
        
        if result.get("workflow_status") == "completed":
            print(f"\n✅ 深度研究完成!")
            print(f"研究主题: {result['research_topic']}")
            print(f"研究方面: {', '.join(result['research_aspects'])}")
            
            # 显示各方面研究结果
            for aspect in result['research_aspects']:
                aspect_data = result['aspect_results'].get(aspect, {})
                search_count = len(aspect_data.get('search', {}).get('results', []))
                print(f"\n📋 {aspect}:")
                print(f"  搜索结果: {search_count} 个")
                
                analysis = aspect_data.get('analysis', {}).get('analysis_result', {})
                if analysis and 'summary' in analysis:
                    summary = analysis['summary'].get('summary', '')
                    if summary:
                        print(f"  分析摘要: {summary[:100]}...")
            
            # 显示综合结果
            synthesis = result.get('synthesis', {}).get('synthesis_result', {})
            if synthesis and 'final_answer' in synthesis:
                print(f"\n📝 综合研究结果:")
                print("-" * 40)
                final_answer = synthesis['final_answer']
                print(final_answer[:300] + "..." if len(final_answer) > 300 else final_answer)
        else:
            print(f"\n❌ 深度研究失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 深度研究演示失败: {e}")
    
    finally:
        await coordinator.stop()


async def trend_analysis_demo():
    """趋势分析演示"""
    print("\n\n📈 趋势分析演示")
    print("=" * 60)
    
    coordinator = AdvancedSearchCoordinator("trend_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        # 执行趋势分析
        result = await coordinator.execute_trend_analysis(
            topic="电动汽车市场",
            time_periods=["2020年", "2022年", "2024年"]
        )
        
        if result.get("workflow_status") == "completed":
            print(f"\n✅ 趋势分析完成!")
            print(f"分析主题: {result['topic']}")
            print(f"时间段: {', '.join(result['time_periods'])}")
            
            # 显示各时间段分析
            for period in result['time_periods']:
                period_data = result['period_analysis'].get(period, {})
                search_count = len(period_data.get('search', {}).get('results', []))
                print(f"\n📅 {period}:")
                print(f"  信息源: {search_count} 个")
            
            # 显示趋势对比
            trend_comparison = result.get('trend_comparison', {}).get('synthesis_result', {})
            if trend_comparison and 'comparison' in trend_comparison:
                print(f"\n📊 趋势对比分析:")
                print("-" * 40)
                comparison_text = trend_comparison['comparison']
                print(comparison_text[:400] + "..." if len(comparison_text) > 400 else comparison_text)
        else:
            print(f"\n❌ 趋势分析失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 趋势分析演示失败: {e}")
    
    finally:
        await coordinator.stop()


async def performance_test():
    """性能测试"""
    print("\n\n⚡ 性能测试")
    print("=" * 60)
    
    coordinator = AdvancedSearchCoordinator("perf_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        # 测试多个并发搜索
        start_time = datetime.now()
        
        tasks = [
            coordinator.execute_search_workflow("Python编程", num_results=3),
            coordinator.execute_search_workflow("机器学习基础", num_results=3),
            coordinator.execute_search_workflow("云计算技术", num_results=3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful = len([r for r in results if isinstance(r, dict) and r.get("workflow_status") == "completed"])
        
        print(f"\n📊 性能测试结果:")
        print(f"  并发任务数: {len(tasks)}")
        print(f"  成功完成: {successful}/{len(tasks)}")
        print(f"  总耗时: {duration:.1f}秒")
        print(f"  平均耗时: {duration/len(tasks):.1f}秒/任务")
        
        # 显示协调器统计
        stats = coordinator.get_stats()
        print(f"\n📈 协调器统计:")
        print(f"  处理消息: {stats['messages_processed']}")
        print(f"  失败消息: {stats['messages_failed']}")
        
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
    
    finally:
        await coordinator.stop()


async def main():
    """主演示函数"""
    print("🚀 高级多智能体框架演示")
    print("展示复杂的工作流和智能体协调")
    print("=" * 80)
    
    # 运行各种高级演示
    await comparative_analysis_demo()
    await deep_research_demo()
    await trend_analysis_demo()
    await performance_test()
    
    print("\n\n🎉 所有高级演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 设置环境变量
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    
    # 运行高级演示
    asyncio.run(main())