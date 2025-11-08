'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Sparkles } from 'lucide-react';
import ChatMessage from './chat-message';
import ChatInput from './chat-input';
import { apiClient, ChatMessage as ChatMessageType } from '@/lib/api';
import { useAuth } from '@/contexts/auth-context';
import { cn } from '@/lib/utils';

interface ChatWidgetProps {
  topicContext?: string;
  lectureId?: string;
  className?: string;
}

export default function ChatWidget({ topicContext, lectureId, className }: ChatWidgetProps) {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const chatPanelRef = useRef<HTMLDivElement>(null);
  
  // Initialize messages with persisted history or default message
  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    // Try to load persisted messages for this lecture/topic
    if (typeof window !== 'undefined') {
      const storageKey = `chat_history_${lectureId || topicContext || 'default'}`;
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          return parsed.map((msg: ChatMessageType) => ({
            ...msg,
            timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          }));
        } catch {
          // Ignore parsing errors
        }
      }
    }
    
    // Default welcome message
    return [
      {
        role: 'assistant',
        content: topicContext
          ? `Hi! I'm here to help you with **"${topicContext}"**. I have access to the full lecture content including:\n\n- All slide titles and key points\n- Narration scripts\n- Topic structure\n\nAsk me anything about this topic, how to improve your lecture, or request specific explanations!`
          : "Hi! I'm your AI assistant. Ask me anything about creating lectures, explaining concepts, or getting educational insights!",
        timestamp: new Date(),
      } as ChatMessageType,
    ];
  });
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  // Persist messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && messages.length > 1) {
      const storageKey = `chat_history_${lectureId || topicContext || 'default'}`;
      localStorage.setItem(storageKey, JSON.stringify(messages));
    }
  }, [messages, lectureId, topicContext]);
  
  // Handle click outside to close chat
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        chatPanelRef.current &&
        !chatPanelRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      // Add small delay to prevent immediate close on open
      setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside);
      }, 100);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMessage]);

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: ChatMessageType = {
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);
    setStreamingMessage('');

    try {
      // Use streaming for better UX
      let fullResponse = '';

      await apiClient.streamChat(
        {
          message: content,
          conversation_history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
          topic_context: topicContext,
          lecture_id: lectureId,
        },
        (chunk) => {
          fullResponse += chunk;
          setStreamingMessage(fullResponse);
        },
        token || undefined
      );

      // Add complete assistant message
      const assistantMessage: ChatMessageType = {
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingMessage('');
    } catch (error) {
      console.error('Chat error:', error);
      // Add error message
      const errorMessage: ChatMessageType = {
        role: 'assistant',
        content: "I'm sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 260, damping: 20 }}
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg flex items-center justify-center',
          'bg-linear-to-br from-primary to-accent text-white',
          'hover:shadow-xl hover:scale-110 transition-all duration-300',
          isOpen && 'scale-0 opacity-0 pointer-events-none',
          className
        )}
      >
        <MessageCircle className="w-6 h-6" />
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={chatPanelRef}
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed bottom-0 right-0 z-50 w-full md:w-[400px] h-[600px] md:h-[700px] md:bottom-6 md:right-6 md:rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl border border-white/10"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 30, 50, 0.95) 0%, rgba(20, 20, 40, 0.95) 100%)',
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10 bg-black/20">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-white">AI Assistant</h3>
                  <p className="text-xs text-muted-foreground">
                    {topicContext ? 'Topic expert' : 'Always here to help'}
                  </p>
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </motion.button>
            </div>

            {/* Messages Area */}
            <div
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto p-4 space-y-4"
              style={{ height: 'calc(100% - 140px)' }}
            >
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
              ))}

              {/* Streaming Message */}
              {isStreaming && streamingMessage && (
                <ChatMessage role="assistant" content={streamingMessage} />
              )}

              {/* Typing Indicator */}
              {isStreaming && !streamingMessage && (
                <div className="flex gap-3">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-linear-to-br from-accent to-primary border border-white/10 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex items-center gap-1 px-4 py-3 rounded-2xl bg-white/5 border border-white/10">
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 1, delay: 0 }}
                      className="w-2 h-2 rounded-full bg-primary"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
                      className="w-2 h-2 rounded-full bg-accent"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
                      className="w-2 h-2 rounded-full bg-primary"
                    />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <ChatInput
              onSend={handleSendMessage}
              disabled={isStreaming}
              placeholder={topicContext ? `Ask about ${topicContext}...` : 'Ask me anything...'}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
