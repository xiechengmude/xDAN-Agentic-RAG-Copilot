#!/usr/bin/env python3
"""
直接测试 S3 RAG 系统
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)

from src.services.s3_service import S3Service
from src.core.config_loader import ConfigLoader

async def test_direct():
    """直接测试"""
    # 初始化 S3 服务
    config_loader = ConfigLoader()
    config = {
        'ragflow_api_url': config_loader.get('ragflow.api_url'),
        'ragflow_api_key': config_loader.get('ragflow.api_key'),
        'default_dataset_id': config_loader.get('ragflow.default_dataset_id')
    }
    s3_service = S3Service(config)
    
    print("🧪 直接测试：智信平台ice-crp系统功能")
    print("=" * 50)
    
    question = "智信平台中的ice-crp系统主要负责什么功能？"
    print(f"问题: {question}")
    print("\n正在处理...")
    
    full_answer = ""
    metadata = {}
    
    async for chunk in s3_service.ask(
        question=question,
        max_rounds=2,
        stream=True
    ):
        if isinstance(chunk, dict):
            if 'answer' in chunk:
                if chunk['answer']:
                    print(f"[答案片段] {chunk['answer']}")
                    full_answer += chunk['answer']
            if 'metadata' in chunk:
                metadata = chunk['metadata']
                print(f"[元数据] {metadata}")
            if 'stage' in chunk:
                print(f"[阶段] {chunk['stage']}")
    
    print("\n" + "=" * 50)
    print("📝 完整答案:")
    print(full_answer if full_answer else "未获取到答案")
    print(f"\n📊 元数据: {metadata}")

if __name__ == "__main__":
    asyncio.run(test_direct())