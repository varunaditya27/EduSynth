'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Lecture } from '@/lib/api';
import GlassCard from '@/components/ui/glass-card';
import StatusBadge from '@/components/ui/status-badge';
import { Calendar, Clock, Eye, Download, Trash2 } from 'lucide-react';

interface LectureCardProps {
  lecture: Lecture;
  onDelete?: (id: string) => void;
}

export default function LectureCard({ lecture, onDelete }: LectureCardProps) {
  const router = useRouter();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <GlassCard className="group cursor-pointer relative">
      <div onClick={() => router.push(`/lecture/${lecture.id}`)}>
        <div className="aspect-video bg-linear-to-br from-primary/20 to-accent/20 rounded-lg mb-4 flex items-center justify-center overflow-hidden">
          {lecture.thumbnailUrl ? (
            <img src={lecture.thumbnailUrl} alt={lecture.topic} className="w-full h-full object-cover" />
          ) : (
            <div className="text-6xl opacity-20">🎬</div>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-bold text-lg line-clamp-2 flex-1">{lecture.topic}</h3>
            <StatusBadge status={lecture.status} />
          </div>

          <p className="text-sm text-muted-foreground line-clamp-1">{lecture.audience}</p>

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{formatDate(lecture.createdAt)}</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{lecture.duration} min</span>
            </div>
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        className="absolute top-4 right-4 flex gap-2"
      >
        {lecture.status === 'completed' && (
          <>
            <motion.button
              onClick={(e) => {
                e.stopPropagation();
                router.push(`/lecture/${lecture.id}`);
              }}
              className="p-2 rounded-lg bg-primary/90 text-white hover:bg-primary"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
            >
              <Eye className="w-4 h-4" />
            </motion.button>
            {lecture.videoUrl && (
              <motion.a
                href={lecture.videoUrl}
                download
                onClick={(e) => e.stopPropagation()}
                className="p-2 rounded-lg bg-accent/90 text-white hover:bg-accent"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Download className="w-4 h-4" />
              </motion.a>
            )}
          </>
        )}
        {onDelete && (
          <motion.button
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('Are you sure you want to delete this lecture?')) {
                onDelete(lecture.id);
              }
            }}
            className="p-2 rounded-lg bg-red-500/90 text-white hover:bg-red-500"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        )}
      </motion.div>
    </GlassCard>
  );
}
