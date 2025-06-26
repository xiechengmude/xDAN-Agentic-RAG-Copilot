# 项目根目录说明

最后更新: 2025-06-26 20:33:07

## 目录结构

- `src/` - 源代码
  - `api/` - API服务器
  - `clients/` - 客户端实现
  - `core/` - 核心框架
  - `services/` - 服务层
  - `utils/` - 工具函数

- `tests/` - 测试代码
  - `unit/` - 单元测试
  - `integration/` - 集成测试
  - `e2e/` - 端到端测试

- `scripts/` - 脚本工具
  - `migration/` - 迁移工具
  - `tools/` - 实用工具
  - `debug/` - 调试脚本

- `examples/` - 示例代码

- `docs/` - 文档
  - `架构文档/` - 架构设计文档

- `config/` - 配置文件

- `archive/` - 归档文件

## 主要文件

- `config.yaml` - 主配置文件
- `pyproject.toml` - 项目配置
- `README.md` - 项目说明

## 运行服务

```bash
# 启动API服务器
python src/api/server.py

# 或使用uv
uv run python src/api/server.py
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/
```
