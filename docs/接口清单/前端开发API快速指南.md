# 前端开发API快速指南

## 🚀 快速开始

### 基础配置
```javascript
// API配置
const API_BASE_URL = 'http://localhost:8050';  // 本地开发
// const API_BASE_URL = 'http://150.109.16.195:8050';  // 远程部署

// 请求头配置
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer xDAN-RAG-Service-Demo-Key'
};
```

## 📋 接口变更对比表

### 变更总览
| 变更类型 | 数量 | 说明 |
|----------|------|------|
| 🆕 新增 | 5个 | 文档查看、批量删除、健康检查等 |
| 🔄 修改 | 8个 | 统一响应格式、认证方式 |
| ✅ 保持 | 12个 | 核心功能接口保持稳定 |

### 详细变更列表

#### 🆕 新增接口
| 接口 | 说明 | 重要性 |
|------|------|--------|
| `GET /health` | 系统健康检查 | ⭐⭐⭐ |
| `GET /api/v1/documents/reference/{document_id}` | 查看引用文档内容 | ⭐⭐⭐⭐⭐ |
| `POST /api/v1/documents/reference/batch` | 批量查看引用文档 | ⭐⭐⭐⭐ |
| `DELETE /api/v1/datasets/{id}/documents` | 批量删除文档 | ⭐⭐⭐ |
| `GET /api/v1/datasets/{id}/documents/{doc_id}/download` | 下载文档 | ⭐⭐⭐ |

#### 🔄 主要修改
| 修改项 | 之前 | 现在 | 影响范围 |
|--------|------|------|----------|
| **认证方式** | 无/自定义 | Bearer Token | 所有接口 |
| **响应格式** | 不统一 | 统一格式 `{code, message, data}` | 所有接口 |
| **SSE响应** | 简单文本流 | 结构化JSON流，包含引用信息 | 对话接口 |
| **错误处理** | 状态码 | 统一错误码体系 | 所有接口 |
| **分页格式** | 各自不同 | 统一使用meta字段 | 列表接口 |

---

## 🔥 核心接口（前端必接）

### 1. 创建对话 
```javascript
// POST /api/v1/chats
const createChat = async (name, datasetIds) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/chats`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      name: name,
      dataset_ids: datasetIds,  // 知识库ID数组
      description: "可选描述"
    })
  });
  
  const result = await response.json();
  // 响应格式
  // {
  //   code: 0,
  //   message: "Success",
  //   data: {
  //     id: "chat_id_xxx",
  //     name: "对话名称",
  //     dataset_ids: ["xxx"],
  //     created_at: "2025-06-26T12:00:00Z"
  //   }
  // }
  return result;
};
```

### 2. 发送消息（流式响应）⭐⭐⭐⭐⭐
```javascript
// POST /api/v1/chats/{chat_id}/completions
const sendMessage = async (chatId, content) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/chats/${chatId}/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ content })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data:')) {
        const jsonStr = line.slice(5).trim();
        if (jsonStr) {
          const data = JSON.parse(jsonStr);
          
          // 处理不同类型的消息
          if (data.code === 0) {
            if (data.data === true) {
              // 流结束
              console.log('Stream ended');
            } else if (data.data.answer) {
              // 初始响应，包含完整引用信息
              console.log('Answer:', data.data.answer);
              console.log('References:', data.data.reference);
              
              // 🆕 新增：S3框架搜索过程
              if (data.data.reference?.search_process) {
                console.log('Search rounds:', data.data.reference.search_rounds);
                data.data.reference.search_process.forEach(round => {
                  console.log(`Round ${round.round}: ${round.query}`);
                  console.log(`Decision: ${round.agent_decision}`);
                });
              }
            } else if (data.data.answer_delta) {
              // 🆕 新增：增量消息（真正的逐字增量）
              console.log('Delta:', data.data.answer_delta);
              // 注意：answer_delta 只包含新增字符，实现逐字效果
              // 客户端需要自行累加以显示完整内容
            }
          }
        }
      }
    }
  }
};
```

### 3. 查看引用文档 🆕
```javascript
// GET /api/v1/documents/reference/{document_id}?dataset_id={dataset_id}
const viewReferenceDocument = async (documentId, datasetId) => {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/reference/${documentId}?dataset_id=${datasetId}`,
    { headers }
  );
  
  const result = await response.json();
  // 响应格式
  // {
  //   code: 0,
  //   message: "Success",
  //   data: {
  //     document_id: "xxx",
  //     document_name: "文档.pdf",
  //     content: "文档全文内容...",
  //     metadata: {
  //       size: 15420,
  //       pages: 25
  //     }
  //   }
  // }
  return result;
};
```

### 4. 知识库检索
```javascript
// POST /api/v1/retrieve
const searchKnowledge = async (question, datasetIds) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/retrieve`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      question: question,
      dataset_ids: datasetIds,
      page: 1,
      page_size: 5
    })
  });
  
  const result = await response.json();
  // 响应包含相关文档片段和相似度分数
  return result;
};
```

---

## 🔧 实用工具函数

### SSE响应处理器
```javascript
class SSEParser {
  constructor(onMessage, onError, onEnd) {
    this.onMessage = onMessage;
    this.onError = onError;
    this.onEnd = onEnd;
    this.buffer = '';
  }

