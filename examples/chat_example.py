#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow API 聊天示例
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
    print("RAGFlow API 聊天示例")
    print("=" * 50)
    
    # 列出聊天助手
    print("\n1. 获取可用的聊天助手:")
    try:
        # 首先列出数据集
        datasets = client.list_datasets(page=1, page_size=5)
        if datasets.get("data") and len(datasets["data"]) > 0:
            print(f"找到 {len(datasets['data'])} 个数据集")
            
            # 选择第一个数据集
            dataset_id = datasets["data"][0]["id"]
            dataset_name = datasets["data"][0]["name"]
            print(f"使用数据集: {dataset_name} (ID: {dataset_id})")
            
            # 提示用户输入聊天助手 ID
            chat_id = input("\n请输入聊天助手 ID (如果没有，请按回车跳过): ")
            
            if not chat_id:
                print("未提供聊天助手 ID，将使用检索 API 进行简单问答...")
                
                # 使用检索 API 进行简单问答
                while True:
                    question = input("\n请输入问题 (输入 'exit' 退出): ")
                    if question.lower() == 'exit':
                        break
                    
                    print("正在检索...")
                    try:
                        results = client.retrieve_chunks(
                            question=question,
                            dataset_ids=[dataset_id],
                            page=1,
                            page_size=3,
                            highlight=True
                        )
                        
                        if results.get("data", {}).get("chunks") and len(results["data"]["chunks"]) > 0:
                            print("\n检索结果:")
                            for i, chunk in enumerate(results["data"]["chunks"]):
                                print(f"\n--- 结果 {i+1} (相似度: {chunk['similarity']:.4f}) ---")
                                print(chunk.get("content", "无内容"))
                        else:
                            print("未找到相关内容")
                    except Exception as e:
                        print(f"检索失败: {e}")
            else:
                print(f"使用聊天助手 ID: {chat_id}")
                
                # 使用聊天助手进行对话
                messages = []
                while True:
                    user_input = input("\n请输入消息 (输入 'exit' 退出): ")
                    if user_input.lower() == 'exit':
                        break
                    
                    # 添加用户消息
                    messages.append({"role": "user", "content": user_input})
                    
                    print("正在生成回复...")
                    try:
                        response = client.create_chat_completion(
                            chat_id=chat_id,
                            model="default",
                            messages=messages,
                            stream=False
                        )
                        
                        if response and response.get("choices") and len(response["choices"]) > 0:
                            assistant_message = response["choices"][0]["message"]["content"]
                            print(f"\n助手: {assistant_message}")
                            
                            # 添加助手消息到历史
                            messages.append({"role": "assistant", "content": assistant_message})
                        else:
                            print("未获得有效回复")
                    except Exception as e:
                        print(f"聊天失败: {e}")
        else:
            print("未找到可用的数据集")
    except Exception as e:
        print(f"获取数据集失败: {e}")

if __name__ == "__main__":
    main()
