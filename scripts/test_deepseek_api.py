#!/usr/bin/env python3
"""
测试DeepSeek API连接
"""

import requests
import json

def test_deepseek_api():
    """测试DeepSeek API"""
    url = "http://43.134.187.48:7220/v1/chat/completions"
    api_key = "sk-vvr2jecYl1lkEu2MF4E3Ef0dC92c4a3eA6F2B633Ba621d81"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "temperature": 0.7
    }
    
    print(f"Testing API: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_deepseek_api()