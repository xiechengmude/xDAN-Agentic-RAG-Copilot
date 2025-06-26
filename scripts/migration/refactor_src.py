#!/usr/bin/env python3
"""
重构src目录结构 - 删除重复实现，保留精简高效的版本
"""

import os
import shutil
from datetime import datetime

# 创建备份目录
backup_dir = f"src_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print(f"创建备份目录: {backup_dir}")
os.makedirs(backup_dir, exist_ok=True)

# 需要删除的文件（重复实现）
files_to_remove = [
    # 重复的LLM客户端
    "src/clients/llm_client.py",
    "src/clients/litellm_sdk_client.py",  # 保留v2
    
    # 重复的S3服务实现
    "src/services/enhanced_s3_rag_service.py",
    "src/services/enhanced_s3_rag_service_v2_fixed.py",
    
    # 旧的RAGFlow客户端（待评估）
    "src/clients/streaming_ragflow_client.py",  # 检索不需要流式
    "src/clients/ragflow_sdk_wrapper.py",  # 过度封装
]

# 需要保留的核心文件
files_to_keep = [
    # 核心框架
    "src/core/s3_framework.py",
    "src/core/config_loader.py",
    "src/core/models.py",
    
    # 客户端
    "src/clients/litellm_sdk_client_v2.py",
    "src/clients/ragflow_client.py",  # 评估后决定是否用new版本替换
    
    # 服务
    "src/services/rag_service_v2.py",  # 最符合架构的实现
    "src/services/service_factory.py",  # 需要更新
]

# 备份所有src文件
print("\n备份src目录...")
shutil.copytree("src", backup_dir, dirs_exist_ok=True)
print(f"✓ 备份完成: {backup_dir}")

# 删除重复文件
print("\n删除重复实现...")
for file_path in files_to_remove:
    if os.path.exists(file_path):
        print(f"  删除: {file_path}")
        os.remove(file_path)
    else:
        print(f"  跳过: {file_path} (不存在)")

# 重命名文件
print("\n重命名文件...")
rename_map = {
    "src/clients/litellm_sdk_client_v2.py": "src/clients/litellm_client.py",
    "src/services/rag_service_v2.py": "src/services/rag_service.py",
}

for old_name, new_name in rename_map.items():
    if os.path.exists(old_name) and not os.path.exists(new_name):
        print(f"  重命名: {old_name} -> {new_name}")
        os.rename(old_name, new_name)

print("\n重构完成！")
print(f"\n备份保存在: {backup_dir}")
print("\n最终的src结构：")
print("""
src/
├── core/
│   ├── __init__.py
│   ├── config_loader.py      # 配置加载
│   ├── models.py             # 数据模型
│   └── s3_framework.py       # S3核心框架
├── clients/
│   ├── __init__.py
│   ├── litellm_client.py     # 统一的LLM客户端
│   └── ragflow_client.py     # RAGFlow检索客户端
├── services/
│   ├── __init__.py
│   ├── rag_service.py        # RAG服务（基于S3框架）
│   ├── s3_service.py         # S3服务封装
│   └── service_factory.py    # 服务工厂
├── api/                      # API层（需要整合）
└── utils/                    # 工具函数
""")

print("\n下一步：")
print("1. 更新所有import语句")
print("2. 更新service_factory.py")
print("3. 整合API层")
print("4. 运行测试确保功能正常")