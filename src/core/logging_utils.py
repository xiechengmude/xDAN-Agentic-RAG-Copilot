"""
DeepSearch日志工具类
提供统一的日志记录功能，支持全链路追踪
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union
import traceback
from datetime import datetime


class DeepSearchLogger:
    """DeepSearch专用日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_phase_start(self, phase: str, **kwargs):
        """记录阶段开始"""
        self.logger.info(f"{'='*60}")
        self.logger.info(f"🚀 [{phase}] 阶段开始")
        if kwargs:
            self.logger.info(f"   参数: {self._format_data(kwargs)}")
    
    def log_phase_end(self, phase: str, success: bool = True, duration: float = None, **kwargs):
        """记录阶段结束"""
        status = "✅ 成功" if success else "❌ 失败"
        msg = f"{status} [{phase}] 阶段结束"
        if duration:
            msg += f" (耗时: {duration:.2f}s)"
        self.logger.info(msg)
        if kwargs:
            self.logger.info(f"   结果: {self._format_data(kwargs)}")
        self.logger.info(f"{'='*60}\n")
    
    def log_input(self, phase: str, data: Any, data_type: str = "输入"):
        """记录输入数据"""
        self.logger.debug(f"📥 [{phase}] {data_type}:")
        self._log_structured_data(data)
    
    def log_output(self, phase: str, data: Any, data_type: str = "输出"):
        """记录输出数据"""
        self.logger.debug(f"📤 [{phase}] {data_type}:")
        self._log_structured_data(data)
    
    def log_api_call(self, api_name: str, method: str, url: str, **kwargs):
        """记录API调用"""
        self.logger.debug(f"🌐 [{api_name}] {method} {url}")
        if kwargs:
            self.logger.debug(f"   参数: {self._format_data(kwargs)}")
    
    def log_api_response(self, api_name: str, status_code: int = None, duration: float = None, **kwargs):
        """记录API响应"""
        msg = f"📡 [{api_name}] 响应"
        if status_code:
            msg += f" - 状态码: {status_code}"
        if duration:
            msg += f" - 耗时: {duration:.2f}s"
        self.logger.debug(msg)
        if kwargs:
            self.logger.debug(f"   数据: {self._format_data(kwargs)}")
    
    def log_llm_call(self, model: str, messages: List[Dict], **kwargs):
        """记录LLM调用"""
        self.logger.debug(f"🤖 [LLM调用] 模型: {model}")
        self.logger.debug(f"   消息数: {len(messages)}")
        if self.logger.isEnabledFor(logging.DEBUG):
            # 只在DEBUG级别记录完整消息
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                preview = content[:200] + '...' if len(content) > 200 else content
                self.logger.debug(f"   [{i}] {role}: {preview}")
        if kwargs:
            self.logger.debug(f"   参数: {self._format_data(kwargs)}")
    
    def log_llm_response(self, model: str, response: Any, duration: float = None):
        """记录LLM响应"""
        msg = f"🤖 [LLM响应] 模型: {model}"
        if duration:
            msg += f" - 耗时: {duration:.2f}s"
        self.logger.debug(msg)
        
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            preview = content[:500] + '...' if len(content) > 500 else content
            self.logger.debug(f"   内容预览: {preview}")
            
            if hasattr(response, 'usage'):
                self.logger.debug(f"   Token使用: {response.usage}")
    
    def log_error(self, phase: str, error: Exception, **context):
        """记录错误"""
        self.logger.error(f"💥 [{phase}] 错误: {type(error).__name__}: {str(error)}")
        if context:
            self.logger.error(f"   上下文: {self._format_data(context)}")
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"   堆栈:\n{traceback.format_exc()}")
    
    def log_summary(self, title: str, data: Dict[str, Any]):
        """记录摘要信息"""
        self.logger.info(f"📊 {title}:")
        for key, value in data.items():
            self.logger.info(f"   {key}: {value}")
    
    def _log_structured_data(self, data: Any, indent: int = 1):
        """记录结构化数据"""
        indent_str = "   " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and len(str(value)) > 100:
                    self.logger.debug(f"{indent_str}{key}: {type(value).__name__}({len(value)} items)")
                    if self.logger.isEnabledFor(logging.DEBUG):
                        self._log_structured_data(value, indent + 1)
                else:
                    preview = self._format_value(value)
                    self.logger.debug(f"{indent_str}{key}: {preview}")
        
        elif isinstance(data, list):
            self.logger.debug(f"{indent_str}列表 ({len(data)} 项):")
            for i, item in enumerate(data[:3]):  # 只显示前3项
                self.logger.debug(f"{indent_str}[{i}]:")
                self._log_structured_data(item, indent + 1)
            if len(data) > 3:
                self.logger.debug(f"{indent_str}... 还有 {len(data) - 3} 项")
        
        else:
            preview = self._format_value(data)
            self.logger.debug(f"{indent_str}{preview}")
    
    def _format_value(self, value: Any, max_length: int = 200) -> str:
        """格式化值的显示"""
        if value is None:
            return "None"
        
        if isinstance(value, str):
            if len(value) > max_length:
                return f'"{value[:max_length]}..."'
            return f'"{value}"'
        
        if isinstance(value, (int, float, bool)):
            return str(value)
        
        if isinstance(value, datetime):
            return value.isoformat()
        
        # 其他类型
        str_value = str(value)
        if len(str_value) > max_length:
            return f"{str_value[:max_length]}..."
        return str_value
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化字典数据为单行显示"""
        items = []
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 50:
                items.append(f"{key}='{value[:50]}...'")
            elif isinstance(value, (list, dict)):
                items.append(f"{key}={type(value).__name__}({len(value)})")
            else:
                items.append(f"{key}={value}")
        return ", ".join(items)


def get_logger(name: str) -> DeepSearchLogger:
    """获取DeepSearch日志记录器"""
    return DeepSearchLogger(name)


def setup_logging(level: str = "INFO", verbose: bool = False):
    """
    配置日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        verbose: 是否显示详细日志
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 配置格式
    if verbose or level.upper() == "DEBUG":
        # DEBUG模式：显示更多信息
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    else:
        # 普通模式：简洁格式
        format_str = "%(asctime)s - %(levelname)s - %(message)s"
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 调整第三方库的日志级别
    if not verbose:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("litellm").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # 特殊处理LiteLLM的DEBUG日志
    if level.upper() == "DEBUG":
        # 即使在DEBUG模式下，也限制LiteLLM的一些噪音日志
        logging.getLogger("litellm.utils").setLevel(logging.INFO)
        logging.getLogger("litellm.llms").setLevel(logging.INFO)