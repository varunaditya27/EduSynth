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
  updated_at?: string;
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

  async getLecture(id: string): Promise<Lecture> {
    const response = await fetch(`${this.baseUrl}/api/lectures/${id}`);

    if (!response.ok) {
      throw new Error('Failed to fetch lecture');
    }

    return response.json();
  }

  async getLectures(): Promise<Lecture[]> {
    const response = await fetch(`${this.baseUrl}/api/lectures`);

    if (!response.ok) {
      throw new Error('Failed to fetch lectures');
    }

    return response.json();
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

  async getMindmapByLecture(lectureId: string, token?: string): Promise<MindMapResponse> {
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

  async deleteMindmap(lectureId: string, token?: string): Promise<void> {
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
}

export const apiClient = new ApiClient(API_BASE_URL);
