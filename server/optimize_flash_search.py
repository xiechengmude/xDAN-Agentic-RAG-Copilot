#!/usr/bin/env python3
"""
FlashSearch Performance Optimization Script
优化FlashSearch搜索性能，目标：从60s降到15s以内
"""

import os
import sys
from pathlib import Path

def apply_performance_optimizations():
    """应用性能优化"""
    
    # 修改环境变量配置
    env_optimizations = {
        'BRIGHTDATA_TIMEOUT': '15',      # 从60s减少到15s
        'CRAWL_TIMEOUT': '10',           # 从30s减少到10s
        'SEARCH_RESULTS': '6',           # 从12减少到6
        'SELECT_URLS': '2',              # 从4减少到2
        'PARALLEL_CRAWL': '2',           # 保持2个并发
        'MAX_ITERATIONS': '2',           # 从3减少到2轮
        'TIME_BUDGET': '30',             # 从60s减少到30s
    }
    
    print("🔧 应用FlashSearch性能优化配置...")
    
    # 更新环境变量
    for key, value in env_optimizations.items():
        os.environ[key] = value
        print(f"  ✅ {key} = {value}")
    
    # 写入优化后的.env文件
    env_file = Path("../.env.optimized")
    with open(env_file, 'w') as f:
        f.write("""# FlashSearch 性能优化配置
# 目标：15秒内完成搜索

# 网络请求优化
BRIGHTDATA_TIMEOUT=15
CRAWL_TIMEOUT=10

# 搜索结果数量优化  
SEARCH_RESULTS=6
SELECT_URLS=2
PARALLEL_CRAWL=2

# 迭代优化
MAX_ITERATIONS=2
TIME_BUDGET=30

# 其他配置保持不变
BRIGHTDATA_API_KEY=test_brightdata_key
FIRECRAWL_API_KEY=test_firecrawl_key  
DEEPSEEK_API_KEY=test_deepseek_key
LITELLM_MODEL=deepseek-chat
LITELLM_API_BASE=https://api.deepseek.com
LOG_LEVEL=info
""")
    
    print(f"\n💾 优化配置已保存到: {env_file}")
    
    return env_optimizations

def apply_code_optimizations():
    """应用代码级优化"""
    
    # 需要修改的核心文件
    optimizations = [
        {
            "file": "../src/core/flash_s3_enhanced.py",
            "changes": [
                "max_iterations = 2  # 减少迭代轮数",
                "time_budget = 30    # 减少时间预算",
                "strategies = ['precision', 'recent']  # 只使用核心策略"
            ]
        },
        {
            "file": "../src/core/flash_search_engine.py", 
            "changes": [
                "SEARCH_RESULTS = 6   # 减少搜索结果数",
                "SELECT_URLS = 2      # 减少爬取URL数",
                "CRAWL_TIMEOUT = 10   # 减少爬取超时"
            ]
        }
    ]
    
    print("\n🔧 建议的代码优化:")
    for opt in optimizations:
        print(f"\n📁 {opt['file']}:")
        for change in opt['changes']:
            print(f"  • {change}")
    
    return optimizations

def create_fast_search_preset():
    """创建快速搜索预设"""
    
    preset_code = '''
# 快速搜索模式配置
FAST_SEARCH_CONFIG = {
    "max_iterations": 1,           # 单轮搜索
    "time_budget": 15,             # 15秒时间限制
    "search_strategies": ["precision"],  # 只使用精确搜索
    "max_results": 4,              # 最多4个结果
    "max_crawl_urls": 2,           # 最多爬取2个URL
    "brightdata_timeout": 10,      # BrightData 10秒超时
    "crawl_timeout": 8,            # 爬取8秒超时
    "skip_s3_evaluation": True,    # 跳过S3评估加速
    "enable_cache": True,          # 启用结果缓存
}
'''
    
    print("\n⚡ 创建快速搜索预设:")
    print(preset_code)
    
    return preset_code

