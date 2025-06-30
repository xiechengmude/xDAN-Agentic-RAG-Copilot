#!/usr/bin/env python3
"""
FlashSearch 简单测试脚本
验证简化架构的基本功能
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import FlashSearchEngine


async def test_flash_search():
    """测试FlashSearch功能"""
    print("🚀 开始测试FlashSearch简化架构")
    print("=" * 60)
    
    # 测试问题
    test_questions = [
        "比亚迪最新财报数据分析",
        "特斯拉和比亚迪销量对比",
        "新能源汽车行业发展趋势"
    ]
    
    engine = FlashSearchEngine()
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[测试 {i}/3] 问题: {question}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            result = await engine.flash_search(question)
            
            duration = time.time() - start_time
            stats = result.get("stats", {})
            
            print(f"✅ 搜索完成 ({duration:.1f}s)")
            print(f"📊 统计信息:")
            print(f"   - 搜索结果: {stats.get('search_results', 0)}个")
            print(f"   - 选择URL: {stats.get('selected_urls', 0)}个")
            print(f"   - 成功爬取: {stats.get('successful_crawls', 0)}个")
            print(f"   - 摘要回退: {stats.get('snippet_fallbacks', 0)}个")
            
            print(f"\n📝 答案预览:")
            answer = result.get("answer", "")
            print(f"   {answer[:200]}...")
            
            # 保存详细结果
            output_file = f"flash_search_test_{i}_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"💾 详细结果已保存: {output_file}")
            
            # 间隔一下避免过度请求
            if i < len(test_questions):
                print("⏳ 等待5秒...")
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 FlashSearch测试完成")


async def test_individual_components():
    """测试各个组件的独立功能"""
    print("\n🔧 测试各个组件...")
    
    engine = FlashSearchEngine()
    question = "比亚迪股价"
    
    try:
        # 测试搜索
        print("\n1. 测试搜索组件")
        search_results = await engine.search(question)
        print(f"   搜索到 {len(search_results)} 个结果")
        
        # 测试选择
        print("\n2. 测试选择组件")
        if search_results:
            selected_urls = await engine.select(question, search_results)
            print(f"   选择了 {len(selected_urls)} 个URL")
            
            # 测试爬取
            print("\n3. 测试爬取组件")
            if selected_urls:
                crawl_results = await engine.crawl(selected_urls[:2], search_results)  # 只测试前2个
                print(f"   爬取了 {len(crawl_results)} 个内容")
                
                # 测试生成
                print("\n4. 测试生成组件")
                if crawl_results:
                    answer = await engine.synthesize(question, crawl_results)
                    print(f"   生成答案长度: {len(answer)} 字符")
                    print(f"   答案预览: {answer[:100]}...")
    
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("FlashSearch 简化架构测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试完整流程
    await test_flash_search()
    
    # 测试各个组件
    await test_individual_components()


if __name__ == "__main__":
    asyncio.run(main())