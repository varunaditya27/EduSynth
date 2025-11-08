'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, Lecture, QuizResponse } from '@/lib/api';
import Iridescence from '@/components/Iridescence';
import VideoPlayer from '@/components/sections/video-player';
import GlassCard from '@/components/ui/glass-card';
import GradientButton from '@/components/ui/gradient-button';
import StatusBadge from '@/components/ui/status-badge';
import QuizPreviewModal from '@/components/modals/quiz-preview-modal';
import LoadingDots from '@/components/ui/loading-dots';
import ChatWidget from '@/components/chat/chat-widget';
import MindmapWidget from '@/components/mindmap/mindmap-widget';
import { ArrowLeft, Download, FileText, PlayCircle, Brain, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function LectureDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lectureId = params.lectureId as string;

  const [lecture, setLecture] = useState<Lecture | null>(null);
  const [loading, setLoading] = useState(true);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizData, setQuizData] = useState<QuizResponse | null>(null);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [quizError, setQuizError] = useState<string | null>(null);

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

  const handleGenerateQuiz = async () => {
    if (!lecture || generatingQuiz) return;
    
    setGeneratingQuiz(true);
    setQuizError(null);

    try {
      const response = await apiClient.generateQuiz(lectureId, 3, 'plain');
      setQuizData(response);
      setShowQuiz(true);
    } catch (err) {
      console.error('Failed to generate quiz:', err);
      setQuizError(err instanceof Error ? err.message : 'Failed to generate quiz');
    } finally {
      setGeneratingQuiz(false);
    }
  };

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

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
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

                <GradientButton
                  variant="secondary"
                  onClick={() => router.push(`/lecture/${lectureId}/interactive`)}
                >
                  <PlayCircle className="w-5 h-5 mr-2" />
                  Interactive Version
                </GradientButton>
              </div>
            </div>
          </GlassCard>

          {/* Quiz Generation Section */}
          <GlassCard>
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Brain className="w-6 h-6 text-primary" />
                    <h2 className="text-2xl font-bold">Quiz Questions</h2>
                  </div>
                  <p className="text-muted-foreground">
                    {quizData 
                      ? `${quizData.num_questions} AI-generated questions ready for export`
                      : 'Generate comprehension questions based on lecture content'
                    }
                  </p>
                </div>
                <Sparkles className="w-8 h-8 text-primary/50" />
              </div>

              {quizError && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                  <p className="text-sm">{quizError}</p>
                </div>
              )}

              <div className="flex items-center gap-3">
                {!quizData ? (
                  <GradientButton 
                    onClick={handleGenerateQuiz}
                    disabled={generatingQuiz || lecture.status !== 'completed'}
                  >
                    {generatingQuiz ? (
                      <>
                        <LoadingDots />
                        <span className="ml-2">Generating Quiz...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 mr-2" />
                        Generate Quiz
                      </>
                    )}
                  </GradientButton>
                ) : (
                  <>
                    <GradientButton onClick={() => setShowQuiz(true)}>
                      <FileText className="w-5 h-5 mr-2" />
                      View Quiz ({quizData.num_questions} Questions)
                    </GradientButton>
                    <GradientButton 
                      variant="secondary"
                      onClick={handleGenerateQuiz}
                      disabled={generatingQuiz}
                    >
                      {generatingQuiz ? 'Regenerating...' : 'Regenerate'}
                    </GradientButton>
                  </>
                )}
              </div>

              {lecture.status !== 'completed' && (
                <p className="text-xs text-muted-foreground">
                  ⚠ Quiz generation available after lecture video is complete
                </p>
              )}
            </div>
          </GlassCard>

          <GlassCard>
            <div className="space-y-4">
              <h2 className="text-2xl font-bold">Concept Map</h2>
              <p className="text-muted-foreground">
                Visualize the lecture structure with an AI-generated mind map
              </p>
              <MindmapWidget lectureId={lecture.id} lectureTopic={lecture.topic} />
            </div>
          </GlassCard>

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

      {quizData && (
        <QuizPreviewModal
          isOpen={showQuiz}
          onClose={() => setShowQuiz(false)}
          questions={quizData.questions}
          topic={quizData.topic}
          formattedText={quizData.formatted_text}
          lectureId={quizData.lecture_id}
        />
      )}

      {/* AI Assistant Chatbot */}
      <ChatWidget topicContext={lecture.topic} lectureId={lecture.id} />
    </div>
  );
}