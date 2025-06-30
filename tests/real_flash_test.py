#!/usr/bin/env python3
"""
使用真实API的FlashSearch测试
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


async def real_flash_test():
    """使用真实API测试FlashSearch"""
    print("🚀 开始真实API测试FlashSearch")
    
    # 检查环境变量
    bright_key = os.getenv('BRIGHTDATA_API_KEY')
    firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
    
    print(f"BrightData API: {'✅' if bright_key else '❌'}")
    print(f"FireCrawl API: {'✅' if firecrawl_key else '❌'}")
    
    if not bright_key or not firecrawl_key:
        print("❌ 缺少必要的API密钥")
        return
    
    question = "比亚迪2024年第三季度财报"
    print(f"\n问题: {question}")
    print("-" * 50)
    
    try:
        engine = FlashSearchEngine()
        result = await engine.flash_search(question)
        
        stats = result.get('stats', {})
        print(f"\n✅ 搜索成功!")
        print(f"📊 统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n📝 答案长度: {len(result.get('answer', ''))} 字符")
        print(f"📄 来源数量: {len(result.get('sources', []))}")
        
        # 分析来源类型
        sources = result.get('sources', [])
        successful = sum(1 for s in sources if not s.get('is_fallback'))
        fallbacks = sum(1 for s in sources if s.get('is_fallback'))
        print(f"🔍 成功爬取: {successful}, 回退摘要: {fallbacks}")
        
        # 保存结果
        output_file = 'real_flash_test_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 详细结果已保存: {output_file}")
        
        # 显示答案预览
        answer = result.get('answer', '')
        print(f"\n📖 答案预览:")
        print(answer[:500] + "..." if len(answer) > 500 else answer)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(real_flash_test())