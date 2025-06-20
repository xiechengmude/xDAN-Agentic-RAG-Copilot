#!/usr/bin/env python3
"""
测试运行脚本
用于验证测试代码的语法正确性
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_test_imports():
    """检查测试模块是否可以正确导入"""
    test_modules = [
        'tests.unit.test_ragflow_sdk_wrapper',
        'tests.unit.test_enhanced_s3_rag_service',
        'tests.unit.test_retrieve_functionality',
        'tests.integration.test_s3_framework_integration'
    ]
    
    print("检查测试模块导入...")
    for module_name in test_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
        except Exception as e:
            print(f"✗ {module_name}: {type(e).__name__}: {e}")
    
    print("\n检查fixture导入...")
    try:
        from tests.fixtures import mock_data
        print("✓ tests.fixtures.mock_data")
    except Exception as e:
        print(f"✗ tests.fixtures.mock_data: {e}")
    
    try:
        from tests import test_config
        print("✓ tests.test_config")
    except Exception as e:
        print(f"✗ tests.test_config: {e}")

def main():
    print("RAGFlow API Client 测试检查\n")
    print("=" * 50)
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print("=" * 50 + "\n")
    
    # 检查测试导入
    check_test_imports()
    
    print("\n" + "=" * 50)
    print("提示：要运行完整测试，请先安装测试依赖：")
    print("pip install -r requirements-test.txt")
    print("然后运行: pytest tests/")

if __name__ == "__main__":
    main()