# 🚀 FlashSearch API 架构流转图 - 2025-07-07

## 🎯 整体架构概览

```ascii
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               USER REQUEST                                     │
│                          ┌─────────────────────┐                              │
│                          │   HTTP API Call     │                              │
│                          │ /api/v1/search      │                              │
│                          │ /api/v1/search/stream│                             │
│                          └─────────┬───────────┘                              │
└──────────────────────────────────────┼─────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            API SERVER LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       main.py (FastAPI)                                │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │   │
│  │  │   Sync Route    │  │  Stream Route   │  │    Health Check         │  │   │
│  │  │ /api/v1/search  │  │ /api/v1/search/ │  │   /api/v1/health        │  │   │
│  │  │                 │  │     stream      │  │                         │  │   │
│  │  └─────────┬───────┘  └─────────┬───────┘  └─────────────────────────┘  │   │
│  └────────────┼─────────────────────┼──────────────────────────────────────┘   │
└───────────────┼─────────────────────┼────────────────────────────────────────────┘
                ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SEARCH ORCHESTRATION                                   │
│                      ┌─────────────────────────┐                              │
│                      │   DeepSearchFramework   │                              │
│                      │    (v1.2.1 → v1.3)     │                              │
│                      │                         │                              │
│                      │ ┌─────────────────────┐ │                              │
│                      │ │   Prompt Manager    │ │                              │
│                      │ │    System Prompt    │ │                              │
│                      │ │     v1.2.1/v1.3     │ │                              │
│                      │ └─────────────────────┘ │                              │
│                      │                         │                              │
│                      │ ┌─────────────────────┐ │                              │
│                      │ │   Search Strategy   │ │                              │
│                      │ │  Question Analysis  │ │                              │
│                      │ │ Domain Detection    │ │                              │
│                      │ │ Intent Recognition  │ │                              │
│                      │ └─────────────────────┘ │                              │
│                      └─────────┬───────────────┘                              │
└──────────────────────────────────┼─────────────────────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SEARCH STRATEGY LAYER                                     │
│        ┌─────────────────────────────────────────────────────────────────┐       │
│        │                  Agent-Driven Search Strategy                   │       │
│        │                                                                 │       │
│        │  User Query  →  LLM Agent  →  Optimized Query + SERP Params    │       │
│        │      ↓             ↓                      ↓                     │       │
│        │  ┌─────────┐  ┌─────────┐  ┌─────────────────────────────────┐  │       │
│        │  │ Domain  │  │ Intent  │  │         SERP Params             │  │       │
│        │  │Analysis │  │Analysis │  │                                 │  │       │
│        │  │         │  │         │  │ search_type: web/news/academic  │  │       │
│        │  │finance  │  │analysis │  │ date_range: d/w/m/y             │  │       │
│        │  │academic │  │trend    │  │ language: zh-CN/en              │  │       │
│        │  │tech     │  │how-to   │  │ country: cn/us                  │  │       │
│        │  │news     │  │         │  │ location: Beijing/China         │  │       │
│        │  │policy   │  │         │  │ num_results: 10-20              │  │       │
│        │  └─────────┘  └─────────┘  └─────────────────────────────────┘  │       │
│        └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────┼───────────────────────────────────────┘
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      S3 FRAMEWORK EXECUTION                                    │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │    🔍 SEARCH    │    │   📋 SELECT     │    │      ✨ SYNTHESIZE         │  │
│  │                 │    │                 │    │                             │  │
│  │ BrightData SERP │───▶│ S3-RAG-RL Agent │───▶│   DeepSeek Generation       │  │
│  │   + Strategy    │    │     (v5→v6)     │    │                             │  │
│  │                 │    │                 │    │                             │  │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────────────────┐ │  │
│  │ │Auto Params  │ │    │ │Doc Selection│ │    │ │  Context Integration    │ │  │
│  │ │tbm=nws/web  │ │    │ │Multi-round  │ │    │ │  Answer Generation      │ │  │
│  │ │tbs=qdr:d/m  │ │    │ │Cumulative   │ │    │ │  Source Attribution     │ │  │
│  │ │hl=zh-CN     │ │    │ │Building     │ │    │ │  Quality Assurance      │ │  │
│  │ │gl=cn        │ │    │ │Quality Gate │ │    │ │                         │ │  │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────────────────┘ │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────────┘  │
│            │                       │                           │                │
│            ▼                       ▼                           ▼                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │Search Results   │    │Selected URLs    │    │  Final Answer               │  │
│  │+ Snippets       │    │for Crawling     │    │  + Sources                  │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────────┘  │
└─────────────────────────────────┼───────────────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONTENT CRAWLING LAYER                                  │
│                                                                                 │
│  ┌─────────────────────────┐         ┌─────────────────────────────────────┐   │
│  │      FireCrawl API      │         │           Fallback Strategy        │   │
│  │                         │         │                                     │   │
│  │ ┌─────────────────────┐ │   ⚠️   │ ┌─────────────────────────────────┐ │   │
│  │ │  Markdown Content   │ │  ───▶  │ │        Snippet Fallback        │ │   │
│  │ │  Full Page Crawl    │ │         │ │   Use SERP Snippets Only       │ │   │
│  │ │  Smart Extraction   │ │         │ │  When Crawling Fails            │ │   │
│  │ └─────────────────────┘ │         │ └─────────────────────────────────┘ │   │
│  └─────────────────────────┘         └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │  BrightData     │  │   FireCrawl     │  │        LiteLLM Client           │  │
│  │   SERP API      │  │   Crawl API     │  │                                 │  │
│  │                 │  │                 │  │  ┌─────────────────────────────┐│  │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │  │      Model Routing          ││  │
│  │ │ Enhanced    │ │  │ │ Markdown    │ │  │  │                             ││  │
│  │ │ Search with │ │  │ │ Extraction  │ │  │  │ DeepSeek-Chat: Generation   ││  │
│  │ │ Strategy    │ │  │ │ Concurrent  │ │  │  │ DeepSeek-Search: Selection  ││  │
│  │ │ Integration │ │  │ │ Processing  │ │  │  │ OpenAI GPT: Fallback        ││  │
│  │ └─────────────┘ │  │ └─────────────┘ │  │  └─────────────────────────────┘│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 搜索流程详细说明

### 1. **请求接收阶段**
```ascii
User Request
     ↓
