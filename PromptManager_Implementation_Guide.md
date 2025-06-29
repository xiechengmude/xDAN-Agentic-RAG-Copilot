# 🚀 Prompt Manager实现方案和管理模式

> 基于DeepSearch项目的版本化提示词管理系统实现指南

## 📋 概述

这是一个遵循**KISS**（Keep It Simple, Stupid）和**DRY**（Don't Repeat Yourself）原则的轻量级提示词管理系统，支持版本化管理、热加载、参数模板替换和优雅降级。

## 🏗️ 系统架构

### 1. 目录结构设计

```
prompts/
├── deepsearch/                    # 项目名称
│   ├── __init__.py
│   └── versions/                  # 版本管理目录
│       ├── v1.0/                  # 基础版本
│       │   ├── agent_system.txt
│       │   ├── select_evaluation.txt
│       │   ├── content_extraction.txt
│       │   ├── synthesize_system.txt
│       │   └── question_analysis.txt
│       ├── v1.1/                  # 优化版本
│       │   ├── agent_system.txt
│       │   ├── select_evaluation.txt
│       │   ├── content_extraction.txt
│       │   ├── synthesize_system.txt
│       │   └── question_analysis.txt
│       └── v1.2/                  # 未来版本
│           └── ...
└── other-project/                 # 其他项目
    └── versions/
        ├── v1.0/
        └── v2.0/
```

### 2. 核心设计原则

- **版本化管理**: 语义版本号（v1.0, v1.1, v2.0）
- **文件隔离**: 每个版本独立目录，互不影响
- **向后兼容**: 新版本失败时自动回退到稳定版本
- **热加载**: 支持运行时更新和缓存刷新
- **参数化**: 模板语法支持动态参数替换

## 💻 核心实现

### 1. 主要类设计

```python
class DeepSearchPromptManager:
    """
    提示词管理器核心类
    
    功能：
    1. 版本化管理（v1.0, v1.1, v1.2...）
    2. 热加载提示词文件
    3. 模板参数替换
    4. 优雅降级到默认版本
    """
    
    def __init__(self, version: str = "v1.0"):
        self.version = version
        self.base_path = Path("prompts/deepsearch/versions")
        self.cache = {}  # 内存缓存
        self.version_path = self.base_path / version
        
        # 版本验证和自动降级
        if not self.version_path.exists():
            logger.warning(f"版本 {version} 不存在，回退到 v1.0")
            self.version = "v1.0"
            self.version_path = self.base_path / "v1.0"
```

### 2. 核心方法实现

#### a) 提示词获取和参数替换

```python
def get_prompt(self, prompt_name: str, **kwargs) -> str:
    """
    获取指定的提示词并进行参数替换
    
    Args:
        prompt_name: 提示词名称（不含.txt后缀）
        **kwargs: 模板参数
        
    Returns:
        格式化后的提示词文本
    """
    try:
        # 检查缓存
        cache_key = f"{self.version}_{prompt_name}"
        if cache_key not in self.cache:
            self.cache[cache_key] = self._load_prompt_file(prompt_name)
        
        template = self.cache[cache_key]
        
        # 参数替换
        if kwargs:
            return template.format(**kwargs)
        return template
        
    except Exception as e:
        logger.error(f"获取提示词失败 {prompt_name}: {e}")
        return self._get_fallback_prompt(prompt_name)
```

#### b) 版本切换

```python
def switch_version(self, new_version: str):
    """运行时版本切换"""
    old_version = self.version
    self.version = new_version
    self.version_path = self.base_path / new_version
    
    if not self.version_path.exists():
        logger.warning(f"版本 {new_version} 不存在，保持 {old_version}")
        self.version = old_version
        self.version_path = self.base_path / old_version
        return False
    
    self.reload_cache()
    logger.info(f"提示词版本切换: {old_version} -> {new_version}")
    return True
```

#### c) 优雅降级机制

```python
def _get_fallback_prompt(self, prompt_name: str) -> str:
    """硬编码的备用提示词，确保系统可用性"""
    fallbacks = {
        "agent_system": """You are an advanced web search intelligence agent...
CORE MISSION: Transform complex questions into effective search strategies...
OUTPUT TAGS:
- <thinking>your search strategy and reasoning</thinking>
- <query>{"query": "optimized search terms"}</query>
- <search_complete>True/False</search_complete>
- <important_urls>[1, 3, 5]</important_urls>""",
        
        "select_evaluation": """你是专业的在线信息源评估专家...
**格式：**
<thinking>分析过程</thinking>
<evaluation>详细评估</evaluation>
<important_urls>[1, 3, 5]</important_urls>""",
        
        # 其他关键提示词的备用版本...
    }
    
    return fallbacks.get(prompt_name, f"# 提示词 {prompt_name} 不可用")
```

