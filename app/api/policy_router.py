# Placeholder for policy_router.py
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from app.services.granite_llm import granite_llm

router = APIRouter()

class PolicySummaryRequest(BaseModel):
    text: str
    summary_type: str = "citizen-friendly"  # citizen-friendly, technical, executive

class PolicySummaryResponse(BaseModel):
    original_length: int
    summary: str
    summary_type: str
    status: str

@router.post("/summarize", response_model=PolicySummaryResponse)
async def summarize_policy(request: PolicySummaryRequest):
    """Summarize policy text"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Policy text cannot be empty")
        
        # Customize prompt based on summary type
        if request.summary_type == "executive":
            prompt_prefix = "Provide an executive summary focusing on key decisions and impacts:"
        elif request.summary_type == "technical":
            prompt_prefix = "Provide a technical summary focusing on implementation details:"
        else:  # citizen-friendly
            prompt_prefix = "Summarize in simple, citizen-friendly language:"
        
        enhanced_text = f"{prompt_prefix}\n\n{request.text}"
        summary = granite_llm.generate_summary(enhanced_text)
        
        return PolicySummaryResponse(
            original_length=len(request.text),
            summary=summary,
            summary_type=request.summary_type,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing policy: {str(e)}")

@router.post("/summarize-file")
async def summarize_policy_file(
    file: UploadFile = File(...),
    summary_type: str = "citizen-friendly"
):
    """Upload and summarize a policy file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file must have a name")

        if not file.filename.endswith(('.txt', '.pdf', '.docx')):
            raise HTTPException(
                status_code=400, 
                detail="Only .txt, .pdf, and .docx files are supported"
            )
        
        # Read file content
        contents = await file.read()
        
        # For now, handle only .txt files (extend for PDF/DOCX later)
        if file.filename.endswith('.txt'):
            text_content = contents.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only .txt files are currently supported")
        
        # Create summary request
        request = PolicySummaryRequest(text=text_content, summary_type=summary_type)
        return await summarize_policy(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing policy file: {str(e)}")

@router.get("/categories")
async def get_policy_categories():
    """Get common policy categories"""
    categories = [
        {"name": "Environmental", "icon": "🌿", "description": "Climate and environmental policies"},
        {"name": "Transportation", "icon": "🚌", "description": "Public transport and mobility"},
        {"name": "Housing", "icon": "🏠", "description": "Urban planning and housing policies"},
        {"name": "Energy", "icon": "⚡", "description": "Energy efficiency and renewable resources"},
        {"name": "Waste Management", "icon": "♻️", "description": "Waste reduction and recycling"},
        {"name": "Water Management", "icon": "💧", "description": "Water conservation and distribution"},
        {"name": "Public Health", "icon": "🏥", "description": "Health and safety regulations"},
        {"name": "Economic Development", "icon": "💼", "description": "Business and economic policies"}
    ]
    return {"categories": categories, "count": len(categories)}