┌─────────────────────────┐
│  FastAPI Router         │
│  - Validate Input       │
│  - Parse Parameters     │
│  - Route to Handler     │
└─────────────────────────┘
     ↓
┌─────────────────────────┐
│  Request Processing     │
│  - Extract Query        │
│  - Determine Mode       │
│  - Set Concurrency     │
└─────────────────────────┘
```

### 2. **智能搜索策略阶段**
```ascii
Original Query: "腾讯2024年第三季度财报分析"
     ↓
┌─────────────────────────────────────────────┐
│           LLM Agent Analysis                │
│  ┌─────────────────────────────────────────┐│
│  │ <thinking>                              ││
│  │ - Domain Analysis: 财经领域             ││
│  │ - Intent: 财务分析                      ││
│  │ - Temporal Context: 2024年特定季度      ││
│  │ - Search Strategy: 使用news search     ││
│  │ </thinking>                             ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────┐
│         Optimized Query + SERP Params      │
│  ┌─────────────────────────────────────────┐│
│  │ <query>{                                ││
│  │   "query": "腾讯2024年第三季度财报",    ││
│  │   "search_type": "news",                ││
│  │   "date_range": "y",                    ││
│  │   "language": "zh-CN",                  ││
│  │   "country": "cn"                       ││
│  │ }</query>                               ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### 3. **S3框架执行阶段**

