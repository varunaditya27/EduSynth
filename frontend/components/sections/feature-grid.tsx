'use client';

import { motion } from 'framer-motion';
import GlassCard from '@/components/ui/glass-card';
import { Sparkles, Video, ClipboardList } from 'lucide-react';

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Generation',
    description: 'Transform any topic into a complete lecture with slides, voiceover, and synchronized content in minutes.',
  },
  {
    icon: Video,
    title: 'Professional Quality',
    description: 'Choose from multiple visual themes and get cinema-quality videos ready to download and share.',
  },
  {
    icon: ClipboardList,
    title: 'Quiz Generator',
    description: 'Automatically generate relevant quiz questions to reinforce learning and assess comprehension.',
  },
];

export default function FeatureGrid() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Everything You Need to Create Engaging Lectures
          </h2>
          <p className="text-xl text-muted-foreground">
            Powerful features designed for educators, trainers, and content creators
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2, duration: 0.5 }}
            >
              <GlassCard className="h-full">
                <div className="flex flex-col items-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                    <feature.icon className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
