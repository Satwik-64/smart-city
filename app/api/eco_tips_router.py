# Placeholder for eco_tips_router.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.granite_llm import granite_llm
from typing import Optional

router = APIRouter()

class EcoTipResponse(BaseModel):
    topic: str
    tips: str
    status: str

@router.get("/generate", response_model=EcoTipResponse)
async def get_eco_tips(topic: str = Query(..., description="Topic for eco-friendly tips")):
    """Generate eco-friendly tips for a specific topic"""
    try:
        if not topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        tips = granite_llm.generate_eco_tip(topic)
        
        return EcoTipResponse(
            topic=topic,
            tips=tips,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating eco tips: {str(e)}")

@router.get("/popular-topics")
async def get_popular_topics():
    """Get list of popular eco-friendly topics"""
    topics = [
        {"name": "Energy Conservation", "icon": "⚡", "description": "Tips for reducing energy consumption"},
        {"name": "Water Management", "icon": "💧", "description": "Water saving and conservation techniques"},
        {"name": "Waste Reduction", "icon": "♻️", "description": "Reduce, reuse, and recycle strategies"},
        {"name": "Sustainable Transport", "icon": "🚲", "description": "Eco-friendly transportation options"},
        {"name": "Green Building", "icon": "🏢", "description": "Sustainable construction and living"},
        {"name": "Air Quality", "icon": "🌿", "description": "Improving indoor and outdoor air quality"},
        {"name": "Urban Gardening", "icon": "🌱", "description": "Growing plants in urban environments"},
        {"name": "Climate Action", "icon": "🌍", "description": "Individual actions for climate change"}
    ]
    return {"topics": topics, "count": len(topics)}
