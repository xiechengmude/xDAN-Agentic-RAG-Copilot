import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Button } from "@/components/ui/button";

// 定义事件数据类型
interface EventData {
  question?: string;
  search_query?: string[];
  queries?: string[];
  sources_gathered?: Source[];
  sources?: Source[];
  answer?: string;
  [key: string]: unknown;
}

// 定义事件类型
interface StreamEvent {
  event_type: string;
  timestamp: string;
  data: EventData;
}

// 定义源数据类型
interface Source {
  label: string;
  [key: string]: unknown;
}

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !isLoading &&
      messages.length > 0
    ) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [messages, isLoading, processedEventsTimeline]);

  // 处理流式事件
  const handleStreamEvent = useCallback((event: StreamEvent) => {
    console.log("收到流式事件:", event); // 添加调试日志
    
    // 直接显示返回的 event_type 和 data
    const processedEvent: ProcessedEvent = {
      title: event.event_type || "未知事件",
      data: JSON.stringify(event.data, null, 2) || "无数据",
    };

    // 特殊处理：如果是答案生成完成事件，添加AI消息
    if (event.event_type === "answer_generated" || 
        event.event_type === "answer_complete" || 
        event.event_type === "complete") {
      
      // 从 data 中提取答案内容
      let answerContent = "";
      if (event.data?.answer && typeof event.data.answer === 'string') {
        answerContent = event.data.answer;
      } else if (event.data?.content && typeof event.data.content === 'string') {
        answerContent = event.data.content;
      } else if (event.data?.result && typeof event.data.result === 'string') {
        answerContent = event.data.result;
      } else {
        // 如果没有找到特定的答案字段，使用整个 data 对象
        answerContent = JSON.stringify(event.data, null, 2);
      }
      
      const aiMessage: Message = {
        type: "ai",
        content: answerContent || "搜索完成",
        id: Date.now().toString(),
      };
      
      console.log("添加AI消息:", aiMessage);
      setMessages(prev => {
        const newMessages = [...prev, aiMessage];
        console.log("更新后的消息列表:", newMessages);
        return newMessages;
      });
      
      hasFinalizeEventOccurredRef.current = true;
      // 不在这里设置 setIsLoading(false)，让流处理完成时统一设置
    }

    setProcessedEventsTimeline((prevEvents) => {
      const newEvents = [...prevEvents, processedEvent];
      console.log("更新后的事件时间线:", newEvents);
      return newEvents;
    });
  }, []);

  // 流式请求处理
  const handleStreamRequest = useCallback(async (question: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // 创建新的 AbortController
      abortControllerRef.current = new AbortController();
      
      const response = await fetch("http://192.168.31.18:8050/api/search/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("无法获取响应流");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.trim() === "") continue;
          
          if (line.startsWith("data: ")) {
            const jsonData = line.slice(6).trim(); // 移除 "data: " 前缀并去除空格
            
            // 跳过 [DONE] 标记
            if (jsonData === "[DONE]") {
              console.log("收到结束标记，流式处理完成");
              setIsLoading(false);
              continue;
            }
            
            try {
              const event: StreamEvent = JSON.parse(jsonData);
              handleStreamEvent(event);
            } catch (e) {
              console.error("解析事件数据失败:", e, "原始数据:", jsonData);
              // 不要因为单个解析错误而中断整个流程
            }
          }
        }
      }
      
      // 确保在流结束时设置 loading 为 false
      setIsLoading(false);
    } catch (error: unknown) {
      if (error instanceof Error) {
        if (error.name === "AbortError") {
          console.log("请求被取消");
        } else {
          console.error("流式请求错误:", error);
          setError(error.message);
        }
      } else {
        console.error("未知错误:", error);
        setError("发生未知错误");
      }
    } finally {
      setIsLoading(false);
    }
  }, [handleStreamEvent]);

  const handleSubmit = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // 添加用户消息
      const userMessage: Message = {
        type: "human",
        content: submittedInputValue,
        id: Date.now().toString(),
      };

      setMessages(prev => [...prev, userMessage]);
      
      // 开始流式请求
      handleStreamRequest(submittedInputValue);
    },
    [handleStreamRequest]
  );

  const handleCancel = useCallback(() => {
    // 取消当前请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsLoading(false);
    window.location.reload();
  }, []);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              onCancel={handleCancel}
            />
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="flex flex-col items-center justify-center gap-4">
                <h1 className="text-2xl text-red-400 font-bold">错误</h1>
                <p className="text-red-400">{JSON.stringify(error)}</p>

                <Button
                  variant="destructive"
                  onClick={() => window.location.reload()}
                >
                  重试
                </Button>
              </div>
            </div>
          ) : (
            <ChatMessagesView
              messages={messages}
              isLoading={isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
      </main>
    </div>
  );
}
