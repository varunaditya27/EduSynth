<div align="center">

# 🎓 EduSynth

### AI-Powered Educational Content Generation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.1-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19.2.0-61dafb.svg)](https://reactjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Transform raw topics into comprehensive, interactive educational content with AI-powered animations, voice narration, and intelligent content structuring.**

[Features](#-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🌟 Features

### 🤖 **AI-Powered Content Generation**
- **Intelligent Topic Parsing**: Automatically breaks down complex topics into digestible subtopics
- **Multi-Modal Content**: Generate text, images, animations, and audio seamlessly
- **Adaptive Learning Paths**: Creates personalized content flows based on learning objectives

### 🎨 **Rich Media Production**
- **Animated Presentations**: Transform static content into engaging animations
- **Text-to-Speech Integration**: Natural voice narration using ElevenLabs
- **Visual Content Synthesis**: AI-generated images and diagrams via Google Gemini
- **Interactive Mind Maps**: Visualize topic relationships with React Flow

### 📚 **Multi-Format Export**
- **Video Lectures**: Complete synchronized video presentations
- **PDF Documents**: Professional-quality study materials
- **PowerPoint Presentations**: Ready-to-use slide decks
- **Interactive Web Content**: Engaging online learning modules

### 🎯 **Smart Content Features**
- **Gamified Learning**: Interactive examples and executable code snippets
- **Prompt-Driven Animations**: Dynamic content that responds to user interactions
- **Contextual Image Fetching**: Relevant visuals automatically matched to content
- **Progress Tracking**: Monitor learning journeys through integrated analytics

---

## 🏗️ Architecture

### System Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Next.js App] --> B[React Components]
        B --> C[Zustand State]
        B --> D[TanStack Query]
    end
    
    subgraph "Backend Layer"
        E[FastAPI Server] --> F[AI Services]
        E --> G[Content Processors]
        E --> H[Media Generators]
        
        F --> F1[Gemini API]
        F --> F2[Groq LLM]
        
        G --> G1[Animation Engine]
        G --> G2[PDF Generator]
        G --> G3[PPT Builder]
        
        H --> H1[Image Synthesis]
        H --> H2[Video Sync]
        H --> H3[TTS Engine]
    end
    
    subgraph "Data Layer"
        I[(PostgreSQL)] 
        J[(Supabase)]
        K[Cloudflare R2]
    end
    
    A -->|REST API| E
    E --> I
    E --> J
    H --> K
    
    style A fill:#000000,stroke:#ffffff,color:#ffffff
    style E fill:#009688,stroke:#00695c,color:#ffffff
    style I fill:#336791,stroke:#1e3a5f,color:#ffffff
</mermaid>

### Technology Stack

<table>
<tr>
<td width="50%">

#### Frontend
- **Framework**: Next.js 16 with App Router
- **UI Library**: React 19.2
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Animations**: GSAP & Framer Motion
- **Visualizations**: React Flow / XYFlow
- **Code Highlighting**: Highlight.js
- **Markdown**: React Markdown with remark-gfm

</td>
<td width="50%">

#### Backend
- **Framework**: FastAPI with Uvicorn
- **Language**: Python 3.11
- **AI/ML**: Google Gemini, Groq
- **Database**: PostgreSQL with Prisma ORM
- **Storage**: Cloudflare R2 (S3-compatible)
- **Auth**: Supabase
- **Media Processing**: MoviePy, Pillow, ReportLab
- **TTS**: ElevenLabs
- **Visualization**: NetworkX, Matplotlib

</td>
</tr>
</table>

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v20 or higher)
- **Python** (v3.11)
- **npm** or **yarn** or **pnpm**
- **PostgreSQL** (v14 or higher)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/varunaditya27/EduSynth.git
   cd EduSynth
   ```

2. **Set up the backend**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your API keys and configuration
   
   # Run database migrations
   npx prisma generate
   npx prisma db push
   
   # Start the server
   uvicorn app.main:app --reload
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Environment Configuration

Create a `.env` file in the `backend` directory with the following variables:

```env
# API Keys
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/edusynth

# Storage (Cloudflare R2)
R2_ENDPOINT=your_r2_endpoint
R2_ACCESS_KEY=your_access_key
R2_SECRET_KEY=your_secret_key
R2_BUCKET_NAME=edusynth-media

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

---

## 📖 Documentation

### Project Structure

```
EduSynth/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App router pages and layouts
│   ├── components/          # React components
│   ├── contexts/            # React contexts
│   ├── lib/                 # Utility functions
│   └── public/              # Static assets
│
├── backend/                 # FastAPI backend application
│   ├── app/                 # Main application code
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic
│   │   ├── models/         # Pydantic models
│   │   ├── schemas/        # Database schemas
│   │   └── core/           # Core configurations
│   ├── assets/             # Static assets
│   ├── prisma/             # Database schema
│   └── scripts/            # Utility scripts
│
└── ai_generation/          # AI model training and utilities
```

### Key Components

#### Content Generation Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant AI as AI Services
    participant DB as Database
    participant S as Storage
    
    U->>F: Submit Topic
    F->>B: POST /api/generate
    B->>AI: Generate Content Structure
    AI-->>B: Topic Breakdown
    B->>DB: Save Content Metadata
    
    par Content Generation
        B->>AI: Generate Text Content
        B->>AI: Generate Images
        B->>AI: Create Animations
    end
    
    AI-->>B: Generated Assets
    B->>S: Upload Media Files
    B->>AI: Generate Narration
    B->>B: Synchronize Media
    B->>S: Upload Final Video
    B-->>F: Content Ready
    F-->>U: Display Results
```

### API Endpoints

Detailed API documentation is available at `/docs` when running the backend server.

**Key Endpoints:**
- `POST /api/generate` - Generate educational content
- `GET /api/content/{id}` - Retrieve generated content
- `POST /api/animate` - Create animations
- `POST /api/export` - Export to various formats
- `GET /api/mindmap/{id}` - Get topic mind map

---

## 🎯 Use Cases

- 📚 **Educators**: Create engaging course materials rapidly
- 🎓 **Students**: Generate personalized study guides
- 💼 **Corporate Training**: Develop professional training modules
- 🔬 **Researchers**: Visualize complex concepts
- 🌐 **Content Creators**: Produce educational videos at scale

---

## 🤝 Contributing

We welcome contributions! Please see our detailed contribution guidelines in each module:

- [Backend Contributing Guide](./backend/README.md#contributing)
- [Frontend Contributing Guide](./frontend/README.md#contributing)

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** for AI content generation
- **Groq** for LLM inference
- **ElevenLabs** for text-to-speech
- **Vercel** for frontend hosting
- **Supabase** for backend infrastructure

---

## 📧 Contact

**Varun Aditya** - [@varunaditya27](https://github.com/varunaditya27)

Portfolio: [varun-aditya-portfolio.vercel.app](https://varun-aditya-portfolio.vercel.app)

Project Link: [https://github.com/varunaditya27/EduSynth](https://github.com/varunaditya27/EduSynth)

---

<div align="center">

**Built with ❤️ at R. V. College of Engineering, Bangalore**

[![GitHub stars](https://img.shields.io/github/stars/varunaditya27/EduSynth?style=social)](https://github.com/varunaditya27/EduSynth/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/varunaditya27/EduSynth?style=social)](https://github.com/varunaditya27/EduSynth/network/members)

</div>
