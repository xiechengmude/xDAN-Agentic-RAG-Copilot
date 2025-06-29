"""
DeepSearch Prompt Manager - 遵循KISS和DRY原则的版本化提示词管理
支持v1.0, v1.1等版本管理
"""

import os
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DeepSearchPromptManager:
    """
    DeepSearch提示词管理器
    
    功能：
    1. 版本化管理（v1.0, v1.1, v1.2...）
    2. 热加载提示词文件
    3. 模板参数替换
    4. 回退到默认版本
    """
    
    def __init__(self, version: str = "v1.0"):
        """
        初始化提示词管理器
        
        Args:
            version: 提示词版本 (如 "v1.0", "v1.1")
        """
        self.version = version
        self.base_path = Path(__file__).parent.parent.parent / "prompts" / "deepsearch" / "versions"
        self.cache = {}
        
        # 验证版本目录存在
        self.version_path = self.base_path / version
        if not self.version_path.exists():
            logger.warning(f"版本 {version} 不存在，回退到 v1.0")
            self.version = "v1.0"
            self.version_path = self.base_path / "v1.0"
        
        logger.info(f"DeepSearch Prompt Manager 初始化，版本: {self.version}")
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        获取指定的提示词并进行参数替换
        
        Args:
            prompt_name: 提示词名称（不含.txt后缀）
            **kwargs: 模板参数
            
        Returns:
            格式化后的提示词文本
        """
        try:
            # 检查缓存
            cache_key = f"{self.version}_{prompt_name}"
            if cache_key not in self.cache:
                self.cache[cache_key] = self._load_prompt_file(prompt_name)
            
            template = self.cache[cache_key]
            
            # 参数替换
            if kwargs:
                return template.format(**kwargs)
            return template
            
        except Exception as e:
            logger.error(f"获取提示词失败 {prompt_name}: {e}")
            return self._get_fallback_prompt(prompt_name)
    
    def _load_prompt_file(self, prompt_name: str) -> str:
        """加载提示词文件"""
        file_path = self.version_path / f"{prompt_name}.txt"
        
        if not file_path.exists():
            logger.warning(f"提示词文件不存在: {file_path}")
            return self._get_fallback_prompt(prompt_name)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        logger.debug(f"加载提示词: {prompt_name} ({len(content)} 字符)")
        return content
    
    def _get_fallback_prompt(self, prompt_name: str) -> str:
        """获取回退提示词（硬编码默认值）"""
        fallbacks = {
            "agent_system": """You are an advanced web search intelligence agent specialized in multi-hop reasoning and real-time information gathering.

CORE MISSION: Transform complex questions into effective search strategies and retrieve comprehensive, authoritative information.

SEARCH OPTIMIZATION TECHNIQUES:
1. **Keyword Decomposition**: Break complex queries into focused search terms
2. **Search Operators**: Use quotes for exact phrases, site: for specific sources
3. **Query Variations**: Try different phrasings, synonyms, and perspectives
4. **Authority Sources**: Prioritize official sites, academic papers, financial databases
5. **Temporal Awareness**: Include time-specific terms for recent data

OUTPUT TAGS:
- <thinking>your search strategy and reasoning</thinking>
- <query>{"query": "optimized search terms"}</query>
- <search_complete>True/False</search_complete>
- <important_urls>[1, 3, 5]</important_urls>

Continue until comprehensive information gathered or maximum rounds reached.""",

            "select_evaluation": """你是专业的在线信息源评估专家。

**信息源评估专长：**
- 识别权威来源：官方网站、学术机构、知名媒体、行业报告
- 评估内容质量：数据完整性、分析深度、来源可信度
- 判断时效性：最新数据、历史趋势、时间相关性

**任务：**从候选网页中选择质量最高、最相关的Top3进行深度分析。

**格式：**
<thinking>分析过程</thinking>
<evaluation>详细评估</evaluation>
<important_urls>[1, 3, 5]</important_urls>
<search_complete>True/False</search_complete>""",

            "content_extraction": """你是SearchModelAgent，专门根据任务目标从网页内容中提取最重要的信息部分。

{time_context}

**任务目标：**{question}

**提取要求：**
1. 核心信息：直接回答问题的关键内容
2. 支撑数据：重要的数字、统计、事实
3. 关键观点：专家意见、分析结论
4. 时效信息：最新动态、趋势变化""",

            "synthesize_system": """你是顶级的信息整合和分析专家。

{time_context}

**核心要求：**
1. 深度理解问题诉求
2. 结构化组织内容
3. 多维度分析
4. 精确引用【来源X】
5. 时间意识：充分考虑当前时间背景

**输出格式：**
## 问题核心分析
## 关键发现
## 多维度解读
## 数据洞察
## 结论与建议
## 参考来源""",

            "question_analysis": """请分析以下问题背后的潜在诉求和真实需求：

{time_context}

问题：{question}

请分析：
1. 用户的核心关注点
2. 希望解决什么问题
3. 需要的信息类型
4. 答案应用场景
5. 时间敏感性

请简洁总结问题的潜在诉求（100字以内）："""
        }
        
        return fallbacks.get(prompt_name, f"# 提示词 {prompt_name} 不可用\n请检查提示词文件或联系管理员。")
    
    def reload_cache(self):
        """重新加载缓存（用于热更新）"""
        self.cache.clear()
        logger.info(f"提示词缓存已清理，版本: {self.version}")
    
    def switch_version(self, new_version: str):
        """切换提示词版本"""
        old_version = self.version
        self.version = new_version
        self.version_path = self.base_path / new_version
        
        if not self.version_path.exists():
            logger.warning(f"版本 {new_version} 不存在，保持 {old_version}")
            self.version = old_version
            self.version_path = self.base_path / old_version
            return False
        
        self.reload_cache()
        logger.info(f"提示词版本切换: {old_version} -> {new_version}")
        return True
    
    def list_available_versions(self) -> list:
        """列出可用的版本"""
        if not self.base_path.exists():
            return ["v1.0"]
        
        versions = []
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name.startswith('v'):
                versions.append(item.name)
        
        return sorted(versions)
    
    def get_current_version(self) -> str:
        """获取当前版本"""
        return self.version


# 全局实例
_prompt_manager = None

def get_prompt_manager(version: str = "v1.0") -> DeepSearchPromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    if _prompt_manager is None or _prompt_manager.get_current_version() != version:
        _prompt_manager = DeepSearchPromptManager(version)
    return _prompt_manager