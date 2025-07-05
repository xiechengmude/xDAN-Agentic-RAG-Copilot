#!/usr/bin/env python3
"""
S3 Single Question Test - 单问题测试
测试单个问题的S3 RAG流程
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")


async def test_single_question():
    """测试单个问题"""
    
    # 测试问题
    question = "授信申请需调用哪些核心接口？"
    
    print(f"🔍 测试问题: {question}")
    print(f"📦 使用数据集: {DEFAULT_DATASET_ID}")
    print("-" * 60)
    
    try:
        # 创建S3服务实例
        print("\n⚙️  初始化S3服务...")
        s3_service = get_default_service()
        print("✅ S3服务初始化成功")
        
        # 开始计时
        start_time = datetime.now()
        
        # 使用S3服务执行问答
        print(f"\n🚀 开始S3 RAG处理...")
        result = None
        async for res in s3_service.ask(
            question=question,
            dataset_ids=[DEFAULT_DATASET_ID],
            max_rounds=3,
            stream=False
        ):
            result = res
            break  # 非流式模式，只取第一个结果
        
        # 计算耗时
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result and result.get('workflow_completed'):
            print("\n✅ S3工作流完成!")
            
            # 提取结果
            answer = result.get('final_answer', '')
            selected_docs = result.get('selected_documents', [])
            rounds = result.get('rounds', [])
            
            print(f"\n📊 处理统计:")
            print(f"   - 耗时: {duration:.2f}秒")
            print(f"   - 搜索轮数: {len(rounds)}")
            print(f"   - 找到文档数: {len(selected_docs)}")
            
            # 显示搜索过程
            if rounds:
                print(f"\n🔄 搜索过程:")
                for i, round_info in enumerate(rounds, 1):
                    query = round_info.get('search_query', 'N/A')
                    count = round_info.get('search_results_count', 0)
                    print(f"   轮次{i}: 查询 '{query}' → 找到 {count} 个文档")
            
            # 显示找到的文档
            if selected_docs:
                print(f"\n📚 相关文档 (显示前3个):")
                for i, doc in enumerate(selected_docs[:3], 1):
                    similarity = doc.get('similarity', 0)
                    content_preview = doc.get('content', '')[:100]
                    print(f"   文档{i}: 相似度={similarity:.3f}")
                    print(f"   内容预览: {content_preview}...")
            
            # 显示最终答案
            print(f"\n💡 最终答案:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
            
            # 保存结果到文件
            output_file = f"/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/s3_single_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"问题: {question}\n")
                f.write(f"耗时: {duration:.2f}秒\n")
                f.write(f"搜索轮数: {len(rounds)}\n")
                f.write(f"找到文档数: {len(selected_docs)}\n")
                f.write(f"\n答案:\n{answer}\n")
                
                if rounds:
                    f.write(f"\n搜索过程:\n")
                    for i, round_info in enumerate(rounds, 1):
                        query = round_info.get('search_query', 'N/A')
                        count = round_info.get('search_results_count', 0)
                        f.write(f"轮次{i}: {query} → {count}个文档\n")
            
            print(f"\n💾 结果已保存到: {output_file}")
            
        else:
            print(f"\n❌ S3工作流未完成")
            print(f"   原因: {result}")
            
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 60)
    print("S3 RAG 单问题测试")
    print("=" * 60)
    
    # 检查环境变量
    S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME")
    S3_GENERATOR_API_BASE = os.getenv("S3_GENERATOR_API_BASE")
    
    print(f"\n🔧 配置信息:")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    print(f"   - S3 API: {S3_GENERATOR_API_BASE}")
    print(f"   - 数据集: {DEFAULT_DATASET_ID}")
    
    # 运行测试
    asyncio.run(test_single_question())
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()