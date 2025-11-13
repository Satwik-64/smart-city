"""Streamlit dashboard for the Sustainable Smart City Assistant."""

from __future__ import annotations

import html
import os
import sys
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit_option_menu import option_menu

# Configure the page before rendering any elements.
try:
    st.set_page_config(
        page_title="Sustainable Smart City Assistant",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except StreamlitAPIException:
    # Streamlit reruns import modules; ignore duplicate page config attempts.
    pass

# Ensure sibling packages resolve when launched via ``streamlit run``.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from frontend import theme
from frontend.api_client import api_get
from frontend.components import (
    chat_assistant,
    announcements,
    eco_tips,
    feedback_form,
    login_page,
    policy_summarizer,
    registration_page,
)



# Inject global CSS and variables.
theme.apply_theme()


# ---------------------------------------------------------------------------
# Feedback statistics helpers
# ---------------------------------------------------------------------------

ECO_TIPS_OPTION = "Eco tips"

STATUS_ORDER = ["reported", "in_process", "solved"]
STATUS_LABELS = {
    "reported": "Reported",
    "in_process": "In process",
    "solved": "Solved",
}


def first_name(full_name: str | None) -> str:
    if not full_name:
        return "Leader"
    return full_name.split()[0]


def fetch_feedback_stats() -> Tuple[Dict[str, int], bool]:
    defaults = {"total": 0, "reported": 0, "in_process": 0, "solved": 0}
    try:
        response = api_get("/feedback/stats")
        if response.ok:
            payload = response.json()
            data = {key: int(payload.get(key, 0) or 0) for key in defaults}
            st.session_state.last_update = datetime.now()
            return data, False
    except Exception:
        pass
    return defaults, True


def render_feedback_stats_header(stats: Dict[str, int]) -> None:
    user = st.session_state.get("user_data", {})
    name = first_name(user.get("name"))
    last_sync = st.session_state.get("last_update")
    if not isinstance(last_sync, datetime):
        last_sync = datetime.now()

    st.markdown(
        f"""
        <div class="hero-banner">
            <div>
                <div class="chip">Citywide feedback insights</div>
                <h1 class="hero-banner__title">Welcome back, {name}</h1>
                <p class="hero-banner__subtitle">
                    Live visibility into citizen reports captured by the Smart City Assistant.
                </p>
            </div>
            <div class="metric-stack" style="min-width: 260px;">
                <div class="metric-block">
                    <span class="metric-block__label">Total submissions</span>
                    <span class="metric-block__value">{stats['total']}</span>
                </div>
                <div class="metric-block">
                    <span class="metric-block__label">Reported</span>
                    <span class="metric-block__value">{stats['reported']}</span>
                </div>
                <div class="metric-block">
                    <span class="metric-block__label">In process</span>
                    <span class="metric-block__value">{stats['in_process']}</span>
                </div>
                <div class="metric-block">
                    <span class="metric-block__label">Solved</span>
                    <span class="metric-block__value">{stats['solved']}</span>
                </div>
            </div>
        </div>
        <div style="margin-top:0.6rem;color:var(--text-muted);">
            Last synchronised {last_sync.strftime('%d %b %Y, %H:%M:%S')}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_refresh_bar() -> None:
    col_refresh, col_hint = st.columns([1, 2])
    with col_refresh:
        if st.button("🔄 Refresh data", use_container_width=True):
            st.session_state.last_update = datetime.now()
            st.rerun()
    with col_hint:
        st.caption("Sync with the latest persisted feedback analytics across the city network.")


def _status_card(title: str, value: int, icon: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-card__icon">{icon}</div>
            <div class="stat-card__title">{title}</div>
            <div class="stat-card__value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_cards(stats: Dict[str, int]) -> None:
    col_reported, col_in_process, col_solved = st.columns(3)
    with col_reported:
        _status_card("Reported", stats["reported"], "🟠")
    with col_in_process:
        _status_card("In process", stats["in_process"], "🛠️")
    with col_solved:
        _status_card("Solved", stats["solved"], "✅")


def render_city_statistics() -> None:
    stats, has_error = fetch_feedback_stats()
    render_feedback_stats_header(stats)
    render_refresh_bar()

    if has_error:
        st.warning("Unable to connect to the analytics service. Displaying the most recent cached totals.")

    st.markdown("---")
    st.markdown("### Feedback status at a glance")
    render_status_cards(stats)

    st.markdown("---")
    st.markdown("### Distribution across the workflow")

    chart_df = pd.DataFrame(
        {
            "Status": [STATUS_LABELS[key] for key in STATUS_ORDER],
            "Count": [stats.get(key, 0) for key in STATUS_ORDER],
        }
    )

    fig = px.bar(
        chart_df,
        x="Status",
        y="Count",
        text="Count",
        color="Status",
        color_discrete_sequence=["#38bdf8", "#facc15", "#34d399"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("All metrics derive from the shared MySQL data store to ensure a single source of truth.")


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <style>
            .sidebar-card {
                background: rgba(15, 23, 42, 0.55);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 18px;
                padding: 18px 20px;
                margin-bottom: 18px;
                backdrop-filter: blur(18px);
                box-shadow: 0 16px 40px rgba(8, 47, 73, 0.28);
            }
            .sidebar-card__title {
                font-size: 0.85rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: #94a3b8;
                margin-bottom: 12px;
            }
            .sidebar-card__title--muted {
                font-size: 0.72rem;
                letter-spacing: 0.2em;
                text-transform: uppercase;
                color: #72809f;
                margin: 4px 0 12px;
            }
            .sidebar-card__row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.88rem;
                color: #e2e8f0;
                padding: 6px 0;
            }
            .sidebar-card__row span {
                color: #94a3b8;
                font-weight: 500;
            }
            .sidebar-separator {
                border-bottom: 1px solid rgba(148, 163, 184, 0.25);
                margin: 8px 0 18px;
            }
            section[data-testid="stSidebar"] .stButton button {
                width: 100%;
                border-radius: 12px;
                padding: 0.65rem 1rem;
                border: 1px solid rgba(148, 163, 184, 0.28);
                background: linear-gradient(120deg, rgba(248, 250, 252, 0.12), rgba(148, 163, 184, 0.08));
                color: #f8fafc;
                font-weight: 600;
            }
            section[data-testid="stSidebar"] .stButton button:hover {
                border-color: rgba(14, 165, 233, 0.45);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        user = st.session_state.get("user_data", {})
        user_type = st.session_state.get("user_type", "user")
        email = user.get("email", "Not provided")
        department = user.get("department")

        profile_items = [
            ("Name", user.get("name", "---")),
            ("Role", user_type.capitalize()),
            ("Email", email),
        ]
        if department:
            profile_items.append(("Department", department))
        if user_type == "authority":
            route_label = user.get("feedback_route") or "Not assigned"
            profile_items.append(("Route", route_label))

        profile_rows = "".join(
            f"<div class='sidebar-card__row'><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></div>"
            for label, value in profile_items
        )

        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="sidebar-card__title">Welcome back</div>
                {profile_rows}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Log out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.user_type = None
            st.session_state.token = None
            st.session_state.page = "login"
            st.rerun()

        st.markdown("<div class='sidebar-separator'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='sidebar-card__title sidebar-card__title--muted'>Navigation</div>",
            unsafe_allow_html=True,
        )

        if user_type == "authority":
            options = [
                "Announcements",
                "Feedback queue",
            ]
            icons = [
                "megaphone",
                "clipboard-data",
            ]
        else:
            options = [
                "City statistics",
                "Smart assistant",
                ECO_TIPS_OPTION,
                "Feedback",
                "Announcements",
                "Policy summarizer",
            ]
            icons = [
                "bar-chart",
                "chat-dots-fill",
                "cloud-sun",
                "pencil-square",
                "megaphone",
                "file-earmark-text",
            ]
        nav_styles = {
            "container": {
                "padding": "6px 8px",
                "background-color": "rgba(15, 23, 42, 0.5)",
                "border-radius": "16px",
                "border": "1px solid rgba(148, 163, 184, 0.25)",
                "box-shadow": "0 16px 38px rgba(8, 47, 73, 0.26)",
            },
            "icon": {"color": "#38bdf8", "font-size": "18px"},
            "nav-link": {
                "display": "flex",
                "align-items": "center",
                "gap": "10px",
                "font-size": "15px",
                "padding": "10px 16px",
                "margin": "2px 0",
                "border-radius": "12px",
                "color": "#dbeafe",
                "border": "1px solid transparent",
                "transition": "all 0.2s ease-in-out",
            },
            "nav-link-selected": {
                "background": "linear-gradient(120deg, rgba(14,165,233,0.35), rgba(59,130,246,0.25))",
                "color": "#f8fafc",
                "border": "1px solid rgba(14,165,233,0.5)",
                "box-shadow": "0 14px 32px rgba(14,165,233,0.25)",
            },
        }

        if user_type != "authority" and ECO_TIPS_OPTION in options:
            eco_index = options.index(ECO_TIPS_OPTION) + 1
            st.markdown(
                f"""
                <style>
                div[data-testid="stSidebarNav"] ul li:nth-child({eco_index}) .nav-link-icon svg {{
                    width: 20px !important;
                    height: 20px !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        if user_type == "authority":
            default_index = 0
        else:
            default_index = 0

        selected = option_menu(
            menu_title="",
            options=options,
            icons=icons,
            default_index=default_index,
            styles=nav_styles,
        )
    return selected


def ensure_session_defaults() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("page", "login")
    st.session_state.setdefault("user_data", None)
    st.session_state.setdefault("user_type", None)
    st.session_state.setdefault("last_update", datetime.now())


def main() -> None:
    ensure_session_defaults()

    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            registration_page.render_registration_page()
        else:
            login_page.render_login_page()
        return

    selected = render_sidebar()

    if selected == "City statistics":
        render_city_statistics()
    elif selected == "Smart assistant":
        chat_assistant.show_chat_assistant()
    elif selected == "Feedback":
        feedback_form.render_feedback_form()
    elif selected == "Feedback queue":
        feedback_form.render_feedback_form()
    elif selected == ECO_TIPS_OPTION:
        eco_tips.render_eco_tips()
    elif selected == "Announcements":
        announcements.render_announcements()
    elif selected == "Policy summarizer":
        policy_summarizer.render_policy_summarizer()


if __name__ == "__main__":
    main()