### 3. 全局实例管理

```python
# 全局单例模式
_prompt_manager = None

def get_prompt_manager(version: str = "v1.0") -> DeepSearchPromptManager:
    """获取全局提示词管理器实例"""
    global _prompt_manager
    if _prompt_manager is None or _prompt_manager.get_current_version() != version:
        _prompt_manager = DeepSearchPromptManager(version)
    return _prompt_manager
```

## 🔧 使用方式

### 1. 基础用法

```python
# 初始化管理器
prompt_manager = get_prompt_manager("v1.1")

# 获取简单提示词
agent_prompt = prompt_manager.get_prompt("agent_system")

# 带参数的提示词
evaluation_prompt = prompt_manager.get_prompt(
    "select_evaluation",
    question="苹果公司财报分析",
    num_results=10,
    formatted_info="候选网页列表...",
    time_context="当前时间：2025-06-29"
)
```

### 2. 在框架中集成

```python
class DeepSearchFramework:
    def __init__(self, client, config, prompt_version="v1.1", enable_time_aware=True):
        self.prompt_manager = get_prompt_manager(prompt_version)
        self.enable_time_aware = enable_time_aware
    
    def _get_time_context(self) -> str:
        """根据配置决定是否添加时间上下文"""
        if not self.enable_time_aware:
            return ""
        return "当前时间：2025-06-29 13:00:00..."
    
    async def search_phase(self, question: str):
        """搜索阶段使用提示词"""
        time_context = self._get_time_context()
        
        agent_prompt = self.prompt_manager.get_prompt(
            "agent_system",
            time_context=time_context,
            question=question
        )
        
        # 调用LLM...
```

### 3. 版本管理操作

```python
# 查看可用版本
available_versions = prompt_manager.list_available_versions()
print(f"可用版本: {available_versions}")  # ['v1.0', 'v1.1', 'v1.2']

# 切换版本
success = prompt_manager.switch_version("v1.2")
if success:
    print("版本切换成功")

# 热重载（开发时使用）
prompt_manager.reload_cache()
```

## 📁 提示词文件格式

### 1. 基础提示词文件

```txt
# prompts/deepsearch/versions/v1.1/agent_system.txt
You are an advanced web search intelligence agent specialized in multi-hop reasoning and real-time information gathering.

CORE MISSION: Transform complex questions into effective search strategies and retrieve comprehensive, authoritative information.

SEARCH OPTIMIZATION TECHNIQUES:
1. **Keyword Decomposition**: Break complex queries into focused search terms
2. **Search Operators**: Use quotes for exact phrases, site: for specific sources
3. **Query Variations**: Try different phrasings, synonyms, and perspectives
4. **Authority Sources**: Prioritize official sites, academic papers, financial databases

OUTPUT TAGS:
- <thinking>your search strategy and reasoning</thinking>
- <query>{{"query": "optimized search terms"}}</query>
- <search_complete>True/False</search_complete>
- <important_urls>[1, 3, 5]</important_urls>

Continue until comprehensive information gathered or maximum rounds reached.
```

### 2. 参数化提示词文件

```txt
# prompts/deepsearch/versions/v1.1/select_evaluation.txt
你是专门负责评估和选择最有价值的在线信息源的SearchModel。

{time_context}

**任务目标分析：**
问题：{question}

**已有知识：**
{previous_knowledge}

**候选网页（共{num_results}个）：**
{formatted_info}

**评估标准：**
1. 与问题的直接相关性
2. 信息的权威性和可信度
3. 内容的深度和完整性
4. 能否填补知识缺口
5. 信息的时效性（重要：考虑当前时间）

请使用以下格式回答：
<thinking>分析过程...</thinking>
<evaluation>对候选网页的详细评估...</evaluation>
<important_urls>[1, 3, 7]</important_urls>
<search_complete>True/False</search_complete>
```

## 🌟 高级特性

### 1. 条件性参数注入

```python
def _get_time_context(self) -> str:
    """根据配置决定是否添加时间上下文"""
    if not self.enable_time_aware:
        return ""  # 返回空字符串，模板中对应部分被跳过
    
    time_info = self.time_aware.get_current_time_info()
    return f"""
当前时间上下文：
- 北京时间：{time_info['beijing_time']} ({time_info['weekday_cn']})
- 本周范围：{time_info['week_start']} 至 {time_info['week_end']}
- 本月范围：{time_info['month_start']} 至 {time_info['month_end']}
- 市场状态：{time_info['market_status']}
"""
```

