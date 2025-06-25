# 本地快速启动指南

## 简介

`local_start.sh` 是一个简化的本地部署脚本，用于快速启动 xDAN RAG Copilot 的前后端服务。该脚本提供了持久化日志记录和结构化输出功能。

## 特性

- 🚀 一键启动前后端服务
- 📝 持久化日志记录，所有日志保存到 `logs/` 目录
- 🎨 结构化的彩色输出，便于识别不同级别的信息
- 🔄 支持服务的启动、停止、重启和状态查看
- 📊 自动健康检查
- 🗂️ 日志轮转支持

## 快速开始

```bash
# 启动所有服务
./deploy/local_start.sh start

# 查看服务状态
./deploy/local_start.sh status

# 停止所有服务
./deploy/local_start.sh stop

# 重启服务
./deploy/local_start.sh restart

# 查看后端日志
./deploy/local_start.sh logs backend

# 查看前端日志
./deploy/local_start.sh logs frontend
```

## 目录结构

启动后会自动创建以下目录：

```
ragflow-api-client/
├── logs/                    # 日志目录
│   ├── backend/            # 后端日志
│   │   ├── service_*.log   # 服务日志（结构化）
│   │   └── output_*.log    # 输出日志
│   ├── frontend/           # 前端日志
│   │   ├── service_*.log   # 服务日志（结构化）
│   │   └── output_*.log    # 输出日志
│   └── archive/            # 归档的压缩日志
├── .pids/                  # PID文件目录
│   ├── backend.pid         # 后端进程ID
│   └── frontend.pid        # 前端进程ID
└── .env                    # 环境配置文件（自动生成）
```

## 日志管理

### 日志格式

所有日志采用结构化格式：
```
[2024-01-20 10:30:45] [INFO] [BACKEND] 启动后端服务 (端口: 8050)
[时间戳] [级别] [组件] 消息
```

### 日志级别

- **INFO**: 一般信息（蓝色）
- **SUCCESS**: 成功信息（绿色）
- **WARNING**: 警告信息（黄色）
- **ERROR**: 错误信息（红色）

### 日志轮转

使用日志轮转脚本管理日志文件：

```bash
# 手动执行日志轮转
./deploy/rotate_logs.sh

# 添加到 crontab 实现自动轮转（每天凌晨3点）
crontab -e
# 添加以下行：
0 3 * * * /path/to/deploy/rotate_logs.sh
```

默认配置：
- 原始日志保留 7 天
- 压缩日志保留 30 天
- 超过期限的日志自动删除

## 环境变量

脚本支持以下环境变量配置：

```bash
# 后端端口（默认: 8050）
BACKEND_PORT=8050

# 前端端口（默认: 5173）
FRONTEND_PORT=5173

# RAGFlow API 配置
RAGFLOW_API_URL=http://150.109.16.195:7080
RAGFLOW_API_KEY=ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm

# 使用示例
BACKEND_PORT=8080 ./deploy/local_start.sh start
```

## 常见问题

### 1. 端口被占用

如果遇到端口被占用的错误，可以：
- 修改环境变量使用其他端口
- 或者先停止占用端口的服务

### 2. Python 依赖问题

脚本会自动创建虚拟环境并安装依赖。如果遇到问题，可以手动安装：

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-multipart requests pydantic
```

### 3. 查看详细日志

```bash
# 实时查看后端日志
tail -f logs/backend/output_*.log

# 查看最新的服务日志
tail -n 100 logs/backend/service_*.log
```

## 服务访问地址

启动成功后，可以访问：

- 前端应用: http://localhost:5173
- API 文档: http://localhost:8050/docs
- 健康检查: http://localhost:8050/health

## 注意事项

1. 脚本使用 `nohup` 确保服务在后台持续运行
2. 所有日志都会保存，注意定期清理或设置日志轮转
3. 停止服务时会优雅关闭，如果无法正常停止会强制终止
4. 前端服务会自动检测是否为 Node.js 项目，如果不是则使用 Python HTTP 服务器