#!/usr/bin/env python3
"""
修复前端与后端API的对接问题
将前端从不存在的接口切换到实际的S3 Chat接口
"""

import os
import re

def fix_app_tsx():
    """修复App.tsx中的API调用"""
    app_tsx_path = "frontend/src/App.tsx"
    
    if not os.path.exists(app_tsx_path):
        print(f"❌ 文件不存在: {app_tsx_path}")
        return False
    
    # 读取原文件
    with open(app_tsx_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    with open(f"{app_tsx_path}.backup", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修改API调用URL
    old_url = 'http://192.168.31.18:8050/api/search/stream'
    new_url = 'http://localhost:8050/api/v1/s3-chat'
    content = content.replace(old_url, new_url)
    
    # 修改请求体格式
    old_body = 'body: JSON.stringify({ question }),'
    new_body = '''body: JSON.stringify({ 
        question,
        dataset_ids: ["7e8d9e924cde11f0afc90242ac140006"], 
        stream: true,
        max_rounds: 3,
        save_history: false
      }),'''
    content = content.replace(old_body, new_body)
    
    # 修改SSE数据解析逻辑
    old_event_handling = '''try {
              const event: StreamEvent = JSON.parse(jsonData);
              handleStreamEvent(event);'''
    
    new_event_handling = '''try {
              const sseData = JSON.parse(jsonData);
              
              // 适配后端SSE格式到前端期望格式
              let event: StreamEvent;
              if (sseData.data?.type) {
                // S3工作流事件
                event = {
                  event_type: sseData.data.type,
                  timestamp: new Date().toISOString(),
                  data: sseData.data
                };
              } else if (sseData.data?.answer) {
                // 答案生成事件
                event = {
                  event_type: "answer_generated",
                  timestamp: new Date().toISOString(),
                  data: {
                    answer: sseData.data.answer,
                    reference: sseData.data.reference
                  }
                };
              } else if (sseData.data === true) {
                // 完成事件
                event = {
                  event_type: "complete",
                  timestamp: new Date().toISOString(),
                  data: {}
                };
              } else {
                // 默认事件
                event = {
                  event_type: "message",
                  timestamp: new Date().toISOString(),
                  data: sseData.data || {}
                };
              }
              
              handleStreamEvent(event);'''
    
    content = content.replace(old_event_handling, new_event_handling)
    
    # 写入修改后的文件
    with open(app_tsx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复 {app_tsx_path}")
    print(f"📁 备份文件: {app_tsx_path}.backup")
    return True

def create_frontend_config():
    """创建前端配置文件"""
    config_content = '''// API配置
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8050',
  ENDPOINTS: {
    S3_CHAT: '/api/v1/s3-chat',
    BASIC_CHAT: '/api/v1/chats/{chat_id}/completions',
    DATASETS: '/api/v1/datasets',
    RETRIEVAL: '/api/v1/retrieval'
  },
  DEFAULT_DATASET_ID: '7e8d9e924cde11f0afc90242ac140006'
};

// S3工作流配置
export const S3_CONFIG = {
  MAX_ROUNDS: 3,
  TOP_K: 10,
  STREAM: true,
  SAVE_HISTORY: false
};
'''
    
    config_path = "frontend/src/config/api.ts"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 已创建配置文件: {config_path}")

def create_test_script():
    """创建前端测试脚本"""
    test_content = '''<!DOCTYPE html>
<html>
<head>
    <title>S3 Chat API 测试</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .chat-container { max-width: 600px; margin: 0 auto; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #007bff; color: white; text-align: right; }
        .ai { background: #f1f1f1; color: black; }
        .activity { background: #e7f3ff; font-size: 12px; margin: 5px 0; }
        input[type="text"] { width: 70%; padding: 8px; }
        button { padding: 8px 16px; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>S3 Chat API 测试</h1>
        <div id="messages"></div>
        <div>
            <input type="text" id="questionInput" placeholder="输入问题..." />
            <button onclick="sendMessage()">发送</button>
            <button onclick="clearMessages()">清空</button>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        
        function addMessage(content, type) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = content;
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function addActivity(content) {
            const div = document.createElement('div');
            div.className = 'activity';
            div.textContent = content;
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            if (!question) return;
            
            addMessage(question, 'user');
            input.value = '';
            
            try {
                const response = await fetch('http://localhost:8050/api/v1/s3-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: question,
                        dataset_ids: ["7e8d9e924cde11f0afc90242ac140006"],
                        stream: true,
                        max_rounds: 3
                    })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullAnswer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const jsonData = line.slice(6).trim();
                            if (jsonData === 'true') continue;
                            
                            try {
                                const data = JSON.parse(jsonData);
                                
                                if (data.data?.type === 'workflow_start') {
                                    addActivity('🚀 开始S3工作流...');
                                } else if (data.data?.type === 'answer_chunk') {
                                    fullAnswer += data.data.content || '';
                                } else if (data.data?.type === 'final_result') {
                                    addMessage(data.data.answer || fullAnswer, 'ai');
                                    if (data.data.reference?.selected_documents) {
                                        addActivity(`📚 召回了 ${data.data.reference.selected_documents.length} 个文档`);
                                    }
                                    if (data.data.reference?.total_rounds) {
                                        addActivity(`🔍 执行了 ${data.data.reference.total_rounds} 轮搜索`);
                                    }
                                }
                            } catch (e) {
                                console.error('解析错误:', e);
                            }
                        }
                    }
                }
            } catch (error) {
                addMessage('错误: ' + error.message, 'ai');
            }
        }
        
        function clearMessages() {
            messagesDiv.innerHTML = '';
        }
        
        // Enter键发送
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>'''
    
    test_path = "test_s3_frontend.html"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"✅ 已创建测试页面: {test_path}")
    print(f"🌐 在浏览器中打开: file://{os.path.abspath(test_path)}")

def main():
    print("🔧 开始修复前端与后端API对接问题...")
    
    # 1. 修复App.tsx
    if fix_app_tsx():
        print("✅ App.tsx修复完成")
    else:
        print("❌ App.tsx修复失败")
        return
    
    # 2. 创建配置文件
    create_frontend_config()
    
    # 3. 创建测试页面
    create_test_script()
    
    print("\\n🎉 修复完成！")
    print("\\n📋 接下来的步骤:")
    print("1. 确保后端API服务器在 http://localhost:8050 运行")
    print("2. 重新启动前端开发服务器: cd frontend && npm run dev")
    print("3. 或者直接在浏览器中测试: 打开 test_s3_frontend.html")
    print("\\n🔍 测试建议:")
    print("- 输入问题: '什么是权益申请？'")
    print("- 观察S3工作流的完整过程")
    print("- 查看召回的文档和搜索轮次")

if __name__ == "__main__":
    main()