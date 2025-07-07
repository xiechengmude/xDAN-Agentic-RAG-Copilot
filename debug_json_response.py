#!/usr/bin/env python3
"""
调试JSON响应格式
"""

import os
import asyncio
import json
from src.core.env_loader import env_loader

# 清除环境变量并重新加载
for var in ['BRIGHTDATA_API_KEY']:
    if var in os.environ:
        del os.environ[var]
env_loader.reload()

from src.clients.brightdata_client import BrightDataAsyncClient

async def debug_json_response():
    """调试JSON响应"""
    
    api_key = os.environ.get('BRIGHTDATA_API_KEY')
    
    async with BrightDataAsyncClient(api_key=api_key) as client:
        
        # 直接调用API查看原始响应
        data = {
            "zone": client.zone,
            "url": client._build_search_url("Python programming", {}),
            "format": "json"
        }
        
        print("=== 调试BrightData JSON响应 ===")
        print(f"请求数据: {json.dumps(data, indent=2)}")
        
        async with client.session.post(
            client.base_url,
            json=data,
            headers=client.headers
        ) as response:
            print(f"\nHTTP状态码: {response.status}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            # 获取原始响应
            try:
                response_data = await response.json()
                print(f"\n响应类型: {type(response_data)}")
                
                # 保存响应用于分析
                with open('brightdata_json_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                print("响应已保存到 brightdata_json_response.json")
                
                # 分析响应结构
                if isinstance(response_data, dict):
                    print(f"\n字典键: {list(response_data.keys())}")
                    for key, value in response_data.items():
                        print(f"  {key}: {type(value)} - {len(value) if isinstance(value, (list, dict, str)) else value}")
                        
                        # 如果是列表，检查第一个元素
                        if isinstance(value, list) and len(value) > 0:
                            first_item = value[0]
                            print(f"    第一个元素类型: {type(first_item)}")
                            if isinstance(first_item, dict):
                                print(f"    第一个元素键: {list(first_item.keys())}")
                
                elif isinstance(response_data, list):
                    print(f"\n数组长度: {len(response_data)}")
                    if len(response_data) > 0:
                        first_item = response_data[0]
                        print(f"第一个元素类型: {type(first_item)}")
                        if isinstance(first_item, dict):
                            print(f"第一个元素键: {list(first_item.keys())}")
                            print(f"第一个元素示例: {json.dumps(first_item, ensure_ascii=False, indent=2)}")
                
                # 测试我们的处理函数
                print(f"\n=== 测试JSON处理函数 ===")
                processed_results = client._process_json_response(response_data)
                print(f"处理后结果数: {len(processed_results)}")
                
                if processed_results:
                    print("前3个处理后的结果:")
                    for i, result in enumerate(processed_results[:3]):
                        print(f"\n结果 {i+1}:")
                        print(f"  标题: {result.get('title', 'N/A')}")
                        print(f"  URL: {result.get('url', 'N/A')[:60]}...")
                        print(f"  摘要: {result.get('snippet', 'N/A')[:100]}...")
                
            except Exception as e:
                print(f"解析JSON失败: {e}")
                
                # 尝试获取文本响应
                response_text = await response.text()
                print(f"原始文本响应长度: {len(response_text)}")
                print(f"响应开头: {response_text[:200]}...")

if __name__ == "__main__":
    asyncio.run(debug_json_response())