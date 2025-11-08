export const VISUAL_THEMES = [
  {
    id: 'minimalist',
    name: 'Minimalist',
    description: 'Clean lines, ample whitespace, sophisticated simplicity',
    colors: ['#FFFFFF', '#F5F5F5', '#E0E0E0'],
    preview: 'bg-gradient-to-br from-gray-50 to-gray-100',
  },
  {
    id: 'chalkboard',
    name: 'Chalkboard',
    description: 'Classic classroom aesthetic with chalk-drawn elements',
    colors: ['#2C3E2C', '#4A5D4A', '#A8D5A8'],
    preview: 'bg-gradient-to-br from-green-900 to-green-800',
  },
  {
    id: 'corporate',
    name: 'Corporate',
    description: 'Professional navy and gold palette for business topics',
    colors: ['#1A237E', '#3949AB', '#FFD700'],
    preview: 'bg-gradient-to-br from-blue-900 to-blue-700',
  },
  {
    id: 'modern',
    name: 'Modern',
    description: 'Bold colors, geometric shapes, contemporary design',
    colors: ['#6200EA', '#B388FF', '#FF4081'],
    preview: 'bg-gradient-to-br from-purple-600 to-pink-500',
  },
  {
    id: 'gradient',
    name: 'Gradient',
    description: 'Vibrant multi-color transitions, eye-catching visuals',
    colors: ['#667EEA', '#764BA2', '#F093FB'],
    preview: 'bg-gradient-to-br from-blue-500 via-purple-500 to-pink-400',
  },
];

export const TOPIC_EXAMPLES = [
  'Explain photosynthesis for 10th-grade students',
  'Introduction to machine learning algorithms',
  'The water cycle and its environmental impact',
  'Renaissance art history overview',
  'Basic principles of quantum mechanics',
  'Digital marketing strategies for beginners',
];

export const AUDIENCE_OPTIONS = [
  'Elementary School (Grades 1-5)',
  'Middle School (Grades 6-8)',
  'High School (Grades 9-12)',
  'Undergraduate Students',
  'Graduate Students',
  'Professional Audience',
  'General Public',
];

export const DURATION_OPTIONS = {
  min: 1,
  max: 5,
  step: 1,
  default: 2,
};

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const POLLING_INTERVAL = 2000; // 2 seconds

export const LECTURE_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;
