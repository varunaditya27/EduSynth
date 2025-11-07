import { motion } from 'framer-motion';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

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
          <p className="text-sm leading-relaxed whitespace-pre-wrap wrap-break-word">
            {content}
          </p>
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
