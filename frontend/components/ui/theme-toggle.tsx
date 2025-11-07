'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ThemeToggle() {
  // Start with a deterministic value for SSR (false) and hydrate on the client
  const [isDark, setIsDark] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // On mount, read the user's preference from localStorage or OS setting
    const theme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDarkMode = theme === 'dark' || (!theme && prefersDark);
    // Defer state update to avoid synchronous setState inside effect
    setTimeout(() => {
      setIsDark(isDarkMode);
      setMounted(true);
    }, 0);
  }, []);

  useEffect(() => {
    // Apply the theme to the document when mounted or when isDark changes
    if (!mounted) return;
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark, mounted]);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  return (
    <motion.button
      onClick={toggleTheme}
      className="relative w-10 h-10 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 360 : 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {/* Render icon only when mounted to avoid SSR/CSR markup mismatch */}
        {mounted ? (
          isDark ? <Moon className="w-5 h-5 text-primary" /> : <Sun className="w-5 h-5 text-primary" />
        ) : (
          <span className="w-5 h-5" />
        )}
      </motion.div>
    </motion.button>
  );
}
