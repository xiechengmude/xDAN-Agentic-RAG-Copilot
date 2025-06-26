#!/usr/bin/env python3
"""
使用已存在数据集的完整API测试
"""

import json
import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('info.debug', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APITesterWithExistingDataset:
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.headers = {
            'Authorization': 'Bearer xdan-demo-key-123456',
            'Content-Type': 'application/json'
        }
        self.existing_dataset_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def log_test_result(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """记录测试结果到日志"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'response_data': response_data,
            'error': error
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name} - 成功")
            if response_data and 'data' in response_data:
                # 只显示关键信息，避免日志过长
                if isinstance(response_data['data'], list):
                    logger.info(f"   返回 {len(response_data['data'])} 条记录")
                elif isinstance(response_data['data'], dict) and 'id' in response_data['data']:
                    logger.info(f"   ID: {response_data['data']['id']}")
                else:
                    logger.info(f"   响应: {response_data['message']}")
        else:
            logger.error(f"❌ {test_name} - 失败")
            if error:
                logger.error(f"   错误信息: {error}")
                
    async def test_health_check(self):
        """测试健康检查接口"""
        logger.info("🔍 测试健康检查接口")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                await self.log_test_result("健康检查", response.status == 200, data)
                return response.status == 200
        except Exception as e:
            await self.log_test_result("健康检查", False, error=str(e))
            return False
            
    async def test_list_datasets(self):
        """测试获取数据集列表并选择一个用于测试"""
        logger.info("🔍 测试获取数据集列表")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取数据集列表", success, data)
                
                if success and data.get('data'):
                    # 选择第一个数据集用于后续测试
                    self.existing_dataset_id = data['data'][0]['id']
                    logger.info(f"📝 选择数据集用于测试: {self.existing_dataset_id}")
                
                return success, data
        except Exception as e:
            await self.log_test_result("获取数据集列表", False, error=str(e))
            return False, None
            
    async def test_get_dataset(self, dataset_id: str):
        """测试获取数据集详情"""
        logger.info(f"🔍 测试获取数据集详情: {dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{dataset_id}", headers=self.headers) as response:
                data = await response.json()
                await self.log_test_result(f"获取数据集详情", response.status == 200, data)
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"获取数据集详情", False, error=str(e))
            return False
            
    async def test_upload_document(self, dataset_id: str):
        """测试上传文档"""
        logger.info(f"🔍 测试上传文档到数据集: {dataset_id}")
        try:
            test_content = """
RAGFlow API 测试文档

这是一个用于测试RAGFlow API功能的示例文档。

主要功能包括：
1. 知识库管理 - 创建、查询、更新、删除知识库
2. 文档处理 - 支持文档上传、解析、状态跟踪  
3. 智能问答 - 基于知识库的实时流式对话
4. 语义检索 - 高精度的文档内容检索

技术特点：
- 使用先进的RAG架构
- 支持多种文档格式
- 实时流式响应
- 高精度语义理解

这个文档将用于验证API的各项功能是否正常工作。
            """
            
            data = aiohttp.FormData()
            data.add_field('file', test_content.encode('utf-8'), filename=f'api_test_doc_{int(time.time())}.txt', content_type='text/plain')
            
            headers_for_upload = {'Authorization': 'Bearer xdan-demo-key-123456'}
            
            async with self.session.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                data=data,
                headers=headers_for_upload
            ) as response:
                response_data = await response.json()
                success = response.status == 200 and response_data.get('code') == 0
                await self.log_test_result(f"上传文档", success, response_data)
                
                if success:
                    document_id = response_data.get('data', {}).get('id')
                    return True, document_id
                else:
                    return False, None
        except Exception as e:
            await self.log_test_result(f"上传文档", False, error=str(e))
            return False, None
            
    async def test_list_documents(self, dataset_id: str):
        """测试获取文档列表"""
        logger.info(f"🔍 测试获取文档列表: {dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents", headers=self.headers) as response:
                data = await response.json()
                await self.log_test_result(f"获取文档列表", response.status == 200, data)
                return response.status == 200, data
        except Exception as e:
            await self.log_test_result(f"获取文档列表", False, error=str(e))
            return False, None
            
    async def test_create_chat(self, dataset_id: str):
        """测试创建聊天"""
        logger.info(f"🔍 测试创建聊天: {dataset_id}")
        try:
            payload = {
                "name": f"API测试聊天_{int(time.time())}",
                "dataset_ids": [dataset_id]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200 and data.get('code') == 0
                await self.log_test_result(f"创建聊天", success, data)
                
                if success:
                    chat_id = data.get('data', {}).get('id')
                    return True, chat_id
                else:
                    return False, None
        except Exception as e:
            await self.log_test_result(f"创建聊天", False, error=str(e))
            return False, None
            
    async def test_chat_completion(self, chat_id: str):
        """测试聊天对话"""
        logger.info(f"🔍 测试聊天对话: {chat_id}")
        try:
            payload = {
                "question": "请介绍一下RAGFlow的主要功能和特点。",
                "stream": False,
                "session_id": f"test_session_{int(time.time())}"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result(f"聊天对话", success, data)
                return success
        except Exception as e:
            await self.log_test_result(f"聊天对话", False, error=str(e))
            return False
            
    async def test_stream_chat(self, chat_id: str):
        """测试流式聊天"""
        logger.info(f"🔍 测试流式聊天: {chat_id}")
        try:
            payload = {
                "question": "请详细解释RAGFlow的检索增强生成原理。",
                "stream": True,
                "session_id": f"stream_session_{int(time.time())}"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=self.headers
            ) as response:
                
                if response.status != 200:
                    await self.log_test_result(f"流式聊天", False, f"HTTP {response.status}")
                    return False
                    
                # 收集流式响应
                chunks_received = 0
                total_size = 0
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunks_received += 1
                        total_size += len(chunk)
                        if chunks_received <= 3:  # 只显示前几个chunk
                            logger.info(f"   收到流式数据块 {chunks_received}: {len(chunk)} 字节")
                        
                await self.log_test_result(
                    f"流式聊天", 
                    True,
                    {"chunks_received": chunks_received, "total_size": total_size}
                )
                return True
        except Exception as e:
            await self.log_test_result(f"流式聊天", False, error=str(e))
            return False
            
    async def test_retrieval(self, dataset_id: str):
        """测试检索功能"""
        logger.info(f"🔍 测试检索功能: {dataset_id}")
        try:
            payload = {
                "question": "RAGFlow的主要特点是什么？",
                "dataset_ids": [dataset_id],
                "top_k": 5
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/retrieval",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                await self.log_test_result(f"检索功能", response.status == 200, data)
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"检索功能", False, error=str(e))
            return False
            
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行完整的API接口测试 - 使用已存在数据集")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        try:
            # 1. 健康检查
            total_tests += 1
            if await self.test_health_check():
                passed_tests += 1
                
            # 2. 获取数据集列表并选择一个
            total_tests += 1
            success, datasets_data = await self.test_list_datasets()
            if success:
                passed_tests += 1
                
                if self.existing_dataset_id:
                    # 3. 获取数据集详情
                    total_tests += 1
                    if await self.test_get_dataset(self.existing_dataset_id):
                        passed_tests += 1
                        
                    # 4. 上传文档
                    total_tests += 1
                    success, document_id = await self.test_upload_document(self.existing_dataset_id)
                    if success:
                        passed_tests += 1
                        
                    # 等待文档处理
                    logger.info("⏳ 等待文档处理完成...")
                    await asyncio.sleep(10)
                    
                    # 5. 获取文档列表
                    total_tests += 1
                    success, docs_data = await self.test_list_documents(self.existing_dataset_id)
                    if success:
                        passed_tests += 1
                        
                    # 6. 创建聊天
                    total_tests += 1
                    success, chat_id = await self.test_create_chat(self.existing_dataset_id)
                    if success:
                        passed_tests += 1
                        
                        if chat_id:
                            # 7. 普通聊天对话
                            total_tests += 1
                            if await self.test_chat_completion(chat_id):
                                passed_tests += 1
                                
                            # 8. 流式聊天
                            total_tests += 1
                            if await self.test_stream_chat(chat_id):
                                passed_tests += 1
                                
                    # 9. 检索功能
                    total_tests += 1
                    if await self.test_retrieval(self.existing_dataset_id):
                        passed_tests += 1
                        
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            logger.error(traceback.format_exc())
            
        # 生成测试报告
        await self.generate_test_report(total_tests, passed_tests)
        
    async def generate_test_report(self, total_tests: int, passed_tests: int):
        """生成测试报告"""
        logger.info("=" * 60)
        logger.info("📊 API接口测试报告")
        logger.info("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"总测试数量: {total_tests}")
        logger.info(f"成功测试数量: {passed_tests}")
        logger.info(f"失败测试数量: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        
        logger.info("\n详细测试结果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {result['test_name']}")
            if not result['success'] and result['error']:
                logger.info(f"    错误: {result['error']}")
                
        # 保存详细报告到文件
        report_data = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat(),
                'dataset_used': self.existing_dataset_id
            },
            'detailed_results': self.test_results
        }
        
        with open('complete_api_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info("\n详细测试报告已保存到: complete_api_test_report.json")
        logger.info("所有测试日志已保存到: info.debug")
        
        if success_rate == 100:
            logger.info("🎉 所有测试通过！API服务运行正常。")
        elif success_rate >= 80:
            logger.info("⚠️  大部分测试通过，服务基本正常。")
        else:
            logger.info("❌ 多个测试失败，需要检查服务配置。")

async def main():
    """主函数"""
    logger.info("开始执行完整的API接口测试 - 使用已存在数据集")
    
    async with APITesterWithExistingDataset() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())