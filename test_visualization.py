#!/usr/bin/env python3
"""
测试搜索可视化API
"""

import requests
import json

def test_search_stream():
    """测试流式搜索API"""
    url = "http://localhost:8000/api/search/stream"
    
    # 测试问题
    questions = [
        "什么是智信平台？它主要有哪些功能？",
        "如果机构不支持用户的银行卡类型，授信时会发生什么？",
        "当还款状态是'申请失败'时，如果系统收到了机构的还款成功/失败通知，系统会如何处理？"
    ]
    
    for question in questions[:1]:  # 先测试第一个问题
        print(f"\n{'='*60}")
        print(f"测试问题: {question}")
        print('='*60)
        
        # 发送POST请求
        response = requests.post(url, 
            json={"question": question},
            stream=True,
            headers={'Accept': 'text/event-stream'}
        )
        
        # 处理流式响应
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]
                    if data == '[DONE]':
                        print("\n✅ 搜索完成")
                        break
                    else:
                        try:
                            event = json.loads(data)
                            print(f"\n[{event['event_type']}] ", end='')
                            
                            if event['event_type'] == 'search_start':
                                print(f"开始搜索: {event['data']['question'][:50]}...")
                            elif event['event_type'] == 'documents_retrieved':
                                print(f"检索到 {event['data']['count']} 个文档")
                            elif event['event_type'] == 'agent_decision':
                                thinking = event['data'].get('thinking', '')
                                if thinking:
                                    print(f"智能体思考: {thinking[:100]}...")
                                print(f"\n  决策: {event['data'].get('decision', '')}")
                            elif event['event_type'] == 'answer_generated':
                                answer = event['data']['answer']
                                print(f"生成答案: {answer[:200]}...")
                            else:
                                print(json.dumps(event['data'], ensure_ascii=False))
                        except json.JSONDecodeError:
                            print(f"解析错误: {data}")

if __name__ == "__main__":
    print("开始测试搜索可视化API...")
    print("请确保演示服务器正在运行: http://localhost:8000")
    test_search_stream()