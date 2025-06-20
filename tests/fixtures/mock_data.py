#!/usr/bin/env python3
"""
Mock数据集合
提供测试用的mock数据
"""

# ==================== 文档和Chunk数据 ====================

MOCK_DOCUMENTS = {
    'python_basics': {
        'id': 'doc_python_001',
        'name': 'Python基础教程',
        'chunks': [
            {
                'id': 'chunk_py_001',
                'content': 'Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。它由Guido van Rossum于1989年发明，第一个公开发行版发行于1991年。',
                'similarity': 0.95
            },
            {
                'id': 'chunk_py_002',
                'content': 'Python的设计哲学强调代码的可读性，使用空格缩进来定义代码块，而不是使用大括号或关键词。',
                'similarity': 0.92
            },
            {
                'id': 'chunk_py_003',
                'content': 'Python支持多种编程范式，包括面向过程、面向对象和函数式编程。它具有动态类型系统和自动内存管理。',
                'similarity': 0.89
            }
        ]
    },
    'python_advanced': {
        'id': 'doc_python_002',
        'name': 'Python高级特性',
        'chunks': [
            {
                'id': 'chunk_py_adv_001',
                'content': '装饰器是Python的一个重要特性，它允许在不修改原函数代码的情况下，为函数添加新的功能。',
                'similarity': 0.93
            },
            {
                'id': 'chunk_py_adv_002',
                'content': '生成器是Python中用于创建迭代器的简单而强大的工具。它们使用yield语句返回数据。',
                'similarity': 0.91
            },
            {
                'id': 'chunk_py_adv_003',
                'content': '元类是创建类的类。Python中的type就是一个元类，所有的类都是type的实例。',
                'similarity': 0.88
            }
        ]
    },
    'ml_basics': {
        'id': 'doc_ml_001',
        'name': '机器学习基础',
        'chunks': [
            {
                'id': 'chunk_ml_001',
                'content': '机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习和改进，而无需明确编程。',
                'similarity': 0.94
            },
            {
                'id': 'chunk_ml_002',
                'content': '监督学习是机器学习的一种方法，其中模型从标记的训练数据中学习，然后对新数据进行预测。',
                'similarity': 0.90
            },
            {
                'id': 'chunk_ml_003',
                'content': '深度学习是机器学习的一个子集，它使用多层神经网络来学习数据的复杂模式。',
                'similarity': 0.87
            }
        ]
    }
}

# ==================== Agent响应模板 ====================

AGENT_RESPONSES = {
    'single_round_complete': """
<think>我已经找到了关于Python的相关信息，这些信息足够回答用户的问题。</think>
<important_info>[1, 2]</important_info>
<search_complete>True</search_complete>
""",
    
    'need_more_info': """
<think>初始搜索结果不够详细，我需要搜索更多关于Python高级特性的信息。</think>
<query>{"question": "Python decorators generators metaclasses advanced features"}</query>
<important_info>[1]</important_info>
<search_complete>False</search_complete>
""",
    
    'second_round_complete': """
<think>现在我有了足够的信息，包括基础知识和高级特性。</think>
<important_info>[1, 3, 4]</important_info>
<search_complete>True</search_complete>
""",
    
    'no_relevant_info': """
<think>搜索结果中没有找到相关信息，需要尝试不同的搜索策略。</think>
<query>{"question": "alternative search query"}</query>
<search_complete>False</search_complete>
""",
    
    'error_response': """
<think>搜索过程中出现了问题</think>
Invalid response format
"""
}

# ==================== LLM响应模板 ====================

LLM_RESPONSES = {
    'python_intro': """
Python是一种高级编程语言，具有以下特点：

1. **简单易学**：Python的语法清晰简洁，适合初学者入门。
2. **功能强大**：支持面向对象、函数式等多种编程范式。
3. **丰富的库**：拥有庞大的标准库和第三方库生态系统。
4. **跨平台**：可在Windows、Linux、Mac等多个平台运行。
5. **应用广泛**：用于Web开发、数据科学、人工智能等领域。

Python由Guido van Rossum创建，因其简洁性和强大功能而广受欢迎。
""",
    
    'ml_explanation': """
机器学习是人工智能的核心技术之一，它使计算机能够从数据中学习规律并做出预测或决策。

主要类型包括：
- **监督学习**：使用标记数据训练模型
- **无监督学习**：发现数据中的隐藏模式
- **强化学习**：通过与环境交互学习最优策略

机器学习在图像识别、自然语言处理、推荐系统等领域有广泛应用。
""",
    
    'short_answer': "Python是一种高级编程语言，以简洁易读的语法著称。",
    
    'error_message': "抱歉，我无法生成答案，请稍后重试。"
}

