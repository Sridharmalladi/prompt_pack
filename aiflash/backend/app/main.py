import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(
    title="AI Study Assistant",
    description="Backend API for the AI Study Assistant — RAG-powered study and interview prep.",
    version="0.1.0",
)

# CORS — update origins before deploying frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import routes

app.include_router(routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
