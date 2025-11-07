'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { QuizQuestion } from '@/lib/api';
import GlassCard from '@/components/ui/glass-card';

interface QuizPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: QuizQuestion[];
}

export default function QuizPreviewModal({ isOpen, onClose, questions }: QuizPreviewModalProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    const text = questions
      .map((q, i) => {
        const options = q.options.map((opt, j) => `${String.fromCharCode(65 + j)}. ${opt}`).join('\n');
        return `Question ${i + 1}: ${q.question}\n${options}\nCorrect Answer: ${String.fromCharCode(65 + q.correctAnswer)}\n`;
      })
      .join('\n');

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="w-full max-w-3xl max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <GlassCard className="relative" hover={false}>
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="space-y-6">
                <div className="flex items-center justify-between pr-12">
                  <h2 className="text-3xl font-bold">Quiz Questions</h2>
                  <button
                    onClick={copyToClipboard}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/20 hover:bg-primary/30 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        <span>Copy All</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="space-y-6">
                  {questions.map((question, index) => (
                    <div key={index} className="p-4 rounded-lg bg-white/5 space-y-3">
                      <h3 className="font-semibold text-lg">
                        Question {index + 1}: {question.question}
                      </h3>
                      <div className="space-y-2">
                        {question.options.map((option, optIndex) => (
                          <div
                            key={optIndex}
                            className={`p-3 rounded-lg ${
                              optIndex === question.correctAnswer
                                ? 'bg-green-500/20 border border-green-500/30'
                                : 'bg-white/5'
                            }`}
                          >
                            <span className="font-semibold mr-2">
                              {String.fromCharCode(65 + optIndex)}.
                            </span>
                            {option}
                            {optIndex === question.correctAnswer && (
                              <span className="ml-2 text-xs text-green-400">(Correct)</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
