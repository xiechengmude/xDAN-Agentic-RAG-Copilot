#!/usr/bin/env python3
"""
简单的搜索测试脚本 - 只测试搜索功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import FlashSearchEngine


async def main():
    """主函数"""
    # 读取问题文件的第一个问题
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/diverse_questions_50.json"
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # 取第一个问题
    question_data = questions[0]
    
    print(f"问题ID: {question_data['id']}")
    print(f"问题: {question_data['question'][:100]}...")
    print(f"类别: {question_data['category']}")
    print(f"评价维度: {', '.join(question_data['verify']['evaluation_dimensions'].keys())}")
    print("\n" + "="*80 + "\n")
    
    # 创建搜索引擎
    search_engine = FlashSearchEngine()
    
    # 执行搜索
    print("开始执行FlashSearch...")
    try:
        result = await search_engine.flash_search(question_data['question'])
        
        print("\n搜索完成！")
        print(f"答案长度: {len(result.get('answer', ''))} 字符")
        print(f"使用的信息源: {len(result.get('sources', []))} 个")
        print(f"总耗时: {result.get('total_time', 0):.1f} 秒")
        
        # 显示部分答案
        print("\n答案预览:")
        print("-" * 80)
        answer = result.get('answer', '')
        print(answer[:500] + "..." if len(answer) > 500 else answer)
        
        # 保存完整结果
        output_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/test_search_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'question_data': question_data,
                'search_result': result
            }, f, ensure_ascii=False, indent=2)
        print(f"\n完整结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"搜索出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())