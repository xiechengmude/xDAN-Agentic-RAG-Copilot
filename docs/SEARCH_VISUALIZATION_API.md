# 搜索过程可视化API文档

## 概述

搜索过程可视化API允许前端实时展示智能体在文档检索过程中的动作和思考过程。通过这个API，用户可以直观地看到：

- 搜索进行了多少轮
- 每轮搜索的查询是什么
- 检索到了哪些文档
- 智能体的思考过程
- 最终选中了哪些文档
- 答案是如何生成的

## API端点

### 1. 流式搜索（Server-Sent Events）

**端点**: `POST /api/v2/search/stream`

**描述**: 使用Server-Sent Events实时返回搜索过程中的每个事件。

**请求参数**:
```json
{
  "question": "用户的问题",
  "dataset_ids": ["数据集ID列表"],  // 可选
  "max_rounds": 3,                   // 最大搜索轮数，默认3
  "top_k": 10,                       // 每轮返回文档数，默认10
  "similarity_threshold": 0.3,       // 相似度阈值，默认0.3
  "stream": true                     // 是否流式返回，默认true
}
```

**响应格式**: Server-Sent Events流

```
data: {"event_type": "search_start", "timestamp": "2024-01-01T12:00:00", "data": {...}}

data: {"event_type": "documents_retrieved", "timestamp": "2024-01-01T12:00:01", "round": 1, "data": {...}}

data: {"event_type": "agent_thinking", "timestamp": "2024-01-01T12:00:02", "round": 1, "data": {...}}

data: [DONE]
```

### 2. 完整搜索结果

**端点**: `POST /api/v2/search/complete`

**描述**: 执行完整搜索并返回所有事件的汇总结果。

**请求参数**: 同上

**响应格式**:
```json
{
  "question": "用户的问题",
  "answer": "生成的答案",
  "search_summary": {
    "total_rounds": 2,
    "total_documents": 30,
    "selected_documents": 3,
    "search_time": 15.3
  },
  "events": [
    {
      "event_type": "search_start",
      "timestamp": "2024-01-01T12:00:00",
      "data": {...}
    },
    // ... 更多事件
  ]
}
```

### 3. WebSocket连接

**端点**: `WS /ws/search/{client_id}`

**描述**: 使用WebSocket进行双向实时通信。

**连接示例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search/client123');

// 发送搜索请求
ws.send(JSON.stringify({
  action: 'search',
  params: {
    question: '什么是智信平台？',
    max_rounds: 3
  }
}));

// 接收事件
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'event') {
    console.log('搜索事件:', data.event);
  } else if (data.type === 'complete') {
    console.log('搜索完成:', data.summary);
  }
};
```

## 事件类型

### 搜索流程事件

| 事件类型 | 说明 | 数据字段 |
|---------|------|---------|
| `search_start` | 搜索开始 | `question`, `config` |
| `search_round_start` | 新一轮搜索开始 | `query`, `round_type` |
| `documents_retrieved` | 文档检索完成 | `count`, `documents` |
| `agent_thinking` | 智能体思考中 | `message` |
| `agent_decision` | 智能体决策 | `thinking`, `search_complete`, `decision` |
| `new_query_generated` | 生成新查询 | `new_query`, `reason` |
| `documents_selected` | 选中文档 | `selected_ids`, `selected_count` |
| `search_complete` | 搜索完成 | `total_rounds`, `total_documents`, `search_time` |
| `answer_generation_start` | 开始生成答案 | `message` |
| `answer_generated` | 答案生成完成 | `answer` |
| `error` | 错误发生 | `message` |

### 事件数据示例

#### search_start
```json
{
  "event_type": "search_start",
  "timestamp": "2024-01-01T12:00:00",
  "data": {
    "question": "什么是智信平台？",
    "config": {
      "max_rounds": 3,
      "top_k": 10,
      "similarity_threshold": 0.3,
      "search_model": "xDAN-R2-Qwen3-14b-RagRL",
      "generator_model": "deepseek-chat"
    }
  }
}
```

#### agent_decision
```json
{
  "event_type": "agent_decision",
  "timestamp": "2024-01-01T12:00:02",
  "round": 1,
  "data": {
    "thinking": "文档1提供了基本介绍，但缺少具体功能描述",
    "search_complete": false,
    "decision": "继续搜索"
  }
}
```

#### documents_retrieved
```json
{
  "event_type": "documents_retrieved",
  "timestamp": "2024-01-01T12:00:01",
  "round": 1,
  "data": {
    "count": 8,
    "documents": [
      {
        "id": 1,
        "similarity": 0.85,
        "content_preview": "智信平台是..."
      }
    ]
  }
}
```

## 前端集成示例

### 1. 使用Server-Sent Events

```javascript
// 创建EventSource连接
const eventSource = new EventSource('/api/v2/search/stream?question=' + encodeURIComponent(question));

