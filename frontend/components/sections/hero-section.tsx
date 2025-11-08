'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import GradientButton from '@/components/ui/gradient-button';
import StarBorder from '@/components/StarBorder';
import SplitText from '@/components/SplitText';
import AuthModal from '@/components/modals/auth-modal';
import { Sparkles, Lock } from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';

export default function HeroSection() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  const handleCreateLecture = () => {
    if (isAuthenticated) {
      router.push('/generator');
    } else {
      setAuthModalOpen(true);
    }
  };

  const title = 'Transform Knowledge Into Cinematic Lectures';

  return (
    <section className="relative min-h-screen flex items-center justify-center px-4 pt-16">
      <div className="max-w-5xl mx-auto text-center space-y-8">
        {/* Animated badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 backdrop-blur-sm border border-white/10"
        >
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-primary">Powered by Advanced AI</span>
        </motion.div>

        {/* SplitText Title */}
        <div className="text-5xl md:text-7xl lg:text-8xl font-bold leading-tight">
          <SplitText
            text={title}
            tag="h1"
            delay={50}
            duration={0.8}
            ease="power3.out"
            splitType="chars"
            threshold={0.1}
            className="inline-block"
            from={{ opacity: 0, y: 60, rotateX: -90 }}
            to={{ opacity: 1, y: 0, rotateX: 0 }}
            textAlign="center"
          />
        </div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.8 }}
          className="text-xl md:text-2xl text-white/80 max-w-3xl mx-auto leading-relaxed"
          style={{ textShadow: '0 2px 20px rgba(0, 0, 0, 0.5)' }}
        >
          AI-powered video generation turns any topic into an engaging presentation—complete with
          slides, voiceover, and quiz questions—in under five minutes.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.8, duration: 0.5, type: 'spring' }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <StarBorder
            as="div"
            color={isAuthenticated ? "rgba(138, 43, 226, 0.8)" : "rgba(156, 163, 175, 0.5)"}
            speed="4s"
            thickness={2}
          >
            <GradientButton
              onClick={handleCreateLecture}
              size="lg"
              className={`group relative overflow-hidden ${!isAuthenticated ? 'opacity-75 cursor-pointer' : ''}`}
            >
              <span className="relative z-10 flex items-center gap-2">
                {!isAuthenticated && <Lock className="w-4 h-4" />}
                Create Your First Lecture
                <motion.span
                  animate={{ x: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                >
                  →
                </motion.span>
              </span>
            </GradientButton>
          </StarBorder>
          
          {!isAuthenticated && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 2.0 }}
              className="text-sm text-white/50 -mt-2"
            >
          
            </motion.p>
          )}
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              const featuresSection = document.querySelector('#features');
              featuresSection?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="px-8 py-4 rounded-lg font-semibold text-white bg-white/5 backdrop-blur-sm border border-white/20 hover:bg-white/10 transition-all"
          >
            See How It Works
          </motion.button>
        </motion.div>

        {/* Floating stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.2, duration: 0.8 }}
          className="pt-12 flex flex-wrap justify-center gap-8 md:gap-16"
        >
          {[
            { value: '5min', label: 'Generation Time' },
            { value: '5+', label: 'Visual Themes' },
            { value: 'HD', label: 'Video Quality' },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 2.4 + index * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl md:text-4xl font-bold gradient-text mb-1">
                {stat.value}
              </div>
              <div className="text-sm text-white/60">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        defaultMode="signup"
      />
    </section>
  );
}
