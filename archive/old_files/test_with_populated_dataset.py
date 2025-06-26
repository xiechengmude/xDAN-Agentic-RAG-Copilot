#!/usr/bin/env python3
"""
使用有内容数据集的RAG功能测试
数据集ID: 7e8d9e924cde11f0afc90242ac140006 (201chunks, 46759tokens)
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

class RAGTesterWithPopulatedDataset:
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.headers = {
            'Authorization': 'Bearer xdan-demo-key-123456',
            'Content-Type': 'application/json'
        }
        # 使用有内容的数据集
        self.dataset_id = "7e8d9e924cde11f0afc90242ac140006"  # 201chunks, 46759tokens
        
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
            if response_data and isinstance(response_data, dict):
                if 'data' in response_data:
                    if isinstance(response_data['data'], list):
                        logger.info(f"   返回 {len(response_data['data'])} 条记录")
                    elif isinstance(response_data['data'], dict) and 'id' in response_data['data']:
                        logger.info(f"   ID: {response_data['data']['id']}")
                    else:
                        logger.info(f"   响应: {response_data.get('message', 'Success')}")
        else:
            logger.error(f"❌ {test_name} - 失败")
            if error:
                logger.error(f"   错误: {error}")
                
    async def test_dataset_details(self):
        """测试获取数据集详情"""
        logger.info(f"🔍 测试获取数据集详情: {self.dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{self.dataset_id}", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取数据集详情", success, data)
                
                if success and data.get('data'):
                    dataset_info = data['data']
                    logger.info(f"   数据集名称: {dataset_info.get('name')}")
                    logger.info(f"   文档数量: {dataset_info.get('document_count')}")
                    logger.info(f"   chunk数量: {dataset_info.get('chunk_count')}")
                    logger.info(f"   token数量: {dataset_info.get('token_count')}")
                
                return success
        except Exception as e:
            await self.log_test_result("获取数据集详情", False, error=str(e))
            return False
            
    async def test_list_documents(self):
        """测试获取文档列表"""
        logger.info(f"🔍 测试获取文档列表: {self.dataset_id}")
        try:
            async with self.session.get(f"{self.base_url}/api/v1/datasets/{self.dataset_id}/documents", headers=self.headers) as response:
                data = await response.json()
                success = response.status == 200
                await self.log_test_result("获取文档列表", success, data)
                
                if success and data.get('data'):
                    docs = data['data']
                    logger.info(f"   找到 {len(docs)} 个文档")
                    for i, doc in enumerate(docs[:3]):  # 只显示前3个
                        logger.info(f"   文档{i+1}: {doc.get('name', 'Unknown')} (状态: {doc.get('status', 'Unknown')})")
                
                return success, data
        except Exception as e:
            await self.log_test_result("获取文档列表", False, error=str(e))
            return False, None
            
    async def test_retrieval(self):
        """测试检索功能"""
        logger.info(f"🔍 测试检索功能: {self.dataset_id}")
        
        test_questions = [
            "360数科的主要业务是什么？",
            "智信引擎有什么功能？", 
            "API接入流程是怎样的？",
            "什么是RAG？",
            "文档中提到了哪些技术？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            try:
                payload = {
                    "question": question,
                    "dataset_ids": [self.dataset_id],
                    "top_k": 5
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/retrieval",
                    json=payload,
                    headers=self.headers
                ) as response:
                    data = await response.json()
                    success = response.status == 200
                    
                    test_name = f"检索测试{i}: {question[:20]}..."
                    await self.log_test_result(test_name, success, data)
                    
                    if success and data.get('data'):
                        chunks = data['data'].get('chunks', [])
                        logger.info(f"   检索到 {len(chunks)} 个相关片段")
                        
                        if chunks:
                            # 显示最相关的片段
                            top_chunk = chunks[0]
                            content_preview = top_chunk.get('content_with_weight', '')[:100]
                            logger.info(f"   最相关内容: {content_preview}...")
                            logger.info(f"   相似度: {top_chunk.get('similarity', 'N/A')}")
                    
                    if not success:
                        break
                        
            except Exception as e:
                await self.log_test_result(f"检索测试{i}", False, error=str(e))
                break
                
        return True
        
    async def test_create_chat(self):
        """测试创建聊天"""
        logger.info(f"🔍 测试创建聊天: {self.dataset_id}")
        try:
            payload = {
                "name": f"RAG测试聊天_{int(time.time())}",
                "dataset_ids": [self.dataset_id]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats",
                json=payload,
                headers=self.headers
            ) as response:
                data = await response.json()
                success = response.status == 200 and data.get('code') == 0
                await self.log_test_result("创建聊天", success, data)
                
                if success:
                    chat_id = data.get('data', {}).get('id')
                    logger.info(f"   聊天ID: {chat_id}")
                    return True, chat_id
                else:
                    return False, None
                    
        except Exception as e:
            await self.log_test_result("创建聊天", False, error=str(e))
            return False, None
            
    async def test_chat_with_rag(self, chat_id: str):
        """测试RAG增强聊天"""
        logger.info(f"🔍 测试RAG增强聊天: {chat_id}")
        
        test_questions = [
            "360数科的主要业务领域有哪些？请详细介绍。",
            "智信引擎的核心技术特点是什么？",
            "如何使用API接入360数科的服务？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            try:
                payload = {
                    "question": question,
                    "stream": False,
                    "session_id": f"rag_test_session_{i}_{int(time.time())}"
                }
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                    json=payload,
                    headers=self.headers
                ) as response:
                    data = await response.json()
                    success = response.status == 200
                    
                    test_name = f"RAG对话{i}: {question[:20]}..."
                    await self.log_test_result(test_name, success, data)
                    
                    if success and data.get('data'):
                        answer = data['data'].get('answer', '')
                        reference = data['data'].get('reference', {})
                        
                        logger.info(f"   回答长度: {len(answer)} 字符")
                        logger.info(f"   引用chunks: {reference.get('total', 0)} 个")
                        logger.info(f"   回答预览: {answer[:150]}...")
                    
                    if not success:
                        break
                        
            except Exception as e:
                await self.log_test_result(f"RAG对话{i}", False, error=str(e))
                break
                
        return True
        
    async def test_stream_chat_with_rag(self, chat_id: str):
        """测试流式RAG聊天"""
        logger.info(f"🔍 测试流式RAG聊天: {chat_id}")
        try:
            payload = {
                "question": "请详细分析360数科的技术优势和市场定位，并说明其核心竞争力。",
                "stream": True,
                "session_id": f"stream_rag_session_{int(time.time())}"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=self.headers
            ) as response:
                
                if response.status != 200:
                    await self.log_test_result("流式RAG聊天", False, f"HTTP {response.status}")
                    return False
                    
                # 收集流式响应
                chunks_received = 0
                total_size = 0
                content_preview = ""
                
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunks_received += 1
                        total_size += len(chunk)
                        
                        if chunks_received <= 3:
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            content_preview += chunk_str[:100]
                            logger.info(f"   流式数据块 {chunks_received}: {len(chunk)} 字节")
                        
                await self.log_test_result(
                    "流式RAG聊天", 
                    True,
                    {
                        "chunks_received": chunks_received, 
                        "total_size": total_size,
                        "content_preview": content_preview[:200]
                    }
                )
                return True
                
        except Exception as e:
            await self.log_test_result("流式RAG聊天", False, error=str(e))
            return False
            
    async def run_all_tests(self):
        """运行所有RAG测试"""
        logger.info("🚀 开始RAG功能完整测试")
        logger.info(f"📚 使用数据集: {self.dataset_id} (201chunks, 46759tokens)")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        try:
            # 1. 数据集详情
            total_tests += 1
            if await self.test_dataset_details():
                passed_tests += 1
                
            # 2. 文档列表
            total_tests += 1
            success, docs_data = await self.test_list_documents()
            if success:
                passed_tests += 1
                
            # 3. 检索功能测试
            total_tests += 1
            if await self.test_retrieval():
                passed_tests += 1
                
            # 4. 创建聊天
            total_tests += 1
            success, chat_id = await self.test_create_chat()
            if success:
                passed_tests += 1
                
                if chat_id:
                    # 5. RAG增强对话
                    total_tests += 1
                    if await self.test_chat_with_rag(chat_id):
                        passed_tests += 1
                        
                    # 6. 流式RAG对话
                    total_tests += 1
                    if await self.test_stream_chat_with_rag(chat_id):
                        passed_tests += 1
                        
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")
            
        # 生成测试报告
        await self.generate_test_report(total_tests, passed_tests)
        
    async def generate_test_report(self, total_tests: int, passed_tests: int):
        """生成测试报告"""
        logger.info("=" * 60)
        logger.info("📊 RAG功能测试报告")
        logger.info("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"总测试数量: {total_tests}")
        logger.info(f"成功测试数量: {passed_tests}")
        logger.info(f"失败测试数量: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"使用数据集: {self.dataset_id}")
        
        logger.info("\n详细测试结果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} {result['test_name']}")
            if not result['success'] and result['error']:
                logger.info(f"    错误: {result['error']}")
                
        # 保存报告
        report_data = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat(),
                'dataset_used': self.dataset_id,
                'dataset_info': "201chunks, 46759tokens"
            },
            'detailed_results': self.test_results
        }
        
        with open('rag_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info("\n详细测试报告已保存到: rag_test_report.json")
        logger.info("所有测试日志已保存到: info.debug")
        
        if success_rate == 100:
            logger.info("🎉 所有RAG功能测试通过！")
        elif success_rate >= 80:
            logger.info("⚠️  大部分RAG功能正常，少量问题需要修复。")
        else:
            logger.info("❌ RAG功能存在多个问题，需要仔细检查。")

async def main():
    logger.info("开始RAG功能完整测试 - 使用有内容的数据集")
    
    async with RAGTesterWithPopulatedDataset() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())