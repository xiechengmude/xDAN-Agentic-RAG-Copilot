"""
Multi-Agent Framework for DeepSearch
纯后端多智能体架构，无需API服务器
"""

__version__ = "1.0.0"

from .core.base_agent import BaseAgent
from .core.agent_manager import AgentManager
from .core.message import Message, MessageType
from .agents.search_agent import SearchAgent
from .agents.analysis_agent import AnalysisAgent
from .agents.synthesis_agent import SynthesisAgent

__all__ = [
    "BaseAgent",
    "AgentManager", 
    "Message",
    "MessageType",
    "SearchAgent",
    "AnalysisAgent",
    "SynthesisAgent"
]