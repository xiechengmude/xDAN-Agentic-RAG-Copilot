#!/usr/bin/env python3
"""
显示当前配置
用于验证环境变量是否正确加载
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tabulate import tabulate

# 加载环境变量
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'
load_dotenv(env_path)

# 添加项目路径
sys.path.append(str(project_root))

from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY,
    HOST, PORT
)

def mask_key(key: str) -> str:
    """隐藏API密钥的部分内容"""
    if not key:
        return "未设置"
    if len(key) <= 10:
        return "*" * len(key)
    return f"{key[:10]}...{key[-4:]}"

def main():
    print("=" * 60)
    print("当前配置信息")
    print(f"配置文件: {env_path}")
    print("=" * 60)
    
    # RAGFlow配置
    ragflow_data = [
        ["API URL", RAGFLOW_API_URL or "未设置"],
        ["API Key", mask_key(RAGFLOW_API_KEY)],
        ["默认数据集ID", DEFAULT_DATASET_ID or "未设置"]
    ]
    
    print("\n## RAGFlow配置")
    print(tabulate(ragflow_data, headers=["配置项", "值"], tablefmt="grid"))
    
    # S3 Search模型配置
    search_data = [
        ["模型名称", S3_SEARCH_MODEL_NAME or "未设置"],
        ["模型URL", S3_SEARCH_MODEL_URL or "未设置"],
        ["API Key", mask_key(S3_SEARCH_API_KEY)]
    ]
    
    print("\n## S3 Search模型配置")
    print(tabulate(search_data, headers=["配置项", "值"], tablefmt="grid"))
    
    # S3 Generator模型配置
    generator_data = [
        ["模型名称", S3_GENERATOR_MODEL_NAME or "未设置"],
        ["模型URL", S3_GENERATOR_MODEL_URL or "未设置"],
        ["API Key", mask_key(S3_GENERATOR_API_KEY)]
    ]
    
    print("\n## S3 Generator模型配置")
    print(tabulate(generator_data, headers=["配置项", "值"], tablefmt="grid"))
    
    # 服务器配置
    server_data = [
        ["主机", HOST],
        ["端口", PORT]
    ]
    
    print("\n## 服务器配置")
    print(tabulate(server_data, headers=["配置项", "值"], tablefmt="grid"))
    
    # 检查必需的环境变量
    print("\n## 环境变量状态")
    required_vars = [
        "RAGFLOW_API_URL",
        "RAGFLOW_API_KEY",
        "S3_SEARCH_MODEL_NAME",
        "S3_SEARCH_MODEL_URL",
        "S3_GENERATOR_MODEL_NAME",
        "S3_GENERATOR_API_BASE",
        "S3_GENERATOR_API_KEY"
    ]
    
    status_data = []
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ 已设置" if value else "❌ 未设置"
        status_data.append([var, status])
    
    print(tabulate(status_data, headers=["环境变量", "状态"], tablefmt="grid"))
    
    # 额外信息
    print(f"\n配置文件路径: {env_path}")
    print(f"配置文件存在: {'✅ 是' if env_path.exists() else '❌ 否'}")

if __name__ == "__main__":
    main()