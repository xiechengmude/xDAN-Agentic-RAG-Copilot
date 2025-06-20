#!/usr/bin/env python3
"""
列出可用的模型
"""

import requests
import json

def list_models():
    """列出可用的模型"""
    url = "http://43.134.187.48:7220/v1/models"
    api_key = "sk-vvr2jecYl1lkEu2MF4E3Ef0dC92c4a3eA6F2B633Ba621d81"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"Listing models from: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Available models:")
            if 'data' in result:
                for model in result['data']:
                    print(f"  - {model.get('id', 'unknown')}")
            else:
                print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()