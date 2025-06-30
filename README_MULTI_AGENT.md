# 🤖 Pure Backend Multi-Agent Framework

这是 **frame/multi-agent** 分支，专门用于纯后端多智能体架构开发。

## 🎯 分支说明

- **分支名称**: `frame/multi-agent`
- **Fork来源**: `search` 分支
- **架构类型**: 纯后端，无API服务器
- **核心功能**: 多智能体协调和工作流编排

## 🏗️ 架构特点

### ✨ 纯后端设计
- ❌ **已移除**: API服务器相关代码
- ❌ **已移除**: FastAPI、uvicorn等Web框架
- ❌ **已移除**: HTTP端点和路由
- ✅ **保留**: 核心多智能体框架
- ✅ **保留**: 搜索、分析、综合功能
- ✅ **保留**: 配置和客户端

### 🤖 多智能体系统
- **BaseAgent**: 智能体基类
- **AgentManager**: 智能体管理器
- **MultiAgentCoordinator**: 高级协调器
- **SearchAgent**: 搜索智能体
- **AnalysisAgent**: 分析智能体  
- **SynthesisAgent**: 综合智能体

## 📁 核心目录

```
frame/multi_agent/          # 多智能体框架
├── README.md               # 框架文档
├── core/                   # 核心组件
│   ├── base_agent.py      # 智能体基类
│   ├── agent_manager.py   # 管理器
│   ├── coordinator.py     # 协调器
│   └── message.py         # 消息系统
├── agents/                 # 专门智能体
│   ├── search_agent.py    # 搜索智能体
│   ├── analysis_agent.py  # 分析智能体
│   └── synthesis_agent.py # 综合智能体
├── examples/               # 使用示例
│   ├── basic_example.py   # 基础示例
│   └── advanced_example.py# 高级示例
└── tests/                  # 测试代码
    └── test_framework.py  # 框架测试

src/                        # 保留的核心组件
├── clients/               # 外部服务客户端
├── core/                  # 核心框架
└── utils/                 # 工具函数
```

## 🚀 快速开始

### 1. 基础使用示例

```bash
python frame/multi_agent/examples/basic_example.py
```

### 2. 高级工作流示例

```bash
python frame/multi_agent/examples/advanced_example.py
```

### 3. 运行测试

```bash
python frame/multi_agent/tests/test_framework.py
```

## 🎯 支持的工作流

1. **基础搜索工作流**
   - 搜索 → 分析 → 综合
   - 单轮完整处理

2. **多轮搜索工作流**
   - 多轮迭代搜索
   - 智能停止条件

3. **对比分析工作流**
   - 并行对比两个主题
   - 综合对比分析

4. **深度研究工作流**
   - 多维度深入研究
   - 全面信息收集

5. **趋势分析工作流**
   - 跨时间段分析
   - 趋势变化追踪

## 💻 编程接口

### 基础使用

```python
import asyncio
from frame.multi_agent.core.coordinator import MultiAgentCoordinator

async def main():
    # 创建协调器
    coordinator = MultiAgentCoordinator()
    
    # 启动系统
    await coordinator.start()
    await coordinator.setup_default_agents()
    
    # 执行搜索
    result = await coordinator.execute_search_workflow(
        question="什么是人工智能？"
    )
    
    # 处理结果
    print(f"答案: {result['final_answer']}")
    
    # 关闭系统
    await coordinator.stop()

asyncio.run(main())
```

### 高级工作流

```python
# 对比分析
result = await coordinator.execute_comparative_analysis(
    topic_a="React框架",
    topic_b="Vue.js框架"
)

# 深度研究
result = await coordinator.execute_deep_research(
    research_topic="人工智能",
    aspects=["技术发展", "应用领域", "未来趋势"]
)

# 多轮搜索
result = await coordinator.execute_multi_round_search(
    question="分析电动车市场竞争格局",
    max_rounds=3
)
```

## 🔧 环境配置

确保已配置以下环境变量和服务：

```bash
# 必需的API密钥
export BRIGHTDATA_API_KEY="your_key"
export FIRECRAWL_API_KEY="your_key" 
export DEEPSEEK_API_KEY="your_key"

# 可选配置
export NO_PROXY="localhost,127.0.0.1"
```

## 📊 性能特点

- ✅ **高并发**: 全异步架构
- ✅ **低延迟**: 无HTTP开销
- ✅ **可扩展**: 易于添加新智能体
- ✅ **容错性**: 完善的错误处理
- ✅ **可观测**: 完整的日志和监控

## 🔄 与其他分支的关系

- **search分支**: 包含API服务器 + 多智能体框架
- **frame/multi-agent分支**: 仅包含纯后端多智能体框架
- **主要差异**: 移除了所有Web服务相关代码

## 📝 开发指南

### 添加新智能体

```python
from frame.multi_agent.core.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name, "自定义智能体")
        # 注册消息处理器
        self.register_handler(MessageType.TASK, self._handle_task)
    
    async def _handle_task(self, message: Message):
        # 处理任务逻辑
        pass
```

### 创建自定义工作流

```python
# 在协调器中添加新的工作流方法
async def execute_custom_workflow(self, params):
    # 工作流实现
    pass
```

## 🤝 贡献

欢迎为多智能体框架贡献代码！请确保：

1. 遵循异步编程范式
2. 添加完整的类型注解
3. 编写测试用例
4. 更新文档

## 📞 支持

如有问题，请：
1. 查看 `frame/multi_agent/README.md`
2. 运行测试用例验证环境
3. 检查日志输出
4. 提交Issue或PR

---

🎉 **享受纯后端多智能体开发体验！**