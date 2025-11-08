'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, SlideAnimation, LectureAnimations } from '@/lib/api';
import Iridescence from '@/components/Iridescence';
import GlassCard from '@/components/ui/glass-card';
import GradientButton from '@/components/ui/gradient-button';
import LoadingDots from '@/components/ui/loading-dots';
import { ArrowLeft, ArrowRight, Play, Pause, RotateCcw } from 'lucide-react';
import Link from 'next/link';

export default function InteractiveLecturePage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.lectureId as string;

  const [animations, setAnimations] = useState<LectureAnimations | null>(null);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [completedSlides, setCompletedSlides] = useState<number[]>([]);
  const [score, setScore] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    const fetchAnimations = async () => {
      try {
        const data = await apiClient.getAnimations(taskId);
        setAnimations(data);
      } catch (err) {
        console.error('Failed to fetch animations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnimations();
  }, [taskId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingDots />
      </div>
    );
  }

  if (!animations) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">Animations not found</h2>
          <GradientButton onClick={() => router.push('/generator')}>
            Create New Lecture
          </GradientButton>
        </div>
      </div>
    );
  }

  const currentSlide = animations.slides[currentSlideIndex];
  const totalSlides = animations.slides.length;
  const progress = ((currentSlideIndex + 1) / totalSlides) * 100;

  const handleNextSlide = () => {
    if (currentSlideIndex < totalSlides - 1) {
      setCurrentSlideIndex(currentSlideIndex + 1);
      setCurrentStepIndex(0);
      setShowFeedback(false);
      setSelectedAnswer(null);
      
      // Track progress
      if (!completedSlides.includes(currentSlideIndex)) {
        const newCompleted = [...completedSlides, currentSlideIndex];
        setCompletedSlides(newCompleted);
        apiClient.trackAnimationProgress(taskId, {
          completed_slides: newCompleted,
          score,
        }).catch(console.error);
      }
    }
  };

  const handlePreviousSlide = () => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex(currentSlideIndex - 1);
      setCurrentStepIndex(0);
      setShowFeedback(false);
      setSelectedAnswer(null);
    }
  };

  const handleNextStep = () => {
    if (currentStepIndex < currentSlide.steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePreviousStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleAnswerSelect = (answer: string, interaction: any) => {
    setSelectedAnswer(answer);
    setShowFeedback(true);

    if (answer === interaction.correct_answer) {
      setScore(score + 10);
    }
  };

  const handleRestart = () => {
    setCurrentSlideIndex(0);
    setCurrentStepIndex(0);
    setCompletedSlides([]);
    setScore(0);
    setShowFeedback(false);
    setSelectedAnswer(null);
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Iridescence
        color={[0.3, 0.5, 0.9]}
        speed={0.4}
        amplitude={0.2}
        mouseReact={false}
      />

      <div className="relative z-10 min-h-screen py-8 px-4">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <Link
              href="/generator"
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back
            </Link>
            <div className="text-sm text-muted-foreground">
              {completedSlides.length} / {totalSlides} slides completed • {score} points
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-white/10 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary to-accent h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Main Content */}
          <GlassCard>
            <div className="space-y-6">
              {/* Slide Title */}
              <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold">{currentSlide.title}</h1>
                <p className="text-muted-foreground">{currentSlide.concept}</p>
                <div className="flex items-center justify-center gap-4 text-sm">
                  <span className="px-3 py-1 rounded-full bg-primary/20">
                    Slide {currentSlideIndex + 1} of {totalSlides}
                  </span>
                  <span className="px-3 py-1 rounded-full bg-accent/20">
                    {currentSlide.difficulty}
                  </span>
                </div>
              </div>

              {/* Animation Canvas */}
              <div className="aspect-video bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg flex items-center justify-center relative overflow-hidden">
                {/* Current Step Display */}
                <div className="absolute inset-0 p-8 flex flex-col items-center justify-center">
                  {currentSlide.steps[currentStepIndex] && (
                    <div className="text-center space-y-4 animate-fade-in">
                      <h2 className="text-2xl font-semibold">
                        {currentSlide.steps[currentStepIndex].description}
                      </h2>
                      {currentSlide.steps[currentStepIndex].narration_text && (
                        <p className="text-lg text-muted-foreground max-w-2xl">
                          {currentSlide.steps[currentStepIndex].narration_text}
                        </p>
                      )}
                      {/* Render elements */}
                      <div className="grid grid-cols-2 gap-4 mt-6">
                        {currentSlide.steps[currentStepIndex].elements.map((element, idx) => (
                          <div
                            key={element.id}
                            className="p-4 bg-white/5 rounded-lg backdrop-blur-sm"
                            style={{
                              animationDelay: `${idx * 200}ms`,
                            }}
                          >
                            <div className="font-medium">{element.type}</div>
                            <div className="text-sm text-muted-foreground mt-1">
                              {element.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Step Navigation */}
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center gap-4">
                  <button
                    onClick={handlePreviousStep}
                    disabled={currentStepIndex === 0}
                    className="p-2 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm">
                    Step {currentStepIndex + 1} / {currentSlide.steps.length}
                  </span>
                  <button
                    onClick={handleNextStep}
                    disabled={currentStepIndex === currentSlide.steps.length - 1}
                    className="p-2 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Interactions */}
              {currentSlide.interactions.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold">Interactive Challenge</h3>
                  {currentSlide.interactions.map((interaction, idx) => (
                    <div key={interaction.id} className="space-y-3">
                      <p className="font-medium">{interaction.prompt}</p>

                      {interaction.type === 'multiple_choice' && interaction.options && (
                        <div className="grid gap-2">
                          {interaction.options.map((option, optIdx) => (
                            <button
                              key={optIdx}
                              onClick={() => handleAnswerSelect(option, interaction)}
                              disabled={showFeedback}
                              className={`p-4 rounded-lg text-left transition-all ${
                                showFeedback
                                  ? option === interaction.correct_answer
                                    ? 'bg-green-500/20 border-2 border-green-500'
                                    : option === selectedAnswer
                                    ? 'bg-red-500/20 border-2 border-red-500'
                                    : 'bg-white/5 border border-white/20'
                                  : 'bg-white/10 hover:bg-white/20 border border-white/20'
                              }`}
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      )}

                      {showFeedback && interaction.success_message && (
                        <div
                          className={`p-4 rounded-lg ${
                            selectedAnswer === interaction.correct_answer
                              ? 'bg-green-500/20 border border-green-500'
                              : 'bg-red-500/20 border border-red-500'
                          }`}
                        >
                          {selectedAnswer === interaction.correct_answer
                            ? interaction.success_message
                            : interaction.hint || 'Try again!'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex items-center justify-between pt-4">
                <GradientButton
                  onClick={handlePreviousSlide}
                  disabled={currentSlideIndex === 0}
                  variant="secondary"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Previous Slide
                </GradientButton>

                {currentSlideIndex === totalSlides - 1 ? (
                  <GradientButton onClick={handleRestart}>
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Restart
                  </GradientButton>
                ) : (
                  <GradientButton onClick={handleNextSlide}>
                    Next Slide
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </GradientButton>
                )}
              </div>
            </div>
          </GlassCard>

          {/* Summary Card */}
          <GlassCard>
            <div className="grid md:grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold">{animations.interaction_count}</div>
                <div className="text-sm text-muted-foreground">Total Interactions</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{Math.floor(animations.total_estimated_time_seconds / 60)} min</div>
                <div className="text-sm text-muted-foreground">Estimated Time</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{animations.gamification.badges.length}</div>
                <div className="text-sm text-muted-foreground">Badges Available</div>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