  async parse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        this.buffer += decoder.decode(value, { stream: true });
        this.processBuffer();
      }
    } catch (error) {
      this.onError(error);
    } finally {
      this.onEnd();
    }
  }

  processBuffer() {
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data:')) {
        const jsonStr = line.slice(5).trim();
        if (jsonStr) {
          try {
            const data = JSON.parse(jsonStr);
            this.onMessage(data);
          } catch (e) {
            console.error('JSON parse error:', e);
          }
        }
      }
    }
  }
}

// 使用示例
const parser = new SSEParser(
  (data) => {
    if (data.data === true) {
      // 流结束
    } else if (data.data?.answer) {
      // 处理答案和引用
    }
  },
  (error) => console.error('SSE Error:', error),
  () => console.log('SSE Stream ended')
);

// 发送消息
const response = await fetch(...);
await parser.parse(response);
```

### 统一错误处理
```javascript
class APIClient {
  async request(url, options = {}) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers
        }
      });
      
      const result = await response.json();
      
      // 统一错误处理
      if (result.code !== 0) {
        throw new APIError(result.code, result.message);
      }
      
      return result.data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(500, '网络请求失败');
    }
  }
}

class APIError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}
```

---

## 📝 响应格式速查

### 统一响应格式
```typescript
interface ApiResponse<T = any> {
  code: number;      // 0表示成功
  message: string;   // 响应消息
  data: T;          // 响应数据
  meta?: {          // 分页信息（可选）
    page: number;
    size: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}
```

### 引用信息格式 🆕
```typescript
interface Reference {
  total: number;
  chunks: Array<{
    id: string;
    content: string;
    document_name: string;
    document_id: string;
    dataset_id: string;
    similarity: number;
    position?: string;  // 🆕 文档位置
  }>;
  search_rounds: number;  // 🆕 搜索轮数
  search_process: Array<{  // 🆕 搜索过程
    round: number;
    query: string;
    documents_found: number;
    agent_decision: string;
    agent_confidence: number;
    time_ms: number;
  }>;
  s3_trace_id?: string;  // 🆕 Langfuse追踪ID
  total_time_ms?: number;  // 🆕 总耗时
}
```

---

## ⚠️ 注意事项

### 1. 认证要求
- **所有接口**都需要Bearer Token
- Token放在Authorization头：`Bearer xDAN-RAG-Service-Demo-Key`

### 2. 文件上传
- 使用`file`字段，不是`files[]`
- Content-Type自动设置，不要手动指定为`application/json`

### 3. SSE流式响应
- 第一条消息包含完整答案和引用
- 后续消息为增量内容（如果启用）
- 最后一条`data: true`表示结束

### 4. 错误处理
- 所有错误都通过`code`字段标识
- `code: 0`表示成功，非0表示错误
- 具体错误信息在`message`字段

### 5. 知识库限制
- 创建对话前确保知识库有已解析文档
- 文档状态必须是`DONE`才能使用
- 知识库名称搜索在客户端过滤，不是服务端
- 删除操作统一使用批量接口（即使删除单个）

### 6. 对话管理限制
- `GET /api/v1/chats/{chat_id}` 获取单个对话详情 - **未实现**
- `PUT /api/v1/chats/{chat_id}` 更新对话信息 - **未实现**
- 可以通过对话列表接口获取对话信息

---

## 🎯 快速集成清单

- [ ] 配置API基础URL和认证Token
- [ ] 实现统一的请求封装（带错误处理）
- [ ] 实现SSE流式响应解析器
- [ ] 集成创建对话接口
- [ ] 集成发送消息接口（支持流式）
- [ ] 集成引用文档查看功能
- [ ] 处理各种错误状态
- [ ] 添加加载状态和用户反馈

---

**文档版本**: v1.2  
**最后更新**: 2025-06-27  
**适用前端**: React/Vue/Angular  
**API版本**: v2.0
**更新内容**:
- 明确增量消息为逐字流式
- 更新删除操作说明
- 添加客户端名称过滤说明
- 修正检索接口路径为 /api/v1/retrieve
- 添加对话管理限制说明