// 事件处理
eventSource.onmessage = function(event) {
  if (event.data === '[DONE]') {
    eventSource.close();
    console.log('搜索完成');
    return;
  }
  
  const data = JSON.parse(event.data);
  
  switch(data.event_type) {
    case 'search_start':
      console.log('搜索开始:', data.data.question);
      break;
    case 'agent_thinking':
      console.log('智能体思考中...');
      break;
    case 'agent_decision':
      console.log('智能体决策:', data.data.thinking);
      break;
    case 'answer_generated':
      console.log('答案:', data.data.answer);
      break;
  }
};

eventSource.onerror = function(error) {
  console.error('连接错误:', error);
  eventSource.close();
};
```

### 2. 使用React Hook

```jsx
import { useState, useEffect, useRef } from 'react';

function useSearchStream(apiUrl) {
  const [events, setEvents] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const eventSourceRef = useRef(null);
  
  const startSearch = (question, options = {}) => {
    // 重置状态
    setEvents([]);
    setIsSearching(true);
    
    // 关闭之前的连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // 创建新连接
    const params = new URLSearchParams({
      question,
      ...options
    });
    
    const eventSource = new EventSource(`${apiUrl}?${params}`);
    eventSourceRef.current = eventSource;
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsSearching(false);
        return;
      }
      
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsSearching(false);
    };
  };
  
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  
  return { events, isSearching, startSearch };
}
```

### 3. 可视化组件示例

```jsx
function SearchProcess() {
  const { events, isSearching, startSearch } = useSearchStream('/api/v2/search/stream');
  
  const handleSearch = () => {
    startSearch('什么是智信平台？', {
      max_rounds: 3,
      top_k: 10
    });
  };
  
  return (
    <div>
      <button onClick={handleSearch} disabled={isSearching}>
        {isSearching ? '搜索中...' : '开始搜索'}
      </button>
      
      <div className="timeline">
        {events.map((event, idx) => (
          <div key={idx} className={`event ${event.event_type}`}>
            <div className="event-type">{event.event_type}</div>
            <div className="event-data">{JSON.stringify(event.data)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 启动服务

```bash
# 安装依赖
uv pip install fastapi uvicorn

# 启动API服务
uv run python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 访问演示页面
# http://localhost:8000/demo
```

## 最佳实践

1. **错误处理**: 始终实现错误处理逻辑，SSE连接可能会意外断开
2. **重连机制**: 对于生产环境，实现自动重连机制
3. **事件缓冲**: 在快速更新时考虑事件缓冲，避免UI过度刷新
4. **性能优化**: 对于大量文档，只显示摘要信息
5. **用户体验**: 提供清晰的加载状态和进度指示

## 扩展功能

1. **事件过滤**: 前端可以选择性订阅特定类型的事件
2. **历史记录**: 保存搜索历史，支持回放
3. **对比视图**: 对比不同问题的搜索过程
4. **导出功能**: 导出搜索过程日志供分析
5. **实时协作**: 多用户共享搜索过程视图