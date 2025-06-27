#!/usr/bin/env python3
"""
调试配置加载问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config_loader import get_config
from src.services.service_factory import get_default_service

def debug_config_loading():
    """调试配置加载"""
    print("="*60)
    print("调试配置加载")
    print("="*60)
    
    # 1. 检查环境变量
    print("1. 环境变量:")
    print(f"  RAGFLOW_API_URL: {os.getenv('RAGFLOW_API_URL', 'not set')}")
    print(f"  RAGFLOW_API_KEY: {os.getenv('RAGFLOW_API_KEY', 'not set')}")
    print()
    
    # 2. 检查配置文件加载
    print("2. 配置文件加载:")
    try:
        config = get_config()
        ragflow_config = config.get_ragflow_config()
        print(f"  api_url: {ragflow_config.get('api_url')}")
        print(f"  api_key: {ragflow_config.get('api_key')}")
        print(f"  default_dataset_id: {ragflow_config.get('default_dataset_id')}")
    except Exception as e:
        print(f"  错误: {e}")
    print()
    
    # 3. 检查service_factory
    print("3. Service Factory:")
    try:
        s3_service = get_default_service()
        print(f"  S3服务创建成功: {s3_service}")
        
        # 检查内部的ragflow_client配置
        ragflow_client = s3_service.ragflow_client
        print(f"  RAGFlow client API URL: {ragflow_client.api_url}")
        print(f"  RAGFlow client API Key: {ragflow_client.api_key}")
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config_loading()