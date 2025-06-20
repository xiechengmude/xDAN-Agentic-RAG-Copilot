/**
 * SSE (Server-Sent Events) 客户端
 * 用于替代 WebSocket 进行实时数据通信
 */

export interface FileStatusUpdate {
  type: 'status' | 'complete' | 'error' | 'timeout'
  doc_id: string
  status?: string
  progress?: number
  progress_msg?: string
  error?: string
  success?: boolean
}

export interface ChatStreamMessage {
  type: 'message' | 'error'
  content: string
  done: boolean
  error?: string
}

export class SSEClient {
  private eventSources: Map<string, EventSource> = new Map()

  /**
   * 订阅文档状态更新
   */
  subscribeFileStatus(
    datasetId: string,
    docId: string,
    onUpdate: (data: FileStatusUpdate) => void,
    onError?: (error: Event) => void
  ): () => void {
    const url = `/api/v1/datasets/${datasetId}/documents/${docId}/status/stream`
    const key = `file-${datasetId}-${docId}`

    // 如果已存在连接，先关闭
    this.closeConnection(key)

    const eventSource = new EventSource(url)
    this.eventSources.set(key, eventSource)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as FileStatusUpdate
        onUpdate(data)

        // 如果是完成状态，自动关闭连接
        if (data.type === 'complete' || data.type === 'timeout') {
          this.closeConnection(key)
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error)
      onError?.(error)
      this.closeConnection(key)
    }

    // 返回清理函数
    return () => this.closeConnection(key)
  }

  /**
   * 订阅批量文档状态更新
   */
  subscribeBatchFileStatus(
    datasetId: string,
    docIds: string[],
    onUpdate: (data: FileStatusUpdate) => void,
    onComplete?: (summary: Record<string, string>) => void
  ): () => void {
    const url = `/api/v1/datasets/${datasetId}/documents/status/stream?doc_ids=${docIds.join(',')}`
    const key = `batch-${datasetId}`

    this.closeConnection(key)

    const eventSource = new EventSource(url)
    this.eventSources.set(key, eventSource)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'batch_status') {
          onUpdate(data as FileStatusUpdate)
        } else if (data.type === 'batch_complete') {
          onComplete?.(data.summary)
          this.closeConnection(key)
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE batch connection error:', error)
      this.closeConnection(key)
    }

    return () => this.closeConnection(key)
  }

  /**
   * 订阅聊天流式响应
   */
  subscribeChatStream(
    chatId: string,
    messages: Array<{role: string, content: string}>,
    datasetId?: string,
    onMessage: (data: ChatStreamMessage) => void,
    onError?: (error: Event) => void
  ): () => void {
    const key = `chat-${chatId}`
    this.closeConnection(key)

    // 使用 fetch 发送 POST 请求并获取流式响应
    const controller = new AbortController()
    
    fetch(`/api/v1/chats/${chatId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        messages,
        dataset_id: datasetId
      }),
      signal: controller.signal
    }).then(async response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        // 处理完整的行，保留最后一个可能不完整的行
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as ChatStreamMessage
              onMessage(data)

              if (data.done) {
                controller.abort()
                return
              }
            } catch (error) {
              console.error('Failed to parse SSE data:', error)
            }
          }
        }
      }
    }).catch(error => {
      if (error.name !== 'AbortError') {
        console.error('Chat stream error:', error)
        onError?.(error)
      }
    })

    // 返回清理函数
    return () => controller.abort()
  }

  /**
   * 关闭指定的 SSE 连接
   */
  private closeConnection(key: string): void {
    const eventSource = this.eventSources.get(key)
    if (eventSource) {
      eventSource.close()
      this.eventSources.delete(key)
    }
  }

  /**
   * 关闭所有 SSE 连接
   */
  closeAll(): void {
    this.eventSources.forEach((eventSource, key) => {
      eventSource.close()
    })
    this.eventSources.clear()
  }
}

// 导出单例实例
export const sseClient = new SSEClient()

// 使用示例
/*
// 1. 监听单个文档状态
const unsubscribe = sseClient.subscribeFileStatus(
  'dataset123',
  'doc456',
  (update) => {
    console.log('文档状态更新:', update)
    if (update.type === 'status') {
      updateDocumentStatus(update.doc_id, update.status, update.progress)
    }
  }
)

// 2. 监听批量文档状态
const unsubscribeBatch = sseClient.subscribeBatchFileStatus(
  'dataset123',
  ['doc1', 'doc2', 'doc3'],
  (update) => {
    console.log('批量状态更新:', update)
  },
  (summary) => {
    console.log('所有文档处理完成:', summary)
  }
)

// 3. 聊天流式响应
const unsubscribeChat = sseClient.subscribeChatStream(
  'chat123',
  [{ role: 'user', content: '你好' }],
  'dataset123',
  (message) => {
    if (message.type === 'message') {
      appendChatMessage(message.content)
    }
    if (message.done) {
      console.log('对话完成')
    }
  }
)

// 清理连接
unsubscribe()
unsubscribeBatch()
unsubscribeChat()

// 或者关闭所有连接
sseClient.closeAll()
*/