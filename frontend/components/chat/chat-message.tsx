import { motion } from 'framer-motion';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-linear-to-br from-primary to-accent'
            : 'bg-linear-to-br from-accent to-primary border border-white/10'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Bubble */}
      <div className={cn('flex flex-col gap-1 max-w-[80%]', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'px-4 py-3 rounded-2xl backdrop-blur-md',
            isUser
              ? 'bg-linear-to-br from-primary/90 to-accent/90 text-white'
              : 'bg-white/10 dark:bg-gray-900/50 border border-white/10 text-foreground'
          )}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap wrap-break-word">
              {content}
            </p>
          ) : (
            <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  // Custom styling for markdown elements
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="text-sm">{children}</li>,
                  code: ({ className, children, ...props }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    return match ? (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded bg-white/10 text-accent font-mono text-xs" {...props}>
                        {children}
                      </code>
                    );
                  },
                  pre: ({ children }) => (
                    <pre className="bg-black/40 rounded-lg p-3 overflow-x-auto mb-2 text-xs">
                      {children}
                    </pre>
                  ),
                  h1: ({ children }) => <h1 className="text-lg font-bold mb-2 mt-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold mb-2 mt-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold mb-1 mt-1">{children}</h3>,
                  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                  em: ({ children }) => <em className="italic">{children}</em>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary/50 pl-3 italic text-gray-300 mb-2">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {timestamp && (
          <span className="text-xs text-muted-foreground px-2">
            {timestamp.toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </motion.div>
  );
}
