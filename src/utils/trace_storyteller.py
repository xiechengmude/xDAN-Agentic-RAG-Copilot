"""
追踪故事书生成器 - 将追踪数据转换为易读的故事
实现可视化的执行过程叙述
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class TraceStoryteller:
    """将追踪数据转换为故事形式"""
    
    def __init__(self):
        self.story_template = {
            "search": {
                "start": "🔍 开始搜索知识库...",
                "iteration": "📚 第{iteration}次搜索，查询: '{query}'",
                "found": "✅ 找到 {count} 个相关文档",
                "complete": "🎯 搜索完成，共进行了 {iterations} 次迭代，耗时 {duration:.2f}秒"
            },
            "select": {
                "start": "🤔 AI智能体开始分析文档...",
                "thinking": "💭 评估信息是否充分回答问题",
                "decision": "📋 决策: {action} - 选择了 {count} 个最相关的文档",
                "complete": "✨ 文档筛选完成，耗时 {duration:.2f}秒"
            },
            "synthesize": {
                "start": "✍️ 开始生成答案...",
                "model": "🤖 使用模型: {model}",
                "streaming": "📡 流式传输响应中...",
                "complete": "📝 答案生成完成，共 {tokens} tokens，耗时 {duration:.2f}秒"
            }
        }
    
    def generate_story(self, trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成追踪故事
        
        Returns:
            故事事件列表，每个事件包含时间戳、图标、描述等
        """
        story = []
        metadata = trace_data.get('metadata', {})
        
        # 开篇
        story.append({
            "timestamp": metadata.get('start_time'),
            "icon": "🚀",
            "title": "查询开始",
            "description": f"用户提问: {metadata.get('question', 'N/A')}",
            "level": "info"
        })
        
        # 各阶段故事
        phases = metadata.get('phases', {})
        
        # Search阶段
        if 'search' in phases:
            story.extend(self._generate_search_story(phases['search'], metadata))
        
        # Select阶段
        if 'select' in phases:
            story.extend(self._generate_select_story(phases['select'], metadata))
        
        # Synthesize阶段
        if 'synthesize' in phases:
            story.extend(self._generate_synthesize_story(phases['synthesize'], metadata))
        
        # 结尾
        story.append({
            "timestamp": metadata.get('end_time'),
            "icon": "🎉",
            "title": "查询完成",
            "description": f"总耗时: {metadata.get('total_duration', 0):.2f}秒, "
                          f"总成本: ${metadata.get('accumulated_cost', 0):.4f}",
            "level": "success" if metadata.get('final_status') == 'success' else "error"
        })
        
        return story
    
    def _generate_search_story(self, phase_data: Dict, metadata: Dict) -> List[Dict]:
        """生成搜索阶段的故事"""
        events = []
        
        # 搜索开始
        events.append({
            "icon": "🔍",
            "title": "搜索阶段",
            "description": self.story_template["search"]["start"],
            "level": "info"
        })
        
        # 每次迭代
        iterations = metadata.get('search_iterations', [])
        for iter_data in iterations:
            events.append({
                "icon": "📚",
                "title": f"第 {iter_data['iteration']} 次搜索",
                "description": self.story_template["search"]["iteration"].format(
                    iteration=iter_data['iteration'],
                    query=iter_data['query']
                ),
                "level": "info",
                "details": {
                    "结果数": iter_data['results_count'],
                    "耗时": f"{iter_data['duration']:.2f}秒"
                }
            })
        
        # 搜索完成
        events.append({
            "icon": "🎯",
            "title": "搜索完成",
            "description": self.story_template["search"]["complete"].format(
                iterations=len(iterations),
                duration=phase_data.get('duration', 0)
            ),
            "level": "success" if phase_data.get('status') == 'success' else "warning"
        })
        
        return events
    
    def _generate_select_story(self, phase_data: Dict, metadata: Dict) -> List[Dict]:
        """生成选择阶段的故事"""
        events = []
        
        agent_decision = metadata.get('agent_decision', {})
        
        events.extend([
            {
                "icon": "🤔",
                "title": "文档筛选",
                "description": self.story_template["select"]["start"],
                "level": "info"
            },
            {
                "icon": "💭",
                "title": "AI分析中",
                "description": self.story_template["select"]["thinking"],
                "level": "info",
                "details": {
                    "使用模型": metadata.get('select_model', 'xdan-r2-qwen3'),
                    "温度": "0.1 (确保稳定性)"
                }
            },
            {
                "icon": "📋",
                "title": "筛选结果",
                "description": self.story_template["select"]["decision"].format(
                    action=agent_decision.get('action', 'sufficient'),
                    count=agent_decision.get('selected_count', 0)
                ),
                "level": "success",
                "details": {
                    "决策理由": agent_decision.get('reasoning', '信息充分')
                }
            }
        ])
        
        return events
    
    def _generate_synthesize_story(self, phase_data: Dict, metadata: Dict) -> List[Dict]:
        """生成合成阶段的故事"""
        events = []
        
        events.extend([
            {
                "icon": "✍️",
                "title": "答案生成",
                "description": self.story_template["synthesize"]["start"],
                "level": "info"
            },
            {
                "icon": "🤖",
                "title": "模型工作中",
                "description": self.story_template["synthesize"]["model"].format(
                    model=metadata.get('synthesize_model', 'deepseek-chat')
                ),
                "level": "info",
                "details": {
                    "Token使用": metadata.get('synthesize_tokens', 0),
                    "成本": f"${metadata.get('synthesize_cost', 0):.4f}"
                }
            }
        ])
        
        if metadata.get('synthesize_stream'):
            events.append({
                "icon": "📡",
                "title": "流式输出",
                "description": self.story_template["synthesize"]["streaming"],
                "level": "info"
            })
        
        events.append({
            "icon": "📝",
            "title": "生成完成",
            "description": self.story_template["synthesize"]["complete"].format(
                tokens=metadata.get('synthesize_tokens', 0),
                duration=phase_data.get('duration', 0)
            ),
            "level": "success"
        })
        
        return events
    
    def format_as_markdown(self, story: List[Dict[str, Any]]) -> str:
        """将故事格式化为Markdown"""
        lines = ["# 🎯 查询执行故事\n"]
        
        for event in story:
            # 标题行
            lines.append(f"## {event['icon']} {event['title']}")
            
            # 描述
            lines.append(f"\n{event['description']}\n")
            
            # 详细信息
            if 'details' in event:
                lines.append("**详细信息:**")
                for key, value in event['details'].items():
                    lines.append(f"- {key}: {value}")
                lines.append("")
            
            # 分隔线
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def format_as_timeline(self, story: List[Dict[str, Any]]) -> str:
        """将故事格式化为时间线"""
        lines = ["```mermaid", "timeline", "    title RAG查询执行时间线\n"]
        
        for event in story:
            # 简化描述用于时间线
            desc = event['description'].replace('"', "'")
            lines.append(f"    {event['icon']} : {desc}")
        
        lines.append("```")
        return "\n".join(lines)


