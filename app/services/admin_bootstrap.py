"""Legacy admin bootstrap removed. Placeholder kept for backward compatibility."""

from __future__ import annotations

from sqlalchemy.orm import Session


def ensure_seed_admin(session: Session) -> None:
    """No-op placeholder retained for legacy import paths."""

    try:
        session.commit()
    except Exception:
        session.rollback()
