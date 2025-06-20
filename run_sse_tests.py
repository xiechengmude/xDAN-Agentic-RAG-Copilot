#!/usr/bin/env python3
"""
SSE 测试运行脚本
"""

import sys
import subprocess
import os
from pathlib import Path

def run_backend_tests():
    """运行后端 SSE 测试"""
    print("🧪 运行后端 SSE 单元测试...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/test_sse_endpoints.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行 SSE 集成测试...")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/integration/test_sse_integration.py",
        "-v",
        "--tb=short",
        "--color=yes",
        "-s"  # 不捕获输出，便于调试
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def run_frontend_tests():
    """运行前端 SSE 测试"""
    print("\n🎨 运行前端 SSE 单元测试...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend 目录不存在，跳过前端测试")
        return True
    
    # 检查是否安装了依赖
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json 不存在，跳过前端测试")
        return True
    
    # 运行前端测试
    cmd = ["npm", "run", "test", "--", "sseClient.test.ts"]
    
    result = subprocess.run(
        cmd, 
        cwd=frontend_dir,
        capture_output=True, 
        text=True
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def check_dependencies():
    """检查测试依赖"""
    print("🔍 检查测试依赖...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "requests",
        "psutil"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print("请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    print("✅ 所有依赖都已安装")
    return True

def main():
    """主函数"""
    print("🚀 开始运行 SSE 测试套件")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境变量
    os.environ["TESTING"] = "1"
    os.environ["PYTHONPATH"] = os.getcwd()
    
    # 运行测试
    results = []
    
    # 1. 后端单元测试
    try:
        backend_success = run_backend_tests()
        results.append(("后端单元测试", backend_success))
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        results.append(("后端单元测试", False))
    
    # 2. 集成测试
    try:
        integration_success = run_integration_tests()
        results.append(("集成测试", integration_success))
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        results.append(("集成测试", False))
    
    # 3. 前端测试
    try:
        frontend_success = run_frontend_tests()
        results.append(("前端测试", frontend_success))
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        results.append(("前端测试", False))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print("-" * 30)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if not success:
            all_passed = False
    
    print("-" * 30)
    overall_status = "✅ 全部通过" if all_passed else "❌ 部分失败"
    print(f"总体状态: {overall_status}")
    
    # 返回适当的退出码
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()