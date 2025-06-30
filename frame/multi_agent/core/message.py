"""
消息定义 - 智能体之间的通信协议
"""

from enum import Enum
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"          # 请求
    RESPONSE = "response"        # 响应
    NOTIFICATION = "notification" # 通知
    ERROR = "error"              # 错误
    COMMAND = "command"          # 命令
    QUERY = "query"              # 查询
    RESULT = "result"            # 结果
    TASK = "task"                # 任务分配
    STATUS = "status"            # 状态更新


class Message:
    """智能体间的消息"""
    
    def __init__(
        self,
        type: MessageType,
        content: Any,
        sender: str,
        receiver: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.type = type
        self.content = content
        self.sender = sender
        self.receiver = receiver  # None表示广播
        self.metadata = metadata or {}
        self.correlation_id = correlation_id  # 用于关联请求和响应
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "sender": self.sender,
            "receiver": self.receiver,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        msg = cls(
            type=MessageType(data["type"]),
            content=data["content"],
            sender=data["sender"],
            receiver=data.get("receiver"),
            metadata=data.get("metadata", {}),
            correlation_id=data.get("correlation_id")
        )
        msg.id = data["id"]
        msg.timestamp = datetime.fromisoformat(data["timestamp"])
        return msg
    
    def create_response(self, content: Any, type: MessageType = MessageType.RESPONSE) -> "Message":
        """创建响应消息"""
        return Message(
            type=type,
            content=content,
            sender=self.receiver,
            receiver=self.sender,
            correlation_id=self.id
        )


class TaskMessage(Message):
    """任务消息 - 特殊的消息类型"""
    
    def __init__(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        sender: str,
        receiver: str,
        priority: int = 5,
        timeout: Optional[int] = None
    ):
        content = {
            "task_type": task_type,
            "task_data": task_data,
            "priority": priority,
            "timeout": timeout
        }
        super().__init__(
            type=MessageType.TASK,
            content=content,
            sender=sender,
            receiver=receiver,
            metadata={"priority": priority}
        )