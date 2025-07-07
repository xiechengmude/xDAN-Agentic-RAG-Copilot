#!/usr/bin/env python3
"""
调试SERP API响应格式
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

async def debug_serp_response():
    """调试SERP API响应"""
    
    api_key = os.environ.get('BRIGHTDATA_API_KEY')
    
    async with BrightDataAsyncClient(api_key=api_key) as client:
        
        # 构建SERP参数
        search_params = client._build_serp_params("Python programming", {})
        
        print("=== 调试BrightData SERP API ===")
        print(f"SERP参数: {json.dumps(search_params, indent=2)}")
        
        # 准备请求数据
        data = {
            "country": "us",
            "query": search_params
        }
        
        print(f"\n请求数据: {json.dumps(data, indent=2)}")
        
        # 发送请求
        url = f"{client.serp_url}?customer=hl_d8b6c945&zone={client.zone}"
        print(f"\n请求URL: {url}")
        
        async with client.session.post(
            url,
            json=data,
            headers=client.headers
        ) as response:
            print(f"\nHTTP状态码: {response.status}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            # 获取原始响应
            try:
                response_data = await response.json()
                
                # 保存响应用于分析
                with open('serp_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                print("SERP响应已保存到 serp_response.json")
                
                print(f"\n响应类型: {type(response_data)}")
                
                if isinstance(response_data, dict):
                    print(f"响应键: {list(response_data.keys())}")
                    
                    # 检查关键字段
                    if 'organic_results' in response_data:
                        organic = response_data['organic_results']
                        print(f"有机结果: {len(organic)} 个")
                        if organic:
                            print(f"第一个有机结果: {json.dumps(organic[0], ensure_ascii=False, indent=2)}")
                    
                    if 'news_results' in response_data:
                        news = response_data['news_results']
                        print(f"新闻结果: {len(news)} 个")
                    
                    # 检查错误信息
                    if 'error' in response_data:
                        print(f"API错误: {response_data['error']}")
                    
                    # 检查其他可能的结果字段
                    for key, value in response_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f"数组字段 '{key}': {len(value)} 个元素")
                            if isinstance(value[0], dict):
                                print(f"  第一个元素键: {list(value[0].keys())}")
                
                # 测试处理函数
                print(f"\n=== 测试SERP结果处理 ===")
                processed_results = client._process_serp_results(response_data)
                print(f"处理后结果数: {len(processed_results)}")
                
                if processed_results:
                    print("前3个处理后的结果:")
                    for i, result in enumerate(processed_results[:3]):
                        print(f"\n结果 {i+1}:")
                        print(f"  标题: {result.get('title', 'N/A')}")
                        print(f"  URL: {result.get('url', 'N/A')[:60]}...")
                        print(f"  摘要: {result.get('snippet', 'N/A')[:100]}...")
                        print(f"  站点: {result.get('site', 'N/A')}")
                
            except Exception as e:
                print(f"解析响应失败: {e}")
                
                # 尝试获取文本响应
                response_text = await response.text()
                print(f"原始文本响应长度: {len(response_text)}")
                print(f"响应开头: {response_text[:300]}...")

if __name__ == "__main__":
    asyncio.run(debug_serp_response())