'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TOPIC_EXAMPLES } from '@/lib/constants';

interface TopicInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function TopicInput({ value, onChange, error }: TopicInputProps) {
  const [currentExampleIndex, setCurrentExampleIndex] = useState(0);
  const [displayText, setDisplayText] = useState('');
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    if (!value) {
      const example = TOPIC_EXAMPLES[currentExampleIndex];
      let currentIndex = 0;

      if (isTyping) {
        if (currentIndex < example.length) {
          const timeout = setTimeout(() => {
            setDisplayText(example.slice(0, currentIndex + 1));
            currentIndex++;
            if (currentIndex === example.length) {
              setTimeout(() => setIsTyping(false), 2000);
            }
          }, 50);
          return () => clearTimeout(timeout);
        }
      } else {
        if (displayText.length > 0) {
          const timeout = setTimeout(() => {
            setDisplayText(displayText.slice(0, -1));
          }, 30);
          return () => clearTimeout(timeout);
        } else {
          setCurrentExampleIndex((prev) => (prev + 1) % TOPIC_EXAMPLES.length);
          setIsTyping(true);
        }
      }
    }
  }, [currentExampleIndex, displayText, isTyping, value]);

  return (
    <div className="space-y-2">
      <label htmlFor="topic" className="block text-sm font-semibold text-foreground">
        Lecture Topic
      </label>
      <div className="relative">
        <textarea
          id="topic"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={value ? '' : displayText}
          className={`w-full min-h-[120px] px-4 py-3 rounded-lg bg-white/10 dark:bg-gray-900/50 border ${
            error ? 'border-red-500' : 'border-white/20 dark:border-white/10'
          } focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none resize-none transition-all`}
        />
      </div>
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-sm text-red-500"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
