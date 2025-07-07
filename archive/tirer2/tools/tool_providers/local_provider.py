"""
本地工具提供者
整合本地工具集
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool, tool
from .base_provider import BaseToolProvider

import logging
logger = logging.getLogger(__name__)


class LocalProvider(BaseToolProvider):
    """本地工具提供者"""
    
    def __init__(self):
        super().__init__("Local")
        
    async def initialize(self) -> bool:
        """初始化本地工具"""
        try:
            # 创建工具
            self.tools = await self._create_tools()
            self.initialized = True
            
            logger.info(f"LocalProvider initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LocalProvider: {e}")
            return False
    
    async def _create_tools(self) -> List[BaseTool]:
        """创建本地工具"""
        tools = []
        
        @tool
        async def calculate(expression: str) -> Dict[str, Any]:
            """
            计算数学表达式
            
            Args:
                expression: 数学表达式字符串
            """
            try:
                # 安全的数学表达式计算
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    return {"success": False, "error": "不允许的字符"}
                
                result = eval(expression)
                return {
                    "success": True,
                    "expression": expression,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "expression": expression,
                    "error": str(e)
                }
        
        @tool
        async def text_analysis(text: str) -> Dict[str, Any]:
            """
            分析文本基本信息
            
            Args:
                text: 要分析的文本
            """
            try:
                words = text.split()
                chars = len(text)
                lines = text.count('\n') + 1
                
                return {
                    "success": True,
                    "text_length": chars,
                    "word_count": len(words),
                    "line_count": lines,
                    "first_words": words[:10] if words else [],
                    "analysis": f"文本包含 {chars} 个字符，{len(words)} 个单词，{lines} 行"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @tool
        async def data_conversion(data: str, from_format: str, to_format: str) -> Dict[str, Any]:
            """
            数据格式转换
            
            Args:
                data: 要转换的数据
                from_format: 源格式 (json, csv, text)
                to_format: 目标格式 (json, csv, text)
            """
            try:
                import json
                
                result_data = data
                
                # 简单的格式转换示例
                if from_format == "json" and to_format == "text":
                    json_data = json.loads(data)
                    result_data = str(json_data)
                elif from_format == "text" and to_format == "json":
                    result_data = json.dumps({"text": data}, ensure_ascii=False)
                
                return {
                    "success": True,
                    "original_format": from_format,
                    "target_format": to_format,
                    "converted_data": result_data
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        tools.extend([calculate, text_analysis, data_conversion])
        return tools
    
    async def get_tools(self) -> List[BaseTool]:
        """获取本地工具列表"""
        if not self.initialized:
            await self.initialize()
        return self.tools