"""Announcement router allowing authorities to broadcast updates."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_role
from app.core.database import get_db
from app.models import Announcement, User, UserType

router = APIRouter()


class AnnouncementCreateRequest(BaseModel):
    title: str
    content: str
    audience: str | None = None


class AnnouncementRecord(BaseModel):
    id: int
    title: str
    content: str
    audience: str | None
    created_at: datetime
    author_id: int | None
    author_name: str | None


def _to_record(entry: Announcement) -> AnnouncementRecord:
    obj = cast(Any, entry)
    author = getattr(obj, "author", None)
    return AnnouncementRecord(
        id=obj.id,
        title=obj.title,
        content=obj.content,
        audience=getattr(obj, "audience", None),
        created_at=obj.created_at,
        author_id=getattr(obj, "author_id", None),
        author_name=getattr(author, "name", None),
    )


@router.get("/", response_model=List[AnnouncementRecord])
async def list_announcements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AnnouncementRecord]:
    """Return announcements ordered by recency."""

    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [_to_record(row) for row in rows]


@router.post("/", response_model=AnnouncementRecord, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_authority: User = Depends(require_role(UserType.AUTHORITY)),
) -> AnnouncementRecord:
    """Allow an authority to publish a new announcement."""

    entry = Announcement(
        title=payload.title,
        content=payload.content,
        audience=payload.audience,
        author_id=current_authority.id,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _to_record(entry)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_authority: User = Depends(require_role(UserType.AUTHORITY)),
) -> Response:
    """Allow an authority member to remove their own announcements."""

    entry = db.get(Announcement, announcement_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    authority_obj = cast(Any, current_authority)
    authority_id = int(getattr(authority_obj, "id"))
    route = (getattr(authority_obj, "feedback_route", "") or "").strip().lower()
    is_mayor_route = route == "mayor's office"

    entry_author_id = getattr(entry, "author_id", None)

    if entry_author_id is None:
        if not is_mayor_route:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only mayor's office can delete unowned announcements",
            )
    elif entry_author_id != authority_id and not is_mayor_route:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete announcement created by another authority",
        )

    db.delete(entry)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
