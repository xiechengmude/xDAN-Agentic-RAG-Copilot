#!/usr/bin/env python3
"""
最简单的FlashSearch测试
验证基本功能是否正常
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import flash_search


async def simple_test():
    """简单测试一个问题"""
    print("🚀 开始简单测试FlashSearch")
    
    question = "什么是人工智能?"
    print(f"问题: {question}")
    
    try:
        result = await flash_search(question)
        
        print("\n✅ 搜索成功!")
        print(f"答案长度: {len(result.get('answer', ''))}")
        print(f"来源数量: {len(result.get('sources', []))}")
        
        stats = result.get('stats', {})
        print(f"\n📊 统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n📝 答案:")
        print(result.get('answer', 'No answer')[:500] + "...")
        
        # 保存结果
        with open('simple_flash_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n💾 结果已保存到 simple_flash_test_result.json")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_test())