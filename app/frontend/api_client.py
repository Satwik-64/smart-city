"""Utility helpers for communicating with the FastAPI backend."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests
import streamlit as st

from app.core.config import settings

API_BASE_URL = f"http://{settings.api_host}:{settings.api_port}/api"


def _auth_headers() -> Dict[str, str]:
    token: Optional[str] = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(path: str, **kwargs: Any) -> requests.Response:
    headers = {
        "Accept": "application/json",
        **_auth_headers(),
        **kwargs.pop("headers", {}),
    }
    return requests.get(f"{API_BASE_URL}{path}", headers=headers, timeout=kwargs.pop("timeout", 15), **kwargs)


def api_post(path: str, json: Any | None = None, **kwargs: Any) -> requests.Response:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        **_auth_headers(),
        **kwargs.pop("headers", {}),
    }
    return requests.post(
        f"{API_BASE_URL}{path}",
        headers=headers,
        json=json,
        timeout=kwargs.pop("timeout", 15),
        **kwargs,
    )


def api_patch(path: str, json: Any | None = None, **kwargs: Any) -> requests.Response:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        **_auth_headers(),
        **kwargs.pop("headers", {}),
    }
    return requests.patch(
        f"{API_BASE_URL}{path}",
        headers=headers,
        json=json,
        timeout=kwargs.pop("timeout", 15),
        **kwargs,
    )


def api_delete(path: str, **kwargs: Any) -> requests.Response:
    headers = {
        "Accept": "application/json",
        **_auth_headers(),
        **kwargs.pop("headers", {}),
    }
    return requests.delete(f"{API_BASE_URL}{path}", headers=headers, timeout=kwargs.pop("timeout", 15), **kwargs)
