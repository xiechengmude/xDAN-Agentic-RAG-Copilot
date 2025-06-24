#!/usr/bin/env python3
"""
无代理环境测试脚本
确保测试不受代理影响
"""

import os
import sys
import subprocess
from pathlib import Path

# 清除所有代理环境变量
proxy_vars = [
    'http_proxy', 'https_proxy', 
    'HTTP_PROXY', 'HTTPS_PROXY',
    'all_proxy', 'ALL_PROXY',
    'no_proxy', 'NO_PROXY'
]

for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

print("✅ 代理环境变量已清除")
print("\n当前环境:")
for var in proxy_vars:
    value = os.environ.get(var, "未设置")
    print(f"  {var}: {value}")

# 运行快速测试
print("\n" + "="*60)
print("运行快速测试（无代理）")
print("="*60)

# 运行测试脚本
test_script = Path(__file__).parent / "quick_test.py"
subprocess.run([sys.executable, str(test_script)])