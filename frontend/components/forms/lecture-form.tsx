'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopicInput from './topic-input';
import AudienceSelect from './audience-select';
import DurationSlider from './duration-slider';
import ThemeSelector from './theme-selector';
import GradientButton from '@/components/ui/gradient-button';
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
      const lecture = await apiClient.createLecture(formData);
      router.push(`/processing/${lecture.id}`);
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

      {errors.submit && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400">
          {errors.submit}
        </div>
      )}

      <div className="flex justify-center pt-4">
        <GradientButton type="submit" disabled={isSubmitting} className="px-12 py-4 text-lg">
          {isSubmitting ? <LoadingDots /> : 'Generate Lecture'}
        </GradientButton>
      </div>
    </form>
  );
}
