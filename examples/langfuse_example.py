#!/usr/bin/env python3
"""
Langfuse集成示例
演示如何在LiteLLM中使用Langfuse进行LLM可观察性追踪
"""

import os
from dotenv import load_dotenv
import litellm
from litellm import completion

# 加载环境变量
load_dotenv('.env.langfuse')

# 配置Langfuse
# 这些值需要从Langfuse UI获取
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

# 设置LiteLLM回调
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

# 可选：设置调试模式查看详细日志
# litellm.set_verbose = True


def simple_chat_example():
    """简单对话示例"""
    print("1. 简单对话示例")
    print("-" * 50)
    
    try:
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain what Langfuse is in one sentence."}
            ],
            # Langfuse元数据
            metadata={
                "user_id": "test-user-001",
                "session_id": "demo-session-001",
                "tags": ["demo", "simple-chat"],
                "custom_field": "example_value"
            }
        )
        
        print(f"回答: {response.choices[0].message.content}")
        print(f"✅ 追踪数据已发送到Langfuse")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def streaming_example():
    """流式响应示例"""
    print("\n2. 流式响应示例")
    print("-" * 50)
    
    try:
        response = completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Count from 1 to 5 slowly"}
            ],
            stream=True,
            metadata={
                "user_id": "test-user-002",
                "session_id": "demo-session-002",
                "tags": ["demo", "streaming"]
            }
        )
        
        print("流式输出: ", end="", flush=True)
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print("\n✅ 流式响应追踪完成")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def multi_turn_conversation():
    """多轮对话示例"""
    print("\n3. 多轮对话示例")
    print("-" * 50)
    
    session_id = "demo-session-003"
    messages = []
    
    try:
        # 第一轮
        messages.append({"role": "user", "content": "My name is Alice"})
        response1 = completion(
            model="gpt-3.5-turbo",
            messages=messages,
            metadata={
                "user_id": "alice",
                "session_id": session_id,
                "turn": 1,
                "tags": ["demo", "multi-turn"]
            }
        )
        
        assistant_msg = response1.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_msg})
        print(f"助手: {assistant_msg}")
        
        # 第二轮
        messages.append({"role": "user", "content": "What's my name?"})
        response2 = completion(
            model="gpt-3.5-turbo",
            messages=messages,
            metadata={
                "user_id": "alice",
                "session_id": session_id,
                "turn": 2,
                "tags": ["demo", "multi-turn"]
            }
        )
        
        print(f"助手: {response2.choices[0].message.content}")
        print(f"✅ 多轮对话追踪完成（会话ID: {session_id}）")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def error_handling_example():
    """错误处理示例"""
    print("\n4. 错误处理示例")
    print("-" * 50)
    
    try:
        # 故意使用无效的模型名称触发错误
        response = completion(
            model="invalid-model-name",
            messages=[{"role": "user", "content": "This will fail"}],
            metadata={
                "user_id": "test-user-error",
                "session_id": "error-session",
                "tags": ["demo", "error-test"]
            }
        )
    except Exception as e:
        print(f"预期的错误: {e}")
        print("✅ 错误已被Langfuse记录")


def main():
    """运行所有示例"""
    print("\n🔍 Langfuse集成示例")
    print("=" * 60)
    
    # 检查配置
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("⚠️  警告: LANGFUSE_PUBLIC_KEY未设置")
        print("   请先在.env.langfuse文件中配置Langfuse密钥")
        print("   或访问 http://localhost:3000 创建项目获取密钥")
        return
    
    # 运行示例
    simple_chat_example()
    streaming_example()
    multi_turn_conversation()
    error_handling_example()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例完成！")
    print(f"📊 查看追踪数据: {os.getenv('LANGFUSE_HOST', 'http://localhost:3000')}")
    print("   在Langfuse UI中可以看到：")
    print("   - 所有LLM调用记录")
    print("   - Token使用统计")
    print("   - 延迟分析")
    print("   - 错误追踪")
    print("   - 会话流程图")


if __name__ == "__main__":
    main()