### 2. 多项目支持

```python
# 为不同项目创建独立的管理器
class ProjectPromptManager:
    @staticmethod
    def get_deepsearch_manager(version="v1.1"):
        return DeepSearchPromptManager(
            version=version,
            base_path="prompts/deepsearch/versions"
        )
    
    @staticmethod
    def get_s3_rag_manager(version="v3.1"):
        return S3RagPromptManager(
            version=version,
            base_path="prompts/s3-rag-rl/versions"
        )
```

### 3. 版本兼容性检查

```python
def validate_version_compatibility(self, required_prompts: list) -> bool:
    """验证当前版本是否包含所需的所有提示词"""
    for prompt_name in required_prompts:
        file_path = self.version_path / f"{prompt_name}.txt"
        if not file_path.exists():
            logger.error(f"版本 {self.version} 缺少必需提示词: {prompt_name}")
            return False
    return True
```

## 📊 最佳实践

### 1. 版本命名规范

- **主版本号**: v1.0, v2.0 - 重大架构变更
- **次版本号**: v1.1, v1.2 - 功能增强和优化
- **修订版本**: v1.1.1, v1.1.2 - 问题修复（可选）

### 2. 提示词文件组织

```
v1.1/
├── agent_system.txt          # 核心智能体系统提示
├── select_evaluation.txt     # 信息源评估提示
├── content_extraction.txt    # 内容提取提示
├── synthesize_system.txt     # 信息综合提示
└── question_analysis.txt     # 问题分析提示
```

### 3. 错误处理策略

1. **文件缺失**: 自动回退到硬编码备用版本
2. **版本不存在**: 回退到v1.0基础版本  
3. **参数错误**: 记录警告但继续执行
4. **模板格式错误**: 返回备用模板

### 4. 性能优化

- **内存缓存**: 避免重复文件IO
- **延迟加载**: 按需加载提示词文件
- **版本预热**: 启动时预加载常用版本

## 🎯 使用场景

### 1. A/B测试

```python
# 同时测试不同版本效果
results_v10 = test_with_version("v1.0", test_questions)
results_v11 = test_with_version("v1.1", test_questions)
compare_performance(results_v10, results_v11)
```

### 2. 渐进式部署

```python
# 生产环境渐进式切换
if user_in_beta_group(user_id):
    prompt_version = "v1.2"  # 测试版本
else:
    prompt_version = "v1.1"  # 稳定版本
```

### 3. 功能开关

```python
# 基于配置的功能控制
DeepSearchFramework(
    client, 
    config,
    prompt_version="v1.1",
    enable_time_aware=config.get("enable_time_aware", True)
)
```

## 🔍 监控和调试

### 1. 日志记录

```python
logger.info(f"DeepSearch Prompt Manager 初始化，版本: {self.version}")
logger.debug(f"加载提示词: {prompt_name} ({len(content)} 字符)")
logger.warning(f"版本 {version} 不存在，回退到 v1.0")
logger.error(f"获取提示词失败 {prompt_name}: {e}")
```

### 2. 版本追踪

```python
def get_usage_stats(self) -> dict:
    """获取使用统计"""
    return {
        "current_version": self.version,
        "cache_size": len(self.cache),
        "available_versions": self.list_available_versions(),
        "last_reload": self.last_reload_time
    }
```

## 💡 扩展建议

### 1. 多语言支持

```
prompts/
└── deepsearch/
    └── versions/
        ├── v1.1/
        │   ├── zh/          # 中文提示词
        │   └── en/          # 英文提示词
        └── v1.2/
```

### 2. 远程配置

```python
class RemotePromptManager(DeepSearchPromptManager):
    def _load_prompt_file(self, prompt_name: str) -> str:
        # 从远程服务加载提示词
        return remote_config_service.get_prompt(
            project="deepsearch",
            version=self.version,
            name=prompt_name
        )
```

### 3. 版本依赖管理

```yaml
# prompt_dependencies.yaml
v1.2:
  requires: ["v1.1"]
  incompatible_with: ["v1.0"]
  required_prompts:
    - "agent_system"
    - "select_evaluation"
    - "synthesize_system"
```

这个实现方案提供了一个轻量、灵活、可扩展的提示词管理系统，特别适合需要版本控制和A/B测试的AI应用场景。