#!/usr/bin/env python3
"""
根据官方文档测试 litellm 的正确用法
"""

import asyncio
from litellm import acompletion
import yaml

async def test_streaming_correct():
    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # 获取 OpenAI 配置
    openai_config = config['llm_providers']['openai']
    
    messages = [{"role": "user", "content": "Say hello in 3 words"}]
    
    print("根据官方文档的正确用法:")
    try:
        # 1. 先 await acompletion 得到 response
        response = await acompletion(
            model="openai/deepseek-chat",
            messages=messages,
            stream=True,
            api_key=openai_config['api_key'],
            api_base=openai_config['base_url']
        )
        
        print(f"Response 类型: {type(response)}")
        
        # 2. 然后 async for 遍历 response
        print("\n开始接收流式数据:")
        async for chunk in response:
            if chunk:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
        
        print("\n\n流式响应完成！")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_correct())