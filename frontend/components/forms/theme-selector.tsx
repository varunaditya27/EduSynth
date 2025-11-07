'use client';

import { motion } from 'framer-motion';
import { VISUAL_THEMES } from '@/lib/constants';
import { Check } from 'lucide-react';

interface ThemeSelectorProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function ThemeSelector({ value, onChange, error }: ThemeSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-foreground">
        Visual Theme
      </label>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {VISUAL_THEMES.map((theme) => (
          <motion.button
            key={theme.id}
            type="button"
            onClick={() => onChange(theme.id)}
            className={`relative p-4 rounded-lg border-2 transition-all ${
              value === theme.id
                ? 'border-primary bg-primary/10'
                : 'border-white/20 dark:border-white/10 hover:border-primary/50'
            }`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className={`w-full h-20 rounded-md mb-3 ${theme.preview}`} />
            <h4 className="font-semibold text-sm mb-1">{theme.name}</h4>
            <p className="text-xs text-muted-foreground line-clamp-2">{theme.description}</p>
            {value === theme.id && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute top-2 right-2 w-6 h-6 bg-primary rounded-full flex items-center justify-center"
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </motion.button>
        ))}
      </div>
      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
