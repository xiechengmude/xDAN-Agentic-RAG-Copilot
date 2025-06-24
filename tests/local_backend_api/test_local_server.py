#!/usr/bin/env python3
"""
本地后端API服务测试
测试本地服务器的所有接口
"""

import os
import sys
import json
import requests
import pytest
import subprocess
import time
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

from src.utils.port_manager import PortManager, ensure_port_free

class TestLocalServer:
    """本地服务器API测试"""
    
    LOCAL_URL = "http://localhost:8050"
    server_process: Optional[subprocess.Popen] = None
    
    @classmethod
    def setup_class(cls):
        """启动本地服务器"""
        print("\n正在启动本地服务器...")
        
        # 确保端口可用
        if not ensure_port_free(8050, auto_kill=True):
            pytest.fail("无法释放端口8050")
        
        # 启动服务器
        server_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "xdan_rag_server.py"
        )
        
        cls.server_process = subprocess.Popen(
            ["uv", "run", "python", server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(server_script)
        )
        
        # 等待服务器启动
        max_wait = 30  # 最多等待30秒
        for i in range(max_wait):
            try:
                response = requests.get(f"{cls.LOCAL_URL}/api/health", timeout=1)
                if response.status_code == 200:
                    print("✅ 本地服务器启动成功")
                    break
            except:
                pass
            time.sleep(1)
        else:
            cls.teardown_class()
            pytest.fail("本地服务器启动超时")
    
    @classmethod
    def teardown_class(cls):
        """停止本地服务器"""
        if cls.server_process:
            print("\n正在停止本地服务器...")
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("✅ 本地服务器已停止")
    
    def test_01_home_page(self):
        """测试1: 主页访问"""
        response = requests.get(self.LOCAL_URL)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("✅ 主页访问成功")
    
    def test_02_health_check(self):
        """测试2: 健康检查接口"""
        response = requests.get(f"{self.LOCAL_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        print(f"✅ 健康检查: {data['status']}")
        print(f"  API连接: {data.get('api_connected', False)}")
    
    def test_03_api_docs(self):
        """测试3: API文档"""
        response = requests.get(f"{self.LOCAL_URL}/docs")
        assert response.status_code == 200
        print("✅ API文档页面可访问")
        
        # 获取OpenAPI规范
        response = requests.get(f"{self.LOCAL_URL}/openapi.json")
        assert response.status_code == 200
        
        openapi = response.json()
        assert "openapi" in openapi
        assert "paths" in openapi
        
        print(f"✅ OpenAPI规范获取成功")
        print(f"  版本: {openapi.get('openapi')}")
        print(f"  标题: {openapi.get('info', {}).get('title')}")
        print(f"  接口数量: {len(openapi.get('paths', {}))}")
    
    def test_04_s3_search_stream(self):
        """测试4: S3智能搜索流式接口"""
        print("\n测试S3智能搜索...")
        
        payload = {
            "question": "什么是RAGFlow？",
            "max_rounds": 2,
            "top_k": 5,
            "similarity_threshold": 0.3
        }
        
        response = requests.post(
            f"{self.LOCAL_URL}/api/search/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        events = []
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        try:
                            event = json.loads(data)
                            events.append(event)
                            print(f"  收到事件: {event.get('event_type')}")
                        except json.JSONDecodeError:
                            pass
        
        print(f"✅ S3搜索测试成功，收到 {len(events)} 个事件")
        
        # 验证必要的事件类型
        event_types = [e.get('event_type') for e in events]
        assert 'search_start' in event_types
    
    def test_05_chat_stream(self):
        """测试5: 对话流式接口"""
        print("\n测试对话功能...")
        
        # 第一次请求，创建新对话
        payload = {
            "question": "你好，介绍一下RAGFlow",
            "chat_id": None
        }
        
        response = requests.post(
            f"{self.LOCAL_URL}/api/chat/stream",
            json=payload,
            stream=True
        )
        
        assert response.status_code == 200
        
        chat_id = None
        events = []
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data:
                        try:
                            event = json.loads(data)
                            events.append(event)
                            
                            # 获取chat_id
                            if event.get('event_type') == 'chat_created':
                                chat_id = event.get('data', {}).get('chat_id')
                                print(f"  创建对话: {chat_id}")
                            elif event.get('event_type') == 'chat_response':
                                print(f"  收到回复")
                                
                        except json.JSONDecodeError:
                            pass
        
        print(f"✅ 对话测试成功，收到 {len(events)} 个事件")
        
        # 如果成功创建对话，测试继续对话
        if chat_id:
            print("\n测试继续对话...")
            
            payload = {
                "question": "RAGFlow有哪些主要功能？",
                "chat_id": chat_id
            }
            
            response = requests.post(
                f"{self.LOCAL_URL}/api/chat/stream",
                json=payload,
                stream=True
            )
            
            assert response.status_code == 200
            print("✅ 继续对话测试成功")
    
    def test_06_error_handling(self):
        """测试6: 错误处理"""
        print("\n测试错误处理...")
        
        # 测试无效的请求
        response = requests.post(
            f"{self.LOCAL_URL}/api/search/stream",
            json={"invalid": "data"}
        )
        
        # 应该返回422（验证错误）或400（错误请求）
        assert response.status_code in [400, 422]
        print("✅ 错误请求处理正确")
        
        # 测试不存在的端点
        response = requests.get(f"{self.LOCAL_URL}/api/nonexistent")
        assert response.status_code == 404
        print("✅ 404错误处理正确")
    
    def test_07_cors_headers(self):
        """测试7: CORS配置"""
        response = requests.options(
            f"{self.LOCAL_URL}/api/search/stream",
            headers={"Origin": "http://example.com"}
        )
        
        # 检查CORS头
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        
        print("✅ CORS配置正确")
        print(f"  允许的源: {response.headers.get('access-control-allow-origin')}")
        print(f"  允许的方法: {response.headers.get('access-control-allow-methods')}")

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("本地后端API服务测试")
    print("=" * 60)
    
    # 使用pytest运行测试
    pytest.main([__file__, "-v", "-s"])

if __name__ == "__main__":
    run_tests()