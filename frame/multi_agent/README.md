# Multi-Agent Framework for DeepSearch

这是一个纯后端的多智能体架构框架，专为复杂的信息检索和分析任务设计。无需API服务器，所有组件都在后端运行。

## 🏗️ 架构概览

### 核心组件

- **BaseAgent**: 所有智能体的基类，提供消息处理、状态管理等基础功能
- **AgentManager**: 智能体管理器，负责智能体的创建、销毁和消息路由
- **MultiAgentCoordinator**: 高级协调器，支持复杂工作流编排
- **Message System**: 完整的消息传递系统，支持各种消息类型

### 专门智能体

1. **SearchAgent** - 搜索智能体
   - 负责信息搜索和网页抓取
   - 集成BrightData和FireCrawl服务
   - 支持搜索结果缓存

2. **AnalysisAgent** - 分析智能体
   - 负责内容分析和信息提取
   - 支持关键点提取、摘要生成、情感分析
   - 基于LLM的智能分析

3. **SynthesisAgent** - 综合智能体
   - 负责信息综合和最终答案生成
   - 支持多源信息对比和结构化输出
   - 生成高质量的最终答案

## 🚀 快速开始

### 基本使用

```python
import asyncio
from frame.multi_agent.core.coordinator import MultiAgentCoordinator

async def main():
    # 创建协调器
    coordinator = MultiAgentCoordinator("my_coordinator")
    
    # 启动协调器
    await coordinator.start()
    
    # 设置默认智能体
    await coordinator.setup_default_agents()
    
    # 执行搜索工作流
    result = await coordinator.execute_search_workflow(
        question="什么是人工智能？",
        num_results=10,
        include_crawl=True
    )
    
    # 处理结果
    if result.get("workflow_status") == "completed":
        print(f"答案: {result['final_answer']}")
        print(f"来源: {len(result['search_results'])} 个")
    
    # 停止协调器
    await coordinator.stop()

if __name__ == "__main__":
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

## 📁 目录结构

```
frame/multi_agent/
├── __init__.py                 # 框架入口
├── core/                       # 核心组件
│   ├── __init__.py
│   ├── base_agent.py          # 基础智能体类
│   ├── agent_manager.py       # 智能体管理器
│   ├── coordinator.py         # 高级协调器
│   └── message.py             # 消息系统
├── agents/                     # 专门智能体
│   ├── __init__.py
│   ├── search_agent.py        # 搜索智能体
│   ├── analysis_agent.py      # 分析智能体
│   └── synthesis_agent.py     # 综合智能体
├── examples/                   # 示例代码
│   ├── __init__.py
│   ├── basic_example.py       # 基础示例
│   └── advanced_example.py    # 高级示例
├── tests/                      # 测试代码
│   ├── __init__.py
│   └── test_framework.py      # 框架测试
└── README.md                   # 本文档
```

## 🎯 功能特性

### 消息系统
- 支持多种消息类型：REQUEST, RESPONSE, TASK, NOTIFICATION等
- 异步消息处理和路由
- 消息关联和响应等待机制

### 智能体管理
- 动态智能体创建和销毁
- 智能体状态监控和统计
- 消息队列管理和监控

### 工作流编排
- 预定义工作流模板
- 自定义工作流支持
- 多轮交互和状态跟踪

### 搜索功能
- 集成多个搜索引擎
- 智能内容抓取和提取
- 搜索结果缓存和优化

### 分析功能
- 基于LLM的内容分析
- 多维度信息提取
- 结构化数据输出

## 🔧 运行示例

### 基础示例
```bash
python frame/multi_agent/examples/basic_example.py
```

### 高级示例
```bash
python frame/multi_agent/examples/advanced_example.py
```

### 运行测试
```bash
python frame/multi_agent/tests/test_framework.py
```

## 📊 性能特性

- **异步处理**: 全异步架构，支持高并发
- **智能缓存**: 多层缓存机制，提升响应速度
- **资源优化**: 智能资源管理和清理
- **错误处理**: 完善的异常处理和恢复机制

## 🛠️ 扩展开发

### 创建自定义智能体

```python
from frame.multi_agent.core.base_agent import BaseAgent
from frame.multi_agent.core.message import Message, MessageType

class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name, "Custom agent description")
        self.register_handler(MessageType.TASK, self._handle_custom_task)
    
    async def on_start(self):
        self.logger.info(f"Custom agent {self.name} started")
    
    async def on_stop(self):
        self.logger.info(f"Custom agent {self.name} stopped")
    
    async def _handle_custom_task(self, message: Message):
        # 处理自定义任务
        result = await self._process_task(message.content)
        
        response = message.create_response(
            content={"result": result},
            type=MessageType.RESULT
        )
        await self.send(response)
```

### 注册和使用自定义智能体

```python
# 注册智能体类型
coordinator.register_agent_type("custom", CustomAgent)

# 创建智能体实例
agent = await coordinator.create_agent("custom", "my_custom_agent")

# 发送任务
task_message = TaskMessage(
    task_type="custom_task",
    task_data={"input": "data"},
    sender="coordinator",
    receiver="my_custom_agent"
)
```

## 🔗 依赖项

- Python 3.8+
- asyncio
- src.clients.brightdata_client
- src.clients.firecrawl_client  
- src.clients.litellm_client
- src.core.config_loader

## 📝 许可证

本项目为内部开发框架，请遵循项目整体许可证。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个框架。

## 📞 支持

如有问题，请联系开发团队或查看项目文档。