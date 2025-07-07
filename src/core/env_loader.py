#!/usr/bin/env python3
"""
统一的环境变量加载器
确保在任何情况下都能正确加载.env文件
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EnvLoader:
    """环境变量加载器 - 单例模式"""
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self.load_env()
            self._loaded = True
    
    @staticmethod
    def find_project_root() -> Path:
        """
        查找项目根目录（包含.env或requirements.txt的目录）
        从当前文件位置向上查找
        """
        current = Path(__file__).resolve()
        
        # 向上查找，最多到系统根目录
        for parent in current.parents:
            # 检查标志性文件
            if any((parent / marker).exists() for marker in [
                '.env', '.env.example', 'requirements.txt', 
                'pyproject.toml', '.git', 'README.md'
            ]):
                return parent
                
        # 如果找不到，返回当前工作目录
        return Path.cwd()
    
    @staticmethod
    def load_env_file(env_path: Path) -> Dict[str, str]:
        """加载.env文件内容"""
        env_vars = {}
        
        if not env_path.exists():
            logger.warning(f".env文件不存在: {env_path}")
            return env_vars
            
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                        
                    # 解析KEY=VALUE格式
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                            
                        env_vars[key] = value
                        
        except Exception as e:
            logger.error(f"加载.env文件失败: {e}")
            
        return env_vars
    
    def load_env(self, env_file: Optional[str] = None):
        """
        加载环境变量
        优先级：
        1. 系统环境变量（最高优先级）
        2. .env文件
        3. .env.example文件（如果.env不存在）
        """
        # 查找项目根目录
        project_root = self.find_project_root()
        logger.info(f"项目根目录: {project_root}")
        
        # 确定.env文件路径
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = project_root / '.env'
            
        # 如果.env不存在，尝试从.env.example复制
        if not env_path.exists():
            example_path = project_root / '.env.example'
            if example_path.exists():
                logger.info(f"从.env.example创建.env文件")
                try:
                    import shutil
                    shutil.copy2(example_path, env_path)
                except Exception as e:
                    logger.error(f"复制.env.example失败: {e}")
        
        # 加载.env文件
        env_vars = self.load_env_file(env_path)
        
        # 设置环境变量（不覆盖已存在的）
        loaded_count = 0
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
                loaded_count += 1
                logger.debug(f"加载环境变量: {key}")
                
        logger.info(f"从.env文件加载了 {loaded_count} 个环境变量")
        
        # 添加项目根目录到Python路径
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            logger.info(f"添加项目根目录到Python路径: {project_root}")
            
        return env_vars
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量值"""
        return os.environ.get(key, default)
    
    @staticmethod
    def set(key: str, value: str):
        """设置环境变量值"""
        os.environ[key] = value
        
    def reload(self):
        """重新加载环境变量"""
        self._loaded = False
        self.load_env()


# 创建全局实例
env_loader = EnvLoader()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量的便捷函数"""
    return env_loader.get(key, default)


def ensure_env_loaded():
    """确保环境变量已加载"""
    if not EnvLoader._loaded:
        env_loader.load_env()
        

# 模块导入时自动加载
ensure_env_loaded()