#!/usr/bin/env python3
"""
S3框架详细流程测试器 - 遵循KISS和DRY原则
专注展示Search-Select-Synthesize每个环节的详细过程
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# API配置
API_BASE_URL = "http://localhost:8050"

class S3DetailedFlowTester:
    """S3框架详细流程测试器"""
    
    def __init__(self):
        self.session = None
        self.results = {
            "rag_chat": [],
            "deepsearch": []
        }
    
    async def create_session_with_dataset(self, mode_name: str) -> str:
        """创建带知识库的会话"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer xDAN-RAG-Service-Demo-Key"
        }
        
        payload = {
            "name": f"{mode_name}详细测试 - {datetime.now().strftime('%H:%M:%S')}",
            "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"]  # 确保触发S3流程
        }
        
        async with self.session.post(
            f"{API_BASE_URL}/api/v1/chats",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                chat_id = data["data"]["id"]
                print(f"✅ 会话创建成功: {chat_id}")
                return chat_id
            else:
                error = await response.text()
                raise Exception(f"会话创建失败: {error}")
    
    async def detailed_s3_test(self, mode: str, question: str, max_rounds: int) -> Dict[str, Any]:
        """详细的S3流程测试"""
        
        print(f"\n{'='*100}")
        print(f"🎯 {mode.upper()}模式详细测试")
        print(f"❓ 问题: {question}")
        print(f"🔄 最大轮数: {max_rounds}")
        print('='*100)
        
        # 创建会话
        print(f"\n📋 步骤1: 创建带知识库的会话")
        chat_id = await self.create_session_with_dataset(mode)
        
        # 发送请求并跟踪整个S3流程
        print(f"\n🚀 步骤2: 发送问题并启动S3流程")
        start_time = time.time()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer xDAN-RAG-Service-Demo-Key"
        }
        
        payload = {
            "content": question,
            "stream": False,
            "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],
            "max_rounds": max_rounds
        }
        
        print(f"⏳ 请求发送中...")
        async with self.session.post(
            f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            
            if response.status == 200:
                result = await response.json()
                duration = time.time() - start_time
                
                # 解析S3响应结构
                answer = result["data"]["answer"]
                s3_tags = result["data"].get("s3_tags", {})
                reference = result["data"].get("reference", {})
                
                print(f"\n✅ S3流程完成! 总耗时: {duration:.2f}秒")
                
                # 详细分析S3流程
                await self.analyze_s3_flow(s3_tags, reference, answer, duration)
                
                return {
                    "mode": mode,
                    "question": question,
                    "answer": answer,
                    "s3_tags": s3_tags,
                    "reference": reference,
                    "duration": duration,
                    "chat_id": chat_id,
                    "success": True
                }
            else:
                error = await response.text()
                print(f"❌ API错误: {error}")
                return {"mode": mode, "success": False, "error": error}
    
    async def analyze_s3_flow(self, s3_tags: Dict, reference: Dict, answer: str, duration: float):
        """详细分析S3流程的每个环节"""
        
        print(f"\n📊 S3框架流程分析")
        print("="*80)
        
        # 1. Think阶段分析
        think_info = s3_tags.get("think", {})
        print(f"\n🧠 Think阶段 - 框架思考过程:")
        print(f"  策略: {think_info.get('strategy', 'N/A')}")
        print(f"  推理: {think_info.get('reasoning', 'N/A')}")
        print(f"  决策: {think_info.get('decision', 'N/A')}")
        
        # 2. Search阶段详细分析
        search_info = s3_tags.get("search", {})
        print(f"\n🔍 Search阶段 - 文档检索过程:")
        print(f"  查询: {search_info.get('query', 'N/A')}")
        print(f"  搜索轮数: {search_info.get('rounds', 0)}")
        print(f"  找到文档数: {search_info.get('total_found', 0)}")
        print(f"  搜索策略: {search_info.get('strategy', 'N/A')}")
        
        # 详细展示搜索过程
        search_process = search_info.get("process", [])
        if search_process:
            print(f"  📋 搜索详细过程:")
            for i, process in enumerate(search_process, 1):
                print(f"    轮次{i}: {process}")
        else:
            print(f"  ⚠️ 未执行搜索过程 (可能直接使用LLM)")
        
        # 3. Documents阶段分析
        documents = s3_tags.get("documents", [])
        print(f"\n📚 Documents阶段 - 文档召回分析:")
        print(f"  召回文档数: {len(documents)}")
        
        if documents:
            print(f"  📄 召回文档详情:")
            for i, doc in enumerate(documents[:3], 1):  # 只显示前3个
                print(f"    文档{i}: {doc.get('name', 'Unknown')}")
                print(f"      相似度: {doc.get('similarity', 'N/A')}")
                print(f"      内容预览: {doc.get('content', '')[:100]}...")
        else:
            print(f"  ⚠️ 未召回任何文档")
        
        # 4. Reference阶段分析
        print(f"\n🔗 Reference阶段 - 引用信息分析:")
        print(f"  引用块数: {reference.get('total', 0)}")
        print(f"  搜索轮数: {reference.get('search_rounds', 0)}")
        
        ref_process = reference.get("search_process", [])
        if ref_process:
            print(f"  🔄 引用搜索过程:")
            for i, process in enumerate(ref_process, 1):
                if isinstance(process, dict):
                    print(f"    轮次{process.get('round', i)}: 查询='{process.get('query', '')[:50]}...'")
                    print(f"      找到文档: {process.get('documents_found', 0)}")
                    print(f"      Agent决策: {process.get('agent_decision', 'N/A')}")
                    print(f"      信心度: {process.get('agent_confidence', 'N/A')}")
                    print(f"      耗时: {process.get('time_ms', 0)}ms")
                else:
                    print(f"    轮次{i}: {process}")
        
        # 5. 最终答案质量分析
        print(f"\n✍️ Synthesize阶段 - 答案生成分析:")
        print(f"  答案长度: {len(answer)} 字符")
        print(f"  平均处理时间: {duration:.2f}秒")
        
        if len(answer) > 0:
            print(f"  📝 答案结构分析:")
            lines = answer.split('\n')
            print(f"    段落数: {len([l for l in lines if l.strip()])}")
            print(f"    是否有结构化内容: {'是' if any(['###' in l or '##' in l or '-' in l for l in lines]) else '否'}")
        
        # 6. 性能指标
        print(f"\n⚡ 性能指标:")
        print(f"  总响应时间: {duration:.2f}秒")
        if search_info.get('rounds', 0) > 0:
            avg_search_time = duration / search_info.get('rounds', 1)
            print(f"  平均搜索时间: {avg_search_time:.2f}秒/轮")
        
        # 7. 质量评估
        print(f"\n🎯 质量评估:")
        
        # 检索质量
        retrieval_quality = "优秀" if search_info.get('total_found', 0) > 5 else "良好" if search_info.get('total_found', 0) > 0 else "待改进"
        print(f"  检索质量: {retrieval_quality}")
        
        # 响应速度
        speed_quality = "优秀" if duration < 20 else "良好" if duration < 40 else "待改进"
        print(f"  响应速度: {speed_quality}")
        
        # 答案完整性
        completeness = "优秀" if len(answer) > 500 else "良好" if len(answer) > 200 else "待改进"
        print(f"  答案完整性: {completeness}")
    
    async def run_rag_chat_test(self):
        """运行S3-RAG-Chat详细测试"""
        
        print(f"\n🎯 S3-RAG-Chat模式 - 智信类问答测试")
        print("专注考察: 文档召回精度、Agent思考过程、快速响应能力")
        
        # 智信类测试问题
        rag_questions = [
            "如何重置我的密码？",
            "公司的年假政策是什么？",
            "财务报销流程的具体步骤"
        ]
        
        for i, question in enumerate(rag_questions, 1):
            print(f"\n{'▶' * 20} RAG-Chat测试 {i}/{len(rag_questions)} {'◀' * 20}")
            result = await self.detailed_s3_test("rag_chat", question, max_rounds=2)
            self.results["rag_chat"].append(result)
            
            if i < len(rag_questions):
                print(f"\n⏸️ 等待3秒后进行下一个测试...")
                await asyncio.sleep(3)
    
    async def run_deepsearch_test(self):
        """运行S3-DeepSearch详细测试"""
        
        print(f"\n🎯 S3-DeepSearch模式 - 深度搜索测试")
        print("专注考察: 多跳推理能力、深度搜索策略、复杂分析质量")
        
        # 深度搜索类测试问题
        deep_questions = [
            "分析2024年第四季度全球半导体供应链紧张对中国新能源汽车出口的具体影响，结合最新贸易数据和政策变化",
            "比较Python和Go语言在后端开发中的优劣势，包括性能、并发、生态、部署等方面的深度分析"
        ]
        
        for i, question in enumerate(deep_questions, 1):
            print(f"\n{'▶' * 20} DeepSearch测试 {i}/{len(deep_questions)} {'◀' * 20}")
            result = await self.detailed_s3_test("deepsearch", question, max_rounds=5)
            self.results["deepsearch"].append(result)
            
            if i < len(deep_questions):
                print(f"\n⏸️ 等待5秒后进行下一个测试...")
                await asyncio.sleep(5)
    
    def generate_comprehensive_report(self):
        """生成综合报告"""
        
        print(f"\n{'='*120}")
        print(f"📊 S3框架详细测试综合报告")
        print(f"{'='*120}")
        
        # 统计成功率
        rag_success = len([r for r in self.results["rag_chat"] if r.get("success")])
        deep_success = len([r for r in self.results["deepsearch"] if r.get("success")])
        
        print(f"\n📈 测试概览:")
        print(f"  RAG-Chat测试: {rag_success}/{len(self.results['rag_chat'])} 成功")
        print(f"  DeepSearch测试: {deep_success}/{len(self.results['deepsearch'])} 成功")
        
        # 性能对比
        if rag_success > 0 and deep_success > 0:
            rag_avg_time = sum(r.get("duration", 0) for r in self.results["rag_chat"] if r.get("success")) / rag_success
            deep_avg_time = sum(r.get("duration", 0) for r in self.results["deepsearch"] if r.get("success")) / deep_success
            
            rag_avg_length = sum(len(r.get("answer", "")) for r in self.results["rag_chat"] if r.get("success")) / rag_success
            deep_avg_length = sum(len(r.get("answer", "")) for r in self.results["deepsearch"] if r.get("success")) / deep_success
            
            print(f"\n⚡ 性能对比:")
            print(f"  RAG-Chat平均响应时间: {rag_avg_time:.2f}秒")
            print(f"  DeepSearch平均响应时间: {deep_avg_time:.2f}秒")
            print(f"  速度差异: DeepSearch比RAG-Chat慢 {(deep_avg_time/rag_avg_time-1)*100:.1f}%")
            
            print(f"\n📝 答案质量对比:")
            print(f"  RAG-Chat平均答案长度: {rag_avg_length:.0f}字符")
            print(f"  DeepSearch平均答案长度: {deep_avg_length:.0f}字符")
            print(f"  详细程度: DeepSearch比RAG-Chat详细 {(deep_avg_length/rag_avg_length):.1f}倍")
        
        # Langfuse查看指南
        print(f"\n🔍 Langfuse可观察性查看指南:")
        print(f"1. 访问 http://localhost:3000/traces")
        print(f"2. 按时间筛选查看刚才的测试traces")
        print(f"3. 重点关注的指标:")
        print(f"   - Token使用量对比")
        print(f"   - 模型调用链路")
        print(f"   - 成本分析")
        print(f"4. 问题定位点:")
        print(f"   - 搜索轮数是否符合预期")
        print(f"   - Agent决策是否合理")
        print(f"   - 响应时间瓶颈在哪个阶段")
        
        print(f"\n✅ 详细测试完成！")
        print(f"📍 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 遵循原则: KISS (保持简单) + DRY (避免重复)")
    
    async def run_full_test(self):
        """运行完整的S3详细测试"""
        
        print(f"🚀 S3框架详细流程测试开始")
        print(f"📍 测试目标: 考察Search-Select-Synthesize各环节质量")
        print(f"📍 API地址: {API_BASE_URL}")
        print(f"📍 Langfuse: http://localhost:3000")
        print(f"📍 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # 健康检查
            try:
                async with session.get(f"{API_BASE_URL}/health") as response:
                    if response.status == 200:
                        print(f"✅ API服务正常")
                    else:
                        print(f"❌ API服务异常")
                        return
            except:
                print(f"❌ 无法连接API服务")
                return
            
            # 运行RAG-Chat测试
            await self.run_rag_chat_test()
            
            # 分隔符
            print(f"\n{'🔄' * 50}")
            
            # 运行DeepSearch测试
            await self.run_deepsearch_test()
            
            # 生成综合报告
            self.generate_comprehensive_report()

async def main():
    """主函数"""
    tester = S3DetailedFlowTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())