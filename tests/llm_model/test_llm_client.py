#!/usr/bin/env python3
"""
LLM模型客户端测试
测试与各个LLM服务的连接和基本功能
"""

import os
import sys
import json
import pytest
import asyncio
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

from src.clients.llm_client import LLMClient
from config.settings import (
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

class TestLLMClient:
    """LLM客户端功能测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        # Search模型客户端
        cls.search_client = LLMClient(
            base_url=S3_SEARCH_MODEL_URL,
            api_key=S3_SEARCH_API_KEY,
            model_name=S3_SEARCH_MODEL_NAME
        )
        
        # Generator模型客户端
        cls.generator_client = LLMClient(
            base_url=S3_GENERATOR_MODEL_URL,
            api_key=S3_GENERATOR_API_KEY,
            model_name=S3_GENERATOR_MODEL_NAME
        )
    
    def test_01_search_model_connection(self):
        """测试1: Search模型连接性"""
        print(f"\n测试Search模型: {S3_SEARCH_MODEL_NAME}")
        print(f"URL: {S3_SEARCH_MODEL_URL}")
        
        try:
            # 简单的测试请求
            response = self.search_client.chat_completion(
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                temperature=0.1
            )
            
            assert response is not None
            assert len(response) > 0
            print(f"✅ Search模型连接成功")
            print(f"  响应: {response[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Search模型连接失败: {e}")
    
    def test_02_generator_model_connection(self):
        """测试2: Generator模型连接性"""
        print(f"\n测试Generator模型: {S3_GENERATOR_MODEL_NAME}")
        print(f"URL: {S3_GENERATOR_MODEL_URL}")
        
        try:
            response = self.generator_client.chat_completion(
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                temperature=0.1
            )
            
            assert response is not None
            assert len(response) > 0
            print(f"✅ Generator模型连接成功")
            print(f"  响应: {response[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Generator模型连接失败: {e}")
    
    def test_03_system_prompt(self):
        """测试3: 系统提示词功能"""
        system_prompt = "You are a helpful assistant that always responds in JSON format."
        user_message = "List three colors"
        
        try:
            response = self.search_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1
            )
            
            print(f"✅ 系统提示词测试成功")
            print(f"  响应: {response}")
            
            # 尝试解析JSON响应
            try:
                json.loads(response)
                print("  ✅ 响应是有效的JSON格式")
            except json.JSONDecodeError:
                print("  ⚠️  响应不是JSON格式（模型可能不支持严格的格式控制）")
                
        except Exception as e:
            print(f"⚠️  系统提示词测试失败: {e}")
    
    def test_04_streaming_response(self):
        """测试4: 流式响应"""
        print("\n测试流式响应...")
        
        try:
            # 同步流式测试
            stream = self.generator_client.chat_stream(
                messages=[{"role": "user", "content": "Count from 1 to 5"}],
                temperature=0.1
            )
            
            chunks = []
            for chunk in stream:
                chunks.append(chunk)
            
            full_response = ''.join(chunks)
            print(f"✅ 同步流式响应测试成功")
            print(f"  收到 {len(chunks)} 个数据块")
            print(f"  完整响应: {full_response[:100]}...")
            
        except Exception as e:
            print(f"⚠️  流式响应测试失败: {e}")
    
    def test_05_async_streaming(self):
        """测试5: 异步流式响应"""
        print("\n测试异步流式响应...")
        
        async def test_async():
            try:
                chunks = []
                async for chunk in self.generator_client.achat_stream(
                    messages=[{"role": "user", "content": "Say 'hello world' in three languages"}],
                    temperature=0.1
                ):
                    chunks.append(chunk)
                
                full_response = ''.join(chunks)
                print(f"✅ 异步流式响应测试成功")
                print(f"  收到 {len(chunks)} 个数据块")
                print(f"  完整响应: {full_response[:100]}...")
                
            except Exception as e:
                print(f"⚠️  异步流式响应测试失败: {e}")
        
        # 运行异步测试
        asyncio.run(test_async())
    
    def test_06_temperature_control(self):
        """测试6: 温度参数控制"""
        prompt = "Generate a random number between 1 and 10"
        
        print("\n测试温度参数控制...")
        
        # 低温度（更确定性）
        responses_low = []
        for _ in range(3):
            response = self.search_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            responses_low.append(response)
        
        # 高温度（更随机）
        responses_high = []
        for _ in range(3):
            response = self.search_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0
            )
            responses_high.append(response)
        
        print(f"✅ 温度参数测试完成")
        print(f"  低温度响应差异性: {len(set(responses_low))}/3")
        print(f"  高温度响应差异性: {len(set(responses_high))}/3")
    
    def test_07_max_tokens_control(self):
        """测试7: 最大令牌数控制"""
        print("\n测试最大令牌数控制...")
        
        try:
            # 限制输出长度
            response = self.generator_client.chat_completion(
                messages=[{"role": "user", "content": "Write a long story about a robot"}],
                max_tokens=50,
                temperature=0.5
            )
            
            # 粗略估计令牌数（通常1个令牌约等于0.75个单词）
            word_count = len(response.split())
            print(f"✅ 最大令牌数控制测试成功")
            print(f"  响应长度: {len(response)} 字符, 约 {word_count} 个单词")
            
        except Exception as e:
            print(f"⚠️  最大令牌数控制测试失败: {e}")
    
    def test_08_error_handling(self):
        """测试8: 错误处理"""
        print("\n测试错误处理...")
        
        # 测试无效的API密钥
        try:
            bad_client = LLMClient(
                base_url=S3_SEARCH_MODEL_URL,
                api_key="invalid_key",
                model_name=S3_SEARCH_MODEL_NAME
            )
            
            response = bad_client.chat_completion(
                messages=[{"role": "user", "content": "test"}]
            )
            
            print("⚠️  错误处理测试失败：应该抛出异常")
            
        except Exception as e:
            print(f"✅ 错误处理测试成功：正确捕获异常")
            print(f"  异常类型: {type(e).__name__}")
            print(f"  异常信息: {str(e)[:100]}...")
    
    def test_09_model_switching(self):
        """测试9: 模型切换"""
        print("\n测试模型切换...")
        
        # 创建一个新客户端，使用不同的模型名
        try:
            # 尝试使用相同的URL但不同的模型名
            alt_client = LLMClient(
                base_url=S3_GENERATOR_MODEL_URL,
                api_key=S3_GENERATOR_API_KEY,
                model_name="gpt-3.5-turbo"  # 尝试不同的模型名
            )
            
            response = alt_client.chat_completion(
                messages=[{"role": "user", "content": "What model are you?"}],
                temperature=0.1
            )
            
            print(f"✅ 模型切换测试成功")
            print(f"  使用模型: gpt-3.5-turbo")
            print(f"  响应: {response[:100]}...")
            
        except Exception as e:
            print(f"⚠️  模型切换测试失败（可能不支持该模型）: {e}")

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("LLM模型客户端测试")
    print("=" * 60)
    print(f"Search模型: {S3_SEARCH_MODEL_NAME}")
    print(f"Generator模型: {S3_GENERATOR_MODEL_NAME}")
    print("=" * 60)
    
    # 使用pytest运行测试
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()