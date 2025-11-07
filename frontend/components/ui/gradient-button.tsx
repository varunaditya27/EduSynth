'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface GradientButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export default function GradientButton({
  children,
  onClick,
  type = 'button',
  disabled = false,
  variant = 'primary',
  className = '',
}: GradientButtonProps) {
  const baseClasses = 'relative px-8 py-3 rounded-lg font-semibold text-white overflow-hidden transition-all';
  const variantClasses = variant === 'primary' 
    ? 'bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/50' 
    : 'bg-gradient-to-r from-secondary to-muted hover:shadow-lg hover:shadow-secondary/50';

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses} ${className} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      whileHover={!disabled ? { scale: 1.05, y: -2 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
    >
      <motion.span
        className="absolute inset-0 bg-white opacity-0"
        whileHover={!disabled ? { opacity: 0.1 } : {}}
        transition={{ duration: 0.3 }}
      />
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
}
