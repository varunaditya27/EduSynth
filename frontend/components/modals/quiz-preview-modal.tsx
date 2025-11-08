'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Copy, Check, Download, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { QuizQuestion } from '@/lib/api';
import GlassCard from '@/components/ui/glass-card';

interface QuizPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: QuizQuestion[];
  topic?: string;
  formattedText?: string;
  lectureId?: string;
}

type QuizFormat = 'plain' | 'moodle' | 'canvas';

export default function QuizPreviewModal({ 
  isOpen, 
  onClose, 
  questions, 
  topic,
  formattedText,
  lectureId 
}: QuizPreviewModalProps) {
  const [copied, setCopied] = useState(false);
  const [showAnswers, setShowAnswers] = useState(true);
  const [selectedFormat, setSelectedFormat] = useState<QuizFormat>('plain');
  const [isDownloading, setIsDownloading] = useState(false);

  const copyToClipboard = () => {
    const contentToCopy = formattedText || generatePlainText();
    navigator.clipboard.writeText(contentToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const generatePlainText = () => {
    return questions
      .map((q, i) => {
        const options = q.options.map((opt, j) => `${String.fromCharCode(65 + j)}. ${opt}`).join('\n');
        const answer = showAnswers ? `\nCorrect Answer: ${String.fromCharCode(65 + q.correctAnswer)}` : '';
        const explanation = showAnswers && q.explanation ? `\nExplanation: ${q.explanation}` : '';
        return `Question ${i + 1}: ${q.question}\n${options}${answer}${explanation}\n`;
      })
      .join('\n');
  };

  const downloadQuiz = () => {
    setIsDownloading(true);
    const content = formattedText || generatePlainText();
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    const extension = selectedFormat === 'canvas' ? 'csv' : 'txt';
    const filename = topic 
      ? `${topic.toLowerCase().replace(/\s+/g, '-')}-quiz.${extension}`
      : `quiz-${lectureId || 'export'}.${extension}`;
    
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setTimeout(() => setIsDownloading(false), 1000);
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
            className="w-full max-w-4xl max-h-[85vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <GlassCard className="relative h-full flex flex-col" hover={false}>
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/10 transition-colors z-10"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Header */}
              <div className="space-y-4 pb-4 border-b border-white/10">
                <div className="pr-12">
                  <h2 className="text-3xl font-bold">Quiz Questions</h2>
                  {topic && <p className="text-sm text-white/60 mt-1">Topic: {topic}</p>}
                  <p className="text-xs text-white/50 mt-1">{questions.length} questions generated</p>
                </div>

                {/* Format Selector & Actions */}
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-white/70">Format:</label>
                    <select
                      value={selectedFormat}
                      onChange={(e) => setSelectedFormat(e.target.value as QuizFormat)}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 
                               focus:border-primary/50 focus:outline-none transition-colors text-sm"
                    >
                      <option value="plain">Plain Text</option>
                      <option value="moodle">Moodle GIFT</option>
                      <option value="canvas">Canvas CSV</option>
                    </select>
                  </div>

                  <button
                    onClick={() => setShowAnswers(!showAnswers)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 
                             hover:bg-white/10 transition-colors text-sm"
                  >
                    {showAnswers ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    <span>{showAnswers ? 'Hide' : 'Show'} Answers</span>
                  </button>

                  <div className="flex items-center gap-2 ml-auto">
                    <button
                      onClick={copyToClipboard}
                      disabled={copied}
                      className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-primary/20 
                               hover:bg-primary/30 transition-colors text-sm disabled:opacity-50"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={downloadQuiz}
                      disabled={isDownloading}
                      className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-green-500/20 
                               hover:bg-green-500/30 transition-colors text-sm disabled:opacity-50"
                    >
                      <Download className="w-4 h-4" />
                      <span>{isDownloading ? 'Downloading...' : 'Download'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Questions List (Scrollable) */}
              <div className="flex-1 overflow-y-auto mt-4 pr-2 space-y-4">
                {questions.map((question, index) => {
                  const correctIndex = question.correctAnswer ?? question.correct_answer ?? 0;
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 rounded-lg bg-white/5 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-semibold text-lg flex-1">
                          <span className="text-primary mr-2">Q{index + 1}.</span>
                          {question.question}
                        </h3>
                        {question.difficulty && (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            question.difficulty.toLowerCase() === 'easy' 
                              ? 'bg-green-500/20 text-green-400'
                              : question.difficulty.toLowerCase() === 'medium'
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {question.difficulty}
                          </span>
                        )}
                      </div>

                      <div className="space-y-2">
                        {question.options.map((option, optIndex) => (
                          <div
                            key={optIndex}
                            className={`p-3 rounded-lg transition-all ${
                              showAnswers && optIndex === correctIndex
                                ? 'bg-green-500/20 border border-green-500/40'
                                : 'bg-white/5 border border-transparent hover:border-white/10'
                            }`}
                          >
                            <span className="font-semibold mr-2 text-primary">
                              {String.fromCharCode(65 + optIndex)}.
                            </span>
                            {option}
                            {showAnswers && optIndex === correctIndex && (
                              <span className="ml-2 text-xs text-green-400 font-medium">✓ Correct</span>
                            )}
                          </div>
                        ))}
                      </div>

                      {showAnswers && question.explanation && (
                        <div className="mt-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                          <p className="text-sm">
                            <span className="font-semibold text-blue-400">Explanation: </span>
                            <span className="text-white/80">{question.explanation}</span>
                          </p>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}