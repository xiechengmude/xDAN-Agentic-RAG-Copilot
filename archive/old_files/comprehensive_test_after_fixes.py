#!/usr/bin/env python3
"""
修复后的完整API测试
使用默认数据集: 7e8d9e924cde11f0afc90242ac140006
"""

import json
import asyncio
import aiohttp
import logging
import time
from datetime import datetime

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

class ComprehensiveTestAfterFixes:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.headers = {
            'Authorization': 'Bearer xdan-demo-key-123456',
            'Content-Type': 'application/json'
        }
        # 使用默认的有内容数据集
        self.default_dataset_id = "7e8d9e924cde11f0afc90242ac140006"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def log_test_result(self, test_name: str, success: bool, response_data: any = None, error: str = None):
        """记录测试结果"""
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
        else:
            logger.error(f"❌ {test_name} - 失败")
            if error:
                logger.error(f"   错误: {error}")
                
    async def test_health_check(self):
        """测试健康检查"""
        logger.info("🔍 测试健康检查接口")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("健康检查", success, data)
                return success
        except Exception as e:
            await self.log_test_result("健康检查", False, error=str(e))
            return False
            
    async def test_list_datasets(self):
        """测试获取数据集列表"""
        logger.info("🔍 测试获取数据集列表")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取数据集列表", success, data)
                return success, data
        except Exception as e:
            await self.log_test_result("获取数据集列表", False, error=str(e))
            return False, None
            
    async def test_get_dataset_detail(self):
        """测试获取数据集详情 - 修复后"""
        logger.info(f"🔍 测试获取数据集详情: {self.default_dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{self.default_dataset_id}", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取数据集详情", success, data)
                
                if success and data.get('data'):
                    rag_info = data['data'].get('rag_availability', {})
                    logger.info(f"   RAG状态: {rag_info.get('status')}")
                    logger.info(f"   RAG消息: {rag_info.get('message')}")
                    logger.info(f"   可以聊天: {rag_info.get('can_chat')}")
                
                return success
        except Exception as e:
            await self.log_test_result("获取数据集详情", False, error=str(e))
            return False
            
    async def test_list_documents(self):
        """测试获取文档列表 - 修复后"""
        logger.info(f"🔍 测试获取文档列表: {self.default_dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{self.default_dataset_id}/documents", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取文档列表", success, data)
                
                if success and data.get('data'):
                    docs = data['data']
                    logger.info(f"   找到 {len(docs)} 个文档")
                
                return success, data
        except Exception as e:
            await self.log_test_result("获取文档列表", False, error=str(e))
            return False, None
            
    async def test_retrieval(self):
        """测试检索功能 - 新增"""
        logger.info(f"🔍 测试检索功能: {self.default_dataset_id}")
        try:
            payload = {
                "question": "360数科的主要业务是什么？",
                "dataset_ids": [self.default_dataset_id],
                "top_k": 5
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/retrieval",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("检索功能", success, data)
                
                if success and data.get('data'):
                    chunks = data['data'].get('chunks', [])
                    logger.info(f"   检索到 {len(chunks)} 个相关片段")
                
                return success
        except Exception as e:
            await self.log_test_result("检索功能", False, error=str(e))
            return False
            
    async def test_create_chat_with_dataset(self):
        """测试创建RAG聊天 - 有数据集"""
        logger.info(f"🔍 测试创建RAG聊天: {self.default_dataset_id}")
        try:
            payload = {
                "name": f"RAG聊天测试_{int(time.time())}",
                "dataset_ids": [self.default_dataset_id],
                "description": "测试RAG模式聊天"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200 and data.get('code') == 0
                await self.log_test_result("创建RAG聊天", success, data)
                
                if success and data.get('data'):
                    chat_data = data['data']
                    chat_id = chat_data.get('id')
                    chat_mode = chat_data.get('chat_mode')
                    available_datasets = chat_data.get('available_datasets', [])
                    logger.info(f"   聊天ID: {chat_id}")
                    logger.info(f"   聊天模式: {chat_mode}")
                    logger.info(f"   可用数据集: {len(available_datasets)}个")
                    return True, chat_id
                else:
                    return False, None
                    
        except Exception as e:
            await self.log_test_result("创建RAG聊天", False, error=str(e))
            return False, None
            
    async def test_create_chat_without_dataset(self):
        """测试创建基础聊天 - 无数据集"""
        logger.info("🔍 测试创建基础聊天（无数据集）")
        try:
            payload = {
                "name": f"基础聊天测试_{int(time.time())}",
                "dataset_ids": [],
                "description": "测试基础LLM模式聊天"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200 and data.get('code') == 0
                await self.log_test_result("创建基础聊天", success, data)
                
                if success and data.get('data'):
                    chat_data = data['data']
                    chat_id = chat_data.get('id')
                    chat_mode = chat_data.get('chat_mode')
                    logger.info(f"   聊天ID: {chat_id}")
                    logger.info(f"   聊天模式: {chat_mode}")
                    return True, chat_id
                else:
                    return False, None
                    
        except Exception as e:
            await self.log_test_result("创建基础聊天", False, error=str(e))
            return False, None
            
    async def test_chat_completion(self, chat_id: str, test_name: str):
        """测试聊天对话 - 修复参数格式"""
        logger.info(f"🔍 {test_name}: {chat_id}")
        try:
            payload = {
                "content": "请介绍一下360数科的主要业务领域。",
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result(test_name, success, data)
                
                if success and data.get('data'):
                    content = data['data'].get('content', '')
                    logger.info(f"   回答长度: {len(content)} 字符")
                    logger.info(f"   回答预览: {content[:100]}...")
                
                return success
        except Exception as e:
            await self.log_test_result(test_name, False, error=str(e))
            return False
            
    async def test_stream_chat(self, chat_id: str, test_name: str):
        """测试流式聊天"""
        logger.info(f"🔍 {test_name}: {chat_id}")
        try:
            payload = {
                "content": "请详细分析360数科的技术优势。",
                "stream": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=self.headers
            ) as response:
                
                if response.status != 200:
                    await self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
                # 收集流式响应
                chunks_received = 0
                total_size = 0
                
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunks_received += 1
                        total_size += len(chunk)
                        if chunks_received <= 3:
                            logger.info(f"   收到流式数据块 {chunks_received}: {len(chunk)} 字节")
                        
                await self.log_test_result(test_name, True, {
                    "chunks_received": chunks_received, 
                    "total_size": total_size
                })
                return True
                
        except Exception as e:
            await self.log_test_result(test_name, False, error=str(e))
            return False
            
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始修复后的完整API测试")
        logger.info(f"📚 默认数据集: {self.default_dataset_id}")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        try:
            # 1. 健康检查
            total_tests += 1
            if await self.test_health_check():
                passed_tests += 1
                
            # 2. 数据集列表
            total_tests += 1
            success, _ = await self.test_list_datasets()
            if success:
                passed_tests += 1
                
            # 3. 数据集详情 - 修复后
            total_tests += 1
            if await self.test_get_dataset_detail():
                passed_tests += 1
                
            # 4. 文档列表 - 修复后
            total_tests += 1
            success, _ = await self.test_list_documents()
            if success:
                passed_tests += 1
                
            # 5. 检索功能 - 新增
            total_tests += 1
            if await self.test_retrieval():
                passed_tests += 1
                
            # 6. 创建RAG聊天
            total_tests += 1
            success, rag_chat_id = await self.test_create_chat_with_dataset()
            if success:
                passed_tests += 1
                
                if rag_chat_id:
                    # 7. RAG聊天对话
                    total_tests += 1
                    if await self.test_chat_completion(rag_chat_id, "RAG聊天对话"):
                        passed_tests += 1
                        
                    # 8. RAG流式聊天
                    total_tests += 1
                    if await self.test_stream_chat(rag_chat_id, "RAG流式聊天"):
                        passed_tests += 1
                        
            # 9. 创建基础聊天
            total_tests += 1
            success, basic_chat_id = await self.test_create_chat_without_dataset()
            if success:
                passed_tests += 1
                
                if basic_chat_id:
                    # 10. 基础聊天对话
                    total_tests += 1
                    if await self.test_chat_completion(basic_chat_id, "基础聊天对话"):
                        passed_tests += 1
                        
                    # 11. 基础流式聊天
                    total_tests += 1
                    if await self.test_stream_chat(basic_chat_id, "基础流式聊天"):
                        passed_tests += 1
                        
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            
        # 生成测试报告
        await self.generate_test_report(total_tests, passed_tests)
        
    async def generate_test_report(self, total_tests: int, passed_tests: int):
        """生成测试报告"""
        logger.info("=" * 60)
        logger.info("📊 修复后的API测试报告")
        logger.info("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"总测试数量: {total_tests}")
        logger.info(f"成功测试数量: {passed_tests}")
        logger.info(f"失败测试数量: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"默认数据集: {self.default_dataset_id}")
        
        logger.info("\n详细测试结果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {result['test_name']}")
                
        # 保存报告
        report_data = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat(),
                'default_dataset': self.default_dataset_id,
                'fixes_applied': [
                    "添加数据集详情路由",
                    "修复文档列表字符串处理",
                    "添加检索功能路由",
                    "修复聊天参数格式",
                    "添加兼容性聊天模式"
                ]
            },
            'detailed_results': self.test_results
        }
        
        with open('test_report_after_fixes.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info("\n详细测试报告已保存到: test_report_after_fixes.json")
        logger.info("所有测试日志已保存到: info.debug")
        
        if success_rate >= 90:
            logger.info("🎉 修复成功！大部分功能正常工作。")
        elif success_rate >= 70:
            logger.info("⚠️  修复部分成功，仍有少量问题需要解决。")
        else:
            logger.info("❌ 仍存在较多问题，需要进一步修复。")

async def main():
    logger.info("开始修复后的完整API测试")
    
    async with ComprehensiveTestAfterFixes() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())