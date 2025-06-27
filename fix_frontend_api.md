# 前端API对接修复指南

## 问题描述
前端请求API时报错，主要原因是：
1. 认证令牌不正确
2. API代理地址配置错误

## 快速修复方案

### 方案1：修改Vite代理配置（推荐用于开发）

修改 `frontend/vite.config.ts` 文件：

```typescript
server: {
  proxy: {
    "/api": {
      target: "http://150.109.16.195:8050", // 改为实际的API服务地址
      changeOrigin: true,
    },
  },
},
```

### 方案2：在前端设置正确的认证令牌

在浏览器控制台执行：
```javascript
// 设置正确的认证令牌
localStorage.setItem('ragflow_auth_token', 'xDAN-RAG-Service-Demo-Key');

// 刷新页面
location.reload();
```

### 方案3：使用环境变量（用于不同环境）

1. 修改 `frontend/.env.development`：
```env
# API服务地址
VITE_API_BASE_URL=http://150.109.16.195:8050

# API认证令牌
VITE_API_TOKEN=xDAN-RAG-Service-Demo-Key
```

2. 在代码中使用环境变量设置token：
```typescript
// 在 App.tsx 或初始化代码中
import { authManager } from '@/api/client';

// 设置认证令牌
authManager.setToken(import.meta.env.VITE_API_TOKEN || 'xDAN-RAG-Service-Demo-Key');
```

## 测试验证

修复后，可以通过以下curl命令测试：

```bash
# 直接测试API服务
curl 'http://150.109.16.195:8050/api/v1/datasets?page=1&page_size=12' \
  -H 'Authorization: Bearer xDAN-RAG-Service-Demo-Key' \
  -H 'Content-Type: application/json'

# 通过前端代理测试（需要先启动前端开发服务器）
curl 'http://localhost:5173/api/v1/datasets?page=1&page_size=12' \
  -H 'Authorization: Bearer xDAN-RAG-Service-Demo-Key' \
  -H 'Content-Type: application/json'
```

## 长期解决方案

1. **统一管理API配置**：创建一个配置文件管理所有环境的API地址和认证信息
2. **使用环境变量**：不同环境使用不同的 .env 文件
3. **避免硬编码**：所有API请求都通过统一的 apiClient 进行

## 注意事项

- 开发环境和生产环境的API地址可能不同
- 认证令牌应该安全存储，不要提交到代码仓库
- 使用HTTPS协议保护敏感信息传输