# ==================== 测试配置数据 ====================

TEST_CONFIGS = {
    'default': {
        'ragflow_api_url': 'http://localhost:7080',
        'ragflow_api_key': 'test-key-123',
        'llm_api_url': 'http://localhost:8000/v1',
        'llm_model': 'test-model',
        'default_dataset': 'test-dataset',
        'max_search_rounds': 3,
        'top_k': 5,
        'similarity_threshold': 0.8
    },
    'production': {
        'ragflow_api_url': 'http://api.ragflow.com:7080',
        'ragflow_api_key': 'prod-key-456',
        'llm_api_url': 'http://llm.api.com/v1',
        'llm_model': 'gpt-4',
        'default_dataset': 'prod-dataset',
        'max_search_rounds': 5,
        'top_k': 10,
        'similarity_threshold': 0.85
    }
}

# ==================== 错误场景数据 ====================

ERROR_SCENARIOS = {
    'api_timeout': {
        'error_type': 'TimeoutError',
        'message': 'API request timed out after 30 seconds',
        'code': 504
    },
    'auth_failed': {
        'error_type': 'AuthenticationError',
        'message': 'Invalid API key provided',
        'code': 401
    },
    'rate_limit': {
        'error_type': 'RateLimitError',
        'message': 'Rate limit exceeded. Please try again later.',
        'code': 429
    },
    'server_error': {
        'error_type': 'ServerError',
        'message': 'Internal server error',
        'code': 500
    },
    'invalid_request': {
        'error_type': 'ValidationError',
        'message': 'Invalid request parameters',
        'code': 400
    }
}

# ==================== Session对话历史 ====================

SESSION_HISTORIES = {
    'python_conversation': [
        {
            'role': 'user',
            'content': 'What is Python?'
        },
        {
            'role': 'assistant',
            'content': 'Python is a high-level, interpreted programming language...'
        },
        {
            'role': 'user',
            'content': 'What are its main features?'
        },
        {
            'role': 'assistant',
            'content': 'Python has several key features including...'
        }
    ],
    'ml_conversation': [
        {
            'role': 'user',
            'content': 'Explain machine learning'
        },
        {
            'role': 'assistant',
            'content': 'Machine learning is a subset of artificial intelligence...'
        }
    ]
}

# ==================== 数据生成函数 ====================

def generate_chunks(count=10, base_similarity=0.9):
    """生成指定数量的mock chunks"""
    chunks = []
    for i in range(count):
        chunk = {
            'id': f'chunk_{i:03d}',
            'content': f'This is test content for chunk {i}. ' * 5,
            'document_id': f'doc_{i // 3:03d}',
            'dataset_id': 'test_dataset',
            'similarity': base_similarity - (i * 0.01),
            'metadata': {
                'source': f'document_{i // 3}.pdf',
                'page': (i % 3) + 1,
                'timestamp': '2024-01-20T12:00:00Z'
            }
        }
        chunks.append(chunk)
    return chunks


def generate_agent_response(search_complete=True, important_docs=None, next_query=None):
    """生成Agent响应"""
    parts = ['<think>Analyzing the search results</think>']
    
    if next_query:
        parts.append(f'<query>{{"question": "{next_query}"}}</query>')
    
    if important_docs:
        docs_str = ', '.join(str(d) for d in important_docs)
        parts.append(f'<important_info>[{docs_str}]</important_info>')
    
    parts.append(f'<search_complete>{str(search_complete)}</search_complete>')
    
    return '\n'.join(parts)


def generate_error_response(error_type='generic', status_code=500):
    """生成错误响应"""
    return {
        'code': status_code,
        'message': ERROR_SCENARIOS.get(error_type, {}).get('message', 'Unknown error'),
        'error_type': error_type,
        'timestamp': '2024-01-20T12:00:00Z'
    }