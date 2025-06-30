# FlashSearch 简化架构设计

**版本**: v2.0.0  
**分支**: frame/flash-search  
**设计原则**: KISS (Keep It Simple, Stupid) + DRY (Don't Repeat Yourself)  
**作者**: admin@xdan.ai

## 设计理念

当前的架构变得过于复杂，包含太多配置层、抽象层和管理器。新的FlashSearch架构将遵循以下原则：

1. **单一职责**: 每个组件只做一件事
2. **最小依赖**: 减少组件间的耦合
3. **直接明了**: 减少抽象层和中间配置
4. **性能优先**: 专注于快速响应

## 核心架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    FlashSearch 简化架构                           │
└─────────────────────────────────────────────────────────────────┘

用户接口层:
┌─────────────────────────────────────────────────────────────────┐
│  async def flash_search(question: str) -> Dict[str, Any]:       │
│  # 只有一个接口，简单直接                                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
核心执行层:
┌─────────────────────────────────────────────────────────────────┐
│  FlashSearchEngine:                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1. search()    - SERP搜索获取候选                            ││
│  │ 2. select()    - 快速选择最相关的3-5个URL                     ││
│  │ 3. crawl()     - 并发爬取内容，失败时使用snippet               ││
│  │ 4. synthesize() - 生成最终答案                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
基础服务层:
┌─────────────────────────────────────────────────────────────────┐
│  • BrightDataClient (搜索)                                      │
│  • FireCrawlClient (爬取)                                       │
│  • LiteLLMClient (LLM调用)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 简化的组件设计

### 1. **FlashSearchEngine** (核心引擎)

```python
class FlashSearchEngine:
    def __init__(self):
        self.bright_client = BrightDataAsyncClient()
        self.crawl_client = FireCrawlAsyncClient()  
        self.llm_client = EnhancedLiteLLMClient()
    
    async def search(self, question: str) -> List[Dict]:
        """快速SERP搜索，固定获取8个结果"""
        
    async def select(self, question: str, results: List[Dict]) -> List[str]:
        """快速选择最相关的3-5个URL，无复杂评分"""
        
    async def crawl(self, urls: List[str], snippets: Dict) -> List[Dict]:
        """并发爬取，超时自动fallback到snippet"""
        
    async def synthesize(self, question: str, content: List[Dict]) -> str:
        """生成最终答案，简单直接"""
        
    async def flash_search(self, question: str) -> Dict[str, Any]:
        """主入口，串联所有步骤"""
```

### 2. **移除的复杂组件**

- ❌ ModeConfigManager (配置管理器)
- ❌ deepsearch_modes.yaml (复杂配置文件)
- ❌ 多层抽象的prompt管理
- ❌ 复杂的并发策略配置
- ❌ 多轮搜索逻辑
- ❌ Agent决策系统

### 3. **保留的核心功能**

- ✅ BrightData SERP搜索
- ✅ FireCrawl内容爬取
- ✅ Snippet回退机制
- ✅ 基础的LLM调用
- ✅ 简单的URL选择逻辑

## 执行流程

```
flash_search(question) 
    │
    ├─ 1. search(question)
    │   └─ BrightData获取8个搜索结果
    │
    ├─ 2. select(question, results) 
    │   └─ LLM快速选择3-5个最相关URL
    │
    ├─ 3. crawl(urls, snippets)
    │   ├─ 并发爬取选中的URL (timeout: 30s)
    │   └─ 失败时fallback到snippet
    │
    └─ 4. synthesize(question, content)
        └─ 生成结构化答案
```

## 性能目标

- **响应时间**: 30-60秒
- **成功率**: >90%
- **代码复杂度**: <500行核心代码
- **配置文件**: 0个（硬编码合理默认值）

## 实现计划

### 阶段1: 核心引擎
1. 创建 `FlashSearchEngine` 类
2. 实现 4个核心方法
3. 硬编码所有配置参数

### 阶段2: 基础测试
1. 创建简单的测试脚本
2. 验证基本功能正常
3. 测试snippet回退机制

### 阶段3: 性能优化
1. 调整超时和并发参数
2. 优化prompt效果
3. 确保目标响应时间

## 配置简化

所有配置直接硬编码在代码中，避免复杂的配置文件：

```python
# 搜索配置
SEARCH_RESULTS = 8
SELECT_URLS = 4
CRAWL_TIMEOUT = 30
PARALLEL_CRAWL = 3

# LLM配置  
SELECT_MODEL = "deepseek-chat"
SYNTHESIZE_MODEL = "deepseek-chat"
MAX_TOKENS = 2000
TEMPERATURE = 0.3
```

## 优势分析

1. **简单性**: 没有复杂的配置层和抽象
2. **可维护性**: 代码量减少70%以上
3. **性能**: 减少不必要的决策和配置开销
4. **可靠性**: 更少的失败点和依赖
5. **易理解**: 新开发者可以快速上手

这个设计将大幅简化当前的复杂架构，专注于快速、可靠的搜索体验。