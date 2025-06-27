"""
Langfuse追踪配置 - 支持S3-RAG-Chat和S3-DeepSearch两种模式
在Langfuse UI中可以直接看到清晰的层级关系
"""

from typing import Dict, Any, Optional, List
from enum import Enum

class S3Mode(Enum):
    """S3框架的两种模式"""
    RAG_CHAT = "s3-rag-chat"          # 普通RAG对话模式
    DEEPSEARCH = "s3-deepsearch"      # 深度搜索模式

class LangfuseTraceConfig:
    """Langfuse追踪配置 - 为不同模式优化展示"""
    
    # 模式配置
    MODE_CONFIG = {
        S3Mode.RAG_CHAT: {
            "emoji": "💬",
            "name": "RAG对话",
            "trace_prefix": "rag_chat",
            "max_iterations": 3,
            "tags": ["rag-chat", "conversational"]
        },
        S3Mode.DEEPSEARCH: {
            "emoji": "🔬",
            "name": "深度搜索",
            "trace_prefix": "deepsearch",
            "max_iterations": 5,
            "tags": ["deep-search", "research"]
        }
    }
    
    # 阶段配置 - 在Langfuse中展示的层级
    PHASE_CONFIG = {
        "search": {
            "emoji": "🔍",
            "name": "搜索阶段",
            "sub_phases": {
                "ragflow": "📚 RAGFlow知识库搜索",
                "brightdata": "🌐 BrightData网络搜索",
                "firecrawl": "🕷️ FireCrawl网页爬取"
            }
        },
        "select": {
            "emoji": "🤔",
            "name": "筛选阶段",
            "sub_phases": {
                "agent_analysis": "🧠 智能体分析",
                "relevance_check": "✅ 相关性检查",
                "dedup": "🔄 去重处理"
            }
        },
        "synthesize": {
            "emoji": "✍️",
            "name": "合成阶段",
            "sub_phases": {
                "generation": "📝 答案生成",
                "streaming": "📡 流式输出",
                "formatting": "🎨 格式化处理"
            }
        }
    }
    
    @staticmethod
    def create_trace_metadata(
        mode: S3Mode,
        session_id: str,
        question: str,
        dataset_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建Trace级别的元数据
        这些信息会在Langfuse的Trace列表中显示
        """
        mode_config = LangfuseTraceConfig.MODE_CONFIG[mode]
        
        # Trace名称 - 在列表中一目了然
        trace_name = f"{mode_config['emoji']} {mode_config['name']}: {question[:50]}..."
        
        return {
            "trace_name": trace_name,
            "session_id": session_id,
            "trace_user_id": user_id,
            "tags": [
                "s3-framework",
                mode.value,  # s3-rag-chat 或 s3-deepsearch
                *mode_config['tags']
            ],
            "trace_metadata": {
                "mode": mode.value,
                "question": question,
                "dataset_ids": dataset_ids or [],
                "config": {
                    "max_iterations": mode_config['max_iterations'],
                    **kwargs
                }
            }
        }
    
    @staticmethod
    def create_generation_metadata(
        trace_id: str,
        mode: S3Mode,
        phase: str,
        sub_phase: str,
        parent_observation_id: Optional[str] = None,
        iteration: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建Generation级别的元数据
        在Langfuse中会显示为Trace下的子节点
        """
        phase_config = LangfuseTraceConfig.PHASE_CONFIG.get(phase, {})
        phase_emoji = phase_config.get("emoji", "📌")
        sub_phase_name = phase_config.get("sub_phases", {}).get(sub_phase, sub_phase)
        
        # Generation名称 - 在层级中清晰展示
        if iteration:
            generation_name = f"{phase_emoji} {sub_phase_name} - 迭代{iteration}"
        else:
            generation_name = f"{phase_emoji} {sub_phase_name}"
        
        return {
            "trace_id": trace_id,
            "parent_observation_id": parent_observation_id,
            "generation_name": generation_name,
            "tags": [
                f"phase:{phase}",
                f"sub_phase:{sub_phase}",
                f"mode:{mode.value}"
            ],
            "metadata": {
                "phase": phase,
                "sub_phase": sub_phase,
                "iteration": iteration,
                **kwargs
            }
        }
    
    @staticmethod
    def create_observation_metadata(
        trace_id: str,
        observation_type: str,
        observation_name: str,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建Observation级别的元数据
        用于非LLM调用的追踪（如数据库查询、API调用等）
        """
        return {
            "trace_id": trace_id,
            "parent_observation_id": parent_id,
            "name": observation_name,
            "type": observation_type,  # "span" or "event"
            "metadata": kwargs
        }


# Langfuse中的展示效果示例：
"""
在Langfuse UI中会看到如下层级结构：

1. S3-RAG-Chat模式:
└── 💬 RAG对话: 什么是机器学习...
    ├── 🔍 📚 RAGFlow知识库搜索 - 迭代1
    ├── 🔍 📚 RAGFlow知识库搜索 - 迭代2
    ├── 🤔 🧠 智能体分析
    ├── 🤔 ✅ 相关性检查
    └── ✍️ 📝 答案生成

2. S3-DeepSearch模式:
└── 🔬 深度搜索: 最新的AI发展趋势...
    ├── 🔍 📚 RAGFlow知识库搜索 - 迭代1
    ├── 🔍 🌐 BrightData网络搜索
    ├── 🔍 🕷️ FireCrawl网页爬取
    ├── 🤔 🧠 智能体分析
    ├── 🤔 🔄 去重处理
    ├── 🔍 📚 RAGFlow知识库搜索 - 迭代2（基于新信息）
    └── ✍️ 📝 答案生成

过滤器使用:
- 查看所有RAG对话: tags:s3-rag-chat
- 查看所有深度搜索: tags:s3-deepsearch
- 查看搜索阶段: tags:phase:search
- 查看特定用户: trace_user_id:user-123
"""