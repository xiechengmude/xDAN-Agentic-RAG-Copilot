#!/usr/bin/env python3
"""
基础示例 - 演示多智能体框架的基本使用
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from frame.multi_agent.core.coordinator import MultiAgentCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 减少噪音日志
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def basic_search_demo():
    """基础搜索演示"""
    print("🤖 多智能体基础搜索演示")
    print("=" * 60)
    
    # 创建协调器
    coordinator = MultiAgentCoordinator("demo_coordinator")
    
    try:
        # 启动协调器
        await coordinator.start()
        
        # 设置默认智能体
        await coordinator.setup_default_agents()
        
        # 列出智能体
        agents = coordinator.list_agents()
        print(f"\n📋 已创建智能体: {len(agents)} 个")
        for agent in agents:
            print(f"  - {agent['name']}: {agent['description']}")
        
        # 执行搜索工作流
        question = "什么是人工智能的发展历史？"
        print(f"\n🔍 执行搜索工作流")
        print(f"问题: {question}")
        
        result = await coordinator.execute_search_workflow(
            question=question,
            num_results=5,
            include_crawl=True
        )
        
        # 显示结果
        if result.get("workflow_status") == "completed":
            print(f"\n✅ 搜索完成!")
            print(f"耗时: {result.get('duration', 0):.1f}秒")
            print(f"搜索结果数: {len(result.get('search_results', []))}")
            
            final_answer = result.get("final_answer", "")
            if final_answer:
                print(f"\n📝 最终答案:")
                print("-" * 40)
                print(final_answer[:500] + "..." if len(final_answer) > 500 else final_answer)
            
            # 显示信息源
            search_results = result.get("search_results", [])
            if search_results:
                print(f"\n📚 信息来源:")
                for i, source in enumerate(search_results[:3], 1):
                    print(f"  {i}. {source.get('title', 'N/A')}")
                    print(f"     {source.get('link', 'N/A')}")
        else:
            print(f"\n❌ 搜索失败: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 停止协调器
        await coordinator.stop()
        print(f"\n🔚 演示结束")


async def multi_round_demo():
    """多轮搜索演示"""
    print("\n\n🔄 多轮搜索演示")
    print("=" * 60)
    
    coordinator = MultiAgentCoordinator("multi_round_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        question = "比较特斯拉和比亚迪在电动车市场的竞争策略"
        print(f"\n🔍 执行多轮搜索工作流")
        print(f"问题: {question}")
        
        result = await coordinator.execute_multi_round_search(
            question=question,
            max_rounds=2,  # 限制轮数以节省时间
            num_results=5
        )
        
        if result.get("workflow_status") == "completed":
            print(f"\n✅ 多轮搜索完成!")
            print(f"总轮数: {result.get('total_rounds', 0)}")
            print(f"总信息源: {len(result.get('all_search_results', []))}")
            
            # 显示轮次详情
            round_details = result.get("round_details", [])
            for round_data in round_details:
                round_num = round_data.get("round", 0)
                query = round_data.get("query", "")
                search_count = len(round_data.get("search_result", {}).get("results", []))
                print(f"\n  第{round_num}轮:")
                print(f"    查询: {query}")
                print(f"    结果: {search_count} 个")
            
            # 显示最终答案
            final_answer = result.get("final_answer", "")
            if final_answer:
                print(f"\n📝 最终综合答案:")
                print("-" * 40)
                print(final_answer[:400] + "..." if len(final_answer) > 400 else final_answer)
        else:
            print(f"\n❌ 多轮搜索失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ 多轮搜索演示失败: {e}")
        
    finally:
        await coordinator.stop()


async def agent_stats_demo():
    """智能体统计演示"""
    print("\n\n📊 智能体统计演示")
    print("=" * 60)
    
    coordinator = MultiAgentCoordinator("stats_coordinator")
    
    try:
        await coordinator.start()
        await coordinator.setup_default_agents()
        
        # 执行几个简单的任务
        questions = [
            "什么是机器学习？",
            "Python编程语言的特点"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n执行第{i}个任务: {question}")
            result = await coordinator.execute_search_workflow(
                question=question,
                num_results=3
            )
            
            if result.get("workflow_status") == "completed":
                print(f"  ✅ 完成 ({result.get('duration', 0):.1f}秒)")
            else:
                print(f"  ❌ 失败")
        
        # 显示统计信息
        print(f"\n📈 协调器统计:")
        stats = coordinator.get_stats()
        print(f"  - 智能体数量: {stats['agents_count']}")
        print(f"  - 处理消息数: {stats['messages_processed']}")
        print(f"  - 失败消息数: {stats['messages_failed']}")
        print(f"  - 运行时间: {stats.get('uptime_seconds', 0):.1f}秒")
        
        # 显示各智能体统计
        for agent_name in ["search_agent", "analysis_agent", "synthesis_agent"]:
            agent = coordinator.get_agent(agent_name)
            if agent:
                if hasattr(agent, 'get_search_stats'):
                    agent_stats = agent.get_search_stats()
                    print(f"\n📊 {agent_name} 统计:")
                    for key, value in agent_stats.items():
                        print(f"    {key}: {value}")
                elif hasattr(agent, 'get_analysis_stats'):
                    agent_stats = agent.get_analysis_stats()
                    print(f"\n📊 {agent_name} 统计:")
                    for key, value in agent_stats.items():
                        print(f"    {key}: {value}")
                elif hasattr(agent, 'get_synthesis_stats'):
                    agent_stats = agent.get_synthesis_stats()
                    print(f"\n📊 {agent_name} 统计:")
                    for key, value in agent_stats.items():
                        print(f"    {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ 统计演示失败: {e}")
        
    finally:
        await coordinator.stop()


async def main():
    """主演示函数"""
    print("🚀 多智能体框架演示")
    print("这是一个纯后端的多智能体架构，无需API服务器")
    print("=" * 80)
    
    # 运行各种演示
    await basic_search_demo()
    await multi_round_demo()
    await agent_stats_demo()
    
    print("\n\n🎉 所有演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 设置环境变量
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    
    # 运行演示
    asyncio.run(main())