#!/usr/bin/env python3
"""
调试S3框架认证问题
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.s3_service import S3Service
from src.clients.ragflow_client import RAGFlowClient

async def debug_s3_auth():
    """调试S3框架认证问题"""
    print("="*60)
    print("调试S3框架认证问题")
    print("="*60)
    
    # 配置信息
    config = {
        'ragflow_api_url': 'http://150.109.16.195:7080',
        'ragflow_api_key': 'ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm',
        'default_dataset_id': '7e8d9e924cde11f0afc90242ac140006'
    }
    
    print(f"配置信息:")
    print(f"- API URL: {config['ragflow_api_url']}")
    print(f"- API Key: {config['ragflow_api_key']}")
    print(f"- Dataset ID: {config['default_dataset_id']}")
    print()
    
    # 1. 直接测试RAGFlowClient
    print("1. 直接测试RAGFlowClient")
    print("-" * 40)
    try:
        ragflow_client = RAGFlowClient(
            api_url=config['ragflow_api_url'],
            api_key=config['ragflow_api_key']
        )
        
        result = ragflow_client.retrieve_chunks(
            question="智信是什么？",
            dataset_ids=[config['default_dataset_id']],
            page_size=5
        )
        
        print(f"结果代码: {result.get('code')}")
        print(f"消息: {result.get('message', 'N/A')}")
        if result.get('code') == 0:
            chunks = result.get('data', {}).get('chunks', [])
            print(f"找到文档: {len(chunks)} 个")
        else:
            print(f"失败详情: {result}")
            
    except Exception as e:
        print(f"异常: {e}")
    
    print()
    
    # 2. 通过S3Service测试
    print("2. 通过S3Service测试")
    print("-" * 40)
    try:
        s3_service = S3Service(config)
        
        # 直接调用S3框架的search_phase
        search_results, success = await s3_service.s3_framework.search_phase(
            question="智信是什么？",
            dataset_ids=[config['default_dataset_id']],
            top_k=5
        )
        
        print(f"搜索成功: {success}")
        print(f"找到文档: {len(search_results)} 个")
        
        if not success:
            print("搜索失败，检查日志输出")
            
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_s3_auth())