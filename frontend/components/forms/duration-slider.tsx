'use client';

import { DURATION_OPTIONS } from '@/lib/constants';
import { motion } from 'framer-motion';

interface DurationSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export default function DurationSlider({ value, onChange }: DurationSliderProps) {
  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <label htmlFor="duration" className="block text-sm font-semibold text-foreground">
          Duration
        </label>
        <motion.span
          key={value}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          className="text-2xl font-bold text-primary"
        >
          {value} min
        </motion.span>
      </div>
      <div className="relative">
        <input
          type="range"
          id="duration"
          min={DURATION_OPTIONS.min}
          max={DURATION_OPTIONS.max}
          step={DURATION_OPTIONS.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-2 bg-white/10 dark:bg-gray-900/50 rounded-lg appearance-none cursor-pointer accent-primary"
        />
        <div className="flex justify-between mt-2 text-xs text-muted-foreground">
          <span>{DURATION_OPTIONS.min} min</span>
          <span>{DURATION_OPTIONS.max} min</span>
        </div>
      </div>
    </div>
  );
}
