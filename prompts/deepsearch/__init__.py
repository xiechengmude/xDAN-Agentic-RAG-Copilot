"""
DeepSearch Prompt Manager
管理DeepSearch工作流中的所有prompt模板
"""

import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DeepSearchPromptManager:
    """DeepSearch prompt模板管理器"""
    
    def __init__(self):
        self.prompt_dir = os.path.dirname(__file__)
        self._prompts = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """加载所有prompt模板"""
        prompt_files = {
            'agent_system': 'agent_system.txt',
            'select_evaluation': 'select_evaluation.txt', 
            'content_extraction': 'content_extraction.txt',
            'synthesize_system': 'synthesize_system.txt',
            'synthesize_user': 'synthesize_user.txt',
            'question_analysis': 'question_analysis.txt'
        }
        
        for key, filename in prompt_files.items():
            file_path = os.path.join(self.prompt_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prompts[key] = f.read().strip()
                logger.debug(f"Loaded prompt: {key}")
            except Exception as e:
                logger.error(f"Failed to load prompt {key} from {file_path}: {e}")
                self._prompts[key] = ""
    
    def get_agent_system_prompt(self) -> str:
        """获取搜索智能体系统提示词"""
        return self._prompts.get('agent_system', '')
    
    def get_select_evaluation_prompt(self, question: str, previous_knowledge: str, 
                                   num_results: int, formatted_info: str) -> str:
        """获取网页评估选择提示词"""
        template = self._prompts.get('select_evaluation', '')
        return template.format(
            question=question,
            previous_knowledge=previous_knowledge or "（第一轮搜索，暂无已有知识）",
            num_results=num_results,
            formatted_info=formatted_info
        )
    
    def get_content_extraction_prompt(self, question: str, task_context: str,
                                    title: str, url: str, content: str) -> str:
        """获取内容提取提示词"""
        template = self._prompts.get('content_extraction', '')
        return template.format(
            question=question,
            task_context=task_context or "这是深度搜索任务，需要全面理解问题背景并提取关键信息",
            title=title,
            url=url,
            content=content[:10000]  # 限制长度避免token超限
        )
    
    def get_synthesize_system_prompt(self) -> str:
        """获取综合分析系统提示词"""
        return self._prompts.get('synthesize_system', '')
    
    def get_synthesize_user_prompt(self, question: str, question_analysis: str,
                                 citation_context: str) -> str:
        """获取综合分析用户提示词"""
        template = self._prompts.get('synthesize_user', '')
        return template.format(
            question=question,
            question_analysis=question_analysis,
            citation_context=citation_context
        )
    
    def get_question_analysis_prompt(self, question: str) -> str:
        """获取问题分析提示词"""
        template = self._prompts.get('question_analysis', '')
        return template.format(question=question)

# 全局实例
prompt_manager = DeepSearchPromptManager()