# 使用示例
def create_trace_story(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建追踪故事
    
    Args:
        trace_data: Langfuse追踪数据
        
    Returns:
        包含多种格式故事的字典
    """
    storyteller = TraceStoryteller()
    
    # 生成故事事件
    story_events = storyteller.generate_story(trace_data)
    
    # 生成不同格式
    return {
        "events": story_events,
        "markdown": storyteller.format_as_markdown(story_events),
        "timeline": storyteller.format_as_timeline(story_events),
        "summary": {
            "total_events": len(story_events),
            "success": all(e.get('level') != 'error' for e in story_events),
            "duration": trace_data['metadata'].get('total_duration', 0),
            "cost": trace_data['metadata'].get('accumulated_cost', 0)
        }
    }


# 模拟数据示例
if __name__ == "__main__":
    # 模拟追踪数据
    sample_trace = {
        "trace_id": "abc-123",
        "metadata": {
            "question": "什么是RAG技术？",
            "start_time": 1234567890,
            "end_time": 1234567895,
            "total_duration": 5.2,
            "accumulated_cost": 0.0215,
            "final_status": "success",
            "search_iterations": [
                {"iteration": 1, "query": "RAG技术", "results_count": 5, "duration": 1.2},
                {"iteration": 2, "query": "Retrieval Augmented Generation", "results_count": 3, "duration": 0.8}
            ],
            "agent_decision": {
                "action": "sufficient",
                "selected_count": 3,
                "reasoning": "找到了关于RAG技术的详细解释"
            },
            "select_model": "xdan-r2-qwen3",
            "synthesize_model": "deepseek-chat",
            "synthesize_tokens": 1200,
            "synthesize_cost": 0.012,
            "phases": {
                "search": {"duration": 2.1, "status": "success"},
                "select": {"duration": 0.8, "status": "success"},
                "synthesize": {"duration": 2.3, "status": "success"}
            }
        }
    }
    
    # 生成故事
    story = create_trace_story(sample_trace)
    print(story["markdown"])