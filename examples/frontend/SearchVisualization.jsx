import React, { useState, useEffect, useRef } from 'react';
import './SearchVisualization.css';

// 事件类型映射
const EVENT_TYPE_NAMES = {
  'search_start': '🚀 搜索开始',
  'search_round_start': '🔍 开始新一轮搜索',
  'documents_retrieved': '📄 文档检索完成',
  'agent_thinking': '🤔 智能体思考中',
  'agent_decision': '💡 智能体决策',
  'new_query_generated': '✨ 生成新查询',
  'documents_selected': '✅ 选中文档',
  'search_complete': '🎯 搜索完成',
  'answer_generation_start': '✍️ 开始生成答案',
  'answer_generated': '📝 答案生成完成',
  'error': '❌ 错误'
};

// 事件组件
const EventCard = ({ event, isSelected, onClick }) => {
  const getEventSummary = () => {
    switch (event.event_type) {
      case 'search_start':
        return `问题: ${event.data.question}`;
      case 'search_round_start':
        return `查询: ${event.data.query}`;
      case 'documents_retrieved':
        return `检索到 ${event.data.count} 个文档`;
      case 'agent_thinking':
        return event.data.message;
      case 'agent_decision':
        return event.data.decision;
      case 'new_query_generated':
        return `新查询: ${event.data.new_query}`;
      case 'documents_selected':
        return `选中 ${event.data.selected_count} 个文档`;
      case 'search_complete':
        return `完成 ${event.data.total_rounds} 轮搜索`;
      case 'answer_generated':
        return '答案已生成';
      case 'error':
        return event.data.message;
      default:
        return JSON.stringify(event.data);
    }
  };

  return (
    <div 
      className={`event-card ${event.event_type} ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="event-header">
        <span className="event-type">
          {EVENT_TYPE_NAMES[event.event_type] || event.event_type}
        </span>
        {event.round && (
          <span className="event-round">第{event.round}轮</span>
        )}
      </div>
      <div className="event-time">
        {new Date(event.timestamp).toLocaleTimeString()}
      </div>
      <div className="event-content">{getEventSummary()}</div>
    </div>
  );
};

// 详情面板组件
const EventDetails = ({ event }) => {
  if (!event) {
    return (
      <div className="empty-state">
        <p>请选择一个事件查看详情</p>
      </div>
    );
  }

  const renderDetails = () => {
    switch (event.event_type) {
      case 'search_start':
        return (
          <>
            <p><strong>问题:</strong> {event.data.question}</p>
            <div className="config-info">
              <h5>配置信息:</h5>
              <ul>
                <li>最大轮数: {event.data.config.max_rounds}</li>
                <li>返回文档数: {event.data.config.top_k}</li>
                <li>相似度阈值: {event.data.config.similarity_threshold}</li>
                <li>搜索模型: {event.data.config.search_model}</li>
                <li>生成模型: {event.data.config.generator_model}</li>
              </ul>
            </div>
          </>
        );
      
      case 'agent_decision':
        return (
          <>
            {event.data.thinking && (
              <div className="thinking-box">
                <strong>智能体思考过程:</strong>
                <p>{event.data.thinking}</p>
              </div>
            )}
            <p><strong>决策:</strong> {event.data.decision}</p>
          </>
        );
      
      case 'documents_retrieved':
        return (
          <>
            <p><strong>检索到 {event.data.count} 个文档</strong></p>
            {event.data.documents && event.data.documents.length > 0 && (
              <div className="documents-list">
                {event.data.documents.map((doc, idx) => (
                  <div key={idx} className="document-item">
                    <span className="similarity-score">
                      {(doc.similarity * 100).toFixed(1)}%
                    </span>
                    文档{doc.id}: {doc.content_preview}
                  </div>
                ))}
              </div>
            )}
          </>
        );
      
      case 'answer_generated':
        return (
          <div className="answer-section">
            <h4>生成的答案:</h4>
            <div className="answer-content">
              {event.data.answer.split('\n').map((line, idx) => (
                <p key={idx}>{line}</p>
              ))}
            </div>
          </div>
        );
      
      default:
        return (
          <pre className="json-display">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        );
    }
  };

  return (
    <div className="event-details">
      <h4>{EVENT_TYPE_NAMES[event.event_type] || event.event_type}</h4>
      <p className="event-meta">
        时间: {new Date(event.timestamp).toLocaleString()}
        {event.round && ` | 第${event.round}轮`}
      </p>
      {renderDetails()}
    </div>
  );
};

// 统计卡片组件
const StatCard = ({ label, value, unit = '' }) => (
  <div className="stat-card">
    <div className="stat-value">{value}{unit}</div>
    <div className="stat-label">{label}</div>
  </div>
);

// 主组件
const SearchVisualization = ({ apiUrl = '/api/v2/search/stream' }) => {
  const [question, setQuestion] = useState('什么是智信平台？它主要有哪些功能？');
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [stats, setStats] = useState({
    rounds: 0,
    documents: 0,
    selected: 0,
    time: 0
  });
  
  const eventSourceRef = useRef(null);
  const startTimeRef = useRef(null);
  const timeIntervalRef = useRef(null);

  useEffect(() => {
    return () => {
      // 清理
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current);
      }
    };
  }, []);

  const startSearch = async () => {
    if (!question.trim()) {
      alert('请输入问题');
      return;
    }

    // 重置状态
    setEvents([]);
    setSelectedEvent(null);
    setStats({ rounds: 0, documents: 0, selected: 0, time: 0 });
    setIsSearching(true);
    startTimeRef.current = Date.now();

    // 开始计时
    timeIntervalRef.current = setInterval(() => {
      if (startTimeRef.current) {
        const elapsed = ((Date.now() - startTimeRef.current) / 1000).toFixed(1);
        setStats(prev => ({ ...prev, time: elapsed }));
      }
    }, 100);

    // 关闭之前的连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // 创建SSE连接
    const url = `${apiUrl}?question=${encodeURIComponent(question)}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsSearching(false);
        clearInterval(timeIntervalRef.current);
        return;
      }

      try {
        const data = JSON.parse(event.data);
        handleEvent(data);
      } catch (e) {
        console.error('Failed to parse event:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      setIsSearching(false);
      clearInterval(timeIntervalRef.current);
    };
  };

  const handleEvent = (event) => {
    setEvents(prev => [...prev, event]);
    
    // 更新统计
    if (event.event_type === 'search_round_start') {
      if (event.data.round_type === 'initial') {
        setStats(prev => ({ ...prev, rounds: 1 }));
      } else {
        setStats(prev => ({ ...prev, rounds: Math.max(prev.rounds, event.round || 1) }));
      }
    } else if (event.event_type === 'documents_retrieved') {
      setStats(prev => ({ ...prev, documents: prev.documents + event.data.count }));
    } else if (event.event_type === 'documents_selected') {
      setStats(prev => ({ ...prev, selected: event.data.selected_count }));
    }
  };

  const queryHistory = events
    .filter(e => e.event_type === 'search_round_start' || e.event_type === 'new_query_generated')
    .map(e => e.data.query || e.data.new_query);

  return (
    <div className="search-visualization">
      <h1>🤖 智能体搜索过程可视化</h1>
      
      <div className="search-section">
        <div className="search-input">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="请输入您的问题..."
            disabled={isSearching}
          />
          <button onClick={startSearch} disabled={isSearching}>
            {isSearching ? '搜索中...' : '开始搜索'}
          </button>
        </div>
      </div>

      {events.length > 0 && (
        <div className="stats-section">
          <StatCard label="搜索轮数" value={stats.rounds} />
          <StatCard label="检索文档数" value={stats.documents} />
          <StatCard label="选中文档数" value={stats.selected} />
          <StatCard label="搜索耗时" value={stats.time} unit="s" />
        </div>
      )}

      <div className="process-visualization">
        <div className="timeline-panel">
          <h3>搜索过程时间线</h3>
          <div className="timeline">
            {events.map((event, idx) => (
              <EventCard
                key={idx}
                event={event}
                isSelected={selectedEvent === idx}
                onClick={() => setSelectedEvent(idx)}
              />
            ))}
          </div>
        </div>
        
        <div className="details-panel">
          <h3>详细信息</h3>
          <EventDetails event={events[selectedEvent]} />
        </div>
      </div>

      {queryHistory.length > 1 && (
        <div className="query-evolution">
          <h3>查询演化过程</h3>
          <ol>
            {queryHistory.map((query, idx) => (
              <li key={idx}>{query}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

export default SearchVisualization;