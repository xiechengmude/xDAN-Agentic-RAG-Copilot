#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow API 客户端基本使用示例
"""

import os
import sys
import json
from dotenv import load_dotenv

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.clients.ragflow_client import RAGFlowClient

# 加载环境变量
load_dotenv()

def print_json(obj):
    """美化打印 JSON 对象"""
    print(json.dumps(obj, ensure_ascii=False, indent=2))

def main():
    """主函数"""
    # 创建 RAGFlow 客户端实例
    client = RAGFlowClient()
    
    print("=" * 50)
    print("RAGFlow API 客户端示例")
    print("=" * 50)
    
    # 列出数据集
    print("\n1. 列出数据集:")
    try:
        datasets = client.list_datasets(page=1, page_size=5)
        print_json(datasets)
    except Exception as e:
        print(f"列出数据集失败: {e}")
    
    # 如果有数据集，尝试列出第一个数据集的文档
    if datasets.get("data") and len(datasets["data"]) > 0:
        dataset_id = datasets["data"][0]["id"]
        dataset_name = datasets["data"][0]["name"]
        
        print(f"\n2. 列出数据集 '{dataset_name}' 的文档:")
        try:
            documents = client.list_documents(dataset_id=dataset_id, page=1, page_size=5)
            print_json(documents)
        except Exception as e:
            print(f"列出文档失败: {e}")
        
        # 尝试检索
        print("\n3. 执行检索:")
        try:
            retrieval_results = client.retrieve_chunks(
                question="什么是 RAGFlow?",
                dataset_ids=[dataset_id],
                page=1,
                page_size=3,
                highlight=True
            )
            print_json(retrieval_results)
        except Exception as e:
            print(f"检索失败: {e}")
    else:
        print("\n没有找到可用的数据集")

if __name__ == "__main__":
    main()