def benchmark_estimate():
    """预估优化后的性能"""
    
    performance_breakdown = {
        "优化前（当前）": {
            "BrightData搜索": "5-10s × 3轮 = 15-30s",
            "FireCrawl爬取": "8-15s × 3轮 = 24-45s", 
            "S3评估": "2-3s × 3轮 = 6-9s",
            "答案生成": "3-5s",
            "总计": "48-89s (实际~60s)"
        },
        "优化后（目标）": {
            "BrightData搜索": "3-5s × 1轮 = 3-5s",
            "FireCrawl爬取": "4-6s × 1轮 = 4-6s",
            "跳过S3评估": "0s",
            "答案生成": "2-3s", 
            "总计": "9-14s ✅"
        }
    }
    
    print("\n📊 性能优化预估:")
    for mode, breakdown in performance_breakdown.items():
        print(f"\n{mode}:")
        for stage, time in breakdown.items():
            print(f"  • {stage}: {time}")
    
    return performance_breakdown

def create_benchmark_test():
    """创建性能基准测试"""
    
    test_code = '''#!/usr/bin/env python3
"""
FlashSearch Performance Benchmark Test
性能基准测试脚本
"""

import asyncio
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.flash_s3_enhanced import flash_s3_enhanced

async def benchmark_search(query, iterations=3):
    """基准测试搜索性能"""
    
    times = []
    
    for i in range(iterations):
        print(f"\\n🔬 第 {i+1}/{iterations} 次测试: {query[:30]}...")
        
        start_time = time.time()
        try:
            result = await flash_s3_enhanced(question=query)
            end_time = time.time()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            
            answer_len = len(result.get("answer", ""))
            sources_count = len(result.get("sources", []))
            
            print(f"  ✅ 完成: {elapsed:.1f}s | {answer_len}字符 | {sources_count}来源")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            times.append(0)
    
    # 统计结果
    valid_times = [t for t in times if t > 0]
    if valid_times:
        avg_time = sum(valid_times) / len(valid_times)
        min_time = min(valid_times)
        max_time = max(valid_times)
        
        print(f"\\n📊 性能统计:")
        print(f"  平均时间: {avg_time:.1f}s")
        print(f"  最快时间: {min_time:.1f}s") 
        print(f"  最慢时间: {max_time:.1f}s")
        print(f"  成功率: {len(valid_times)}/{iterations}")
        
        return avg_time
    
    return None

async def main():
    """主测试函数"""
    
    test_queries = [
        "人工智能最新发展趋势",
        "2024年科技创新报告", 
        "机器学习在医疗领域应用"
    ]
    
    print("🧪 FlashSearch 性能基准测试")
    print("="*50)
    
    all_times = []
    
    for query in test_queries:
        avg_time = await benchmark_search(query)
        if avg_time:
            all_times.append(avg_time)
    
    if all_times:
        overall_avg = sum(all_times) / len(all_times)
        print(f"\\n🎯 总体平均时间: {overall_avg:.1f}s")
        
        if overall_avg <= 15:
            print("✅ 性能目标达成!")
        else:
            print(f"⚠️ 距离15s目标还需优化 {overall_avg-15:.1f}s")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    benchmark_file = Path("benchmark_test.py")
    with open(benchmark_file, 'w') as f:
        f.write(test_code)
    
    print(f"\n🧪 性能基准测试脚本已创建: {benchmark_file}")
    return benchmark_file

def main():
    """主函数"""
    print("⚡ FlashSearch 性能优化工具")
    print("="*50)
    
    # 1. 应用环境变量优化
    env_opts = apply_performance_optimizations()
    
    # 2. 建议代码优化
    code_opts = apply_code_optimizations()
    
    # 3. 创建快速搜索预设
    preset = create_fast_search_preset()
    
    # 4. 性能预估
    estimates = benchmark_estimate()
    
    # 5. 创建基准测试
    benchmark_file = create_benchmark_test()
    
    print(f"\n🎯 优化总结:")
    print(f"  • 环境变量: {len(env_opts)}项优化")
    print(f"  • 代码修改: {len(code_opts)}个文件")
    print(f"  • 预估加速: 60s → 9-14s (4-7倍)")
    print(f"  • 基准测试: {benchmark_file}")
    
    print(f"\n📋 下一步操作:")
    print(f"  1. 使用优化后的环境配置")
    print(f"  2. 根据建议修改核心代码")
    print(f"  3. 运行基准测试验证效果")
    print(f"  4. 监控实际搜索性能")

if __name__ == "__main__":
    main()