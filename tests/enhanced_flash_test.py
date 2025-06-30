#!/usr/bin/env python3
"""
测试增强版FlashSearch（时间感知+引用标注）
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import FlashSearchEngine


async def test_enhanced_features():
    """测试增强功能"""
    print("🚀 测试增强版FlashSearch功能")
    print("=" * 50)
    
    try:
        engine = FlashSearchEngine()
        
        # 测试时间感知功能
        print("\n1. 测试时间感知功能:")
        test_questions = [
            "人工智能发展",  # 无时间上下文
            "比亚迪最新财报",  # 有时间上下文
            "特斯拉2024年销量",  # 已有年份
        ]
        
        for question in test_questions:
            enhanced = engine._enhance_question_with_time(question)
            print(f"   {question:<20} → {enhanced}")
        
        # 测试引用标注功能
        print("\n2. 测试引用标注功能:")
        test_sources = [
            {"title": "测试文章1", "is_fallback": False},
            {"title": "测试文章2", "is_fallback": True},
            {"title": "", "is_fallback": False},
        ]
        
        for i, source in enumerate(test_sources, 1):
            citation = engine._format_source_citation(source, i)
            print(f"   来源{i}: {citation}")
        
        # 测试完整搜索流程
        print("\n3. 测试完整的增强搜索:")
        question = "新能源汽车发展趋势"  # 无时间上下文，应该会添加年份
        print(f"   问题: {question}")
        
        result = await engine.flash_search(question)
        
        stats = result.get('stats', {})
        print(f"   总耗时: {stats.get('total_duration', 0):.1f}秒")
        print(f"   搜索结果: {stats.get('search_results', 0)}个")
        print(f"   成功爬取: {stats.get('successful_crawls', 0)}个")
        print(f"   摘要回退: {stats.get('snippet_fallbacks', 0)}个")
        
        # 检查答案中的引用标注
        answer = result.get('answer', '')
        print(f"   答案长度: {len(answer)}字符")
        
        # 查找引用标注
        import re
        citations = re.findall(r'【来源\d+(?:-摘要)?】', answer)
        if citations:
            print(f"   发现引用标注: {citations}")
        else:
            print("   未发现引用标注")
        
        # 保存结果
        output_file = 'enhanced_flash_test_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"   结果已保存: {output_file}")
        
        # 显示答案片段
        print(f"\n   答案预览:")
        print(f"   {answer[:300]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_features())