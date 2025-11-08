<div align="center">

# ⚙️ EduSynth Backend

### FastAPI-Powered AI Content Generation Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-0.30.0-green.svg)](https://www.uvicorn.org/)
[![Prisma](https://img.shields.io/badge/Prisma-0.12.0-2D3748.svg)](https://www.prisma.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**High-performance API server powering intelligent educational content generation with AI, multimedia processing, and real-time content synthesis.**

</div>

---

## 📚 Table of Contents

* [🌟 Features](#-features)
* [🎗️ Architecture](#-architecture)
* [🚀 Getting Started](#-getting-started)
* [📝 API Documentation](#-api-documentation)
* [🗁 Project Structure](#-project-structure)
* [🔧 Configuration](#-configuration)
* [🤪 Testing](#-testing)
* [🚀 Deployment](#-deployment)

---

## 🌟 Features

### 🤖 AI-Powered Generation

* **Multi-Model AI Integration**

  * Google Gemini for content generation and image synthesis
  * Groq LLM for fast inference and text processing
  * Intelligent prompt engineering and content structuring

* **Smart Content Pipeline**

  * Automated topic breakdown and subtopic extraction
  * Context-aware content generation
  * Adaptive learning path creation

### 🎨 Multimedia Processing

* **Video Generation**

  * Synchronized audio-visual content
  * Animated presentations with MoviePy
  * Frame-perfect timing with audio narration

* **Image Processing**

  * AI-generated educational images
  * Dynamic image fetching and optimization
  * Format conversion and compression

* **Audio Synthesis**

  * High-quality TTS with ElevenLabs
  * Multiple voice options
  * Emotion and emphasis control

### 📊 Document Generation

* **PDF Creation**: Professional study materials with ReportLab
* **PowerPoint Export**: Slide decks with python-pptx
* **Mind Maps**: NetworkX-powered visualizations
* **Flowcharts**: Graphviz integration for diagrams

### 🔒 Security & Performance

* **Authentication**: JWT-based auth with bcrypt
* **Rate Limiting**: Request throttling and quota management
* **Async Processing**: Non-blocking I/O operations
* **Caching**: Redis-ready architecture
* **Cloud Storage**: Cloudflare R2 (S3-compatible)

---

## 🎗️ Architecture

### System Architecture

```mermaid
flowchart TB
    subgraph API_Layer[API Layer]
        A[FastAPI Application]
        B[Router Modules]
        C[Middleware Stack]
    end

    subgraph Service_Layer[Service Layer]
        D[Content Service]
        E[Animation Service]
        F[Export Service]
        G[Media Service]
    end

    subgraph AI_Integration[AI Integration]
        H[Gemini Client]
        I[Groq Client]
        J[ElevenLabs TTS]
    end

    subgraph Data_Layer[Data Layer]
        K[(PostgreSQL)]
        L[Prisma ORM]
        M[Supabase Client]
    end

    subgraph Storage_Layer[Storage Layer]
        N[Cloudflare R2]
        O[Local Cache]
    end

    A --> B --> C
    B --> D & E & F & G

    D --> H & I
    E --> H
    F --> J

    D & E & F & G --> L
    L --> K
    G --> M

    E & F & G --> N

    style A fill:#009688,stroke:#00695c,color:#ffffff
    style K fill:#336791,stroke:#1e3a5f,color:#ffffff
    style N fill:#F38020,stroke:#d66800,color:#ffffff
```

### Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant S as Service
    participant AI as AI Engine
    participant DB as Database
    participant ST as Storage

    C->>R: POST /api/generate
    R->>R: Validate Request
    R->>S: Process Content

    S->>AI: Generate Structure
    AI-->>S: Topic Breakdown

    S->>DB: Save Metadata

    par Parallel Processing
        S->>AI: Generate Text
        S->>AI: Generate Images
        S->>AI: Create Audio
    end

    AI-->>S: Generated Assets

    S->>ST: Upload Media
    ST-->>S: Media URLs

    S->>S: Synchronize Content
    S->>DB: Update Status
    S-->>R: Processing Complete
    R-->>C: Response with URLs
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# System Requirements
Python 3.11 or higher
PostgreSQL 14 or higher
pip or poetry

# Optional
Docker & Docker Compose
Redis (for caching)
```

### Installation

1. **Navigate to backend directory**

   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

5. **Initialize database**

   ```bash
   npx prisma generate
   npx prisma db push
   python scripts/seed_db.py
   ```

6. **Run the server**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Verify installation**

   * API: [http://localhost:8000](http://localhost:8000)
   * Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📝 API Documentation

See `/docs` or `/redoc` after running the server.

---

## 🔧 Configuration

See `.env.example` for all available variables and tweak them as needed.

---

## 🤪 Testing

```bash
pip install pytest pytest-asyncio pytest-cov httpx
pytest -v --cov=app
```

---

## 🚀 Deployment

```bash
docker build -t edusynth-backend .
docker run -d -p 8000:8000 --env-file .env edusynth-backend
```

---

## 📊 Monitoring & Logging

### Health Check

```http
GET /health
```

---

## 🤝 Contributing

Follow PEP8, use `black`, and make PRs small and focused.

---

## 📝 License

MIT License.

---

<div align="center">

**Built with FastAPI ⚡ | Powered by AI 🤖**

</div>
