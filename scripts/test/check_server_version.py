#!/usr/bin/env python3
"""
检查服务器代码版本
"""

import requests
import subprocess

# 获取本地最新的commit
result = subprocess.run(['git', 'log', '-1', '--format=%h %s'], capture_output=True, text=True)
local_commit = result.stdout.strip()
print(f"本地最新commit: {local_commit}")

# 测试服务器健康状态
response = requests.get("http://150.109.16.195:8050/health")
print(f"\n服务器健康状态: {response.status_code}")
if response.status_code == 200:
    print(f"响应: {response.json()}")

# 获取服务器的版本信息（如果有的话）
response = requests.get("http://150.109.16.195:8050/")
print(f"\n根路径响应: {response.json()}")

print("\n建议：")
print("1. 确认服务器已拉取最新代码：git pull origin dev")
print("2. 确认服务器已重启API服务")
print("3. 检查服务器日志查看详细错误信息")