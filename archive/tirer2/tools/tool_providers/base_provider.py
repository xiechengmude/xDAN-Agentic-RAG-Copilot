"""
基础工具提供者抽象类
定义LangGraph工具提供者的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.tools import BaseTool
import logging

# 导入xDAN统一日志系统
try:
    from ....logging_config import get_xdan_logger
    logger = get_xdan_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class BaseToolProvider(ABC):
    """LangGraph工具提供者基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self.tools = []
        logger.debug(f"初始化工具提供者: {name}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        异步初始化工具提供者
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def get_tools(self) -> List[BaseTool]:
        """
        获取工具列表
        
        Returns:
            List[BaseTool]: LangChain标准工具列表
        """
        pass
    
    async def cleanup(self):
        """清理资源（可选实现）"""
        pass
    
    def is_available(self) -> bool:
        """检查工具提供者是否可用"""
        return self.initialized and len(self.tools) > 0
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [tool.name for tool in self.tools]
    
    def __str__(self) -> str:
        return f"{self.name}Provider(tools={len(self.tools)}, available={self.is_available()})"