#### 🔍 **SEARCH Phase**
```ascii
Optimized Query + SERP Params
     ↓
┌─────────────────────────────────────┐
│        BrightData SERP API          │
│                                     │
│  Parameters Applied:                │
│  - tbm=nws (news search)           │
│  - tbs=qdr:y (past year)           │
│  - hl=zh-CN&gl=cn (Chinese)        │
│  - num=10-20 (result count)        │
│                                     │
│  Returns: Search Results + Snippets │
└─────────────────────────────────────┘
     ↓
Search Results: [URL1, URL2, URL3, ...]
```

#### 📋 **SELECT Phase**
```ascii
Search Results
     ↓
┌─────────────────────────────────────┐
│      S3-RAG-RL Agent (v5→v6)       │
│                                     │
│  Multi-Round Selection Strategy:    │
│  ┌─────────────────────────────────┐│
│  │ Round 1: Broad Coverage         ││
│  │ - Select ALL relevant docs      ││
│  │ - No artificial limits          ││
│  │                                 ││
│  │ Round 2+: Fill Gaps             ││
│  │ - Identify missing info         ││
│  │ - Cumulative building           ││
│  │ - Quality threshold             ││
│  └─────────────────────────────────┘│
│                                     │
│  Output: <important_info>[1,3,5]    │
└─────────────────────────────────────┘
     ↓
Selected URLs for Crawling
```

#### 🕷️ **CRAWL Phase**
```ascii
Selected URLs
     ↓
┌─────────────────────────────────────┐
│         FireCrawl Processing        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Primary: FireCrawl API         ││
│  │  - Full page markdown           ││
│  │  - Smart content extraction     ││
│  │  - Concurrent processing        ││
│  │                                 ││
│  │  Fallback: SERP Snippets        ││
│  │  - Use when crawling fails      ││
│  │  - Maintain search continuity   ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
     ↓
Extracted Content + Metadata
```

#### ✨ **SYNTHESIZE Phase**
```ascii
Extracted Content
     ↓
┌─────────────────────────────────────┐
│       DeepSeek Generation           │
│                                     │
│  Context Integration:               │
│  - Combine all sources              │
│  - Maintain source attribution      │
│  - Apply quality assurance          │
│                                     │
│  Answer Generation:                 │
│  - Comprehensive response           │
│  - Structured formatting           │
│  - Source citations                 │
└─────────────────────────────────────┘
     ↓
Final Answer + Sources
```

## 🚀 搜索模式对比

### Flash Mode (2轮)
```ascii
用户查询 → 问题分解 → 并发搜索 → 快速合成
         (1轮拆分)   (2-3个子问题)   (30s内)
```

### Standard Mode (5轮)
```ascii
用户查询 → 深度分析 → 迭代搜索 → 全面合成
         (多轮优化)   (逐步深入)   (1-2分钟)
```

### Deep Mode (无限制)
```ascii
用户查询 → 穷尽搜索 → 专家级合成
         (直到完整)   (研究级质量)
```

## 🔧 当前版本状态

### ✅ 已优化组件
- **SearchStrategy**: 完整集成，支持领域检测和参数优化
- **BrightData Client**: 集成策略优化，支持SERP参数自动配置
- **S3框架**: 完整集成DeepSearch，支持并发搜索
- **API Routes**: 完整支持同步/流式搜索

### 🔄 待升级组件
- **Prompt版本**: v1.2.1 → v1.3 (获得最新搜索策略)
- **S3-RAG-RL**: v5 → v6 (更强文档选择能力)

### 📊 性能特征
- **搜索延迟**: 通常1-3秒获得搜索结果
- **爬取速度**: 并发处理，支持回退机制
- **准确性**: 基于领域检测的智能参数优化
- **可扩展性**: 模块化设计，支持新策略快速集成

---

## 🎯 架构优势总结

1. **一体化智能**: LLM驱动的搜索策略，避免硬编码规则
2. **参数自适应**: 基于问题分析自动优化SERP参数  
3. **多轮迭代**: S3框架支持逐步完善信息收集
4. **容错机制**: 完善的回退策略确保服务稳定性
5. **可解释性**: 完整的推理过程可追踪和调试

这个架构实现了从**传统关键词搜索**到**智能语义搜索**的根本性升级！🚀