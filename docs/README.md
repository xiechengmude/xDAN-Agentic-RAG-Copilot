# 📚 DeepSearch 文档中心

## 📁 文档结构

```
docs/
├── README.md                 # 文档导航（本文件）
├── API文档/                  # API相关文档
│   └── README_API.md        # API服务器使用指南
├── 使用指南/                 # 用户使用指南
│   ├── SEARCH_MODES_GUIDE.md    # 搜索模式详解
│   └── V12_PROMPT_USAGE_GUIDE.md # V1.2版本使用指南
├── 技术文档/                 # 技术实现文档
│   ├── SEARCH_MODES_IMPLEMENTATION.md # 搜索模式实现细节
│   └── GLOBAL_TEST_ANALYSIS_REPORT.md  # 全局测试分析报告
├── 架构设计/                 # 系统架构文档
│   └── MULTI_ROUND_SEARCH_FLOW.md     # 多轮搜索流程设计
└── 测试优化/                 # 测试和优化相关
    └── DeepSearch测试检查清单.md       # 测试清单
```

## 🚀 快速开始

### 新用户推荐阅读顺序

1. **[搜索模式详解](使用指南/SEARCH_MODES_GUIDE.md)** - 了解Flash/Standard/Deep三种模式
2. **[API使用指南](API文档/README_API.md)** - 学习如何调用API
3. **[V1.2版本指南](使用指南/V12_PROMPT_USAGE_GUIDE.md)** - 了解最新版本特性

### 开发者推荐阅读

1. **[搜索模式实现](技术文档/SEARCH_MODES_IMPLEMENTATION.md)** - 代码和Prompt层面的实现细节
2. **[多轮搜索流程](架构设计/MULTI_ROUND_SEARCH_FLOW.md)** - 理解搜索传递机制
3. **[全局测试报告](技术文档/GLOBAL_TEST_ANALYSIS_REPORT.md)** - 性能和质量分析

## 📖 文档索引

### API文档
- [API接口设计文档](API文档/API_INTERFACE_DESIGN.md) - RESTful API接口详细说明
- [API调用示例](API文档/API_EXAMPLES.md) - 各种语言的调用示例和最佳实践
- [API部署文档](API文档/API_DEPLOYMENT.md) - 服务器部署、配置和维护指南

### 使用指南
- [搜索模式详解](使用指南/SEARCH_MODES_GUIDE.md) - Flash/Standard/Deep模式完整介绍
- [V1.2版本使用指南](使用指南/V12_PROMPT_USAGE_GUIDE.md) - 最新版本特性和使用方法

### 技术文档
- [搜索模式实现细节](技术文档/SEARCH_MODES_IMPLEMENTATION.md) - 代码和Prompt层面的差异分析
- [全局测试分析报告](技术文档/GLOBAL_TEST_ANALYSIS_REPORT.md) - 三版本性能对比

### 架构设计
- [多轮搜索流程设计](架构设计/MULTI_ROUND_SEARCH_FLOW.md) - 搜索传递和决策机制

### 测试优化
- [DeepSearch测试检查清单](测试优化/DeepSearch测试检查清单.md) - 测试要点和检查项

## 🔍 主题导航

### 搜索模式相关
- 模式介绍：[搜索模式详解](使用指南/SEARCH_MODES_GUIDE.md)
- 实现细节：[搜索模式实现](技术文档/SEARCH_MODES_IMPLEMENTATION.md)

### API相关
- 接口设计：[API接口设计文档](API文档/API_INTERFACE_DESIGN.md)
- 调用示例：[API调用示例](API文档/API_EXAMPLES.md)
- 部署指南：[API部署文档](API文档/API_DEPLOYMENT.md)

### 架构相关
- 搜索流程：[多轮搜索流程设计](架构设计/MULTI_ROUND_SEARCH_FLOW.md)
- 系统设计：见架构设计目录

## 💡 贡献指南

欢迎贡献文档！请遵循以下规范：

1. **文件命名**：使用大写字母和下划线，如 `SEARCH_MODES_GUIDE.md`
2. **文档结构**：包含目录、概述、详细内容、示例
3. **放置位置**：根据内容类型放到相应子目录
4. **更新索引**：修改本README.md添加新文档链接

## 📞 获取帮助

- 技术问题：查看技术文档目录
- 使用问题：查看使用指南目录
- API问题：查看API文档目录

---
*最后更新：2024-06-30*