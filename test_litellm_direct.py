#!/usr/bin/env python3
"""
直接测试 litellm 的流式行为
"""

import asyncio
from litellm import acompletion

async def test_litellm_streaming():
    messages = [{"role": "user", "content": "Say hello in 3 words"}]
    
    print("测试1: 尝试直接使用 acompletion (不带 await)")
    try:
        response = acompletion(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )
        print(f"返回类型: {type(response)}")
        print(f"是否是协程: {asyncio.iscoroutine(response)}")
        print(f"是否是异步生成器: {hasattr(response, '__aiter__')}")
        
        if asyncio.iscoroutine(response):
            print("\n这是一个协程，需要 await")
            actual_stream = await response
            print(f"await 后的类型: {type(actual_stream)}")
            print(f"是否是异步生成器: {hasattr(actual_stream, '__aiter__')}")
            
            if hasattr(actual_stream, '__aiter__'):
                print("\n开始读取流式数据:")
                async for chunk in actual_stream:
                    if chunk:
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            print(content, end="", flush=True)
                print("\n完成!")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_litellm_streaming())