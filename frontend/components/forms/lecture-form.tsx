'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopicInput from './topic-input';
import AudienceSelect from './audience-select';
import DurationSlider from './duration-slider';
import ThemeSelector from './theme-selector';
import GradientButton from '@/components/ui/gradient-button';
import StarBorder from '@/components/StarBorder';
import LoadingDots from '@/components/ui/loading-dots';
import { apiClient } from '@/lib/api';
import { DURATION_OPTIONS } from '@/lib/constants';

export default function LectureForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    topic: '',
    audience: '',
    duration: DURATION_OPTIONS.default,
    theme: '',
    format: 'video' as 'video' | 'interactive' | 'both',  // NEW: Generation format
  });

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.topic.trim()) {
      newErrors.topic = 'Please enter a lecture topic';
    }

    if (!formData.audience) {
      newErrors.audience = 'Please select a target audience';
    }

    if (!formData.theme) {
      newErrors.theme = 'Please select a visual theme';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Generate based on selected format
      if (formData.format === 'interactive') {
        // Generate interactive animation only
        const response = await apiClient.generateAnimations({
          topic: formData.topic,
          audience: formData.audience,
          length: `${formData.duration}`,
          theme: formData.theme,
          interaction_level: 'medium',
          animation_style: 'dynamic',
          include_quizzes: true,
        });
        router.push(`/lecture/${response.task_id}/interactive`);
      } else if (formData.format === 'video') {
        // Generate video only
        const response = await apiClient.generateVideo({
          topic: formData.topic,
          audience: formData.audience,
          length: `${formData.duration}`,
          theme: formData.theme,
        });
        router.push(`/processing/${response.task_id}`);
      } else {
        // Generate both (video first, then animation)
        const videoResponse = await apiClient.generateVideo({
          topic: formData.topic,
          audience: formData.audience,
          length: `${formData.duration}`,
          theme: formData.theme,
        });
        // Trigger animation generation in background (can be done on processing page)
        router.push(`/processing/${videoResponse.task_id}?format=both`);
      }
    } catch (error) {
      console.error('Failed to create lecture:', error);
      setErrors({ submit: 'Failed to create lecture. Please try again.' });
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      <TopicInput
        value={formData.topic}
        onChange={(value) => setFormData({ ...formData, topic: value })}
        error={errors.topic}
      />

      <AudienceSelect
        value={formData.audience}
        onChange={(value) => setFormData({ ...formData, audience: value })}
        error={errors.audience}
      />

      <DurationSlider
        value={formData.duration}
        onChange={(value) => setFormData({ ...formData, duration: value })}
      />

      <ThemeSelector
        value={formData.theme}
        onChange={(value) => setFormData({ ...formData, theme: value })}
        error={errors.theme}
      />

      {/* Format Selector (NEW) */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">
          Output Format
        </label>
        <div className="grid md:grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => setFormData({ ...formData, format: 'video' })}
            className={`p-4 rounded-lg border-2 transition-all ${
              formData.format === 'video'
                ? 'border-primary bg-primary/10'
                : 'border-white/20 hover:border-white/40'
            }`}
          >
            <div className="text-lg font-semibold mb-1">🎥 Video</div>
            <div className="text-sm text-muted-foreground">
              Traditional lecture with voiceover
            </div>
          </button>
          <button
            type="button"
            onClick={() => setFormData({ ...formData, format: 'interactive' })}
            className={`p-4 rounded-lg border-2 transition-all ${
              formData.format === 'interactive'
                ? 'border-primary bg-primary/10'
                : 'border-white/20 hover:border-white/40'
            }`}
          >
            <div className="text-lg font-semibold mb-1">✨ Interactive</div>
            <div className="text-sm text-muted-foreground">
              Step-by-step animated experience
            </div>
          </button>
          <button
            type="button"
            onClick={() => setFormData({ ...formData, format: 'both' })}
            className={`p-4 rounded-lg border-2 transition-all ${
              formData.format === 'both'
                ? 'border-primary bg-primary/10'
                : 'border-white/20 hover:border-white/40'
            }`}
          >
            <div className="text-lg font-semibold mb-1">🎬 Both</div>
            <div className="text-sm text-muted-foreground">
              Video + Interactive versions
            </div>
          </button>
        </div>
      </div>

      {errors.submit && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400">
          {errors.submit}
        </div>
      )}

      <div className="flex justify-center pt-4">
        <StarBorder
          as="div"
          color="rgba(138, 43, 226, 0.9)"
          speed="3s"
          thickness={2}
        >
          <GradientButton type="submit" disabled={isSubmitting} className="px-12 py-4 text-lg">
            {isSubmitting ? <LoadingDots /> : 'Generate Lecture'}
          </GradientButton>
        </StarBorder>
      </div>
    </form>
  );
}
