# app/api/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from typing import Any, Optional, cast
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import auth_service
from app.models import User, UserType
from datetime import datetime

router = APIRouter()

# Request Models
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)
    address: Optional[str] = None

class AuthorityRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    position: str = Field(..., min_length=2, max_length=255)
    feedback_route: str = Field(..., min_length=2, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Phone number or email")
    password: str

# Response Models
class UserResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    email: Optional[str]
    address: Optional[str]
    department: Optional[str]
    position: Optional[str]
    feedback_route: Optional[str]
    user_type: str
    is_active: bool
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    message: str
    token: str
    user_type: str
    user_data: dict

def serialize_user(user: User) -> UserResponse:
    obj = cast(Any, user)
    user_type = obj.user_type.value if isinstance(obj.user_type, UserType) else str(obj.user_type)
    return UserResponse(
        id=obj.id,
        name=obj.name,
        phone_number=obj.phone_number,
        email=obj.email,
        address=obj.address,
        department=getattr(obj, "department", None),
        position=getattr(obj, "position", None),
        feedback_route=getattr(obj, "feedback_route", None),
        user_type=user_type,
        is_active=obj.is_active,
        is_approved=bool(getattr(obj, "is_approved", False)),
        created_at=obj.created_at,
    )

# Endpoints
@router.post("/register/user", response_model=UserResponse)
async def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        result = auth_service.register_user(
            db=db,
            name=request.name,
            phone_number=request.phone_number,
            password=request.password,
            email=request.email,
            address=request.address
        )
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        user = cast(Any, result)
        return serialize_user(user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/register/authority", response_model=UserResponse)
async def register_authority(request: AuthorityRegisterRequest, db: Session = Depends(get_db)):
    """Register a new authority"""
    try:
        result = auth_service.register_authority(
            db=db,
            name=request.name,
            position=request.position,
            feedback_route=request.feedback_route,
            phone_number=request.phone_number,
            email=request.email,
            password=request.password
        )
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        authority = cast(Any, result)
        return serialize_user(authority)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login for both users and authorities"""
    try:
        # Authenticate user
        authenticated_user = auth_service.authenticate_user(
            db=db,
            identifier=request.identifier,
            password=request.password
        )
        
        if not authenticated_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        # Create access token
        user_type_enum = authenticated_user.user_type
        if not isinstance(user_type_enum, UserType):
            try:
                user_type_enum = UserType(str(user_type_enum))
            except ValueError:
                user_type_enum = UserType.USER

        token_data = {
            "sub": str(authenticated_user.id),
            "user_type": user_type_enum.value,
            "phone": authenticated_user.phone_number,
        }
        access_token = auth_service.create_access_token(data=token_data)
        
        # Prepare user data based on type
        user_type_value = user_type_enum.value

        user_data = {
            "id": authenticated_user.id,
            "name": authenticated_user.name,
            "phone_number": authenticated_user.phone_number,
            "email": authenticated_user.email,
            "address": authenticated_user.address,
            "department": authenticated_user.department,
            "position": authenticated_user.position,
            "feedback_route": getattr(authenticated_user, "feedback_route", None),
            "user_type": user_type_value,
            "is_active": bool(getattr(authenticated_user, "is_active", False)),
            "is_approved": bool(getattr(authenticated_user, "is_approved", False)),
        }
        
        return LoginResponse(
            message="Login successful",
            token=access_token,
            user_type=user_type_value,
            user_data=user_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/verify-token")
async def verify_token(token: str):
    """Verify if a token is valid"""
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "payload": payload}

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {"status": "healthy", "service": "authentication"}
