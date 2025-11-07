'use client';

import { motion } from 'framer-motion';
import SpotlightCard from '@/components/SpotlightCard';
import StarBorder from '@/components/StarBorder';
import { Sparkles, Video, ClipboardList, Zap, Palette, Download } from 'lucide-react';

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Generation',
    description: 'Transform any topic into a complete lecture with slides, voiceover, and synchronized content in minutes.',
    gradient: 'from-blue-500 to-purple-500',
    spotlightColor: 'rgba(65, 105, 225, 0.2)' as const,
  },
  {
    icon: Video,
    title: 'Professional Quality',
    description: 'Choose from multiple visual themes and get cinema-quality videos ready to download and share.',
    gradient: 'from-purple-500 to-pink-500',
    spotlightColor: 'rgba(186, 85, 211, 0.2)' as const,
  },
  {
    icon: ClipboardList,
    title: 'Quiz Generator',
    description: 'Automatically generate relevant quiz questions to reinforce learning and assess comprehension.',
    gradient: 'from-pink-500 to-rose-500',
    spotlightColor: 'rgba(255, 105, 180, 0.2)' as const,
  },
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Generate complete video lectures in under 5 minutes with our optimized AI pipeline.',
    gradient: 'from-cyan-500 to-blue-500',
    spotlightColor: 'rgba(65, 105, 225, 0.2)' as const,
  },
  {
    icon: Palette,
    title: 'Multiple Themes',
    description: 'Choose from Minimalist, Chalkboard, Corporate, Modern, or Gradient visual styles.',
    gradient: 'from-violet-500 to-purple-500',
    spotlightColor: 'rgba(138, 43, 226, 0.2)' as const,
  },
  {
    icon: Download,
    title: 'Export Ready',
    description: 'Download your lecture as MP4 video and PDF slides, ready to use anywhere.',
    gradient: 'from-fuchsia-500 to-pink-500',
    spotlightColor: 'rgba(255, 20, 147, 0.2)' as const,
  },
];

export default function FeatureGrid() {
  return (
    <section id="features" className="py-20 px-4 relative">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-linear-to-b from-transparent via-black/40 to-black/60 pointer-events-none" />
      
      <div className="max-w-7xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-block px-4 py-2 mb-6 rounded-full bg-white/5 backdrop-blur-sm border border-white/10"
          >
            <span className="text-sm font-medium text-primary">Feature Packed</span>
          </motion.div>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 gradient-text">
            Everything You Need to Create Engaging Lectures
          </h2>
          <p className="text-xl text-white/70 max-w-2xl mx-auto">
            Powerful features designed for educators, trainers, and content creators
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              whileHover={{ y: -8, scale: 1.02 }}
            >
              <SpotlightCard
                spotlightColor={feature.spotlightColor}
                className="h-full"
              >
                <div className="flex flex-col items-start space-y-4">
                  {/* Icon with gradient background */}
                  <motion.div
                    whileHover={{ rotate: 360, scale: 1.1 }}
                    transition={{ duration: 0.6, type: 'spring' }}
                    className={`w-14 h-14 rounded-xl bg-linear-to-br ${feature.gradient} p-0.5`}
                  >
                    <div className="w-full h-full rounded-xl bg-black/80 backdrop-blur-sm flex items-center justify-center">
                      <feature.icon className="w-7 h-7 text-white" />
                    </div>
                  </motion.div>

                  <div className="space-y-2">
                    <h3 className="text-xl font-bold text-white group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-white/60 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </SpotlightCard>
            </motion.div>
          ))}
        </div>

        {/* Call to action */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-16 text-center"
        >
          <p className="text-lg text-white/70 mb-6">
            Ready to revolutionize your content creation?
          </p>
          <StarBorder
            as="a"
            href="/generator"
            color="rgba(255, 105, 180, 0.8)"
            speed="3s"
            thickness={2}
            className="inline-block cursor-pointer"
          >
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-8 py-4 rounded-lg font-semibold text-white bg-linear-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg shadow-purple-500/25 flex items-center gap-2"
            >
              Start Creating Now
              <Sparkles className="w-5 h-5" />
            </motion.div>
          </StarBorder>
        </motion.div>
      </div>
    </section>
  );
}
