from fastapi import FastAPI
from app.core.config import settings
from app.routers import slides
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EduSynth Slides Solo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(slides.router)

@app.get("/healthz")
def health():
    return {"ok": True}
