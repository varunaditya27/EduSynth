'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import GradientButton from '@/components/ui/gradient-button';

export default function HeroSection() {
  const router = useRouter();

  const title = 'Transform Knowledge Into Cinematic Lectures';
  const words = title.split(' ');

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4">
      <div className="max-w-5xl mx-auto text-center space-y-8">
        <motion.h1
          className="text-5xl md:text-7xl font-bold leading-tight"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          {words.map((word, wordIndex) => (
            <motion.span
              key={wordIndex}
              className="inline-block mr-4 bg-linear-to-r from-primary via-accent to-pink-500 bg-clip-text text-transparent"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: wordIndex * 0.1, duration: 0.5 }}
            >
              {word}
            </motion.span>
          ))}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5, duration: 0.8 }}
          className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto"
        >
          AI-powered video generation turns any topic into an engaging presentation—complete with
          slides, voiceover, and quiz questions—in under five minutes.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 2, duration: 0.5, type: 'spring' }}
        >
          <GradientButton
            onClick={() => router.push('/generator')}
            className="text-xl px-12 py-5"
          >
            Create Your First Lecture
          </GradientButton>
        </motion.div>
      </div>
    </section>
  );
}
