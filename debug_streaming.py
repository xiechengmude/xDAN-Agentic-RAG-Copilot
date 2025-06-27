#!/usr/bin/env python3
"""
调试流式接口问题
"""

import asyncio
from litellm import acompletion

async def test_litellm_streaming():
    """直接测试litellm的流式功能"""
    
    messages = [
        {"role": "user", "content": "Say hello in 3 words"}
    ]
    
    print("测试1: 使用await acompletion (错误的方式)")
    try:
        # 这是错误的方式 - 会导致 'async for' 错误
        response = await acompletion(
            model="openai/deepseek-chat",
            messages=messages,
            stream=True,
            api_key="sk-f5250464c4714af2a80b789f3418feea",
            api_base="https://api.siliconflow.cn/v1"
        )
        async for chunk in response:
            print(chunk)
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*50 + "\n")
    
    print("测试2: 不使用await (正确的方式)")
    try:
        # 这是正确的方式
        response = acompletion(
            model="openai/deepseek-chat",
            messages=messages,
            stream=True,
            api_key="sk-f5250464c4714af2a80b789f3418feea",
            api_base="https://api.siliconflow.cn/v1"
        )
        async for chunk in response:
            if chunk:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
        print()
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_litellm_streaming())