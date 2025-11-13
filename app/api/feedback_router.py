"""Feedback API router with role-based access and persistent storage."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.models import Feedback, FeedbackStatus, User, UserType

router = APIRouter()


class FeedbackCreateRequest(BaseModel):
    category: str
    message: str
    authority_type: Optional[str] = None
    priority: Optional[str] = None
    location: Optional[str] = None


class FeedbackUpdateRequest(BaseModel):
    status: FeedbackStatus
    authority_notes: Optional[str] = None


class FeedbackRecord(BaseModel):
    id: int
    category: str
    message: str
    authority_type: Optional[str]
    priority: Optional[str]
    location: Optional[str]
    status: FeedbackStatus
    authority_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    citizen_name: Optional[str]
    citizen_contact: Optional[str]
    authority_name: Optional[str]

    @field_validator("status", mode="before")
    @classmethod
    def _normalise_status(cls, value: Any) -> FeedbackStatus:
        if isinstance(value, FeedbackStatus):
            return value
        return FeedbackStatus(str(value))


class FeedbackSummary(BaseModel):
    total: int
    reported: int
    in_process: int
    solved: int


def _feedback_to_record(entry: Feedback) -> FeedbackRecord:
    obj = cast(Any, entry)
    citizen = getattr(obj, "user", None)
    authority = getattr(obj, "assigned_authority", None)
    return FeedbackRecord(
        id=obj.id,
        category=obj.category,
        message=obj.message,
        authority_type=getattr(obj, "authority_type", None),
        priority=getattr(obj, "priority", None),
        location=getattr(obj, "location", None),
        status=obj.status,
        authority_notes=getattr(obj, "authority_notes", None),
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        citizen_name=getattr(citizen, "name", None),
        citizen_contact=getattr(citizen, "phone_number", None),
        authority_name=getattr(authority, "name", None),
    )


@router.post("/submit", response_model=FeedbackRecord, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreateRequest,
    current_user: User = Depends(require_role(UserType.USER)),
    db: Session = Depends(get_db),
) -> FeedbackRecord:
    """Allow a citizen to submit feedback assigned to an authority type."""

    entry = Feedback(
        user_id=current_user.id,
        category=payload.category,
        message=payload.message,
        authority_type=payload.authority_type,
        priority=payload.priority,
        location=payload.location,
        status=FeedbackStatus.REPORTED,
    )

    if payload.authority_type:
        assigned_authority = (
            db.query(User)
            .filter(
                User.user_type == UserType.AUTHORITY,
                User.feedback_route == payload.authority_type,
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc())
            .first()
        )
        if assigned_authority:
            setattr(entry, "authority_id", assigned_authority.id)

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _feedback_to_record(entry)


@router.get("/my", response_model=List[FeedbackRecord])
async def list_my_feedback(
    current_user: User = Depends(require_role(UserType.USER)),
    db: Session = Depends(get_db),
) -> List[FeedbackRecord]:
    """Retrieve all feedback submitted by the logged-in citizen."""

    entries = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return [_feedback_to_record(entry) for entry in entries]


@router.get("/manage", response_model=List[FeedbackRecord])
async def list_feedback_for_authority(
    status_filter: Optional[FeedbackStatus] = Query(default=None),
    db: Session = Depends(get_db),
    current_authority: User = Depends(require_role(UserType.AUTHORITY)),
) -> List[FeedbackRecord]:
    """Allow authorities to review and manage citizen feedback."""

    query = db.query(Feedback).order_by(Feedback.created_at.desc())
    if status_filter:
        query = query.filter(Feedback.status == status_filter)

    route = getattr(current_authority, "feedback_route", None)
    if route and route.strip().lower() == "mayor's office":
        entries = query.all()
    elif route:
        query = query.filter(
            (Feedback.authority_id == current_authority.id)
            | (Feedback.authority_type == route)
            | (Feedback.authority_id.is_(None))
        )
        entries = query.all()
    else:
        query = query.filter(
            (Feedback.authority_id == current_authority.id) | (Feedback.authority_id.is_(None))
        )
        entries = query.all()
    return [_feedback_to_record(entry) for entry in entries]


@router.patch("/{feedback_id}", response_model=FeedbackRecord)
async def update_feedback_status(
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    db: Session = Depends(get_db),
    current_authority: User = Depends(require_role(UserType.AUTHORITY)),
) -> FeedbackRecord:
    """Update feedback status and optional notes as an authority."""

    entry = db.get(Feedback, feedback_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    setattr(entry, "status", payload.status)
    setattr(entry, "authority_notes", payload.authority_notes)
    setattr(entry, "authority_id", current_authority.id)
    setattr(entry, "updated_at", datetime.utcnow())

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _feedback_to_record(entry)


@router.get("/stats", response_model=FeedbackSummary)
async def feedback_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackSummary:
    """Return aggregate counts for dashboard visualisations."""

    total = db.query(func.count(Feedback.id)).scalar() or 0

    def count_status(target: FeedbackStatus) -> int:
        return (
            db.query(func.count(Feedback.id))
            .filter(Feedback.status == target)
            .scalar()
            or 0
        )

    return FeedbackSummary(
        total=total,
        reported=count_status(FeedbackStatus.REPORTED),
        in_process=count_status(FeedbackStatus.IN_PROCESS),
        solved=count_status(FeedbackStatus.SOLVED),
    )
