import { API_BASE_URL } from './constants';

export interface Lecture {
  id: string;
  topic: string;
  audience: string;
  duration: number;
  theme: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  videoUrl?: string;
  slidesUrl?: string;
  quizQuestions?: QuizQuestion[];
  createdAt: string;
  thumbnailUrl?: string;
  progress?: number;
  errorMessage?: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correctAnswer: number;
  correct_answer?: number;  // Backend compatibility
  explanation?: string;
  difficulty?: string;
}

export interface QuizResponse {
  lecture_id: string;
  topic: string;
  num_questions: number;
  questions: QuizQuestion[];
  formatted_text: string;
  format: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
  topic_context?: string;
  lecture_id?: string;
}

export interface ChatResponse {
  message: string;
  timestamp: string;
  conversation_id?: string;
  model: string;
}

export interface MindMapNode {
  id: string;
  label: string;
  description?: string;
}

export interface MindMapChild {
  id: string;
  label: string;
  description?: string;
}

export interface MindMapBranch {
  id: string;
  label: string;
  parent: string;
  description?: string;
  children: MindMapChild[];
}

export interface MindMapConnection {
  from: string;
  to: string;
  type: string;
}

export interface MindMapData {
  central: MindMapNode;
  branches: MindMapBranch[];
  connections: MindMapConnection[];
}

export interface MindMapResponse {
  lecture_id: string;
  mindmap_id: string;
  mind_map: MindMapData;
  mermaid_syntax: string;
  metadata: {
    node_count: number;
    branch_count: number;
    max_depth: number;
    connection_count?: number;
  };
  created_at: string;
}

export interface MindMapRetrieveResponse {
  lecture_id: string;
  mindmap_id: string;
  mind_map: MindMapData;
  mermaid_syntax: string;
  metadata: {
    node_count: number;
    branch_count: number;
    max_depth: number;
    connection_count?: number;
  };
  created_at: string;
  updated_at: string;
}

export interface MindMapDeleteResponse {
  message: string;
  lecture_id: string;
  deleted_at: string;
}

export interface MindMapHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  gemini_available: boolean;
  database_connected: boolean;
}

export interface MindMapGenerateRequest {
  lecture_id: string;
  regenerate?: boolean;
  max_branches?: number;
  max_depth?: number;
}

export interface CreateLectureInput {
  topic: string;
  audience: string;
  duration: number;
  theme: string;
  format?: 'video' | 'interactive' | 'both'; // NEW: Choose generation type
}

export interface GenerateVideoRequest {
  topic: string;
  audience: string;
  length: string; // "5 min" or "5"
  theme: string;
}

export interface GenerateVideoResponse {
  task_id: string;
  status: string;
  message: string;
}

// Animation Interfaces (NEW)
export interface AnimationElement {
  id: string;
  type: 'text' | 'shape' | 'image' | 'diagram' | 'arrow' | 'icon' | 'equation';
  content: string;
  position: { x: number; y: number };
  style?: Record<string, any>;
}

export interface AnimationStep {
  step_number: number;
  description: string;
  elements: AnimationElement[];
  animation_type: 'fade_in' | 'slide_in' | 'scale_up' | 'draw' | 'typewriter' | 'bounce' | 'rotate' | 'morph' | 'particle' | 'highlight';
  duration_ms: number;
  delay_ms?: number;
  audio_segment_start?: number;
  audio_segment_end?: number;
  narration_text?: string;
}

export interface InteractionPoint {
  id: string;
  type: 'click_to_reveal' | 'drag_and_drop' | 'hover_info' | 'input_answer' | 'multiple_choice' | 'slider_adjust' | 'simulation' | 'auto_advance';
  prompt: string;
  target_element_id?: string;
  position: { x: number; y: number };
  correct_answer?: string;
  options?: string[];
  success_message?: string;
  hint?: string;
  unlocks_step?: number;
}

