"""
基础智能体类 - 所有智能体的基类
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid

from .message import Message, MessageType


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, name: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # 消息队列
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.outbox: asyncio.Queue = asyncio.Queue()
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # 状态
        self.is_running = False
        self.state: Dict[str, Any] = {}
        self.created_at = datetime.now()
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.register_handler(MessageType.STATUS, self._handle_status_request)
        self.register_handler(MessageType.ERROR, self._handle_error)
    
    async def _handle_status_request(self, message: Message):
        """处理状态请求"""
        status = {
            "id": self.id,
            "name": self.name,
            "is_running": self.is_running,
            "state": self.state,
            "inbox_size": self.inbox.qsize(),
            "created_at": self.created_at.isoformat()
        }
        
        response = message.create_response(
            content=status,
            type=MessageType.STATUS
        )
        await self.send(response)
    
    async def _handle_error(self, message: Message):
        """处理错误消息"""
        self.logger.error(f"Received error: {message.content}")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    async def send(self, message: Message):
        """发送消息"""
        await self.outbox.put(message)
        self.logger.debug(f"Sent {message.type.value} to {message.receiver}")
    
    async def receive(self) -> Message:
        """接收消息"""
        message = await self.inbox.get()
        self.logger.debug(f"Received {message.type.value} from {message.sender}")
        return message
    
    async def process_message(self, message: Message):
        """处理消息"""
        handlers = self.message_handlers.get(message.type, [])
        
        if not handlers:
            self.logger.warning(f"No handler for message type: {message.type.value}")
            return
        
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error in handler: {e}")
                # 发送错误响应
                if message.type == MessageType.REQUEST:
                    error_response = message.create_response(
                        content={"error": str(e)},
                        type=MessageType.ERROR
                    )
                    await self.send(error_response)
    
    async def start(self):
        """启动智能体"""
        self.is_running = True
        self.logger.info(f"Agent {self.name} started")
        
        # 启动消息处理循环
        asyncio.create_task(self._message_loop())
        
        # 调用子类的启动方法
        await self.on_start()
    
    async def stop(self):
        """停止智能体"""
        self.is_running = False
        
        # 调用子类的停止方法
        await self.on_stop()
        
        self.logger.info(f"Agent {self.name} stopped")
    
    async def _message_loop(self):
        """消息处理循环"""
        while self.is_running:
            try:
                # 使用超时避免永久阻塞
                message = await asyncio.wait_for(self.inbox.get(), timeout=1.0)
                await self.process_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
    
    @abstractmethod
    async def on_start(self):
        """启动时的钩子方法"""
        pass
    
    @abstractmethod
    async def on_stop(self):
        """停止时的钩子方法"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取智能体信息"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_running": self.is_running,
            "state": self.state,
            "created_at": self.created_at.isoformat()
        }