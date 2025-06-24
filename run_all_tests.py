#!/usr/bin/env python3
"""
运行所有测试套件
按照依赖顺序执行各个维度的测试
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_test_suite(test_path: str, name: str) -> bool:
    """运行单个测试套件"""
    print("\n" + "=" * 60)
    print(f"运行 {name} 测试")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["uv", "run", "python", test_path],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="运行RAGFlow API客户端测试套件")
    parser.add_argument(
        "--suite",
        choices=["ragflow", "llm", "local", "rag", "all"],
        default="all",
        help="选择要运行的测试套件"
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="在第一个失败时停止"
    )
    
    args = parser.parse_args()
    
    # 定义测试套件
    test_suites = [
        ("tests/ragflow_remote_service/test_ragflow_api.py", "RAGFlow远程服务"),
        ("tests/llm_model/test_llm_client.py", "LLM模型"),
        ("tests/rag_model/test_s3_rag_service.py", "S3 RAG模型"),
        ("tests/local_backend_api/test_local_server.py", "本地后端API"),
    ]
    
    # 根据参数过滤测试套件
    if args.suite != "all":
        suite_map = {
            "ragflow": 0,
            "llm": 1,
            "rag": 2,
            "local": 3
        }
        if args.suite in suite_map:
            test_suites = [test_suites[suite_map[args.suite]]]
    
    print(f"\n🚀 开始运行测试套件")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {args.suite}")
    
    results = []
    
    for test_path, test_name in test_suites:
        success = run_test_suite(test_path, test_name)
        results.append((test_name, success))
        
        if not success and args.stop_on_failure:
            print("\n❌ 测试失败，停止执行")
            break
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {total_tests} 个测试套件")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n❌ {failed_tests} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())