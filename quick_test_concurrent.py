#!/usr/bin/env python3
"""
快速并发搜索测试 - 验证基本功能
"""

import asyncio
import time
import logging
import os
import sys
from datetime import datetime

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手动读取.env文件
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.litellm_client import LiteLLMSDKClientV2

# 设置日志级别为WARNING，减少输出
logging.basicConfig(level=logging.WARNING)

async def quick_test():
    """快速测试并发搜索功能"""
    print("🚀 快速并发搜索测试")
    
    try:
        # 初始化
        litellm_client = LiteLLMSDKClientV2()
        framework = DeepSearchFramework(litellm_client=litellm_client, config={})
        
        # 简单测试问题
        question = "人工智能的发展趋势"
        
        print(f"📝 测试问题: {question}")
        
        # 测试不同模式
        modes = [
            ("single", "单次搜索"),
            ("smart", "并发扩展"),
            ("flash", "并发拆分")
        ]
        
        results = {}
        
        for mode, desc in modes:
            print(f"\n🔍 测试 {desc} ({mode})...")
            start_time = time.time()
            
            try:
                result = None
                async for result in framework.execute_deepsearch_workflow(
                    question=question,
                    max_rounds=1,  # 只测试1轮
                    search_mode=mode
                ):
                    result = result
                    break
                
                duration = time.time() - start_time
                
                if result and result.get('final_answer'):
                    answer_length = len(result.get('final_answer', ''))
                    rounds = len(result.get('rounds', []))
                    results[mode] = {
                        'success': True,
                        'duration': duration,
                        'answer_length': answer_length,
                        'rounds': rounds
                    }
                    print(f"✅ {desc}: {duration:.1f}秒, {rounds}轮, {answer_length}字符")
                    
                    # 显示搜索查询
                    if result.get('rounds'):
                        first_round = result['rounds'][0]
                        query = first_round.get('search_query', '未知')
                        print(f"   搜索查询: {query}")
                else:
                    results[mode] = {'success': False, 'duration': duration}
                    print(f"❌ {desc}: 失败")
                    
            except Exception as e:
                duration = time.time() - start_time
                results[mode] = {'success': False, 'duration': duration, 'error': str(e)}
                print(f"❌ {desc}: 异常 - {e}")
        
        # 分析结果
        print(f"\n📊 结果对比:")
        success_count = sum(1 for r in results.values() if r['success'])
        
        if success_count > 0:
            for mode, desc in modes:
                if mode in results and results[mode]['success']:
                    r = results[mode]
                    print(f"  {desc}: {r['duration']:.1f}秒, {r['answer_length']}字符")
            
            # 检查并发搜索是否生效
            flash_success = results.get('flash', {}).get('success', False)
            smart_success = results.get('smart', {}).get('success', False)
            
            if flash_success or smart_success:
                print("✅ 并发搜索功能正常工作！")
                return True
            else:
                print("⚠️ 并发搜索功能可能有问题")
                return False
        else:
            print("❌ 所有测试都失败了")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\n🎉 并发搜索功能验证成功！")
        print("可以继续进行完整的50问题测试。")
    else:
        print("\n⚠️ 功能验证失败，请检查实现。")