from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import slides
from .core.config import settings

app = FastAPI(title="EduSynth Slide Deck Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(slides.router, prefix="/v1/slides", tags=["slides"])
