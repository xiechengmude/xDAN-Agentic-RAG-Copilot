#!/usr/bin/env python3
"""
Import更新脚本
自动替换项目中的旧import语句为新的模块名称
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# 定义需要替换的import映射
IMPORT_MAPPINGS = {
    # 旧import -> 新import
    'from src.clients.litellm_sdk_client_v2': 'from src.clients.litellm_client',
    'from src.clients.llm_client': 'from src.clients.litellm_client',
    'from src.services.enhanced_s3_rag_service': 'from src.services.s3_service',
    'from src.services.rag_service_v2': 'from src.services.s3_service',
    'from src.clients.streaming_ragflow_client': 'from src.clients.ragflow_client',
}

# 定义类名映射（如果import语句中包含具体的类名）
CLASS_MAPPINGS = {
    'LiteLLMSDKClientV2': 'LiteLLMClient',
    'LLMClient': 'LiteLLMClient',
    'EnhancedS3RAGService': 'S3Service',
    'RAGServiceV2': 'S3Service',
    'StreamingRAGFlowClient': 'RAGFlowClient',
}

def find_python_files(root_dir: Path, exclude_dirs: List[str] = None) -> List[Path]:
    """
    递归查找所有Python文件
    
    Args:
        root_dir: 根目录
        exclude_dirs: 需要排除的目录名列表
        
    Returns:
        Python文件路径列表
    """
    if exclude_dirs is None:
        exclude_dirs = ['__pycache__', '.git', 'venv', 'env', '.venv']
    
    python_files = []
    for path in root_dir.rglob('*.py'):
        # 检查是否在排除目录中
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        # 排除本脚本
        if path.name == 'update_imports.py':
            continue
        python_files.append(path)
    
    return python_files

def update_imports_in_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    更新单个文件中的import语句
    
    Args:
        file_path: 文件路径
        dry_run: 是否只是预览，不实际修改文件
        
    Returns:
        (是否有修改, 修改详情列表)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    changes = []
    
    # 替换import语句
    for old_import, new_import in IMPORT_MAPPINGS.items():
        if old_import in content:
            # 处理带有具体导入的情况
            # 例如: from src.clients.litellm_sdk_client_v2 import LiteLLMSDKClientV2
            pattern = rf'{re.escape(old_import)}\s+import\s+([^;\n]+)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                imported_items = match.group(1)
                new_imported_items = imported_items
                
                # 替换类名
                for old_class, new_class in CLASS_MAPPINGS.items():
                    if old_class in imported_items:
                        new_imported_items = new_imported_items.replace(old_class, new_class)
                
                old_line = match.group(0)
                new_line = f'{new_import} import {new_imported_items}'
                
                content = content.replace(old_line, new_line)
                changes.append(f"  - {old_line.strip()}")
                changes.append(f"  + {new_line.strip()}")
            
            # 处理没有具体导入的情况
            # 例如: from src.clients.litellm_sdk_client_v2
            if f'{old_import}\n' in content or f'{old_import}\r\n' in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  - {old_import}")
                changes.append(f"  + {new_import}")
    
    # 替换类名的使用（如果直接使用了旧类名）
    for old_class, new_class in CLASS_MAPPINGS.items():
        # 匹配独立的类名（不是作为其他标识符的一部分）
        pattern = rf'\b{re.escape(old_class)}\b'
        if re.search(pattern, content):
            content = re.sub(pattern, new_class, content)
            changes.append(f"  Class rename: {old_class} -> {new_class}")
    
    # 如果有修改，写回文件
    if content != original_content and not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            return False, [f"Error writing file: {e}"]
    
    return content != original_content, changes

def create_backup(file_path: Path) -> Path:
    """
    创建文件备份
    
    Args:
        file_path: 原文件路径
        
    Returns:
        备份文件路径
    """
    backup_dir = file_path.parent / '.import_update_backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    import shutil
    shutil.copy2(file_path, backup_path)
    return backup_path

def main():
    """主函数"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='更新项目中的import语句')
    parser.add_argument('--dry-run', action='store_true', help='只预览更改，不实际修改文件')
    parser.add_argument('--path', type=str, default='.', help='要处理的目录路径')
    parser.add_argument('--exclude', nargs='*', default=[], help='额外排除的目录')
    parser.add_argument('--backup', action='store_true', help='在修改前创建备份文件')
    args = parser.parse_args()
    
    root_dir = Path(args.path).resolve()
    exclude_dirs = ['__pycache__', '.git', 'venv', 'env', '.venv', 'src_backup_20250626_201255'] + args.exclude
    
    print(f"开始扫描目录: {root_dir}")
    print(f"排除目录: {exclude_dirs}")
    if args.dry_run:
        print("*** DRY RUN MODE - 不会实际修改文件 ***")
    print()
    
    # 查找所有Python文件
    python_files = find_python_files(root_dir, exclude_dirs)
    print(f"找到 {len(python_files)} 个Python文件")
    print()
    
    # 统计信息
    total_modified = 0
    all_changes = []
    
    # 处理每个文件
    for file_path in python_files:
        # 如果需要备份且不是dry run，先创建备份
        if args.backup and not args.dry_run:
            # 先检查文件是否会被修改
            will_modify, _ = update_imports_in_file(file_path, dry_run=True)
            if will_modify:
                backup_path = create_backup(file_path)
                print(f"创建备份: {backup_path.relative_to(root_dir)}")
        
        modified, changes = update_imports_in_file(file_path, dry_run=args.dry_run)
        
        if modified:
            total_modified += 1
            relative_path = file_path.relative_to(root_dir)
            print(f"{'[DRY RUN] ' if args.dry_run else ''}修改文件: {relative_path}")
            for change in changes:
                print(f"  {change}")
            print()
            all_changes.append((str(relative_path), changes))
    
    # 输出总结
    print("=" * 60)
    print(f"总计: 扫描了 {len(python_files)} 个文件，{'将要' if args.dry_run else ''}修改 {total_modified} 个文件")
    
    # 保存更改日志
    if not args.dry_run and total_modified > 0:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'import_updates_{timestamp}.log'
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Import更新日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
            f.write(f"扫描文件数: {len(python_files)}\n")
            f.write(f"修改文件数: {total_modified}\n")
            f.write(f"备份已创建: {'是' if args.backup else '否'}\n")
            f.write("\n详细更改:\n")
            f.write("-" * 60 + "\n")
            for file_path, changes in all_changes:
                f.write(f"\n文件: {file_path}\n")
                for change in changes:
                    f.write(f"{change}\n")
        
        print(f"\n更改日志已保存到: {log_file}")
    
    if args.dry_run and total_modified > 0:
        print("\n要实际执行这些更改，请运行:")
        print(f"  python3 {Path(__file__).name}")
        print("\n要在修改前创建备份，请运行:")
        print(f"  python3 {Path(__file__).name} --backup")

if __name__ == '__main__':
    main()