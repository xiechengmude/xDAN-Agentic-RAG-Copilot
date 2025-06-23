"""
测试知识库管理系统接口
"""
import pytest
import asyncio
import aiohttp
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import time
from datetime import datetime

# 从环境变量读取配置
# 使用本地演示服务器进行测试
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8050')
API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm')

# 测试数据
TEST_DATASET_NAME = f"测试知识库_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_DATASET_DESC = "用于API接口测试的知识库"


class TestKnowledgeBaseAPIs:
    """知识库管理接口测试类"""
    
    def setup_class(self):
        """测试类初始化"""
        self.headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        self.created_datasets = []  # 记录创建的知识库，用于清理
        self.uploaded_files = []    # 记录上传的文件，用于清理
    
    def teardown_class(self):
        """测试类清理"""
        # 清理测试创建的资源
        asyncio.run(self._cleanup_resources())
    
    async def _cleanup_resources(self):
        """清理测试资源"""
        async with aiohttp.ClientSession() as session:
            # 删除创建的知识库
            for dataset_id in self.created_datasets:
                try:
                    await session.delete(
                        f"{BASE_URL}/api/v1/datasets/{dataset_id}",
                        headers=self.headers
                    )
                except:
                    pass
    
    @pytest.mark.asyncio
    async def test_01_create_dataset(self):
        """测试创建知识库"""
        async with aiohttp.ClientSession() as session:
            data = {
                "name": TEST_DATASET_NAME,
                "description": TEST_DATASET_DESC
            }
            
            async with session.post(
                f"{BASE_URL}/api/v1/datasets",
                headers=self.headers,
                json=data
            ) as response:
                assert response.status == 200, f"创建知识库失败: {await response.text()}"
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert 'id' in result['data']
                
                # 保存知识库ID用于后续测试
                self.dataset_id = result['data']['id']
                self.created_datasets.append(self.dataset_id)
                
                print(f"✓ 创建知识库成功: {self.dataset_id}")
    
    @pytest.mark.asyncio
    async def test_02_list_datasets(self):
        """测试获取知识库列表"""
        async with aiohttp.ClientSession() as session:
            params = {
                "page": 1,
                "page_size": 12,
                "name": TEST_DATASET_NAME
            }
            
            async with session.get(
                f"{BASE_URL}/api/v1/datasets",
                headers=self.headers,
                params=params
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert isinstance(result['data'], list)
                
                # 验证创建的知识库在列表中
                dataset_names = [d['name'] for d in result['data']]
                assert TEST_DATASET_NAME in dataset_names
                
                print(f"✓ 获取知识库列表成功，共 {len(result['data'])} 个")
    
    @pytest.mark.asyncio
    async def test_03_update_dataset(self):
        """测试更新知识库"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        async with aiohttp.ClientSession() as session:
            data = {
                "name": f"{TEST_DATASET_NAME}_更新",
                "description": f"{TEST_DATASET_DESC}_已更新"
            }
            
            async with session.put(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}",
                headers=self.headers,
                json=data
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                
                print(f"✓ 更新知识库成功: {self.dataset_id}")
    
    @pytest.mark.asyncio
    async def test_04_upload_file(self):
        """测试文件上传"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        # 创建测试文件
        test_file_path = Path("test_document.txt")
        test_content = f"""测试文档
创建时间: {datetime.now()}
        
这是一个用于测试知识库文件上传功能的文档。
包含以下内容：
1. 测试标题
2. 测试段落
3. 测试列表

测试内容：知识库管理系统支持多种文件格式的上传和解析。
"""
        test_file_path.write_text(test_content, encoding='utf-8')
        
        try:
            async with aiohttp.ClientSession() as session:
                # 准备文件上传
                form_data = aiohttp.FormData()
                form_data.add_field(
                    'files',
                    open(test_file_path, 'rb'),
                    filename='test_document.txt',
                    content_type='text/plain'
                )
                
                # 移除Content-Type header，让aiohttp自动设置
                upload_headers = {
                    'Authorization': self.headers['Authorization']
                }
                
                async with session.post(
                    f"{BASE_URL}/api/v1/datasets/{self.dataset_id}/documents/upload",
                    headers=upload_headers,
                    data=form_data
                ) as response:
                    assert response.status == 200, f"文件上传失败: {await response.text()}"
                    
                    result = await response.json()
                    assert result['code'] == 0
                    assert 'data' in result
                    assert len(result['data']) > 0
                    
                    # 保存文件ID
                    self.doc_id = result['data'][0]['id']
                    self.uploaded_files.append(self.doc_id)
                    
                    print(f"✓ 文件上传成功: {self.doc_id}")
        
        finally:
            # 清理测试文件
            if test_file_path.exists():
                test_file_path.unlink()
    
    @pytest.mark.asyncio
    async def test_05_list_documents(self):
        """测试获取文件列表"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        async with aiohttp.ClientSession() as session:
            params = {
                "page": 1,
                "page_size": 20
            }
            
            async with session.get(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}/documents",
                headers=self.headers,
                params=params
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert isinstance(result['data'], list)
                
                if hasattr(self, 'doc_id'):
                    doc_ids = [d['id'] for d in result['data']]
                    assert self.doc_id in doc_ids
                
                print(f"✓ 获取文件列表成功，共 {len(result['data'])} 个文件")
    
    @pytest.mark.asyncio
    async def test_06_trigger_parse(self):
        """测试触发文件解析"""
        if not hasattr(self, 'dataset_id') or not hasattr(self, 'doc_id'):
            pytest.skip("需要先上传文件")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}/documents/{self.doc_id}/parse",
                headers=self.headers
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert 'task_id' in result['data']
                
                self.task_id = result['data']['task_id']
                print(f"✓ 触发文件解析成功，任务ID: {self.task_id}")
    
    @pytest.mark.asyncio
    async def test_07_get_file_status(self):
        """测试获取文件状态"""
        if not hasattr(self, 'dataset_id') or not hasattr(self, 'doc_id'):
            pytest.skip("需要先上传文件")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}/documents/{self.doc_id}/status",
                headers=self.headers
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert 'status' in result['data']
                
                print(f"✓ 获取文件状态成功: {result['data']['status']}")
    
    @pytest.mark.asyncio
    async def test_08_knowledge_retrieval(self):
        """测试知识库检索"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        async with aiohttp.ClientSession() as session:
            data = {
                "question": "测试内容",
                "dataset_ids": [self.dataset_id]
            }
            
            async with session.post(
                f"{BASE_URL}/api/v1/retrieval",
                headers=self.headers,
                json=data
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                assert 'data' in result
                assert 'chunks' in result['data']
                
                print(f"✓ 知识库检索成功，返回 {len(result['data']['chunks'])} 个结果")
    
    @pytest.mark.asyncio
    async def test_09_send_chat_message(self):
        """测试发送对话消息"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        # 创建一个临时的chat_id
        chat_id = f"test_chat_{int(time.time())}"
        
        async with aiohttp.ClientSession() as session:
            data = {
                "content": "请介绍一下测试内容",
                "dataset_id": self.dataset_id
            }
            
            async with session.post(
                f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
                headers=self.headers,
                json=data
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                
                print(f"✓ 发送对话消息成功")
    
    @pytest.mark.asyncio
    async def test_10_batch_delete_files(self):
        """测试批量删除文件"""
        if not hasattr(self, 'dataset_id') or not self.uploaded_files:
            pytest.skip("需要先上传文件")
        
        async with aiohttp.ClientSession() as session:
            data = {
                "ids": self.uploaded_files
            }
            
            async with session.delete(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}/documents",
                headers=self.headers,
                json=data
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                
                print(f"✓ 批量删除文件成功")
    
    @pytest.mark.asyncio
    async def test_11_delete_dataset(self):
        """测试删除知识库"""
        if not hasattr(self, 'dataset_id'):
            pytest.skip("需要先创建知识库")
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{BASE_URL}/api/v1/datasets/{self.dataset_id}",
                headers=self.headers
            ) as response:
                assert response.status == 200
                
                result = await response.json()
                assert result['code'] == 0
                
                # 从列表中移除
                if self.dataset_id in self.created_datasets:
                    self.created_datasets.remove(self.dataset_id)
                
                print(f"✓ 删除知识库成功: {self.dataset_id}")


def run_api_tests():
    """运行API测试"""
    print(f"\n开始测试知识库管理API...")
    print(f"API地址: {BASE_URL}")
    print(f"测试时间: {datetime.now()}\n")
    
    # 运行pytest
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_api_tests()