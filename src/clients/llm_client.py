#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 客户端，用于连接外部生成模型服务
"""

import requests
import json
from typing import List, Dict, Any, Optional, Iterator
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM 客户端，支持 OpenAI 兼容的 API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化 LLM 客户端
        
        Args:
            base_url: LLM 服务的基础 URL
            api_key: API 密钥（可选）
            model_name: 模型名称
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name if model_name else "default-model"
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RAGFlow-Client/1.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称（可选，默认使用初始化时的模型）
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式返回
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model or self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            **kwargs
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            if stream:
                return self._stream_request(url, payload)
            else:
                response = self.session.post(url, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            raise Exception(f"LLM API 请求失败: {e}")
    
    def _stream_request(self, url: str, payload: Dict[str, Any]) -> Iterator[str]:
        """
        处理流式请求
        
        Args:
            url: 请求 URL
            payload: 请求负载
            
        Yields:
            流式响应数据
        """
        try:
            response = self.session.post(
                url, 
                json=payload, 
                stream=True, 
                timeout=60
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # 移除 'data: ' 前缀
                        if data.strip() == '[DONE]':
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"流式请求失败: {e}")
            raise Exception(f"流式请求失败: {e}")
    
    def generate_answer(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        基于问题和上下文生成答案
        
        Args:
            question: 问题
            context: 上下文信息
            system_prompt: 系统提示（可选）
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            生成的答案
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system", 
                "content": "你是一个专业的问答助手。请根据提供的上下文信息准确回答用户的问题。如果上下文中没有相关信息，请诚实地说明。"
            })
        
        # 构建用户消息
        user_message = f"上下文信息：\n{context}\n\n问题：{question}\n\n请根据上下文信息回答问题："
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.get("choices") and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"].strip()
            else:
                raise Exception("未获得有效的生成响应")
                
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            raise Exception(f"生成答案失败: {e}")
    
    def evaluate_answer_quality(
        self,
        question: str,
        answer: str,
        gold_answer: str
    ) -> float:
        """
        评估答案质量（用于计算 Gain Beyond RAG 奖励）
        
        Args:
            question: 问题
            answer: 生成的答案
            gold_answer: 标准答案
            
        Returns:
            质量分数 (0-1)
        """
        evaluation_prompt = f"""
请评估以下答案的质量：

问题：{question}
生成的答案：{answer}
标准答案：{gold_answer}

请从以下几个方面评估生成答案的质量：
1. 准确性：答案是否正确
2. 完整性：答案是否完整
3. 相关性：答案是否与问题相关

请给出一个0-1之间的分数，其中1表示完美答案，0表示完全错误。
只返回数字分数，不要其他解释。
"""
        
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的答案质量评估专家。"},
                {"role": "user", "content": evaluation_prompt}
            ]
            
            response = self.chat_completion(
                messages=messages,
                temperature=0.1,  # 使用较低的温度以获得更一致的评估
                max_tokens=10
            )
            
            if response.get("choices") and len(response["choices"]) > 0:
                score_text = response["choices"][0]["message"]["content"].strip()
                try:
                    score = float(score_text)
                    return max(0.0, min(1.0, score))  # 确保分数在 0-1 范围内
                except ValueError:
                    logger.warning(f"无法解析评估分数: {score_text}")
                    return 0.5  # 默认分数
            else:
                return 0.5  # 默认分数
                
        except Exception as e:
            logger.error(f"评估答案质量失败: {e}")
            return 0.5  # 默认分数
    
    def health_check(self) -> bool:
        """
        检查 LLM 服务健康状态
        
        Returns:
            服务是否健康
        """
        try:
            # 发送一个简单的测试请求
            test_messages = [
                {"role": "user", "content": "Hello, are you working?"}
            ]
            
            response = self.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.1
            )
            
            return response.get("choices") is not None
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
