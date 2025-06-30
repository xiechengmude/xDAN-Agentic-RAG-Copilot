"""
智能体管理器 - 负责智能体的创建、管理和协调
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

from .base_agent import BaseAgent
from .message import Message, MessageType


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, name: str = "AgentManager"):
        self.name = name
        self.logger = logging.getLogger(f"Manager.{name}")
        
        # 智能体注册表
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, Type[BaseAgent]] = {}
        
        # 消息路由
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
        # 统计信息
        self.stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "start_time": None
        }
    
    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]):
        """注册智能体类型"""
        self.agent_types[name] = agent_class
        self.logger.info(f"Registered agent type: {name}")
    
    async def create_agent(self, agent_type: str, name: str, **kwargs) -> BaseAgent:
        """创建智能体实例"""
        if agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # 创建智能体
        agent_class = self.agent_types[agent_type]
        agent = agent_class(name=name, **kwargs)
        
        # 注册智能体
        self.agents[name] = agent
        
        # 启动智能体
        await agent.start()
        
        self.logger.info(f"Created agent: {name} (type: {agent_type})")
        return agent
    
    async def remove_agent(self, name: str):
        """移除智能体"""
        if name not in self.agents:
            return
        
        agent = self.agents[name]
        await agent.stop()
        del self.agents[name]
        
        self.logger.info(f"Removed agent: {name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        return [agent.get_info() for agent in self.agents.values()]
    
    async def send_message(self, message: Message):
        """发送消息到指定智能体"""
        if message.receiver:
            # 单播
            agent = self.agents.get(message.receiver)
            if agent:
                await agent.inbox.put(message)
                self.logger.debug(f"Delivered message to {message.receiver}")
            else:
                self.logger.warning(f"Agent not found: {message.receiver}")
        else:
            # 广播
            for agent in self.agents.values():
                if agent.name != message.sender:  # 不发送给自己
                    await agent.inbox.put(message)
            self.logger.debug(f"Broadcasted message from {message.sender}")
    
    async def start(self):
        """启动管理器"""
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        # 启动消息路由循环
        asyncio.create_task(self._message_router())
        
        # 启动智能体输出监控
        for agent in self.agents.values():
            asyncio.create_task(self._monitor_agent_output(agent))
        
        self.logger.info("Agent manager started")
    
    async def stop(self):
        """停止管理器"""
        self.is_running = False
        
        # 停止所有智能体
        for agent in list(self.agents.values()):
            await agent.stop()
        
        self.logger.info("Agent manager stopped")
    
    async def _message_router(self):
        """消息路由循环"""
        while self.is_running:
            try:
                # 处理全局消息队列
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.send_message(message)
                self.stats["messages_processed"] += 1
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in message router: {e}")
                self.stats["messages_failed"] += 1
    
    async def _monitor_agent_output(self, agent: BaseAgent):
        """监控智能体输出"""
        while self.is_running and agent.is_running:
            try:
                # 从智能体的输出队列获取消息
                message = await asyncio.wait_for(agent.outbox.get(), timeout=1.0)
                
                # 路由消息
                await self.send_message(message)
                
                self.stats["messages_processed"] += 1
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error monitoring agent {agent.name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            "agents_count": len(self.agents),
            "messages_processed": self.stats["messages_processed"],
            "messages_failed": self.stats["messages_failed"],
            "uptime_seconds": uptime,
            "is_running": self.is_running
        }


class AgentOrchestrator(AgentManager):
    """高级智能体编排器 - 支持工作流编排"""
    
    def __init__(self, name: str = "Orchestrator"):
        super().__init__(name)
        self.workflows: Dict[str, Dict[str, Any]] = {}
    
    def register_workflow(self, name: str, workflow: Dict[str, Any]):
        """注册工作流"""
        self.workflows[name] = workflow
        self.logger.info(f"Registered workflow: {name}")
    
    async def execute_workflow(self, workflow_name: str, initial_data: Any) -> Any:
        """执行工作流"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        steps = workflow.get("steps", [])
        
        result = initial_data
        
        for step in steps:
            agent_name = step["agent"]
            task_type = step["task"]
            
            # 创建任务消息
            task_message = Message(
                type=MessageType.TASK,
                content={
                    "task_type": task_type,
                    "data": result
                },
                sender=self.name,
                receiver=agent_name
            )
            
            # 发送任务
            await self.send_message(task_message)
            
            # 等待响应
            response = await self._wait_for_response(task_message.id, timeout=step.get("timeout", 60))
            
            if response and response.type != MessageType.ERROR:
                result = response.content
            else:
                raise Exception(f"Workflow step failed: {step}")
        
        return result
    
    async def _wait_for_response(self, correlation_id: str, timeout: int = 60) -> Optional[Message]:
        """等待响应消息"""
        # 这里需要实现响应等待逻辑
        # 简化版本，实际应该监听特定的响应消息
        await asyncio.sleep(1)
        return None