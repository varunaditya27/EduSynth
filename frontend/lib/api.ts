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
}

export const apiClient = new ApiClient(API_BASE_URL);
