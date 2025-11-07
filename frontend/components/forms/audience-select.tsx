'use client';

import { AUDIENCE_OPTIONS } from '@/lib/constants';
import { motion, AnimatePresence } from 'framer-motion';

interface AudienceSelectProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function AudienceSelect({ value, onChange, error }: AudienceSelectProps) {
  return (
    <div className="space-y-2">
      <label htmlFor="audience" className="block text-sm font-semibold text-foreground">
        Target Audience
      </label>
      <select
        id="audience"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-4 py-3 rounded-lg bg-white/10 dark:bg-gray-900/50 border ${
          error ? 'border-red-500' : 'border-white/20 dark:border-white/10'
        } focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none cursor-pointer transition-all`}
      >
        <option value="">Select audience level</option>
        {AUDIENCE_OPTIONS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
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
