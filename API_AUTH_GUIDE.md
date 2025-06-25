# API 认证机制说明

## 概述

xDAN RAG Copilot API Proxy V2 实现了双层认证机制：

1. **第三方调用者认证**：第三方调用者使用自己的 API Key 进行认证
2. **RAGFlow 认证**：由代理服务器在后端统一处理，第三方无需关心

## 认证方式

### 1. 使用 X-API-Key Header（推荐）

```bash
curl -X GET http://localhost:8050/api/v1/datasets \
  -H "X-API-Key: xdan-demo-key-123456"
```

### 2. 使用 Authorization Bearer Token

```bash
curl -X GET http://localhost:8050/api/v1/datasets \
  -H "Authorization: Bearer xdan-demo-key-123456"
```

## 测试用 API Keys

开发环境提供了两个测试用的 API Key：

| API Key | 说明 | 权限 | 速率限制 |
|---------|------|------|----------|
| `xdan-demo-key-123456` | 演示客户端 | 读写 | 100次/分钟 |
| `xdan-prod-key-789012` | 生产客户端 | 读写 | 1000次/分钟 |

## 示例代码

### Python 示例

```python
import requests

# 配置
API_BASE_URL = "http://localhost:8050"
API_KEY = "xdan-demo-key-123456"

# 创建 session
session = requests.Session()
session.headers.update({
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
})

# 获取数据集列表
response = session.get(f"{API_BASE_URL}/api/v1/datasets")
print(response.json())

# 创建数据集
dataset_data = {
    "name": "测试知识库",
    "description": "这是一个测试知识库"
}
response = session.post(f"{API_BASE_URL}/api/v1/datasets", json=dataset_data)
print(response.json())
```

### JavaScript/Node.js 示例

```javascript
const axios = require('axios');

// 配置
const API_BASE_URL = 'http://localhost:8050';
const API_KEY = 'xdan-demo-key-123456';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

// 获取数据集列表
async function getDatasets() {
  try {
    const response = await apiClient.get('/api/v1/datasets');
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// 创建数据集
async function createDataset() {
  try {
    const response = await apiClient.post('/api/v1/datasets', {
      name: '测试知识库',
      description: '这是一个测试知识库'
    });
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}
```

### cURL 示例

```bash
# 获取数据集列表
curl -X GET http://localhost:8050/api/v1/datasets \
  -H "X-API-Key: xdan-demo-key-123456"

# 创建数据集
curl -X POST http://localhost:8050/api/v1/datasets \
  -H "X-API-Key: xdan-demo-key-123456" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试知识库",
    "description": "这是一个测试知识库"
  }'

# 上传文档
curl -X POST http://localhost:8050/api/v1/datasets/{dataset_id}/documents \
  -H "X-API-Key: xdan-demo-key-123456" \
  -F "file=@document.pdf" \
  -F "parser_id=default"
```

## 生产环境配置

在生产环境中，应该：

1. **使用环境变量配置 RAGFlow 凭据**
   ```bash
   export RAGFLOW_API_URL="http://your-ragflow-server:7080"
   export RAGFLOW_API_KEY="your-ragflow-api-key"
   ```

2. **从数据库或配置文件加载客户端 API Keys**
   ```python
   # 示例：从数据库加载
   def load_api_keys_from_db():
       # 连接数据库
       # 查询 api_keys 表
       # 返回 dict 格式的 API Keys
       pass
   ```

3. **实现更复杂的认证机制**
   - JWT Token
   - OAuth 2.0
   - API Key + Secret
   - IP 白名单

4. **添加速率限制和配额管理**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

## 错误响应

所有错误响应都遵循统一格式：

```json
{
  "code": 401,
  "message": "未授权：无效的 API Key",
  "data": null
}
```

常见错误码：
- 401: 未授权（无效的 API Key）
- 403: 禁止访问（权限不足）
- 429: 请求过多（超过速率限制）
- 500: 服务器内部错误

## 安全建议

1. **定期轮换 API Keys**
2. **使用 HTTPS 传输**
3. **记录所有 API 调用日志**
4. **监控异常调用模式**
5. **实施 IP 白名单（可选）**
6. **设置合理的速率限制**

## 迁移指南

从 V1 迁移到 V2：

1. **更换认证头**
   - 旧版：`Authorization: Bearer ragflow-xxxxx`
   - 新版：`X-API-Key: xdan-demo-key-123456`

2. **联系管理员获取新的 API Key**

3. **更新客户端代码**（参考上面的示例）

4. **测试所有接口调用**

## 联系支持

如需申请生产环境 API Key 或遇到问题，请联系：
- 技术支持邮箱：support@xdan.ai
- API 文档：http://localhost:8050/docs