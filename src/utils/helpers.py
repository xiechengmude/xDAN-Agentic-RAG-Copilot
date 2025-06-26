"""
辅助函数
提供通用的工具函数
"""

import logging
import json
from typing import Any, Dict, Optional

def setup_logging(level: str = "INFO"):
    """
    设置日志配置
    
    Args:
        level: 日志级别
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    
    Args:
        text: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default

def format_bytes(size: int) -> str:
    """
    格式化字节大小
    
    Args:
        size: 字节数
        
    Returns:
        格式化的字符串（如：1.2 MB）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix