# 项目根目录说明

最后更新: 2025-06-27

## 目录结构

### 核心代码
- `src/` - 源代码
  - `api/` - API服务器实现
  - `clients/` - 客户端实现（RAGFlow, LiteLLM, BrightData, FireCrawl）
  - `core/` - 核心框架（S3框架、配置加载器）
  - `services/` - 服务层
  - `utils/` - 工具函数

### 测试相关
- `tests/` - 测试代码
  - `unit/` - 单元测试
  - `integration/` - 集成测试
  - `fixtures/` - 测试数据

### 脚本工具
- `scripts/` - 各类脚本
  - `debug/` - 调试脚本（debug_*.py, analyze_*.py）
  - `test/` - 测试脚本（test_*.py, check_*.py）
  - `deployment/` - 部署脚本（deploy_*.sh, start_*.sh）
  - `migration/` - 迁移工具
  - `tools/` - 实用工具

### 演示代码
- `demos/` - 演示脚本
  - `deepsearch/` - DeepSearch功能演示
    - `demo_single_complex_question.py` - 单个复杂问题处理
    - `test_challenging_questions.py` - 批量测试10个挑战性问题
    - `demo_deepsearch_complete.py` - 完整DeepSearch流程
  - `api/` - API使用演示
  - `integration/` - 集成演示

### 文档
- `docs/` - 项目文档
  - `architecture/` - 架构设计文档
  - `api/` - API文档
  - `deployment/` - 部署指南
  - `接口清单/` - 接口文档
  - `CHALLENGING_QUESTIONS.md` - DeepSearch挑战性问题集

## 根目录主要文件

### 配置文件
- `config.yaml` - 主配置文件
- `.env` - 环境变量（API密钥等）
- `pyproject.toml` - Python项目配置
- `requirements.txt` - 依赖包列表

### 部署脚本
- `install.sh` - 安装脚本
- `quick_deploy.sh` - 快速部署
- `diagnose.sh` - 诊断工具
- `stop_server.sh` - 停止服务

### 文档
- `README.md` - 项目说明
- `ROOT_DIRECTORY_GUIDE.md` - 本文件

## 快速开始

### 1. 安装依赖
```bash
./install.sh
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 添加API密钥
```

### 3. 启动服务
```bash
# 启动API服务器
python src/api/server.py

# 或使用uv
uv run python src/api/server.py
```

### 4. 运行演示
```bash
# DeepSearch演示
python demos/deepsearch/demo_single_complex_question.py

# 批量测试
python demos/deepsearch/test_challenging_questions.py
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/
```

## 调试工具

```bash
# 诊断系统状态
./diagnose.sh

# 检查API端点
python scripts/test/check_api_endpoints.py

# 调试S3工作流
python scripts/debug/debug_s3_workflow.py
```

## 重要说明

1. **API密钥管理**: 所有API密钥应配置在 `.env` 文件中，不要提交到代码库
2. **日志文件**: 日志文件生成在 `logs/` 目录下
3. **临时文件**: 搜索结果和爬取数据可能生成JSON文件，定期清理
4. **性能考虑**: DeepSearch演示可能产生大量API调用，注意费用