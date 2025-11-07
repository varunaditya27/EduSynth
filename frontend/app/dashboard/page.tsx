'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, Lecture } from '@/lib/api';
import Iridescence from '@/components/Iridescence';
import ThemeToggle from '@/components/ui/theme-toggle';
import GradientButton from '@/components/ui/gradient-button';
import LectureList from '@/components/sections/lecture-list';
import LoadingDots from '@/components/ui/loading-dots';
import { Plus } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLectures();
  }, []);

  const fetchLectures = async () => {
    try {
      const data = await apiClient.getLectures();
      setLectures(data);
    } catch (err) {
      console.error('Failed to fetch lectures:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiClient.deleteLecture(id);
      setLectures(lectures.filter((lecture) => lecture.id !== id));
    } catch (err) {
      console.error('Failed to delete lecture:', err);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Iridescence
        color={[0.4, 0.5, 0.9]}
        speed={0.3}
        amplitude={0.1}
        mouseReact={false}
      />

      <div className="relative z-10 min-h-screen py-12 px-4">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-5xl font-bold gradient-text mb-2">Your Lectures</h1>
              <p className="text-muted-foreground">
                Manage and view all your generated lectures
              </p>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <GradientButton onClick={() => router.push('/generator')}>
                <Plus className="w-5 h-5 mr-2" />
                Create New
              </GradientButton>
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <LoadingDots />
            </div>
          ) : (
            <>
              {lectures.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 space-y-6">
                  <div className="text-8xl opacity-20">🎓</div>
                  <div className="text-center space-y-2">
                    <h3 className="text-2xl font-bold">Your lecture studio is ready</h3>
                    <p className="text-muted-foreground">
                      Let&apos;s create something amazing
                    </p>
                  </div>
                  <GradientButton onClick={() => router.push('/generator')}>
                    <Plus className="w-5 h-5 mr-2" />
                    Create First Lecture
                  </GradientButton>
                </div>
              ) : (
                <LectureList lectures={lectures} onDelete={handleDelete} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
