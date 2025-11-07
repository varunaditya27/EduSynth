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

export interface CreateLectureInput {
  topic: string;
  audience: string;
  duration: number;
  theme: string;
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
}

export const apiClient = new ApiClient(API_BASE_URL);