export interface SlideAnimation {
  slide_index: number;
  title: string;
  steps: AnimationStep[];
  interactions: InteractionPoint[];
  concept: string;
  difficulty: 'easy' | 'medium' | 'hard';
  estimated_time_seconds: number;
  theme_effects?: Record<string, any>;
}

export interface LectureAnimations {
  lecture_id: string;
  topic: string;
  audience: string;
  theme: string;
  slides: SlideAnimation[];
  total_estimated_time_seconds: number;
  interaction_count: number;
  gamification: {
    total_points: number;
    badges: string[];
    progress_tracking: boolean;
  };
}

export interface AnimationGenerationRequest {
  topic: string;
  audience: string;
  length: string;
  theme: string;
  interaction_level?: 'low' | 'medium' | 'high';
  animation_style?: 'gentle' | 'dynamic' | 'professional';
  include_simulations?: boolean;
  include_quizzes?: boolean;
}

export interface AnimationGenerationResponse {
  task_id: string;
  status: string;
  message: string;
  estimated_time_seconds: number;
  interaction_count: number;
}

export interface AnimationMetadata {
  task_id: string;
  topic: string;
  audience: string;
  theme: string;
  slide_count: number;
  interaction_count: number;
  estimated_time_seconds: number;
  gamification: Record<string, any>;
  slides_overview: Array<{
    index: number;
    title: string;
    concept: string;
    steps: number;
    interactions: number;
    difficulty: string;
  }>;
}

export interface ProgressTrackingRequest {
  completed_slides: number[];
  score?: number;
}

export interface ProgressTrackingResponse {
  progress_percent: number;
  completed_slides: number;
  total_slides: number;
  remaining_slides: number;
  estimated_time_remaining: number;
  points_earned: number;
  points_possible: number;
  next_slide_index: number;
  completion_status: string;
}

// Authentication Interfaces
export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface UserInfo {
  id: string;
  email: string;
  name?: string;
  created_at: string;
}

export interface GoogleAuthRequest {
  id_token: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async createLecture(data: CreateLectureInput): Promise<Lecture> {
    const response = await fetch(`${this.baseUrl}/api/lectures`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to create lecture');
    }

    return response.json();
  }

  // Video Generation Methods (NEW)
  async generateVideo(data: GenerateVideoRequest): Promise<GenerateVideoResponse> {
    const response = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate video' }));
      throw new Error(error.detail || 'Failed to generate video');
    }

