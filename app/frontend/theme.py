"""Shared visual theme helpers for the Streamlit frontend."""

from __future__ import annotations

import streamlit as st

GLOBAL_CSS = """
<style>
:root {
    --brand-50: #f0f9ff;
    --brand-100: #e0f2fe;
    --brand-200: #bae6fd;
    --brand-500: #0ea5e9;
    --brand-600: #0284c7;
    --brand-700: #0369a1;
    --brand-900: #0b1120;
    --surface-900: rgba(15, 23, 42, 0.78);
    --surface-800: rgba(30, 41, 59, 0.82);
    --surface-contrast: rgba(148, 163, 184, 0.3);
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
    --success: #22c55e;
    --warning: #f97316;
    --danger: #ef4444;
    --radius-lg: 22px;
    --radius-md: 16px;
    --radius-sm: 12px;
    --shadow-soft: 0 20px 45px rgba(15, 23, 42, 0.25);
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0b1120 0%, #0f172a 45%, #111c2f 100%) !important;
    color: var(--text-primary);
    font-family: "Inter", "Segoe UI", sans-serif;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(11, 17, 32, 0.95), rgba(11, 17, 32, 0.8));
    backdrop-filter: blur(24px);
    border-right: 1px solid rgba(148, 163, 184, 0.2);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

.block-container {
    padding-top: 2.5rem !important;
    max-width: 1200px;
}

.stApp header {
    background: transparent;
}

.stApp [data-testid="stToolbar"] {
    background: transparent;
}

.stApp a {
    color: var(--brand-200);
}

.glass-panel {
    background: var(--surface-900);
    border: 1px solid var(--surface-contrast);
    border-radius: var(--radius-lg);
    padding: 1.5rem 1.7rem;
    box-shadow: var(--shadow-soft);
    transition: border 0.2s ease, transform 0.2s ease;
}

.glass-panel:hover {
    border-color: rgba(14, 165, 233, 0.45);
    transform: translateY(-2px);
}

.hero-banner {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    background: linear-gradient(120deg, rgba(14, 165, 233, 0.16), rgba(14, 116, 144, 0.12));
    border-radius: var(--radius-lg);
    border: 1px solid rgba(148, 163, 184, 0.25);
    padding: 2.5rem 2.2rem;
    box-shadow: var(--shadow-soft);
}

.hero-banner__title {
    font-size: clamp(2.1rem, 4vw, 2.9rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.4rem;
}

.hero-banner__subtitle {
    color: var(--text-muted);
    font-size: 1.05rem;
    max-width: 40rem;
}

.stat-grid {
    display: grid;
    gap: 1.2rem;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.stat-card {
    position: relative;
    border-radius: var(--radius-md);
    padding: 1.25rem 1.4rem;
    background: linear-gradient(160deg, rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(148, 163, 184, 0.2);
    overflow: hidden;
}

.stat-card::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(140deg, rgba(14, 165, 233, 0.18), transparent 65%);
    opacity: 0;
    transition: opacity 0.2s ease;
}

.stat-card:hover::after {
    opacity: 1;
}

.stat-card__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    border-radius: 0.8rem;
    background: rgba(14, 165, 233, 0.18);
    color: var(--brand-200);
    font-size: 1.45rem;
    margin-bottom: 0.9rem;
}

.stat-card__title {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 0.45rem;
}

.stat-card__value {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

.stat-card__delta {
    font-size: 0.9rem;
    font-weight: 500;
}

.stat-card--success .stat-card__delta {
    color: var(--success);
}

.stat-card--warning .stat-card__delta {
    color: var(--warning);
}

.stat-card--danger .stat-card__delta {
    color: var(--danger);
}

.section-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 0 1rem 0;
}

.section-heading h3 {
    font-size: 1.35rem;
    font-weight: 600;
    margin: 0;
}

.section-heading span {
    color: var(--text-muted);
    font-size: 0.95rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(14, 165, 233, 0.15);
    color: var(--brand-200);
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.85rem;
}

.metric-stack {
    display: grid;
    gap: 1rem;
}

.metric-block {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 23, 42, 0.65);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
}

.metric-block__label {
    font-size: 0.95rem;
    color: var(--text-muted);
}

.metric-block__value {
    font-size: 1.2rem;
    font-weight: 600;
}

.recommendation-card {
    background: rgba(22, 163, 74, 0.12);
    border-left: 3px solid rgba(34, 197, 94, 0.8);
    border-radius: var(--radius-md);
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}

.recommendation-card.warning {
    background: rgba(234, 179, 8, 0.1);
    border-left-color: rgba(234, 179, 8, 0.65);
}

.recommendation-card.danger {
    background: rgba(239, 68, 68, 0.12);
    border-left-color: rgba(239, 68, 68, 0.8);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    padding: 0.75rem 1.4rem;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    transition: border 0.2s ease, color 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: rgba(14, 165, 233, 0.12);
    border-color: rgba(14, 165, 233, 0.35);
    color: var(--text-primary) !important;
}

.stButton > button {
    border-radius: 999px;
    padding: 0.65rem 1.4rem;
    border: 1px solid rgba(14, 165, 233, 0.35);
    background: linear-gradient(120deg, rgba(14, 165, 233, 0.25), rgba(14, 165, 233, 0.1));
    color: var(--text-primary);
    font-weight: 600;
    transition: transform 0.2s ease, border 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(14, 165, 233, 0.6);
}

.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox select, .stMultiSelect div[data-baseweb="select"] > div {
    background: rgba(15, 23, 42, 0.65) !important;
    border: 1px solid rgba(148, 163, 184, 0.25) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

.stMetric label {
    color: var(--text-muted) !important;
}

/* Streamlit option menu overrides */
ul[role="tablist"] li {
    border-radius: var(--radius-sm) !important;
}

/* Notification container */
.stAlert {
    border-radius: var(--radius-md) !important;
    border: 1px solid rgba(148, 163, 184, 0.3) !important;
}

</style>
"""


def apply_theme() -> None:
    """Inject the shared CSS theme into the current Streamlit page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)