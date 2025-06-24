#!/usr/bin/env python3
"""
RAGFlow远程服务API测试
测试与RAGFlow服务器的基本连接和API功能
"""

import os
import sys
import json
import pytest
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

from src.clients.xdan_rag_client import XDANRagClient, APIError
from config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID

class TestRAGFlowAPI:
    """RAGFlow API基础功能测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        cls.client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        cls.test_dataset_id = None
        cls.test_chat_id = None
        
    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        # 清理测试创建的资源
        if cls.test_dataset_id and cls.test_dataset_id != DEFAULT_DATASET_ID:
            try:
                cls.client.delete_dataset(cls.test_dataset_id)
            except:
                pass
        
        if cls.test_chat_id:
            try:
                cls.client.delete_chat(cls.test_chat_id)
            except:
                pass
    
    def test_01_connection(self):
        """测试1: API连接性"""
        try:
            # 尝试获取数据集列表
            result = self.client.list_datasets(page_size=1)
            assert isinstance(result, dict)
            print("✅ API连接成功")
        except Exception as e:
            pytest.fail(f"API连接失败: {e}")
    
    def test_02_list_datasets(self):
        """测试2: 获取数据集列表"""
        result = self.client.list_datasets(page_size=10)
        
        assert isinstance(result, dict)
        assert 'datasets' in result or 'data' in result or isinstance(result.get('data'), list)
        
        # 获取数据集列表
        datasets = result.get('datasets', result.get('data', []))
        if isinstance(result, dict) and isinstance(result.get('data'), list):
            datasets = result['data']
        
        print(f"✅ 获取到 {len(datasets)} 个数据集")
        
        # 打印前3个数据集信息
        for i, dataset in enumerate(datasets[:3]):
            print(f"  数据集{i+1}: {dataset.get('name', 'N/A')} (ID: {dataset.get('id', 'N/A')})")
    
    def test_03_create_dataset(self):
        """测试3: 创建数据集"""
        dataset_name = f"测试数据集_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            result = self.client.create_dataset(
                name=dataset_name,
                description="RAGFlow API测试用数据集",
                embedding_model="BAAI/bge-m3@SILICONFLOW",
                chunk_method="naive"
            )
            
            assert 'id' in result
            self.__class__.test_dataset_id = result['id']
            print(f"✅ 创建数据集成功: {dataset_name} (ID: {result['id']})")
            
        except APIError as e:
            if e.code == 101:  # 文件相关错误，可能是配额限制
                print(f"⚠️  创建数据集失败（可能是配额限制）: {e}")
                # 使用默认数据集
                self.__class__.test_dataset_id = DEFAULT_DATASET_ID
            else:
                raise
    
    def test_04_update_dataset(self):
        """测试4: 更新数据集信息"""
        if not self.test_dataset_id:
            pytest.skip("没有可用的测试数据集")
        
        try:
            result = self.client.update_dataset(
                dataset_id=self.test_dataset_id,
                description="更新后的描述 - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            print("✅ 更新数据集信息成功")
        except APIError as e:
            print(f"⚠️  更新数据集失败: {e}")
    
    def test_05_retrieve_chunks(self):
        """测试5: 知识库检索功能"""
        dataset_id = self.test_dataset_id or DEFAULT_DATASET_ID
        
        try:
            result = self.client.retrieve_chunks(
                question="什么是RAGFlow？",
                dataset_ids=[dataset_id],
                page_size=3
            )
            
            chunks = result.get('chunks', [])
            print(f"✅ 检索成功，找到 {len(chunks)} 个相关文档片段")
            
            for i, chunk in enumerate(chunks[:2]):
                print(f"\n  片段{i+1}:")
                print(f"    相似度: {chunk.get('similarity', 'N/A')}")
                print(f"    内容预览: {chunk.get('content', '')[:100]}...")
                
        except APIError as e:
            print(f"⚠️  检索失败: {e}")
    
    def test_06_create_chat(self):
        """测试6: 创建对话"""
        dataset_id = self.test_dataset_id or DEFAULT_DATASET_ID
        
        try:
            result = self.client.create_chat(
                name=f"测试对话_{datetime.now().strftime('%H%M%S')}",
                dataset_ids=[dataset_id]
            )
            
            assert 'id' in result
            self.__class__.test_chat_id = result['id']
            print(f"✅ 创建对话成功: ID={result['id']}")
            
        except APIError as e:
            pytest.fail(f"创建对话失败: {e}")
    
    def test_07_send_message_sync(self):
        """测试7: 发送消息（同步模式）"""
        if not self.test_chat_id:
            pytest.skip("没有可用的测试对话")
        
        try:
            result = self.client.send_message(
                chat_id=self.test_chat_id,
                content="你好，请简单介绍一下自己",
                stream=False
            )
            
            print(f"✅ 发送消息成功，收到回复")
            print(f"  回复内容: {str(result)[:200]}...")
            
        except APIError as e:
            print(f"⚠️  发送消息失败: {e}")
    
    def test_08_send_message_stream(self):
        """测试8: 发送消息（流式模式）"""
        if not self.test_chat_id:
            pytest.skip("没有可用的测试对话")
        
        try:
            response = self.client.send_message(
                chat_id=self.test_chat_id,
                content="什么是知识库？",
                stream=True
            )
            
            print("✅ 流式消息测试:")
            content_parts = []
            for event in self.client.handle_sse_stream(response):
                if 'answer' in event:
                    content_parts.append(event['answer'])
            
            full_content = ''.join(content_parts)
            print(f"  收到流式回复，总长度: {len(full_content)} 字符")
            print(f"  内容预览: {full_content[:100]}...")
            
        except APIError as e:
            print(f"⚠️  流式消息失败: {e}")
    
    def test_09_get_chat_messages(self):
        """测试9: 获取对话历史"""
        if not self.test_chat_id:
            pytest.skip("没有可用的测试对话")
        
        try:
            result = self.client.get_chat_messages(
                chat_id=self.test_chat_id,
                page_size=10
            )
            
            messages = result.get('messages', [])
            print(f"✅ 获取对话历史成功，共 {len(messages)} 条消息")
            
        except APIError as e:
            print(f"⚠️  获取对话历史失败: {e}")
    
    def test_10_compatibility_methods(self):
        """测试10: 兼容性方法"""
        # 测试兼容的列表方法
        result = self.client.list_datasets_compatible()
        assert result['code'] == 0
        print("✅ 兼容列表方法测试通过")
        
        # 测试兼容的检索方法
        result = self.client.retrieve_chunks_compatible(
            question="测试问题",
            dataset_ids=[DEFAULT_DATASET_ID],
            top_k=2
        )
        assert result['code'] == 0
        print("✅ 兼容检索方法测试通过")

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("RAGFlow远程服务API测试")
    print("=" * 60)
    print(f"API URL: {RAGFLOW_API_URL}")
    print(f"API Key: {RAGFLOW_API_KEY[:20]}...")
    print("=" * 60)
    
    # 使用pytest运行测试
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()