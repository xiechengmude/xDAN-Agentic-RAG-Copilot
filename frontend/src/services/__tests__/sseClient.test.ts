/**
 * SSE 客户端单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SSEClient } from '../sseClient'
import type { FileStatusUpdate, ChatStreamMessage } from '../sseClient'

// Mock EventSource
class MockEventSource {
  url: string
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = 0 // CONNECTING
  
  constructor(url: string) {
    this.url = url
    this.readyState = 1 // OPEN
  }
  
  close() {
    this.readyState = 2 // CLOSED
  }
  
  // 模拟发送消息
  sendMessage(data: any) {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data: JSON.stringify(data) })
      this.onmessage(event)
    }
  }
  
  // 模拟错误
  sendError() {
    if (this.onerror) {
      this.onerror(new Event('error'))
    }
  }
}

// 全局 mock
global.EventSource = MockEventSource as any

describe('SSEClient', () => {
  let sseClient: SSEClient
  let mockEventSources: MockEventSource[] = []
  
  beforeEach(() => {
    sseClient = new SSEClient()
    mockEventSources = []
    
    // 拦截 EventSource 创建
    vi.spyOn(global, 'EventSource').mockImplementation((url: string) => {
      const source = new MockEventSource(url)
      mockEventSources.push(source)
      return source as any
    })
  })
  
  afterEach(() => {
    sseClient.closeAll()
    vi.restoreAllMocks()
  })
  
  describe('subscribeFileStatus', () => {
    it('应该正确订阅文档状态更新', () => {
      const onUpdate = vi.fn()
      const datasetId = 'dataset123'
      const docId = 'doc456'
      
      const unsubscribe = sseClient.subscribeFileStatus(
        datasetId,
        docId,
        onUpdate
      )
      
      // 验证 EventSource 创建
      expect(mockEventSources).toHaveLength(1)
      expect(mockEventSources[0].url).toBe(
        `/api/v1/datasets/${datasetId}/documents/${docId}/status/stream`
      )
      
      // 模拟状态更新
      const statusUpdate: FileStatusUpdate = {
        type: 'status',
        doc_id: docId,
        status: 'PARSING',
        progress: 0.5,
        progress_msg: '解析中...'
      }
      
      mockEventSources[0].sendMessage(statusUpdate)
      
      // 验证回调被调用
      expect(onUpdate).toHaveBeenCalledWith(statusUpdate)
      
      // 清理
      unsubscribe()
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
    })
    
    it('应该在完成时自动关闭连接', () => {
      const onUpdate = vi.fn()
      
      sseClient.subscribeFileStatus('dataset123', 'doc456', onUpdate)
      
      // 发送完成事件
      const completeUpdate: FileStatusUpdate = {
        type: 'complete',
        doc_id: 'doc456',
        success: true
      }
      
      mockEventSources[0].sendMessage(completeUpdate)
      
      // 验证连接被关闭
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
    })
    
    it('应该处理错误情况', () => {
      const onUpdate = vi.fn()
      const onError = vi.fn()
      
      sseClient.subscribeFileStatus(
        'dataset123',
        'doc456',
        onUpdate,
        onError
      )
      
      // 触发错误
      mockEventSources[0].sendError()
      
      // 验证错误处理
      expect(onError).toHaveBeenCalled()
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
    })
    
    it('应该处理 JSON 解析错误', () => {
      const onUpdate = vi.fn()
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      sseClient.subscribeFileStatus('dataset123', 'doc456', onUpdate)
      
      // 发送无效 JSON
      if (mockEventSources[0].onmessage) {
        const event = new MessageEvent('message', { data: 'invalid json' })
        mockEventSources[0].onmessage(event)
      }
      
      // 验证错误被记录但不会崩溃
      expect(consoleError).toHaveBeenCalledWith(
        'Failed to parse SSE message:',
        expect.any(Error)
      )
      expect(onUpdate).not.toHaveBeenCalled()
      
      consoleError.mockRestore()
    })
  })
  
  describe('subscribeBatchFileStatus', () => {
    it('应该正确处理批量文档状态', () => {
      const onUpdate = vi.fn()
      const onComplete = vi.fn()
      const datasetId = 'dataset123'
      const docIds = ['doc1', 'doc2', 'doc3']
      
      sseClient.subscribeBatchFileStatus(
        datasetId,
        docIds,
        onUpdate,
        onComplete
      )
      
      // 验证 URL 参数
      expect(mockEventSources[0].url).toBe(
        `/api/v1/datasets/${datasetId}/documents/status/stream?doc_ids=${docIds.join(',')}`
      )
      
      // 模拟批量状态更新
      const batchUpdate = {
        type: 'batch_status',
        doc_id: 'doc1',
        status: 'PARSING',
        progress: 0.3
      }
      
      mockEventSources[0].sendMessage(batchUpdate)
      expect(onUpdate).toHaveBeenCalledWith(batchUpdate)
      
      // 模拟批量完成
      const batchComplete = {
        type: 'batch_complete',
        summary: {
          doc1: 'PARSE_SUCCESS',
          doc2: 'PARSE_SUCCESS',
          doc3: 'PARSE_FAILED'
        }
      }
      
      mockEventSources[0].sendMessage(batchComplete)
      expect(onComplete).toHaveBeenCalledWith(batchComplete.summary)
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
    })
  })
  
  describe('subscribeChatStream', () => {
    it('应该正确处理聊天流', async () => {
      const onMessage = vi.fn()
      const chatId = 'chat123'
      const messages = [{ role: 'user', content: '你好' }]
      
      // Mock fetch
      const mockResponse = {
        ok: true,
        body: {
          getReader: () => ({
            read: vi.fn()
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"type":"message","content":"你","done":false}\n\n')
              })
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"type":"message","content":"好","done":false}\n\n')
              })
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"type":"message","content":"!","done":true}\n\n')
              })
              .mockResolvedValueOnce({
                done: true,
                value: undefined
              })
          })
        }
      }
      
      global.fetch = vi.fn().mockResolvedValue(mockResponse)
      
      const unsubscribe = sseClient.subscribeChatStream(
        chatId,
        messages,
        undefined,
        onMessage
      )
      
      // 等待异步处理
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 验证消息处理
      expect(onMessage).toHaveBeenCalledTimes(3)
      expect(onMessage).toHaveBeenCalledWith({
        type: 'message',
        content: '你',
        done: false
      })
      expect(onMessage).toHaveBeenCalledWith({
        type: 'message',
        content: '好',
        done: false
      })
      expect(onMessage).toHaveBeenCalledWith({
        type: 'message',
        content: '!',
        done: true
      })
    })
    
    it('应该处理 fetch 错误', async () => {
      const onMessage = vi.fn()
      const onError = vi.fn()
      
      // Mock fetch 失败
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
      
      sseClient.subscribeChatStream(
        'chat123',
        [{ role: 'user', content: 'test' }],
        undefined,
        onMessage,
        onError
      )
      
      // 等待错误处理
      await new Promise(resolve => setTimeout(resolve, 100))
      
      expect(onError).toHaveBeenCalled()
    })
  })
  
  describe('连接管理', () => {
    it('应该正确管理多个连接', () => {
      const unsubscribe1 = sseClient.subscribeFileStatus(
        'dataset1',
        'doc1',
        vi.fn()
      )
      
      const unsubscribe2 = sseClient.subscribeFileStatus(
        'dataset2',
        'doc2',
        vi.fn()
      )
      
      expect(mockEventSources).toHaveLength(2)
      
      // 关闭第一个连接
      unsubscribe1()
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
      expect(mockEventSources[1].readyState).toBe(1) // OPEN
      
      // 关闭所有连接
      sseClient.closeAll()
      expect(mockEventSources[1].readyState).toBe(2) // CLOSED
    })
    
    it('应该在重复订阅同一文档时关闭旧连接', () => {
      const datasetId = 'dataset123'
      const docId = 'doc456'
      
      // 第一次订阅
      sseClient.subscribeFileStatus(datasetId, docId, vi.fn())
      expect(mockEventSources).toHaveLength(1)
      const firstSource = mockEventSources[0]
      
      // 第二次订阅同一文档
      sseClient.subscribeFileStatus(datasetId, docId, vi.fn())
      expect(mockEventSources).toHaveLength(2)
      
      // 验证第一个连接被关闭
      expect(firstSource.readyState).toBe(2) // CLOSED
      expect(mockEventSources[1].readyState).toBe(1) // OPEN
    })
  })
  
  describe('边界情况', () => {
    it('应该处理空消息', () => {
      const onUpdate = vi.fn()
      
      sseClient.subscribeFileStatus('dataset123', 'doc456', onUpdate)
      
      // 发送空数据
      if (mockEventSources[0].onmessage) {
        const event = new MessageEvent('message', { data: '' })
        mockEventSources[0].onmessage(event)
      }
      
      // 不应该调用回调
      expect(onUpdate).not.toHaveBeenCalled()
    })
    
    it('应该处理超时事件', () => {
      const onUpdate = vi.fn()
      
      sseClient.subscribeFileStatus('dataset123', 'doc456', onUpdate)
      
      // 发送超时事件
      const timeoutUpdate: FileStatusUpdate = {
        type: 'timeout',
        doc_id: 'doc456',
        error: 'Processing timeout'
      }
      
      mockEventSources[0].sendMessage(timeoutUpdate)
      
      expect(onUpdate).toHaveBeenCalledWith(timeoutUpdate)
      expect(mockEventSources[0].readyState).toBe(2) // CLOSED
    })
  })
})

describe('SSEClient 集成测试', () => {
  it('应该支持完整的文档处理流程', () => {
    const sseClient = new SSEClient()
    const statusHistory: FileStatusUpdate[] = []
    
    const unsubscribe = sseClient.subscribeFileStatus(
      'dataset123',
      'doc456',
      (update) => statusHistory.push(update)
    )
    
    // 模拟完整的处理流程
    const eventSource = mockEventSources[0]
    
    // 开始解析
    eventSource.sendMessage({
      type: 'status',
      doc_id: 'doc456',
      status: 'PARSING',
      progress: 0.0,
      progress_msg: '开始解析'
    })
    
    // 解析进度更新
    eventSource.sendMessage({
      type: 'status',
      doc_id: 'doc456',
      status: 'PARSING',
      progress: 0.5,
      progress_msg: '解析中...'
    })
    
    // 解析完成
    eventSource.sendMessage({
      type: 'complete',
      doc_id: 'doc456',
      success: true
    })
    
    // 验证历史记录
    expect(statusHistory).toHaveLength(3)
    expect(statusHistory[0].progress).toBe(0.0)
    expect(statusHistory[1].progress).toBe(0.5)
    expect(statusHistory[2].type).toBe('complete')
    
    // 验证连接被自动关闭
    expect(eventSource.readyState).toBe(2) // CLOSED
  })
})