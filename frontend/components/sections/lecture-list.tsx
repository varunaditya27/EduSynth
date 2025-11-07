'use client';

import { motion } from 'framer-motion';
import { Lecture } from '@/lib/api';
import LectureCard from './lecture-card';

interface LectureListProps {
  lectures: Lecture[];
  onDelete?: (id: string) => void;
}

export default function LectureList({ lectures, onDelete }: LectureListProps) {
  if (lectures.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="text-8xl opacity-20">🎓</div>
        <h3 className="text-2xl font-bold">Your lecture studio is ready</h3>
        <p className="text-muted-foreground">Let&apos;s create something amazing</p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {lectures.map((lecture, index) => (
        <motion.div
          key={lecture.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.3 }}
        >
          <LectureCard lecture={lecture} onDelete={onDelete} />
        </motion.div>
      ))}
    </div>
  );
}
