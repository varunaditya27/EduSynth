'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, Lecture } from '@/lib/api';
import { POLLING_INTERVAL } from '@/lib/constants';
import Iridescence from '@/components/Iridescence';
import ProgressIndicator from '@/components/sections/progress-indicator';
import ErrorModal from '@/components/modals/error-modal';

const STAGES = [
  { progress: 20, label: 'Analyzing topic and generating outline' },
  { progress: 40, label: 'Creating slide content and visuals' },
  { progress: 60, label: 'Generating voiceover narration' },
  { progress: 80, label: 'Synchronizing video and audio' },
  { progress: 100, label: 'Finalizing lecture package' },
];

export default function ProcessingPage() {
  const router = useRouter();
  const params = useParams();
  const lectureId = params.lectureId as string;

  const [lecture, setLecture] = useState<Lecture | null>(null);
  const [currentStage, setCurrentStage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lectureId) return;

    const pollStatus = async () => {
      try {
        const data = await apiClient.getLecture(lectureId);
        setLecture(data);

        if (data.status === 'completed') {
          router.push(`/lecture/${lectureId}`);
        } else if (data.status === 'failed') {
          setError(data.errorMessage || 'Something went wrong during generation');
        } else if (data.progress) {
          const stageIndex = Math.floor((data.progress / 100) * STAGES.length);
          setCurrentStage(Math.min(stageIndex, STAGES.length - 1));
        }
      } catch (err) {
        console.error('Failed to fetch lecture status:', err);
        setError('Failed to fetch lecture status. Please check your connection.');
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [lectureId, router]);

  const handleRetry = () => {
    router.push('/generator');
  };

  const progress = lecture?.progress || STAGES[currentStage]?.progress || 0;
  const stage = STAGES[currentStage]?.label || 'Processing...';

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Iridescence
        color={[0.3, 0.5, 0.9]}
        speed={0.5}
        amplitude={0.3}
        mouseReact={false}
      />

      <div className="relative z-10 min-h-screen flex items-center justify-center px-4">
        <div className="max-w-2xl w-full text-center space-y-12">
          <div className="space-y-4">
            <h1 className="text-4xl md:text-5xl font-bold gradient-text">
              Creating Your Lecture
            </h1>
            <p className="text-xl text-muted-foreground">
              Please wait while we generate your complete lecture package
            </p>
          </div>

          <ProgressIndicator progress={progress} stage={stage} />

          {lecture && (
            <div className="backdrop-blur-md bg-white/10 dark:bg-gray-900/50 border border-white/20 dark:border-white/10 rounded-xl p-6 space-y-2">
              <h3 className="font-semibold text-lg">{lecture.topic}</h3>
              <p className="text-sm text-muted-foreground">
                {lecture.audience} • {lecture.duration} minutes • {lecture.theme} theme
              </p>
            </div>
          )}
        </div>
      </div>

      <ErrorModal
        isOpen={!!error}
        onClose={() => setError(null)}
        title="Generation Failed"
        message={error || ''}
        onRetry={handleRetry}
      />
    </div>
  );
}
