#!/usr/bin/env python3
"""
直接检查Agent的输出
看看system prompt的能力是否发挥
"""

import asyncio
import yaml
import re
from pathlib import Path
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

async def check_agent_direct():
    """直接测试Agent的输出"""
    
    # 读取v1.2的agent system prompt
    prompt_path = Path("prompts/deepsearch/versions/v1.2/agent_system.txt")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        agent_system_prompt = f.read()
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 测试查询
    test_query = "Apple 2024 Q3 earnings report gross margin"
    
    print("🔍 测试Agent直接输出")
    print("="*60)
    print(f"测试查询: {test_query}")
    print("="*60)
    
    # 构造完整的用户消息（模拟DeepSearch的调用）
    user_message = f"""Current question: {test_query}

You are in the first round of search. No previous knowledge available.

Remember to:
1. Use search optimization techniques from your training
2. Generate an optimized search query, not the raw question
3. Apply relevant operators (site:, filetype:, quotes, etc.)

Please provide your search strategy and optimized query."""
    
    try:
        client = EnhancedLiteLLMClient()
        
        # 调用Agent (使用deepseek-chat模型)
        response = await client.acall_with_trace(
            model='openai/deepseek-chat',
            messages=[
                {"role": "system", "content": agent_system_prompt},
                {"role": "user", "content": user_message}
            ],
            use_case='agent',
            phase='search',
            temperature=0.1,
            max_tokens=1500
        )
        
        agent_output = response.choices[0].message.content
        
        print("\n📄 Agent完整输出:")
        print("-"*60)
        print(agent_output)
        print("-"*60)
        
        # 分析输出
        print("\n🔍 输出分析:")
        
        # 检查thinking标签
        if "<thinking>" in agent_output:
            print("✅ 包含thinking标签")
            thinking_match = re.search(r'<thinking>(.*?)</thinking>', agent_output, re.DOTALL)
            if thinking_match:
                thinking = thinking_match.group(1)[:200]
                print(f"   思考过程预览: {thinking}...")
                
                # 检查是否提到优化技巧
                optimization_keywords = ['site:', 'filetype:', 'Search Operators', 'Keyword Decomposition', 
                                       'Authority Sources', 'official', 'investor']
                mentioned = [kw for kw in optimization_keywords if kw in thinking_match.group(1)]
                if mentioned:
                    print(f"   💡 提到的优化概念: {', '.join(mentioned)}")
        else:
            print("❌ 缺少thinking标签")
        
        # 检查query标签
        if "<query>" in agent_output:
            print("\n✅ 包含query标签")
            query_match = re.search(r'<query>\s*{\s*"query":\s*"([^"]+)"\s*}\s*</query>', agent_output)
            if query_match:
                actual_query = query_match.group(1)
                print(f"   生成的查询: {actual_query}")
                
                # 对比原始查询
                print(f"\n📊 查询对比:")
                print(f"   原始: {test_query}")
                print(f"   优化: {actual_query}")
                
                # 检查优化技巧
                print(f"\n🔧 使用的优化技巧:")
                optimizations = []
                
                if actual_query == test_query:
                    print("   ❌ 查询未优化（与原始相同）")
                else:
                    if 'site:' in actual_query:
                        optimizations.append("✓ site:操作符")
                    if 'filetype:' in actual_query:
                        optimizations.append("✓ filetype:操作符")
                    if '"' in actual_query:
                        optimizations.append("✓ 精确短语（引号）")
                    if ' OR ' in actual_query or ' AND ' in actual_query:
                        optimizations.append("✓ 布尔操作符")
                    if 'investor' in actual_query.lower() or 'official' in actual_query.lower():
                        optimizations.append("✓ 权威来源关键词")
                    if '2024' in actual_query or 'Q3' in actual_query:
                        optimizations.append("✓ 时间限定词")
                    
                    if optimizations:
                        for opt in optimizations:
                            print(f"   {opt}")
                    else:
                        print("   ⚠️ 有变化但未使用明显的搜索操作符")
        else:
            print("❌ 缺少query标签")
        
        # 测试中文查询
        print("\n\n🌏 测试中文查询:")
        print("="*60)
        
        chinese_query = "苹果公司2024年第三季度财报毛利率"
        user_message_cn = f"""Current question: {chinese_query}

You are in the first round of search. No previous knowledge available.

Remember to use search optimization techniques."""
        
        response_cn = await client.acall_with_trace(
            model='openai/deepseek-chat',
            messages=[
                {"role": "system", "content": agent_system_prompt},
                {"role": "user", "content": user_message_cn}
            ],
            use_case='agent',
            phase='search',
            temperature=0.1,
            max_tokens=1000
        )
        
        agent_output_cn = response_cn.choices[0].message.content
        
        # 只提取查询部分
        query_match_cn = re.search(r'<query>\s*{\s*"query":\s*"([^"]+)"\s*}\s*</query>', agent_output_cn)
        if query_match_cn:
            actual_query_cn = query_match_cn.group(1)
            print(f"中文原始查询: {chinese_query}")
            print(f"Agent优化查询: {actual_query_cn}")
            
            if actual_query_cn == chinese_query:
                print("❌ 中文查询未被优化")
            else:
                print("✅ 中文查询已优化")
                
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_agent_direct())