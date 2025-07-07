"""
FastMCP工具提供者 - 基于FastMCP的真正MCP协议连接
使用FastMCP客户端连接到MCP服务器并提供工具调用能力
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool
from .base_provider import BaseToolProvider

import logging
logger = logging.getLogger(__name__)

try:
    from fastmcp import Client
    from fastmcp.client.transports import SSETransport, WSTransport
    import mcp.types as mcp_types
    FASTMCP_AVAILABLE = True
    logger.info("FastMCP available for MCP client connections")
except ImportError as e:
    FASTMCP_AVAILABLE = False
    logger.warning(f"FastMCP not available: {e}")
    # 创建一个空的types模块用于类型提示
    class DummyTypes:
        class Tool:
            def __init__(self):
                self.name = ""
                self.description = ""
                self.inputSchema = None
    mcp_types = DummyTypes()


class FastMCPProvider(BaseToolProvider):
    """基于FastMCP的MCP工具提供者"""
    
    def __init__(self):
        super().__init__("FastMCP")
        self.mcp_server_url = None
        self.fastmcp_client = None
        self.mcp_tools = []
        self.connected = False
        self._client_context = None  # Store the context manager
        self._client_session = None  # Store the active session
        
    async def initialize(self) -> bool:
        """初始化FastMCP客户端"""
        try:
            if not FASTMCP_AVAILABLE:
                logger.warning("FastMCP not available, skipping initialization")
                self.tools = []
                self.initialized = True
                return False
            
            # 检查MCP服务器配置
            self.mcp_server_url = os.getenv("MCP_SERVER_URL")
            logger.info(f"FastMCP初始化，服务器URL: {self.mcp_server_url}")
            
            if not self.mcp_server_url:
                logger.warning("MCP_SERVER_URL not configured for FastMCP")
                self.tools = []
                self.initialized = True
                return False
            
            # 创建并连接到MCP服务器
            success = await self._create_and_connect()
            
            if success:
                # 获取真实的MCP工具
                await self._discover_mcp_tools()
                logger.info(f"✅ FastMCP连接成功，发现{len(self.mcp_tools)}个MCP工具")
                self.tools = await self._create_langchain_tools()
            else:
                logger.warning("❌ FastMCP连接失败")
                self.tools = []
            
            self.initialized = True
            return success
            
        except Exception as e:
            logger.error(f"FastMCP初始化失败: {e}")
            self.tools = []
            self.initialized = True
            return False
    
    async def _create_and_connect(self) -> bool:
        """创建客户端并建立持久连接"""
        try:
            # 根据URL选择传输类型
            if "/sse" in self.mcp_server_url:
                logger.info("检测到SSE端点，使用SSETransport")
                transport = SSETransport(url=self.mcp_server_url)
                self.fastmcp_client = Client(transport)
            else:
                logger.info("尝试直接使用URL，让FastMCP自动推断传输类型")
                self.fastmcp_client = Client(self.mcp_server_url)
            
            # 建立持久连接
            self._client_context = self.fastmcp_client
            self._client_session = await self._client_context.__aenter__()
            
            # 测试连接
            await self.fastmcp_client.ping()
            logger.info("✅ FastMCP连接成功")
            self.connected = True
            return True
                
        except Exception as e:
            logger.error(f"FastMCP连接失败: {e}")
            self.connected = False
            # 清理失败的连接
            if self._client_context and self._client_session:
                try:
                    await self._client_context.__aexit__(None, None, None)
                except:
                    pass
            self._client_context = None
            self._client_session = None
            return False
    
    async def _discover_mcp_tools(self) -> bool:
        """发现MCP服务器上的工具"""
        try:
            if not self.fastmcp_client or not self.connected:
                return False
            
            # 使用已建立的连接
            tools = await self.fastmcp_client.list_tools()
            logger.info(f"发现{len(tools)}个MCP工具")
            
            self.mcp_tools = tools
            
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                if tool.inputSchema:
                    logger.debug(f"    参数模式: {tool.inputSchema}")
            
            return len(tools) > 0
                
        except Exception as e:
            logger.error(f"MCP工具发现失败: {e}")
            return False
    
    async def _create_langchain_tools(self) -> List[BaseTool]:
        """将MCP工具转换为LangChain工具"""
        langchain_tools = []
        
        for mcp_tool in self.mcp_tools:
            try:
                # 动态创建LangChain工具
                langchain_tool = await self._create_langchain_tool(mcp_tool)
                if langchain_tool:
                    langchain_tools.append(langchain_tool)
            except Exception as e:
                logger.error(f"创建LangChain工具失败 {mcp_tool.name}: {e}")
                continue
        
        logger.info(f"成功创建{len(langchain_tools)}个LangChain工具")
        return langchain_tools
    
    async def _create_langchain_tool(self, mcp_tool: mcp_types.Tool) -> Optional[BaseTool]:
        """将单个MCP工具转换为LangChain工具"""
        try:
            tool_name = mcp_tool.name
            tool_description = mcp_tool.description or f"MCP工具: {tool_name}"
            
            # 从输入模式中提取参数信息
            parameters = {}
            if mcp_tool.inputSchema:
                schema = mcp_tool.inputSchema
                if isinstance(schema, dict):
                    properties = schema.get("properties", {})
                    for param_name, param_info in properties.items():
                        if isinstance(param_info, dict):
                            param_type = param_info.get("type", "string")
                            parameters[param_name] = param_type
            
            @tool(description=tool_description)
            async def dynamic_mcp_tool(**kwargs) -> Dict[str, Any]:
                """动态MCP工具调用"""
                return await self._call_mcp_tool(tool_name, kwargs)
            
            # 手动设置工具名称
            dynamic_mcp_tool.name = tool_name
            
            return dynamic_mcp_tool
            
        except Exception as e:
            logger.error(f"创建LangChain工具失败: {e}")
            return None
    
    async def _call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具 - 使用持久连接"""
        try:
            if not self.fastmcp_client or not self.connected or not self._client_session:
                return {
                    "success": False,
                    "error": "FastMCP客户端未连接",
                    "tool": tool_name,
                    "params": params
                }
            
            logger.info(f"调用FastMCP工具: {tool_name} with params: {params}")
            
            # 使用已建立的持久连接
            result = await self.fastmcp_client.call_tool(
                tool_name, 
                params
            )
            
            # 处理结果 - 检查是否返回列表
            if isinstance(result, list):
                # 处理列表响应 - 这似乎是当前FastMCP的实际行为
                logger.info(f"MCP工具调用成功 (列表响应): {tool_name}")
                
                response_data = {
                    "success": True,
                    "tool": tool_name,
                    "params": params,
                    "method": "fastmcp",
                    "server": self.mcp_server_url
                }
                
                # 从列表中提取内容
                text_content = []
                for item in result:
                    if hasattr(item, 'text'):
                        text_content.append(item.text)
                    elif hasattr(item, 'type') and item.type == 'text':
                        text_content.append(item.text)
                
                response_data["data"] = "\n".join(text_content)
                response_data["note"] = "从FastMCP列表响应中提取的文本数据"
                
                return response_data
                
            # 处理对象响应 - 按照文档应该是这样，但保留以防API更新
            elif hasattr(result, 'is_error'):
                if result.is_error:
                    logger.error(f"MCP工具调用失败: {tool_name}")
                    return {
                        "success": False,
                        "error": f"工具执行失败: {result.content[0].text if result.content else 'Unknown error'}",
                        "tool": tool_name,
                        "params": params,
                        "method": "fastmcp"
                    }
                else:
                    logger.info(f"MCP工具调用成功 (对象响应): {tool_name}")
                    
                    # FastMCP提供多种结果访问方式
                    response_data = {
                        "success": True,
                        "tool": tool_name,
                        "params": params,
                        "method": "fastmcp",
                        "server": self.mcp_server_url
                    }
                    
                    # 优先使用结构化数据
                    if result.data is not None:
                        response_data["data"] = result.data
                        response_data["note"] = "使用FastMCP .data属性获取的结构化数据"
                    elif result.structured_content:
                        response_data["data"] = result.structured_content
                        response_data["note"] = "使用FastMCP .structured_content获取的JSON数据"
                    else:
                        # 回退到文本内容
                        text_content = []
                        for content in result.content:
                            if hasattr(content, 'text'):
                                text_content.append(content.text)
                        response_data["data"] = "\n".join(text_content)
                        response_data["note"] = "使用FastMCP .content获取的文本数据"
                    
                    return response_data
            else:
                # 未知响应类型
                logger.warning(f"MCP工具返回未知类型: {type(result)}")
                return {
                    "success": True,
                    "tool": tool_name,
                    "params": params,
                    "method": "fastmcp",
                    "server": self.mcp_server_url,
                    "data": str(result),
                    "note": f"未知响应类型: {type(result)}"
                }
                
        except Exception as tool_error:
            # 处理特定的工具错误
            if "ToolError" in str(type(tool_error).__name__):
                logger.error(f"FastMCP工具调用异常: {tool_error}")
                return {
                    "success": False,
                    "error": f"FastMCP工具调用异常: {str(tool_error)}",
                    "tool": tool_name,
                    "params": params,
                    "method": "fastmcp"
                }
            else:
                # 对于其他异常，记录并返回错误
                logger.error(f"FastMCP工具调用失败: {tool_error}")
                return {
                    "success": False,
                    "error": str(tool_error),
                    "tool": tool_name,
                    "params": params,
                    "method": "fastmcp"
                }
    
    async def cleanup(self):
        """清理资源和关闭连接"""
        if self._client_context and self._client_session:
            try:
                await self._client_context.__aexit__(None, None, None)
                logger.info("FastMCP连接已关闭")
            except Exception as e:
                logger.error(f"关闭FastMCP连接时出错: {e}")
            finally:
                self._client_context = None
                self._client_session = None
                self.connected = False
    
    async def get_tools(self) -> List[BaseTool]:
        """获取工具列表"""
        if not self.initialized:
            await self.initialize()
        return self.tools
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "provider": "FastMCP",
            "connected": self.connected,
            "server_url": self.mcp_server_url,
            "tools_count": len(self.mcp_tools),
            "fastmcp_available": FASTMCP_AVAILABLE,
            "tools": [tool.name for tool in self.mcp_tools] if self.mcp_tools else []
        }
    
    def __del__(self):
        """析构函数 - 确保连接被关闭"""
        if self._client_context and self._client_session:
            # 在析构函数中不能使用async，记录警告
            import warnings
            warnings.warn(
                "FastMCPProvider was not properly cleaned up. "
                "Please call await provider.cleanup() before deletion.",
                ResourceWarning
            )


# 便捷函数
async def create_fastmcp_provider() -> FastMCPProvider:
    """创建并初始化FastMCP提供者"""
    provider = FastMCPProvider()
    await provider.initialize()
    return provider


async def test_fastmcp_connection() -> Dict[str, Any]:
    """测试FastMCP连接"""
    provider = FastMCPProvider()
    await provider.initialize()
    status = await provider.get_connection_status()
    await provider.cleanup()  # 确保测试后清理
    return status