'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import GlassCard from '@/components/ui/glass-card';
import GradientButton from '@/components/ui/gradient-button';

interface ErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorModal({
  isOpen,
  onClose,
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorModalProps) {
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
            className="w-full max-w-md"
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
                <div className="flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
                    <span className="text-4xl">⚠️</span>
                  </div>
                </div>

                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-bold">{title}</h2>
                  <p className="text-muted-foreground">{message}</p>
                </div>

                <div className="flex gap-3">
                  {onRetry && (
                    <GradientButton onClick={onRetry} className="flex-1">
                      Try Again
                    </GradientButton>
                  )}
                  <GradientButton onClick={onClose} variant="secondary" className="flex-1">
                    {onRetry ? 'Cancel' : 'Close'}
                  </GradientButton>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
