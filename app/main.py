# Placeholder for main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import (
    announcement_router,
    auth_router,
    chat_router,
    dashboard_router,
    eco_tips_router,
    feedback_router,
    policy_router,
)
from dotenv import load_dotenv
from app.core.config import settings
load_dotenv()  # Load environment variables

app = FastAPI(
    title="Sustainable Smart City Assistant API",
    description="AI-powered platform for urban sustainability and governance",
    version="1.0.0"
)

# CORS middleware based on settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["authentication"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(feedback_router.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(eco_tips_router.router, prefix="/api/eco-tips", tags=["eco-tips"])
app.include_router(policy_router.router, prefix="/api/policy", tags=["policy"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(announcement_router.router, prefix="/api/announcements", tags=["announcements"])

@app.get("/")
async def root():
    return {"message": "Sustainable Smart City Assistant API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is operational"}
