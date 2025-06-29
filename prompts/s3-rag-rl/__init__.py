"""
S3-RAG-RL Prompt Manager
管理S3框架(Search-Select-Synthesize)工作流中的所有prompt模板
"""

import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class S3PromptManager:
    """S3框架prompt模板管理器"""
    
    def __init__(self, version: str = "v3"):
        """
        初始化prompt管理器
        
        Args:
            version: prompt版本 (original, v1, v2, v3)
        """
        self.prompt_dir = os.path.dirname(__file__)
        self.version = version
        self._prompts = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """加载所有prompt模板（新的文件夹结构）"""
        # 使用新的版本文件夹结构
        version_dir = os.path.join(self.prompt_dir, "versions", self.version)
        
        prompt_files = {
            'agent_system': 'agent_system.txt',
            'generation_system': 'generation_system.txt', 
            'generation_user': 'generation_user.txt',
            'search_phase_user': 'search_phase_user.txt',
            'initial_search_user': 'initial_search_user.txt'
        }
        
        # 如果版本文件夹不存在，回退到original版本
        if not os.path.exists(version_dir) and self.version != "original":
            logger.warning(f"Version {self.version} folder not found, falling back to original")
            version_dir = os.path.join(self.prompt_dir, "versions", "original")
        
        for key, filename in prompt_files.items():
            file_path = os.path.join(version_dir, filename)
            
            # 如果文件不存在，尝试从original版本加载
            if not os.path.exists(file_path):
                original_path = os.path.join(self.prompt_dir, "versions", "original", filename)
                if os.path.exists(original_path):
                    file_path = original_path
                    logger.warning(f"Version {self.version} not found for {key}, using original version")
                else:
                    logger.error(f"Prompt file not found: {filename} in any version")
                    self._prompts[key] = ""
                    continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prompts[key] = f.read().strip()
                logger.debug(f"Loaded S3 prompt: {key} (version: {self.version})")
            except Exception as e:
                logger.error(f"Failed to load S3 prompt {key} from {file_path}: {e}")
                self._prompts[key] = ""
    
    def get_agent_system_prompt(self) -> str:
        """获取S3智能体系统提示词"""
        return self._prompts.get('agent_system', '')
    
    def get_generation_system_prompt(self) -> str:
        """获取生成系统提示词"""
        return self._prompts.get('generation_system', '')
    
    def get_generation_user_prompt(self, context: str, question: str) -> str:
        """获取生成用户提示词"""
        template = self._prompts.get('generation_user', '')
        return template.format(
            context=context,
            question=question
        )
    
    def get_search_phase_user_prompt(self, question: str, formatted_info: str, 
                                     round_num: int = 1, max_rounds: int = 5) -> str:
        """获取搜索阶段用户提示词"""
        template = self._prompts.get('search_phase_user', '')
        return template.format(
            question=question,
            formatted_info=formatted_info,
            round_num=round_num,
            max_rounds=max_rounds
        )
    
    def get_initial_search_user_prompt(self, question: str, formatted_info: str) -> str:
        """获取初始搜索用户提示词"""
        template = self._prompts.get('initial_search_user', '')
        return template.format(
            question=question,
            formatted_info=formatted_info
        )

# 全局实例 - 默认使用v3.1版本
s3_prompt_manager = S3PromptManager(version="v3.1")