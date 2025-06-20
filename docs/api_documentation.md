# 智能搜索API对接文档

## 概述

本文档描述了智能搜索服务的API接口，该服务基于S3（Search-Select-Synthesize）框架，提供实时的文档检索和答案生成功能。API使用Server-Sent Events (SSE)技术实现流式响应，让前端能够实时展示搜索过程。

## 基础信息

- **基础URL**: `http://localhost:8050`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **响应格式**: Server-Sent Events (SSE)

## API端点

### 1. 流式搜索接口

执行智能搜索并实时返回搜索过程事件。

**端点**: `POST /api/search/stream`

**Content-Type**: `application/json`

#### 请求参数

```json
{
  "question": "string",           // 必填：用户问题
  "dataset_ids": ["string"],      // 选填：数据集ID列表，默认使用系统配置
  "max_rounds": 3,                // 选填：最大搜索轮数，默认3
  "top_k": 10,                    // 选填：每轮检索的文档数量，默认10
  "similarity_threshold": 0.3     // 选填：相似度阈值，默认0.3
}
```

#### 请求示例

```bash
curl -X POST http://localhost:8050/api/search/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是智信平台？",
    "max_rounds": 3,
    "top_k": 10,
    "similarity_threshold": 0.3
  }'
```

#### 响应格式

响应使用Server-Sent Events格式，每个事件包含一个JSON对象：

```
data: {"event_type": "事件类型", "timestamp": "时间戳", "data": {...}}

data: [DONE]
```

#### 事件类型说明

| 事件类型 | 说明 | 数据结构 |
|---------|------|----------|
| `search_start` | 搜索开始 | `{"question": "用户问题"}` |
| `documents_retrieved` | 文档检索完成 | `{"count": 检索到的文档数量}` |
| `agent_decision` | 智能体决策 | `{"thinking": "思考过程", "decision": "继续搜索/完成搜索"}` |
| `answer_generation_start` | 开始生成答案 | `{"message": "正在生成答案..."}` |
| `answer_generated` | 答案生成完成 | `{"answer": "完整答案内容"}` |
| `error` | 错误信息 | `{"message": "错误描述"}` |

#### 完整响应示例

```
data: {"event_type": "search_start", "timestamp": "2025-06-20T10:00:00.000Z", "data": {"question": "什么是智信平台？"}}

data: {"event_type": "documents_retrieved", "timestamp": "2025-06-20T10:00:01.000Z", "round": 1, "data": {"count": 30}}

data: {"event_type": "agent_decision", "timestamp": "2025-06-20T10:00:03.000Z", "round": 1, "data": {"thinking": "从文档中找到了智信平台的基本定义...", "decision": "继续搜索"}}

data: {"event_type": "documents_retrieved", "timestamp": "2025-06-20T10:00:04.000Z", "round": 2, "data": {"count": 15}}

data: {"event_type": "agent_decision", "timestamp": "2025-06-20T10:00:06.000Z", "round": 2, "data": {"thinking": "已获得足够信息...", "decision": "完成搜索"}}

data: {"event_type": "answer_generation_start", "timestamp": "2025-06-20T10:00:07.000Z", "data": {"message": "正在生成答案..."}}

data: {"event_type": "answer_generated", "timestamp": "2025-06-20T10:00:10.000Z", "data": {"answer": "智信平台是奇富借条旗下的一个子产品..."}}

data: [DONE]
```

## 前端对接示例

### 1. 原生JavaScript (使用EventSource)

```javascript
function searchWithSSE(question) {
    // 创建请求体
    const requestBody = {
        question: question,
        max_rounds: 3,
        top_k: 10,
        similarity_threshold: 0.3
    };
    
    // 使用fetch发送POST请求
    fetch('/api/search/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        const readStream = async () => {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            console.log('搜索完成');
                            return;
                        } else if (data) {
                            try {
                                const event = JSON.parse(data);
                                handleSearchEvent(event);
                            } catch (e) {
                                console.error('解析错误:', e);
                            }
                        }
                    }
                }
            }
        };
        
        readStream();
    }).catch(error => {
        console.error('请求错误:', error);
    });
}

function handleSearchEvent(event) {
    switch (event.event_type) {
        case 'search_start':
            console.log('开始搜索:', event.data.question);
            break;
        case 'documents_retrieved':
            console.log(`检索到 ${event.data.count} 个文档`);
            break;
        case 'agent_decision':
            console.log('智能体思考:', event.data.thinking);
            console.log('决策:', event.data.decision);
            break;
        case 'answer_generated':
            console.log('答案:', event.data.answer);
            // 在UI中显示完整答案
            displayAnswer(event.data.answer);
            break;
        case 'error':
            console.error('错误:', event.data.message);
            break;
    }
}
```

