# DeepSearch架构分析报告

## 1. Agent数量和协作模式分析

### 1.1 当前架构中的Agent/Model数量

基于对`deepsearch_framework.py`的分析，系统中实际使用的Agent/Model数量为：

1. **SearchModel Agent** - 用于搜索策略制定和信息源评估
   - 在`select_phase`中使用（评估和选择URL）
   - 在`extract_important_content_with_task_focus`中使用（内容提取）
   - 在`plan_search_strategy`中使用（制定搜索策略）
   - 在`_analyze_question_intent`中使用（问题分析）

2. **Generation Model (deepseek-chat)** - 用于最终答案生成
   - 在`synthesize_phase_with_structured_output`中使用

**结论**：架构中实际只有2个模型在工作，而不是3个独立的agent。

### 1.2 协作模式分析

当前的协作模式是**串行流水线模式**：

```
用户问题 → SearchModel(策略制定) → SERP搜索 → SearchModel(评估选择) 
    → FireCrawl爬取 → SearchModel(内容提取) → Generation Model(答案生成)
```

特点：
- SearchModel承担了多个角色（策略制定、评估、提取）
- 没有真正的多Agent并行协作
- 是一个单线程的串行处理流程

### 1.3 版本演进中的变化

- **v1.0**: 简单的搜索智能体，功能单一
- **v1.1**: 增强了搜索策略和领域知识
- **v1.2**: 
  - 引入了`searchmodel_system.txt`，明确定义SearchModel的角色
  - 但架构上没有增加新的agent，只是强化了SearchModel的职责

## 2. Prompt版本兼容性检查

### 2.1 版本管理机制

`prompt_manager.py`实现了完善的版本管理：

1. **版本目录结构**：
   ```
   prompts/deepsearch/versions/
   ├── v1.0/
   ├── v1.1/
   └── v1.2/
   ```

2. **核心功能**：
   - 动态加载指定版本的prompt文件
   - 支持热重载（`reload_cache`）
   - 版本切换（`switch_version`）
   - 自动回退机制（版本不存在时回退到v1.0）
   - 硬编码的fallback prompts

3. **兼容性保证**：
   - 所有版本都保持相同的prompt文件命名
   - 使用相同的参数替换机制
   - 向后兼容的设计

### 2.2 版本切换和回退机制

1. **初始化时版本验证**：
   ```python
   if not self.version_path.exists():
       logger.warning(f"版本 {version} 不存在，回退到 v1.0")
       self.version = "v1.0"
   ```

2. **运行时版本切换**：
   - `switch_version()`方法支持动态切换
   - 切换失败时保持原版本
   - 自动清理缓存

3. **Fallback机制**：
   - 文件不存在时使用硬编码的默认prompt
   - 确保系统在任何情况下都能运行

## 3. v1.2中需要整合的Prompt分析

### 3.1 v1.2目录下的所有prompt文件

1. **agent_system.txt** - Agent的通用系统提示
2. **agent_system_improved.txt** - Agent系统提示的改进版
3. **content_extraction.txt** - 内容提取提示
4. **question_analysis.txt** - 问题分析提示
5. **searchmodel_system.txt** - SearchModel专用系统提示（新增）
6. **select_evaluation.txt** - 选择评估提示
7. **synthesize_system.txt** - 答案合成系统提示

### 3.2 重复和可整合的Prompt分析

#### 3.2.1 agent_system.txt vs agent_system_improved.txt

**相同点**：
- 完全相同的内容（通过diff确认）
- 都是v1.2版本的Agent系统提示
- 都强调了"ADAPTIVE SEARCH STRATEGY"和"OPTIONAL DOMAIN GUIDANCE"

**建议**：
- 删除`agent_system_improved.txt`，只保留`agent_system.txt`
- 避免维护两份相同的文件

#### 3.2.2 agent_system.txt vs searchmodel_system.txt

**差异分析**：
- `agent_system.txt`：通用的搜索智能体提示，偏重搜索技巧
- `searchmodel_system.txt`：专门为SearchModel设计，强调：
  - 搜索策略制定能力
  - 信息源智能评估
  - 迭代搜索决策
  - 主动性和创新性

**整合建议**：
- 保持两者分离，它们服务于不同的用途
- `agent_system.txt`用于初始策略制定
- `searchmodel_system.txt`用于Select阶段的评估

### 3.3 v1.2优化建议

1. **删除重复文件**：
   - 删除`agent_system_improved.txt`

2. **明确prompt用途**：
   - 在文件头部添加注释，说明每个prompt的具体使用场景
   - 建立prompt使用映射文档

3. **优化prompt调用**：
   - 在代码中明确使用`searchmodel_system`而不是`agent_system`
   - 确保每个阶段使用正确的prompt

4. **版本迭代规范**：
   - 新版本应该清理冗余文件
   - 保持文件命名的一致性和清晰性

## 4. 总结和建议

### 4.1 架构现状

1. **实际是2个模型的系统**，不是3个agent
2. SearchModel承担了过多职责（策略、评估、提取）
3. 协作模式是串行的，没有并行处理

### 4.2 改进建议

1. **明确模型职责**：
   - 考虑真正实现3个独立的agent
   - 或者明确当前是"一个SearchModel多角色"的设计

2. **优化v1.2 prompts**：
   - 删除`agent_system_improved.txt`
   - 在代码中正确使用`searchmodel_system`
   - 建立prompt使用指南

3. **版本管理优化**：
   - 添加版本变更日志
   - 记录每个版本的主要改进
   - 建立prompt A/B测试机制

4. **性能优化方向**：
   - 考虑某些阶段的并行处理（如多URL并行爬取已实现）
   - 优化prompt以减少token使用
   - 实现更智能的搜索终止条件