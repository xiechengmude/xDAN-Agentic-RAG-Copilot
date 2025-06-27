# 远程服务器API接口检查清单

**远程服务器**: http://150.109.16.195:8050  
**测试时间**: 2025-06-27 12:42:33 12:21:30  
**API版本**: v2.0  

## 📋 接口检查清单

### 系统管理接口
- [x] `GET /health` - 健康检查
- [x] `GET /docs` - Swagger文档
- [x] `GET /openapi.json` - OpenAPI规范

### 知识库管理 (Dataset Management)
- [x] `GET /api/v1/datasets` - 获取知识库列表
- [x] `GET /api/v1/datasets?name=xxx` - 搜索知识库（客户端过滤）
- [x] `POST /api/v1/datasets` - 创建知识库
- [x] `PUT /api/v1/datasets/{dataset_id}` - 更新知识库
- [x] `DELETE /api/v1/datasets/{dataset_id}` - 删除知识库（单个）
- [ ] `DELETE /api/v1/datasets` - 批量删除知识库

### 文档管理 (Document Management)
- [x] `POST /api/v1/datasets/{dataset_id}/documents` - 上传文档
- [x] `GET /api/v1/datasets/{dataset_id}/documents` - 获取文档列表
- [x] `GET /api/v1/datasets/{dataset_id}/documents/{doc_id}` - 获取文档内容
- [x] `DELETE /api/v1/datasets/{dataset_id}/documents/{doc_id}` - 删除文档（单个）
- [x] `DELETE /api/v1/datasets/{dataset_id}/documents` - 批量删除文档
- [x] `GET /api/v1/datasets/{dataset_id}/documents/{doc_id}/download` - 下载文档
- [x] `POST /api/v1/datasets/{dataset_id}/documents/parse` - 解析文档

### 对话管理 (Chat Management)
- [x] `POST /api/v1/chats` - 创建对话
- [x] `GET /api/v1/chats` - 获取对话列表
- [x] `GET /api/v1/chats/{chat_id}` - 获取对话详情
- [x] `PUT /api/v1/chats/{chat_id}` - 更新对话
- [x] `DELETE /api/v1/chats/{chat_id}` - 删除对话
- [x] `POST /api/v1/chats/{chat_id}/completions` - 发送消息（SSE流式）
- [x] `GET /api/v1/chats/{chat_id}/messages` - 获取对话历史

### 检索接口 (Retrieval)
- [ ] `POST /api/v1/retrieval` - 知识库检索
- [x] `POST /api/v1/retrieve` - 知识库检索（别名）

### 引用文档查看 (Reference Documents)
- [x] `GET /api/v1/documents/reference/{document_id}` - 查看引用文档
- [x] `POST /api/v1/documents/reference/batch` - 批量查看引用文档

## 测试注意事项

### 1. 认证要求
- 所有接口需要 Bearer Token: `xDAN-RAG-Service-Demo-Key`
- Header: `Authorization: Bearer xDAN-RAG-Service-Demo-Key`

### 2. 已知的特殊行为
- 数据集名称搜索在客户端实现（避免RAGFlow权限错误）
- 删除操作统一使用批量接口（即使删除单个）
- 文档上传使用 `file` 字段，不是 `files[]`
- SSE流式响应返回真正的逐字增量（answer_delta）

### 3. 测试数据
- 可用的测试数据集ID: `7e8d9e924cde11f0afc90242ac140006`
- 该数据集包含已解析的文档，可用于对话测试

### 4. 预期响应格式
```json
{
  "code": 0,        // 0表示成功
  "message": "Success",
  "data": {},       // 具体数据
  "meta": {}        // 分页信息（可选）
}
```

## 测试结果记录

| 接口类别 | 总数 | 通过 | 失败 | 通过率 |
|---------|------|------|------|--------|
| 系统管理 | 3 | - | - | - |
| 知识库管理 | 6 | - | - | - |
| 文档管理 | 7 | - | - | - |
| 对话管理 | 7 | - | - | - |
| 检索接口 | 2 | - | - | - |
| 引用文档 | 2 | - | - | - |
| **总计** | **27** | - | - | - |

## 测试结果统计

- 总接口数: 27
- 通过: 20
- 失败: 7
- 通过率: 74.1%
