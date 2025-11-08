from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import slides

app = FastAPI(
    title="EduSynth API",
    version="2.0",
    description="Slide deck + PDF generation backend with Supabase integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(slides.router)

@app.get("/")
async def root():
    return {"message": "EduSynth backend running 🚀"}

# for `python -m` path running convenience
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.solo:app", host="127.0.0.1", port=8000, reload=True)
