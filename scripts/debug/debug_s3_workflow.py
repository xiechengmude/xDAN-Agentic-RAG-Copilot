#!/usr/bin/env python3
"""
调试S3完整工作流
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.s3_service import S3Service

async def debug_s3_workflow():
    """调试S3完整工作流"""
    print("="*60)
    print("调试S3完整工作流")
    print("="*60)
    
    # 配置信息
    config = {
        'ragflow_api_url': 'http://150.109.16.195:7080',
        'ragflow_api_key': 'ragflow-g4ZWE3OTNhNDUxYTExZjA8MTljMDI0Mm',
        'default_dataset_id': '7e8d9e924cde11f0afc90242ac140006'
    }
    
    try:
        s3_service = S3Service(config)
        print("✓ S3Service初始化成功")
        
        question = "智信是什么？"
        dataset_ids = [config['default_dataset_id']]
        
        print(f"\n测试问题: {question}")
        print(f"数据集ID: {dataset_ids}")
        print("-" * 40)
        
        # 调用完整的S3工作流
        result_count = 0
        async for result in s3_service.ask(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=1,  # 只执行1轮，便于调试
            stream=False
        ):
            result_count += 1
            print(f"\n收到结果 {result_count}:")
            print(f"类型: {type(result)}")
            print(f"键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            
            if isinstance(result, dict):
                # 检查是否有错误
                if 'error' in result:
                    print(f"错误: {result['error']}")
                
                # 检查工作流状态
                if 'workflow_completed' in result:
                    print(f"工作流完成: {result['workflow_completed']}")
                
                # 检查搜索轮次
                if 'rounds' in result:
                    rounds = result['rounds']
                    print(f"搜索轮次: {len(rounds)}")
                    for i, round_info in enumerate(rounds, 1):
                        print(f"  轮次{i}: 查询='{round_info.get('search_query', 'N/A')}', 结果数={round_info.get('search_results_count', 0)}")
                
                # 检查选定文档
                if 'selected_documents' in result:
                    docs = result['selected_documents']
                    print(f"选定文档: {len(docs)} 个")
                
                # 检查最终答案
                if 'final_answer' in result:
                    answer = result['final_answer']
                    print(f"答案: {answer[:100]}...")
            
            break  # 只处理第一个结果
        
        if result_count == 0:
            print("✗ 没有收到任何结果")
        
    except Exception as e:
        print(f"✗ 异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_s3_workflow())