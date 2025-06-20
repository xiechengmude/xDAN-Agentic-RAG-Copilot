# xDAN-Agentic-RAG-Copilot

基于S3（Search-Select-Synthesize）框架的智能RAG系统，提供透明的搜索决策过程可视化。

## 🌟 特性

- **S3搜索框架**：基于智能体的多轮迭代搜索策略
- **决策透明化**：实时展示AI的思考和决策过程
- **流式响应**：使用Server-Sent Events提供实时反馈
- **现代化前端**：React + TypeScript + Tailwind CSS
- **完整API文档**：FastAPI自动生成的交互式文档

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/xiechengmude/xDAN-Agentic-RAG-Copilot.git
cd xDAN-Agentic-RAG-Copilot
```

### 2. 安装依赖
```bash
# 安装Python依赖
uv pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 3. 配置环境
复制配置模板并填入您的API密钥：
```bash
cp config/settings_template.py config/settings.py
```

### 4. 启动服务
```bash
# 启动所有服务
./start_server.sh start

# 或分别启动
./start_server.sh api start      # 仅启动API
./start_server.sh frontend start  # 仅启动前端
```

## 📍 访问地址

- **前端应用**: http://localhost:5173/app/
- **API服务**: http://localhost:8050
- **API文档**: http://localhost:8050/docs

## 🏗️ 架构说明

### S3搜索框架
1. **Search（搜索）**: 基于问题进行初始文档检索
2. **Select（选择）**: 智能体分析并选择相关文档
3. **Synthesize（综合）**: 基于选中文档生成最终答案

### 核心组件
- `demo_server_simple.py`: API服务器，提供SSE流式接口
- `enhanced_s3_rag_service_v2.py`: S3搜索框架核心实现
- `frontend/`: React前端应用
- `start_server.sh`: 服务管理脚本

## 🛠️ 开发指南

### API开发
查看 [API文档](docs/api_documentation.md) 了解接口详情。

### 前端开发
```bash
cd frontend
npm run dev  # 开发模式
npm run build  # 生产构建
```

### 服务管理
```bash
./start_server.sh status   # 查看服务状态
./start_server.sh restart  # 重启所有服务
./start_server.sh stop     # 停止所有服务
```

## 📚 文档

- [API对接文档](docs/api_documentation.md)
- [服务部署指南](docs/service_deployment.md)
- [搜索模型说明](docs/search_model_example.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License