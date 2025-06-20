# 服务部署指南

## 概述

本项目包含两个主要服务：
1. **API服务**：提供智能搜索的后端API（端口：8050）
2. **前端服务**：React应用程序，提供用户界面（端口：5173/5174）

## 快速启动

使用提供的脚本 `start_server.sh` 来管理服务：

```bash
# 启动所有服务（API和前端）
./start_server.sh start

# 查看服务状态
./start_server.sh status

# 停止所有服务
./start_server.sh stop

# 重启所有服务
./start_server.sh restart
```

## 单独管理服务

### API服务管理
```bash
# 仅启动API服务
./start_server.sh api start

# 仅停止API服务
./start_server.sh api stop

# 仅重启API服务
./start_server.sh api restart
```

### 前端服务管理
```bash
# 仅启动前端服务
./start_server.sh frontend start

# 仅停止前端服务
./start_server.sh frontend stop

# 仅重启前端服务
./start_server.sh frontend restart
```

## 访问地址

服务启动后，可以通过以下地址访问：

- **API服务**：http://localhost:8050
- **API文档**：http://localhost:8050/docs
- **前端应用**：http://localhost:5173/app/ 或 http://localhost:5174/app/

## 日志位置

所有服务日志都保存在 `logs/` 目录下：

- **API日志**：`logs/demo_server_*.log`
- **前端日志**：`logs/frontend_*.log`
- **主日志文件**：`demo_server_simple.log`

查看日志的命令：
```bash
# 查看API日志
tail -f logs/demo_server_*.log

# 查看前端日志
tail -f logs/frontend_*.log

# 查看主日志
tail -f demo_server_simple.log
```

## 故障排查

### 端口冲突
如果启动时提示端口已被占用：
```bash
# 查看占用端口的进程
lsof -i:8050    # API端口
lsof -i:5173    # 前端端口

# 强制停止所有服务
./start_server.sh stop
```

### 前端无法访问API
1. 确保API服务正在运行：`./start_server.sh status`
2. 检查API日志是否有错误
3. 确认防火墙设置允许本地访问

### 依赖问题
如果前端启动失败，可能需要重新安装依赖：
```bash
cd frontend
npm install
cd ..
./start_server.sh frontend restart
```

## 开发模式

当前配置为开发模式，特点：
- 支持热重载（前端代码修改自动刷新）
- 详细的错误日志
- CORS已配置，允许跨域请求

## 生产部署

生产环境部署建议：
1. 使用进程管理器（如PM2、systemd）
2. 配置反向代理（如Nginx）
3. 启用HTTPS
4. 设置环境变量
5. 使用生产构建：`cd frontend && npm run build`

## 外部访问

如需允许外部设备访问（如手机测试）：

1. 查看本机IP：
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

2. 修改前端启动命令以暴露服务：
```bash
cd frontend
npm run dev -- --host
```

3. 确保防火墙允许相应端口访问

## 环境要求

- Node.js >= 16
- Python >= 3.8
- uv (Python包管理器)
- 足够的内存（建议4GB+）用于运行LLM模型