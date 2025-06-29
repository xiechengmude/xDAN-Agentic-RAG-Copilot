#!/usr/bin/env python3
"""
调试v1.2 Agent决策提取问题
"""

import json
import logging
import sys
import os
from datetime import datetime
import asyncio
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# 专门捕获Agent响应
class AgentResponseCapture:
    def __init__(self):
        self.responses = []
    
    def capture(self, response):
        self.responses.append({
            'time': datetime.now().isoformat(),
            'content': response
        })

capture = AgentResponseCapture()

# Monkey patch extract_deepsearch_decision to capture response
original_extract = DeepSearchFramework.extract_deepsearch_decision

def patched_extract(self, agent_response):
    print("\n" + "="*80)
    print("CAPTURED AGENT RESPONSE:")
    print("="*80)
    print(agent_response)
    print("="*80 + "\n")
    
    # Save to file
    with open('debug_agent_response.txt', 'w', encoding='utf-8') as f:
        f.write(agent_response)
    
    capture.capture(agent_response)
    
    # Call original method
    result = original_extract(self, agent_response)
    
    print("\nEXTRACTED DECISION:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()
    
    return result

DeepSearchFramework.extract_deepsearch_decision = patched_extract

async def test_agent_decision():
    """Test Agent decision extraction"""
    
    # Load configuration
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize components with v1.2
    litellm_client = EnhancedLiteLLMClient()
    deepsearch = DeepSearchFramework(litellm_client, config, prompt_version="v1.2")
    
    # Test question
    question = "苹果公司2024年第四季度财报的关键数据"
    
    print(f"\n{'='*80}")
    print(f"Testing v1.2 Agent Decision Extraction")
    print(f"Question: {question}")
    print(f"{'='*80}\n")
    
    try:
        # Run single round
        round_count = 0
        async for result in deepsearch.execute_deepsearch_workflow(
            question=question,
            max_rounds=2,  # Allow 2 rounds to see if next_query is generated
            stream=False
        ):
            if result.get("rounds"):
                round_count = len(result["rounds"])
                
                for i, round_data in enumerate(result["rounds"]):
                    print(f"\n--- Round {i+1} Decision ---")
                    decision = round_data.get("decision", {})
                    print(f"search_complete: {decision.get('search_complete')}")
                    print(f"next_query: {decision.get('next_query')}")
                    print(f"thinking: {decision.get('thinking', '')[:200]}...")
                    
                    # Check Agent response
                    if i < len(capture.responses):
                        resp = capture.responses[i]['content']
                        # Check if response contains required tags
                        has_thinking = '<thinking>' in resp
                        has_query = '<query>' in resp
                        has_complete = '<search_complete>' in resp
                        has_next_query = '<next_query>' in resp
                        
                        print(f"\nResponse Analysis:")
                        print(f"  Has <thinking>: {has_thinking}")
                        print(f"  Has <query>: {has_query}")
                        print(f"  Has <search_complete>: {has_complete}")
                        print(f"  Has <next_query>: {has_next_query}")
        
        print(f"\n{'='*80}")
        print(f"Total rounds executed: {round_count}")
        print(f"{'='*80}")
        
        # Save debug info
        debug_info = {
            'question': question,
            'rounds': round_count,
            'responses': capture.responses,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('debug_v12_agent_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, indent=2, ensure_ascii=False)
        
        print("\nDebug information saved to:")
        print("- debug_agent_response.txt (last raw response)")
        print("- debug_v12_agent_analysis.json (full analysis)")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await deepsearch._cleanup_clients()

if __name__ == "__main__":
    asyncio.run(test_agent_decision())