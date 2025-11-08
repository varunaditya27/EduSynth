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

- [🌟 Features](#-features)
- [🏗️ Architecture](#-architecture)
- [🚀 Getting Started](#-getting-started)
- [📝 API Documentation](#-api-documentation)
- [📁 Project Structure](#-project-structure)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)

---

## 🌟 Features

### 🤖 AI-Powered Generation

- **Multi-Model AI Integration**
  - Google Gemini for content generation and image synthesis
  - Groq LLM for fast inference and text processing
  - Intelligent prompt engineering and content structuring

- **Smart Content Pipeline**
  - Automated topic breakdown and subtopic extraction
  - Context-aware content generation
  - Adaptive learning path creation

### 🎨 Multimedia Processing

- **Video Generation**
  - Synchronized audio-visual content
  - Animated presentations with MoviePy
  - Frame-perfect timing with audio narration

- **Image Processing**
  - AI-generated educational images
  - Dynamic image fetching and optimization
  - Format conversion and compression

- **Audio Synthesis**
  - High-quality TTS with ElevenLabs
  - Multiple voice options
  - Emotion and emphasis control

### 📊 Document Generation

- **PDF Creation**: Professional study materials with ReportLab
- **PowerPoint Export**: Slide decks with python-pptx
- **Mind Maps**: NetworkX-powered visualizations
- **Flowcharts**: Graphviz integration for diagrams

### 🔒 Security & Performance

- **Authentication**: JWT-based auth with bcrypt
- **Rate Limiting**: Request throttling and quota management
- **Async Processing**: Non-blocking I/O operations
- **Caching**: Redis-ready architecture
- **Cloud Storage**: Cloudflare R2 (S3-compatible)

---

## 🏗️ Architecture

### System Architecture

```mermaid
graph TB
    subgraph "API Layer"
        A[FastAPI Application]
        B[Router Modules]
        C[Middleware Stack]
    end
    
    subgraph "Service Layer"
        D[Content Service]
        E[Animation Service]
        F[Export Service]
        G[Media Service]
    end
    
    subgraph "AI Integration"
        H[Gemini Client]
        I[Groq Client]
        J[ElevenLabs TTS]
    end
    
    subgraph "Data Layer"
        K[(PostgreSQL)]
        L[Prisma ORM]
        M[Supabase Client]
    end
    
    subgraph "Storage Layer"
        N[Cloudflare R2]
        O[Local Cache]
    end
    
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    
    D --> H
    D --> I
    E --> H
    F --> J
    
    D --> L
    E --> L
    F --> L
    G --> L
    
    L --> K
    G --> M
    
    E --> N
    F --> N
    G --> N
    
    style A fill:#009688,stroke:#00695c,color:#ffffff
    style K fill:#336791,stroke:#1e3a5f,color:#ffffff
    style N fill:#F38020,stroke:#d66800,color:#ffffff
</mermaid>

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
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n edusynth python=3.11
   conda activate edusynth
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # Generate Prisma client
   npx prisma generate
   
   # Push schema to database
   npx prisma db push
   
   # Optional: Seed database
   python scripts/seed_db.py
   ```

6. **Run the server**
   ```bash
   # Development mode with auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Production mode
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

7. **Verify installation**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 📝 API Documentation

### Core Endpoints

#### Content Generation

```http
POST /api/v1/generate
Content-Type: application/json

{
  "topic": "Quantum Computing Basics",
  "depth": "intermediate",
  "format": ["video", "pdf"],
  "duration": 300,
  "language": "en"
}
```

**Response:**
```json
{
  "content_id": "uuid-here",
  "status": "processing",
  "estimated_time": 120,
  "assets": {
    "video_url": null,
    "pdf_url": null
  }
}
```

#### Animation Generation

```http
POST /api/v1/animate
Content-Type: application/json

{
  "content_id": "uuid-here",
  "animation_type": "slide_transition",
  "style": "modern",
  "prompts": ["Introduction", "Key Concepts", "Examples"]
}
```

#### Content Export

```http
GET /api/v1/export/{content_id}
Accept: application/pdf

Query Parameters:
  - format: pdf|pptx|video
  - quality: low|medium|high
```

### Authentication

All API requests require authentication (except health check):

```http
Authorization: Bearer <your_jwt_token>
```

### Rate Limits

- **Anonymous**: 10 requests/hour
- **Authenticated**: 100 requests/hour
- **Premium**: 1000 requests/hour

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── db.py                      # Database connection
│   │
│   ├── core/                      # Core configurations
│   │   ├── config.py              # App settings
│   │   ├── security.py            # Auth utilities
│   │   └── middleware.py          # Custom middleware
│   │
│   ├── routers/                   # API route handlers
│   │   ├── content.py             # Content endpoints
│   │   ├── animation.py           # Animation endpoints
│   │   ├── export.py              # Export endpoints
│   │   └── auth.py                # Auth endpoints
│   │
│   ├── services/                  # Business logic
│   │   ├── content_service.py     # Content generation
│   │   ├── animation_service.py   # Animation creation
│   │   ├── export_service.py      # Export handlers
│   │   └── media_service.py       # Media processing
│   │
│   ├── models/                    # Pydantic models
│   │   ├── content.py             # Content models
│   │   ├── user.py                # User models
│   │   └── animation.py           # Animation models
│   │
│   ├── schemas/                   # Database schemas
│   │   └── ...
│   │
│   ├── clients/                   # External service clients
│   │   ├── gemini_client.py       # Google Gemini
│   │   ├── groq_client.py         # Groq LLM
│   │   ├── elevenlabs_client.py   # TTS
│   │   └── storage_client.py      # R2 storage
│   │
│   ├── deps/                      # Dependencies
│   │   ├── auth.py                # Auth dependencies
│   │   └── database.py            # DB dependencies
│   │
│   ├── ai_animator.py             # Animation AI engine
│   ├── animation_generator.py     # Animation builder
│   ├── gemini_generator.py        # Content generator
│   ├── gemini_pdf_generator.py    # PDF generator
│   ├── video_sync.py              # Video synchronization
│   ├── tts_utils.py               # Text-to-speech
│   └── merge_utils.py             # Media merging
│
├── assets/                        # Static assets
│   ├── fonts/
│   ├── templates/
│   └── images/
│
├── prisma/                        # Prisma ORM
│   └── schema.prisma              # Database schema
│
├── scripts/                       # Utility scripts
│   ├── seed_db.py
│   ├── migrate.py
│   └── cleanup.py
│
├── tests/                         # Test suite
│   ├── test_content.py
│   ├── test_animation.py
│   └── test_export.py
│
├── .env.example                   # Environment template
├── .gitignore
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
ENVIRONMENT=development
DEBUG=true
PORT=8000
HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/edusynth
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# AI Services
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Storage (Cloudflare R2)
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your_r2_access_key
R2_SECRET_KEY=your_r2_secret_key
R2_BUCKET_NAME=edusynth-media
R2_PUBLIC_URL=https://cdn.your-domain.com

# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com

# Rate Limiting
RATE_LIMIT_PER_HOUR=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Database Schema

View the complete schema in `prisma/schema.prisma`. Key models:

- **User**: User accounts and authentication
- **Content**: Generated content metadata
- **Animation**: Animation definitions and assets
- **Export**: Export job tracking
- **MediaAsset**: Media file references

---

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_content.py

# Run with verbose output
pytest -v
```

### Test Structure

```python
# Example test
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_generate_content():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/generate",
            json={"topic": "Test Topic", "depth": "basic"}
        )
        assert response.status_code == 200
        assert "content_id" in response.json()
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t edusynth-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name edusynth-api \
  edusynth-backend

# Using Docker Compose
docker-compose up -d
```

### Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Use strong `SECRET_KEY`
- [ ] Configure CORS properly
- [ ] Set up SSL/TLS certificates
- [ ] Enable rate limiting
- [ ] Configure logging to external service
- [ ] Set up database backups
- [ ] Configure monitoring (Sentry, DataDog)
- [ ] Set up CI/CD pipeline
- [ ] Load test API endpoints

### Performance Optimization

```python
# Use connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Enable response caching
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379

# Configure workers
WORKERS=4  # Generally 2-4 x CPU cores
```

---

## 📊 Monitoring & Logging

### Health Check

```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-11-08T14:35:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "storage": "connected",
    "ai": "available"
  }
}
```

### Logging

Structured JSON logging for production:

```python
import logging
import json

logger = logging.getLogger(__name__)
logger.info(json.dumps({
    "event": "content_generated",
    "content_id": content_id,
    "duration_ms": duration,
    "user_id": user_id
}))
```

---

## 🤝 Contributing

### Development Guidelines

1. **Code Style**
   - Follow PEP 8
   - Use type hints
   - Write docstrings (Google style)
   - Format with `black`

2. **Commit Messages**
   ```
   type(scope): subject
   
   Types: feat, fix, docs, style, refactor, test, chore
   ```

3. **Pull Requests**
   - Create feature branches
   - Write tests for new features
   - Update documentation
   - Keep PRs focused and small

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
black app/
flake8 app/
mypy app/
```

---

## 📝 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 📧 Support

For issues and questions:
- 🐛 [GitHub Issues](https://github.com/varunaditya27/EduSynth/issues)
- 📧 Email: varun.paparajugari@gmail.com
- 💬 Discord: [Join our community](https://discord.gg/edusynth)

---

<div align="center">

**Built with FastAPI ⚡ | Powered by AI 🤖**

[![API Status](https://img.shields.io/badge/API-Online-success.svg)](http://localhost:8000/docs)
[![Response Time](https://img.shields.io/badge/Response%20Time-<100ms-brightgreen.svg)](#)

</div>
