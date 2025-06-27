#!/usr/bin/env python3
"""
测试流式响应修复
"""

import asyncio
from src.clients.litellm_client_fixed import LiteLLMSDKClientV2Fixed
import yaml

async def test_streaming():
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    client = LiteLLMSDKClientV2Fixed(config)
    
    messages = [{"role": "user", "content": "Say hello"}]
    
    print("测试流式响应...")
    try:
        stream = await client.chat_completion(
            messages=messages,
            stream=True
        )
        
        print("开始接收流式数据:")
        async for chunk in stream:
            if chunk:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
        print("\n流式响应完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())