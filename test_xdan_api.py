#!/usr/bin/env python3
"""
测试xDAN RAG Copilot API客户端
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.xdan_rag_client import XDANRagClient, APIError
from config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID

def test_basic_api():
    """测试基本API功能"""
    print("=== 测试xDAN RAG Copilot API ===")
    print(f"API URL: {RAGFLOW_API_URL}")
    print(f"API Key: {RAGFLOW_API_KEY[:20]}...")
    
    try:
        # 初始化客户端
        client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        print("✅ 客户端初始化成功")
        
        # 测试1: 获取数据集列表
        print("\n📋 测试1: 获取数据集列表")
        datasets_result = client.list_datasets(page_size=5)
        print(f"找到 {len(datasets_result.get('datasets', []))} 个数据集")
        
        # 测试2: 创建数据集
        print("\n📦 测试2: 创建数据集")
        test_dataset_name = f"测试数据集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            new_dataset = client.create_dataset(
                name=test_dataset_name,
                description="API测试用数据集",
                embedding_model="BAAI/bge-m3@SILICONFLOW"
            )
            print(f"✅ 创建数据集成功: ID={new_dataset.get('id')}")
            dataset_id = new_dataset.get('id')
        except APIError as e:
            print(f"❌ 创建数据集失败: {e}")
            dataset_id = DEFAULT_DATASET_ID
            print(f"使用默认数据集: {dataset_id}")
        
        # 测试3: 知识库检索
        print("\n🔍 测试3: 知识库检索")
        try:
            retrieval_result = client.retrieve_chunks(
                question="什么是智信平台？",
                dataset_ids=[dataset_id],
                page_size=3
            )
            chunks = retrieval_result.get('chunks', [])
            print(f"检索到 {len(chunks)} 个相关文档片段")
            for i, chunk in enumerate(chunks[:2]):
                print(f"\n片段{i+1}:")
                print(f"  相似度: {chunk.get('similarity', 'N/A')}")
                print(f"  内容: {chunk.get('content', '')[:100]}...")
        except APIError as e:
            print(f"❌ 检索失败: {e}")
        
        # 测试4: 创建对话
        print("\n💬 测试4: 创建对话")
        try:
            chat = client.create_chat(
                name=f"测试对话_{datetime.now().strftime('%H%M%S')}",
                dataset_ids=[dataset_id]
            )
            chat_id = chat.get('id')
            print(f"✅ 创建对话成功: ID={chat_id}")
            
            # 测试5: 发送消息（非流式）
            print("\n📨 测试5: 发送消息（非流式）")
            try:
                response = client.send_message(
                    chat_id=chat_id,
                    content="你好，请介绍一下自己",
                    stream=False
                )
                print(f"✅ 收到回复: {response}")
            except APIError as e:
                print(f"❌ 发送消息失败: {e}")
            
            # 测试6: 发送消息（流式）
            print("\n📨 测试6: 发送消息（流式）")
            try:
                stream_response = client.send_message(
                    chat_id=chat_id,
                    content="什么是RAGFlow？",
                    stream=True
                )
                print("流式响应:")
                for event in client.handle_sse_stream(stream_response):
                    if 'answer' in event:
                        print(event['answer'], end='', flush=True)
                print("\n✅ 流式响应完成")
            except APIError as e:
                print(f"❌ 流式消息失败: {e}")
            
            # 测试7: 获取对话历史
            print("\n📜 测试7: 获取对话历史")
            try:
                messages = client.get_chat_messages(chat_id=chat_id)
                print(f"获取到 {len(messages.get('messages', []))} 条消息")
            except APIError as e:
                print(f"❌ 获取历史失败: {e}")
            
            # 清理: 删除测试对话
            try:
                client.delete_chat(chat_id)
                print("\n✅ 清理: 删除测试对话成功")
            except:
                pass
                
        except APIError as e:
            print(f"❌ 对话测试失败: {e}")
        
        # 清理: 删除测试数据集
        if dataset_id != DEFAULT_DATASET_ID and 'new_dataset' in locals():
            try:
                client.delete_dataset(dataset_id)
                print("✅ 清理: 删除测试数据集成功")
            except:
                pass
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_compatibility():
    """测试兼容性方法"""
    print("\n=== 测试兼容性方法 ===")
    
    try:
        client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        
        # 测试兼容的列表方法
        print("\n📋 测试兼容列表方法")
        result = client.list_datasets_compatible()
        print(f"兼容方法返回: code={result.get('code')}, 数据集数量={len(result.get('data', []))}")
        
        # 测试兼容的检索方法
        print("\n🔍 测试兼容检索方法")
        result = client.retrieve_chunks_compatible(
            question="测试问题",
            dataset_ids=[DEFAULT_DATASET_ID],
            top_k=3
        )
        print(f"兼容方法返回: code={result.get('code')}, chunks数量={len(result.get('data', {}).get('chunks', []))}")
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")

if __name__ == "__main__":
    # 运行基本测试
    test_basic_api()
    
    # 运行兼容性测试
    test_compatibility()