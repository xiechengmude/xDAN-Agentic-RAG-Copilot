"""
简单的Langfuse测试 - 直接调用S3服务
"""

import asyncio
import os
import sys

# 设置路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Langfuse环境变量
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-b5e54e4c-4e9a-4c20-b5a7-5148d0f9683e"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-ef7ef641-8f04-41ef-a474-338a80e7dedf"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"

# 启用Langfuse
import litellm
litellm.success_callback = ["langfuse"]

from src.services.service_factory import ServiceFactory

async def test_rag_chat():
    """测试RAG Chat模式"""
    print("🔍 测试 RAG Chat 模式")
    
    # 创建S3服务
    s3_service = ServiceFactory.create_default_service()
    
    questions = [
        "什么是Python编程语言？",
        "Docker的基本概念是什么？",
        "解释REST API"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"问题 {i}: {question}")
        
        try:
            # 调用S3服务 - 使用较少的迭代次数模拟RAG Chat
            response = await s3_service.ask(
                question=question,
                dataset_ids=["7e8d9e924cde11f0afc90242ac140006"],  # 默认数据集
                max_rounds=2,  # RAG Chat模式 - 较少迭代
                stream=False,
                metadata={
                    "trace_name": f"💬 RAG对话: {question[:30]}...",
                    "tags": ["s3-rag-chat", "test"],
                    "session_id": f"rag-chat-test-{i}"
                }
            )
            
            # 收集响应
            answer = ""
            async for chunk in response:
                answer += chunk
            
            print(f"✅ 成功")
            print(f"答案预览: {answer[:150]}...")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
        
        await asyncio.sleep(2)  # 避免请求过快

async def test_deepsearch():
    """测试DeepSearch模式"""
    print("\n\n🔬 测试 DeepSearch 模式")
    
    # 创建S3服务
    s3_service = ServiceFactory.create_default_service()
    
    questions = [
        "比较Python和JavaScript在Web开发中的优劣势",
        "2024年人工智能领域的最新发展趋势",
        "深度学习框架TensorFlow和PyTorch的对比分析"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"问题 {i}: {question}")
        
        try:
            # 调用S3服务 - 使用更多迭代模拟DeepSearch
            response = await s3_service.ask(
                question=question,
                dataset_ids=["7e8d9e924cde11f0afc90242ac140006"],
                max_rounds=4,  # DeepSearch模式 - 更多迭代
                stream=False,
                metadata={
                    "trace_name": f"🔬 深度搜索: {question[:30]}...",
                    "tags": ["s3-deepsearch", "test"],
                    "session_id": f"deepsearch-test-{i}"
                }
            )
            
            # 收集响应
            answer = ""
            async for chunk in response:
                answer += chunk
            
            print(f"✅ 成功")
            print(f"答案预览: {answer[:150]}...")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
        
        await asyncio.sleep(2)

async def main():
    """主函数"""
    print("🚀 Langfuse 集成测试（直接调用S3服务）")
    print(f"📍 Langfuse地址: {os.environ.get('LANGFUSE_HOST')}")
    
    # 运行测试
    await test_rag_chat()
    await test_deepsearch()
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("\n🔍 在Langfuse中查看结果:")
    print("  1. 访问: http://localhost:3000")
    print("  2. 在Traces页面查看:")
    print("     - 💬 标记为 s3-rag-chat 的是RAG对话")
    print("     - 🔬 标记为 s3-deepsearch 的是深度搜索")
    print("  3. 点击具体的Trace查看:")
    print("     - 搜索阶段的迭代次数")
    print("     - Agent的决策过程")
    print("     - 最终答案的生成")
    print("  4. 对比两种模式的性能差异")

if __name__ == "__main__":
    asyncio.run(main())