    return response.json();
  }

  async getVideoStatus(taskId: string): Promise<{ status: string; progress?: number; videoUrl?: string; errorMessage?: string }> {
    // This endpoint needs to be added to the backend
    const response = await fetch(`${this.baseUrl}/status/${taskId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch video status');
    }

    return response.json();
  }

  // Animation Generation Methods (NEW)
  async generateAnimations(request: AnimationGenerationRequest): Promise<AnimationGenerationResponse> {
    const response = await fetch(`${this.baseUrl}/v1/animations/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate animations' }));
      throw new Error(error.detail || 'Failed to generate animations');
    }

    return response.json();
  }

  async getAnimations(taskId: string): Promise<LectureAnimations> {
    const response = await fetch(`${this.baseUrl}/v1/animations/${taskId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Animations not found');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch animations' }));
      throw new Error(error.detail || 'Failed to fetch animations');
    }

    return response.json();
  }

  async getSlideAnimation(taskId: string, slideIndex: number): Promise<{ slide: SlideAnimation; total_slides: number; current_index: number }> {
    const response = await fetch(`${this.baseUrl}/v1/animations/${taskId}/slides/${slideIndex}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Slide not found');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch slide' }));
      throw new Error(error.detail || 'Failed to fetch slide');
    }

    return response.json();
  }

  async getAnimationMetadata(taskId: string): Promise<AnimationMetadata> {
    const response = await fetch(`${this.baseUrl}/v1/animations/${taskId}/metadata`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Animation metadata not found');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch metadata' }));
      throw new Error(error.detail || 'Failed to fetch metadata');
    }

    return response.json();
  }

  async trackAnimationProgress(taskId: string, request: ProgressTrackingRequest): Promise<ProgressTrackingResponse> {
    const response = await fetch(`${this.baseUrl}/v1/animations/${taskId}/progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to track progress' }));
      throw new Error(error.detail || 'Failed to track progress');
    }

    return response.json();
  }

  async getLecture(id: string): Promise<Lecture> {
    // For now, redirect to status endpoint since we're using task_id
    const response = await fetch(`${this.baseUrl}/status/${id}`);

    if (!response.ok) {
      throw new Error('Failed to fetch lecture');
    }

    const data = await response.json();
    
    // Transform status response to Lecture format
    return {
      id: data.task_id,
      topic: data.topic || 'Lecture',
      audience: 'Students', // Not available in status, use default
      duration: 10, // Not available in status, use default
      theme: 'Minimalist', // Not available in status, use default
      status: data.status === 'completed' ? 'completed' : data.status === 'processing' ? 'processing' : 'pending',
      videoUrl: data.videoUrl,
      progress: data.progress,
      createdAt: new Date().toISOString(),
    };
  }

  async getLectures(): Promise<Lecture[]> {
    const response = await fetch(`${this.baseUrl}/api/lectures`);

    if (!response.ok) {
      throw new Error('Failed to fetch lectures');
    }

    const data = await response.json();
    
    // Transform backend response to frontend Lecture format
    return data.map((lecture: any) => ({
      id: lecture.id,
      topic: lecture.topic,
      audience: lecture.targetAudience || 'Students',
      duration: lecture.desiredLength,
      theme: lecture.visualTheme?.toLowerCase() || 'minimalist',
      status: this.mapVideoStatusToFrontend(lecture.videoStatus),
      videoUrl: lecture.videoUrl,
      slidesUrl: lecture.slidesPdfUrl,
      createdAt: lecture.createdAt,
      progress: this.calculateProgress(lecture.videoStatus),
      errorMessage: lecture.errorMessage,
    }));
  }

  private mapVideoStatusToFrontend(status: string): 'pending' | 'processing' | 'completed' | 'failed' {
    const statusMap: Record<string, 'pending' | 'processing' | 'completed' | 'failed'> = {
      'PENDING': 'pending',
      'GENERATING_CONTENT': 'processing',
      'CREATING_SLIDES': 'processing',
      'FETCHING_IMAGES': 'processing',
      'GENERATING_AUDIO': 'processing',
      'ASSEMBLING_VIDEO': 'processing',
      'COMPLETED': 'completed',
      'FAILED': 'failed',
    };
    return statusMap[status] || 'pending';
  }

  private calculateProgress(status: string): number {
    const progressMap: Record<string, number> = {
      'PENDING': 0,
      'GENERATING_CONTENT': 20,
      'CREATING_SLIDES': 40,
      'FETCHING_IMAGES': 60,
      'GENERATING_AUDIO': 70,
      'ASSEMBLING_VIDEO': 90,
      'COMPLETED': 100,
      'FAILED': 0,
    };
    return progressMap[status] || 0;
  }

  async deleteLecture(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/lectures/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete lecture');
    }
  }

  // Chatbot Methods
  async chat(request: ChatRequest, token?: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/v1/chatbot/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to chat' }));
      throw new Error(error.detail || 'Failed to chat');
    }

    return response.json();
  }

  async streamChat(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    token?: string
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/v1/chatbot/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to stream chat' }));
      throw new Error(error.detail || 'Failed to stream chat');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            onChunk(data);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async quickAsk(question: string, topicContext?: string, token?: string): Promise<ChatResponse> {
    const params = new URLSearchParams({ question });
    if (topicContext) {
      params.append('topic_context', topicContext);
    }

    const response = await fetch(`${this.baseUrl}/v1/chatbot/quick-ask?${params}`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to ask question' }));
      throw new Error(error.detail || 'Failed to ask question');
    }

    return response.json();
  }

  // Mindmap Methods
  async generateMindmap(request: MindMapGenerateRequest, token?: string): Promise<MindMapResponse> {
    const response = await fetch(`${this.baseUrl}/v1/mindmap/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate mindmap' }));
      throw new Error(error.detail || 'Failed to generate mindmap');
    }

    return response.json();
  }

  async getMindmapByLecture(lectureId: string, token?: string): Promise<MindMapRetrieveResponse> {
    const response = await fetch(`${this.baseUrl}/v1/mindmap/lecture/${lectureId}`, {
      method: 'GET',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('MINDMAP_NOT_FOUND');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to get mindmap' }));
      throw new Error(error.detail || 'Failed to get mindmap');
    }

    return response.json();
  }

  async getMindmapById(mindmapId: string, token?: string): Promise<MindMapRetrieveResponse> {
    const response = await fetch(`${this.baseUrl}/v1/mindmap/${mindmapId}`, {
      method: 'GET',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('MINDMAP_NOT_FOUND');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to get mindmap' }));
      throw new Error(error.detail || 'Failed to get mindmap');
    }

    return response.json();
  }

  async deleteMindmap(lectureId: string, token?: string): Promise<MindMapDeleteResponse> {
    const response = await fetch(`${this.baseUrl}/v1/mindmap/lecture/${lectureId}`, {
      method: 'DELETE',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete mindmap' }));
      throw new Error(error.detail || 'Failed to delete mindmap');
    }

    return response.json();
  }

  async getMindmapHealth(): Promise<MindMapHealthResponse> {
    const response = await fetch(`${this.baseUrl}/v1/mindmap/health`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to get mindmap health' }));
      throw new Error(error.detail || 'Failed to get mindmap health');
    }

    return response.json();
  }

  // Authentication Methods
  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/v1/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to sign up' }));
      // Handle FastAPI validation errors (422)
      if (error.detail && Array.isArray(error.detail)) {
        const messages = error.detail.map((err: { loc: string[]; msg: string }) => `${err.loc.join('.')}: ${err.msg}`).join(', ');
        throw new Error(messages);
      }
      throw new Error(error.detail || 'Failed to sign up');
    }

    return response.json();
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Invalid email or password' }));
      // Handle FastAPI validation errors (422)
      if (error.detail && Array.isArray(error.detail)) {
        const messages = error.detail.map((err: { loc: string[]; msg: string }) => `${err.loc.join('.')}: ${err.msg}`).join(', ');
        throw new Error(messages);
      }
      throw new Error(error.detail || 'Failed to login');
    }

    return response.json();
  }

  async loginWithGoogle(idToken: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/v1/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id_token: idToken }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to authenticate with Google' }));
      throw new Error(error.detail || 'Failed to authenticate with Google');
    }

    return response.json();
  }

  async getCurrentUser(token: string): Promise<UserInfo> {
    const response = await fetch(`${this.baseUrl}/v1/auth/me`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to get user info' }));
      throw new Error(error.detail || 'Failed to get user info');
    }

    return response.json();
  }

  async logout(token: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/v1/auth/logout`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to logout' }));
      throw new Error(error.detail || 'Failed to logout');
    }
  }

  // Quiz Generation
  async generateQuiz(
    lectureId: string, 
    numQuestions: number = 3, 
    format: 'plain' | 'moodle' | 'canvas' = 'plain'
  ): Promise<QuizResponse> {
    const response = await fetch(`${this.baseUrl}/generate-quiz/${lectureId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ num_questions: numQuestions, format }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to generate quiz' }));
      throw new Error(error.detail || 'Failed to generate quiz');
    }

    return response.json();
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