### 2. React示例

```jsx
import React, { useState } from 'react';

function SearchComponent() {
    const [events, setEvents] = useState([]);
    const [searching, setSearching] = useState(false);
    const [answer, setAnswer] = useState('');
    
    const performSearch = async (question) => {
        setSearching(true);
        setEvents([]);
        setAnswer('');
        
        try {
            const response = await fetch('/api/search/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    max_rounds: 3,
                    top_k: 10,
                    similarity_threshold: 0.3
                })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            setSearching(false);
                        } else if (data) {
                            try {
                                const event = JSON.parse(data);
                                setEvents(prev => [...prev, event]);
                                
                                if (event.event_type === 'answer_generated') {
                                    setAnswer(event.data.answer);
                                }
                            } catch (e) {
                                console.error('解析错误:', e);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error('搜索错误:', error);
            setSearching(false);
        }
    };
    
    return (
        <div>
            {/* 搜索界面 */}
            <SearchInput onSearch={performSearch} disabled={searching} />
            
            {/* 搜索过程时间线 */}
            <Timeline events={events} />
            
            {/* 答案显示 */}
            {answer && <AnswerDisplay answer={answer} />}
        </div>
    );
}
```

### 3. Vue.js示例

```vue
<template>
  <div>
    <input v-model="question" @keyup.enter="search" :disabled="searching">
    <button @click="search" :disabled="searching">搜索</button>
    
    <div v-for="event in events" :key="event.timestamp">
      <EventDisplay :event="event" />
    </div>
    
    <div v-if="answer" class="answer">
      {{ answer }}
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      question: '',
      events: [],
      answer: '',
      searching: false
    };
  },
  
  methods: {
    async search() {
      if (!this.question.trim()) return;
      
      this.searching = true;
      this.events = [];
      this.answer = '';
      
      try {
        const response = await fetch('/api/search/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: this.question,
            max_rounds: 3,
            top_k: 10,
            similarity_threshold: 0.3
          })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        await this.readStream(reader, decoder);
      } catch (error) {
        console.error('搜索错误:', error);
      } finally {
        this.searching = false;
      }
    },
    
    async readStream(reader, decoder) {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            } else if (data) {
              try {
                const event = JSON.parse(data);
                this.events.push(event);
                
                if (event.event_type === 'answer_generated') {
                  this.answer = event.data.answer;
                }
              } catch (e) {
                console.error('解析错误:', e);
              }
            }
          }
        }
      }
    }
  }
};
</script>
```

## 错误处理

### HTTP错误码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误

### 错误事件

当搜索过程中发生错误时，会返回error类型的事件：

```json
{
  "event_type": "error",
  "timestamp": "2025-06-20T10:00:00.000Z",
  "data": {
    "message": "错误描述信息"
  }
}
```

## 最佳实践

1. **连接管理**
   - 实现重连机制，处理网络中断
   - 设置合理的超时时间（建议60秒）
   - 正确关闭连接，避免资源泄露

2. **用户体验**
   - 显示搜索进度指示器
   - 实时展示搜索过程，让用户了解系统在做什么
   - 对长答案提供折叠/展开功能
   - 支持搜索历史记录

3. **错误处理**
   - 捕获并友好展示错误信息
   - 提供重试机制
   - 记录错误日志用于调试

4. **性能优化**
   - 避免频繁发起搜索请求，实现防抖
   - 缓存搜索结果，避免重复请求
   - 对事件进行批量处理，减少UI更新频率

## 测试建议

1. 使用curl或Postman测试API连通性
2. 测试各种异常情况（空问题、超长问题、特殊字符等）
3. 测试网络中断和恢复情况
4. 测试并发请求处理

## 联系方式

如有问题或需要支持，请联系开发团队。