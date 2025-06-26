#!/usr/bin/env python3
"""
完整的API接口测试脚本
测试所有xDAN-RAG-Copilot-API接口，并将结果写入info.debug文件
"""

import json
import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('info.debug', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveAPITester:
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.created_resources = {
            'datasets': [],
            'chats': [],
            'documents': []
        }
        self.headers = {
            'Authorization': 'Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm',
            'Content-Type': 'application/json'
        }
        
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
            if response_data:
                logger.info(f"   响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
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
                await self.log_test_result(
                    "健康检查", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result("健康检查", False, error=str(e))
            return False
            
    async def test_list_datasets(self):
        """测试获取数据集列表"""
        logger.info("🔍 测试获取数据集列表")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets", headers=self.headers) as response:
                data = await response.json()
                await self.log_test_result(
                    "获取数据集列表", 
                    response.status == 200,
                    data
                )
                return response.status == 200, data
        except Exception as e:
            await self.log_test_result("获取数据集列表", False, error=str(e))
            return False, None
            
    async def test_create_dataset(self):
        """测试创建数据集"""
        logger.info("🔍 测试创建数据集")
        try:
            payload = {
                "name": f"测试数据集_{int(time.time())}",
                "description": "API测试创建的数据集",
                "language": "Chinese",
                "embedding_model": "BAAI/bge-large-zh-v1.5",
                "permission": "me",
                "document_count": 0,
                "chunk_count": 0,
                "parse_method": "naive",
                "parser_config": {
                    "chunk_token_count": 128,
                    "layout_recognize": "DeepDOC",
                    "delimiter": "\\n!?;。;；！？",
                    "task_page_size": 12
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/datasets",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                
                if response.status == 200 and data.get('code') == 0:
                    dataset_id = data.get('data', {}).get('id')
                    if dataset_id:
                        self.created_resources['datasets'].append(dataset_id)
                    await self.log_test_result("创建数据集", True, data)
                    return True, dataset_id
                else:
                    await self.log_test_result("创建数据集", False, data)
                    return False, None
        except Exception as e:
            await self.log_test_result("创建数据集", False, error=str(e))
            return False, None
            
    async def test_get_dataset(self, dataset_id: str):
        """测试获取数据集详情"""
        logger.info(f"🔍 测试获取数据集详情: {dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{dataset_id}", headers=self.headers) as response:
                data = await response.json()
                await self.log_test_result(
                    f"获取数据集详情({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"获取数据集详情({dataset_id})", False, error=str(e))
            return False
            
    async def test_update_dataset(self, dataset_id: str):
        """测试更新数据集"""
        logger.info(f"🔍 测试更新数据集: {dataset_id}")
        try:
            payload = {
                "name": f"更新的测试数据集_{int(time.time())}",
                "description": "API测试更新的数据集描述",
                "language": "Chinese",
                "embedding_model": "BAAI/bge-large-zh-v1.5",
                "permission": "me",
                "chunk_method": "naive",
                "parser_config": {
                    "chunk_token_count": 256,
                    "layout_recognize": "DeepDOC",
                    "delimiter": "\\n!?;。;；！？",
                    "task_page_size": 12
                }
            }
            
            async with self.session.put(
                f"{self.base_url}/api/v1/datasets/{dataset_id}",
                json=payload
            ) as response:
                data = await response.json()
                await self.log_test_result(
                    f"更新数据集({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"更新数据集({dataset_id})", False, error=str(e))
            return False
            
    async def test_upload_document(self, dataset_id: str):
        """测试上传文档"""
        logger.info(f"🔍 测试上传文档到数据集: {dataset_id}")
        try:
            # 创建测试文档内容
            test_content = """
            这是一个测试文档的内容。
            
            第一章：介绍
            本文档用于测试RAGFlow API的文档上传功能。
            
            第二章：详细内容
            RAGFlow是一个基于检索增强生成（RAG）的知识库系统，
            能够处理多种格式的文档，包括PDF、TXT、DOC等。
            
            第三章：结论
            通过这个测试文档，我们可以验证文档上传和处理功能是否正常工作。
            """
            
            # 准备文件数据
            data = aiohttp.FormData()
            data.add_field('file', test_content.encode('utf-8'), filename='test_document.txt', content_type='text/plain')
            
            async with self.session.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                data=data
            ) as response:
                response_data = await response.json()
                
                if response.status == 200 and response_data.get('code') == 0:
                    document_id = response_data.get('data', {}).get('id')
                    if document_id:
                        self.created_resources['documents'].append(document_id)
                    await self.log_test_result(f"上传文档到数据集({dataset_id})", True, response_data)
                    return True, document_id
                else:
                    await self.log_test_result(f"上传文档到数据集({dataset_id})", False, response_data)
                    return False, None
        except Exception as e:
            await self.log_test_result(f"上传文档到数据集({dataset_id})", False, error=str(e))
            return False, None
            
    async def test_list_documents(self, dataset_id: str):
        """测试获取文档列表"""
        logger.info(f"🔍 测试获取文档列表: {dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents") as response:
                data = await response.json()
                await self.log_test_result(
                    f"获取文档列表({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200, data
        except Exception as e:
            await self.log_test_result(f"获取文档列表({dataset_id})", False, error=str(e))
            return False, None
            
    async def test_create_chat(self, dataset_id: str):
        """测试创建聊天"""
        logger.info(f"🔍 测试创建聊天: {dataset_id}")
        try:
            payload = {
                "name": f"测试聊天_{int(time.time())}",
                "dataset_ids": [dataset_id]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload
            ) as response:
                data = await response.json()
                
                if response.status == 200 and data.get('code') == 0:
                    chat_id = data.get('data', {}).get('id')
                    if chat_id:
                        self.created_resources['chats'].append(chat_id)
                    await self.log_test_result(f"创建聊天({dataset_id})", True, data)
                    return True, chat_id
                else:
                    await self.log_test_result(f"创建聊天({dataset_id})", False, data)
                    return False, None
        except Exception as e:
            await self.log_test_result(f"创建聊天({dataset_id})", False, error=str(e))
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
                json=payload
            ) as response:
                data = await response.json()
                await self.log_test_result(
                    f"聊天对话({chat_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"聊天对话({chat_id})", False, error=str(e))
            return False
            
    async def test_stream_chat(self, chat_id: str):
        """测试流式聊天"""
        logger.info(f"🔍 测试流式聊天: {chat_id}")
        try:
            payload = {
                "question": "请详细解释RAGFlow的工作原理。",
                "stream": True,
                "session_id": f"stream_session_{int(time.time())}"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload
            ) as response:
                
                if response.status != 200:
                    await self.log_test_result(f"流式聊天({chat_id})", False, f"HTTP {response.status}")
                    return False
                    
                # 收集流式响应
                stream_data = []
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunk_str = chunk.decode('utf-8')
                        stream_data.append(chunk_str)
                        
                await self.log_test_result(
                    f"流式聊天({chat_id})", 
                    True,
                    {"stream_chunks": len(stream_data), "total_size": sum(len(chunk) for chunk in stream_data)}
                )
                return True
        except Exception as e:
            await self.log_test_result(f"流式聊天({chat_id})", False, error=str(e))
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
                json=payload
            ) as response:
                data = await response.json()
                await self.log_test_result(
                    f"检索功能({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"检索功能({dataset_id})", False, error=str(e))
            return False
            
    async def test_delete_documents(self, dataset_id: str, document_ids: List[str]):
        """测试批量删除文档"""
        if not document_ids:
            logger.info("⚠️  没有文档需要删除")
            return True
            
        logger.info(f"🔍 测试批量删除文档: {document_ids}")
        try:
            payload = {"ids": document_ids}
            
            async with self.session.request(
                "DELETE",
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                json=payload
            ) as response:
                data = await response.json()
                await self.log_test_result(
                    f"批量删除文档({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"批量删除文档({dataset_id})", False, error=str(e))
            return False
            
    async def test_delete_dataset(self, dataset_id: str):
        """测试删除数据集"""
        logger.info(f"🔍 测试删除数据集: {dataset_id}")
        try:
            async with self.session.delete(f"{self.base_url}/api/v1/datasets/{dataset_id}") as response:
                data = await response.json()
                await self.log_test_result(
                    f"删除数据集({dataset_id})", 
                    response.status == 200,
                    data
                )
                return response.status == 200
        except Exception as e:
            await self.log_test_result(f"删除数据集({dataset_id})", False, error=str(e))
            return False
            
    async def cleanup_resources(self):
        """清理创建的测试资源"""
        logger.info("🧹 开始清理测试资源")
        
        # 删除文档
        for doc_id in self.created_resources['documents']:
            try:
                # 注意：这里需要知道文档属于哪个数据集，简化处理
                pass
            except Exception as e:
                logger.error(f"清理文档 {doc_id} 时出错: {e}")
                
        # 删除聊天
        for chat_id in self.created_resources['chats']:
            try:
                # 注意：当前API可能没有删除聊天的接口
                pass
            except Exception as e:
                logger.error(f"清理聊天 {chat_id} 时出错: {e}")
                
        # 删除数据集
        for dataset_id in self.created_resources['datasets']:
            try:
                await self.test_delete_dataset(dataset_id)
            except Exception as e:
                logger.error(f"清理数据集 {dataset_id} 时出错: {e}")
                
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行完整的API接口测试")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        try:
            # 1. 健康检查
            total_tests += 1
            if await self.test_health_check():
                passed_tests += 1
                
            # 2. 获取数据集列表
            total_tests += 1
            success, datasets_data = await self.test_list_datasets()
            if success:
                passed_tests += 1
                
            # 3. 创建数据集
            total_tests += 1
            success, dataset_id = await self.test_create_dataset()
            if success:
                passed_tests += 1
                
                if dataset_id:
                    # 4. 获取数据集详情
                    total_tests += 1
                    if await self.test_get_dataset(dataset_id):
                        passed_tests += 1
                        
                    # 5. 更新数据集
                    total_tests += 1
                    if await self.test_update_dataset(dataset_id):
                        passed_tests += 1
                        
                    # 6. 上传文档
                    total_tests += 1
                    success, document_id = await self.test_upload_document(dataset_id)
                    if success:
                        passed_tests += 1
                        
                    # 等待文档处理完成
                    await asyncio.sleep(5)
                    
                    # 7. 获取文档列表
                    total_tests += 1
                    success, docs_data = await self.test_list_documents(dataset_id)
                    if success:
                        passed_tests += 1
                        
                    # 8. 创建聊天
                    total_tests += 1
                    success, chat_id = await self.test_create_chat(dataset_id)
                    if success:
                        passed_tests += 1
                        
                        if chat_id:
                            # 9. 普通聊天对话
                            total_tests += 1
                            if await self.test_chat_completion(chat_id):
                                passed_tests += 1
                                
                            # 10. 流式聊天
                            total_tests += 1
                            if await self.test_stream_chat(chat_id):
                                passed_tests += 1
                                
                    # 11. 检索功能
                    total_tests += 1
                    if await self.test_retrieval(dataset_id):
                        passed_tests += 1
                        
                    # 12. 批量删除文档
                    if document_id:
                        total_tests += 1
                        if await self.test_delete_documents(dataset_id, [document_id]):
                            passed_tests += 1
                            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            logger.error(traceback.format_exc())
        finally:
            # 清理资源
            await self.cleanup_resources()
            
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
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.test_results,
            'created_resources': self.created_resources
        }
        
        with open('api_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info("\n详细测试报告已保存到: api_test_report.json")
        logger.info("所有测试日志已保存到: info.debug")
        
        if success_rate == 100:
            logger.info("🎉 所有测试通过！API服务运行正常。")
        elif success_rate >= 80:
            logger.info("⚠️  大部分测试通过，但仍有一些问题需要修复。")
        else:
            logger.info("❌ 多个测试失败，API服务可能存在严重问题。")

async def main():
    """主函数"""
    logger.info("开始执行完整的API接口测试")
    
    async with ComprehensiveAPITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())