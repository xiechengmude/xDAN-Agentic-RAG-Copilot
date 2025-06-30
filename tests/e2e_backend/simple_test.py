#!/usr/bin/env python3
"""
简化的单问题测试 - 验证系统工作
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

async def test_single_simple():
    """测试一个简单问题"""
    
    # 简单问题
    question = "什么是人工智能的基本定义？"
    
    print(f"测试问题: {question}")
    
    # 创建框架
    client = EnhancedLiteLLMClient()
    framework = DeepSearchFramework(client)
    
    start_time = datetime.now()
    result_parts = []
    
    try:
        # 收集结果
        async for chunk in framework.execute_deepsearch_workflow(
            question=question,
            max_rounds=1  # 只要1轮
        ):
            result_parts.append(chunk)
            print(f"收到chunk: {type(chunk)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_result = result_parts[-1] if result_parts else None
        
        print(f"测试完成，耗时: {duration:.2f}秒")
        print(f"结果类型: {type(final_result)}")
        print(f"结果: {final_result}")
        
        # 保存结果
        trace_data = {
            "question": question,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "result": final_result,
            "success": True
        }
        
        # 保存到文件
        with open('tests/e2e_backend/traces/simple_test_trace.json', 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)
        
        print("结果已保存到 simple_test_trace.json")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        trace_data = {
            "question": question,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "result": None,
            "success": False,
            "error": str(e)
        }
        
        with open('tests/e2e_backend/traces/simple_test_trace.json', 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(test_single_simple())