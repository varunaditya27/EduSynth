'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, Lecture } from '@/lib/api';
import Iridescence from '@/components/Iridescence';
import VideoPlayer from '@/components/sections/video-player';
import GlassCard from '@/components/ui/glass-card';
import GradientButton from '@/components/ui/gradient-button';
import StatusBadge from '@/components/ui/status-badge';
import QuizPreviewModal from '@/components/modals/quiz-preview-modal';
import LoadingDots from '@/components/ui/loading-dots';
import { ArrowLeft, Download, FileText, PlayCircle } from 'lucide-react';
import Link from 'next/link';

export default function LectureDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lectureId = params.lectureId as string;

  const [lecture, setLecture] = useState<Lecture | null>(null);
  const [loading, setLoading] = useState(true);
  const [showQuiz, setShowQuiz] = useState(false);

  useEffect(() => {
    if (!lectureId) return;

    const fetchLecture = async () => {
      try {
        const data = await apiClient.getLecture(lectureId);
        setLecture(data);
      } catch (err) {
        console.error('Failed to fetch lecture:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLecture();
  }, [lectureId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingDots />
      </div>
    );
  }

  if (!lecture) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">Lecture not found</h2>
          <GradientButton onClick={() => router.push('/dashboard')}>
            Back to Dashboard
          </GradientButton>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Iridescence
        color={[0.3, 0.4, 0.8]}
        speed={0.3}
        amplitude={0.1}
        mouseReact={false}
      />

      <div className="relative z-10 min-h-screen py-12 px-4">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Dashboard
            </Link>
          </div>

          <GlassCard>
            <div className="space-y-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <h1 className="text-4xl font-bold">{lecture.topic}</h1>
                  <p className="text-muted-foreground">
                    {lecture.audience} • {lecture.duration} minutes
                  </p>
                </div>
                <StatusBadge status={lecture.status} />
              </div>

              {lecture.status === 'completed' && lecture.videoUrl ? (
                <VideoPlayer src={lecture.videoUrl} poster={lecture.thumbnailUrl} />
              ) : (
                <div className="aspect-video bg-linear-to-br from-primary/20 to-accent/20 rounded-lg flex items-center justify-center">
                  <div className="text-center space-y-4">
                    <PlayCircle className="w-16 h-16 mx-auto text-muted-foreground" />
                    <p className="text-muted-foreground">
                      {lecture.status === 'processing'
                        ? 'Video is being generated...'
                        : 'Video not available yet'}
                    </p>
                  </div>
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-4">
                {lecture.videoUrl && (
                  <GradientButton
                    onClick={() => {
                      const a = document.createElement('a');
                      a.href = lecture.videoUrl!;
                      a.download = `${lecture.topic}.mp4`;
                      a.click();
                    }}
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download Video
                  </GradientButton>
                )}

                {lecture.slidesUrl && (
                  <GradientButton
                    variant="secondary"
                    onClick={() => {
                      const a = document.createElement('a');
                      a.href = lecture.slidesUrl!;
                      a.download = `${lecture.topic}-slides.pdf`;
                      a.click();
                    }}
                  >
                    <FileText className="w-5 h-5 mr-2" />
                    Download Slides
                  </GradientButton>
                )}
              </div>
            </div>
          </GlassCard>

          {lecture.quizQuestions && lecture.quizQuestions.length > 0 && (
            <GlassCard>
              <div className="space-y-4">
                <h2 className="text-2xl font-bold">Quiz Questions</h2>
                <p className="text-muted-foreground">
                  Test comprehension with {lecture.quizQuestions.length} auto-generated questions
                </p>
                <GradientButton onClick={() => setShowQuiz(true)}>
                  View Quiz Questions
                </GradientButton>
              </div>
            </GlassCard>
          )}

          <GlassCard>
            <div className="space-y-4">
              <h2 className="text-2xl font-bold">Lecture Details</h2>
              <dl className="grid md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-muted-foreground">Theme</dt>
                  <dd className="font-semibold capitalize">{lecture.theme}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Created</dt>
                  <dd className="font-semibold">
                    {new Date(lecture.createdAt).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </dd>
                </div>
              </dl>
            </div>
          </GlassCard>
        </div>
      </div>

      {lecture.quizQuestions && (
        <QuizPreviewModal
          isOpen={showQuiz}
          onClose={() => setShowQuiz(false)}
          questions={lecture.quizQuestions}
        />
      )}
    </div>
  );
}
