"""
DemandWise - Professional UI Components
Reusable, polished Streamlit UI components with enterprise styling.
"""
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from src.styles.theme import COLORS

def render_header(title: str, subtitle: Optional[str] = None, badge: Optional[str] = None, icon: str = "📊"):
    """Render a consistent, modern page header."""
    badge_html = f'<span style="background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]}); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; vertical-align: middle; margin-left: 10px;">{badge}</span>' if badge else ''

    subtitle_html = f'<p style="font-size: 1.1rem; color: {COLORS["text_secondary"]}; margin-top: -0.5rem; margin-bottom: 1.5rem;">{subtitle}</p>' if subtitle else ''

    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.25rem;">
            <span style="font-size: 2.2rem;">{icon}</span>
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, {COLORS['text_primary']} 0%, {COLORS['primary']} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{title}</h1>
            {badge_html}
        </div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)

def render_card(title: str, content: str, icon: Optional[str] = None, color: str = "primary", footer: Optional[str] = None):
    """Render a styled information card."""
    border_color = COLORS.get(color, COLORS['primary'])
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 8px;">{icon}</span>' if icon else ''
    footer_html = f'<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #edf2f7; font-size: 0.8rem; color: {COLORS["text_muted"]};">{footer}</div>' if footer else ''

    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #E1E8ED; border-left: 4px solid {border_color}; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            {icon_html}
            <h3 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: {COLORS['text_primary']};">{title}</h3>
        </div>
        <div style="color: {COLORS['text_secondary']}; font-size: 0.95rem; line-height: 1.5;">
            {content}
        </div>
        {footer_html}
    </div>
    """, unsafe_allow_html=True)

def render_kpi_card(label: str, value: str, delta: Optional[str] = None, delta_type: str = "positive", icon: str = "📈"):
    """Render an executive KPI card with delta indicator."""
    delta_color = COLORS['success'] if delta_type == "positive" else COLORS['danger'] if delta_type == "negative" else COLORS['text_secondary']
    delta_arrow = "↑" if delta_type == "positive" else "↓" if delta_type == "negative" else "•"
    delta_html = f'<span style="color: {delta_color}; font-weight: 600; font-size: 0.85rem; margin-left: 8px;">{delta_arrow} {delta}</span>' if delta else ''

    st.markdown(f"""
    <div style="background: white; border-radius: 12px; padding: 1.25rem 1.5rem; border: 1px solid #E1E8ED; box-shadow: 0 2px 6px rgba(0,0,0,0.04); transition: transform 0.2s ease;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: {COLORS['text_secondary']};">{label}</span>
            <span style="font-size: 1.25rem;">{icon}</span>
        </div>
        <div style="display: flex; align-items: baseline;">
            <span style="font-size: 1.8rem; font-weight: 700; color: {COLORS['primary_dark']}; font-family: 'Space Grotesk', sans-serif;">{value}</span>
            {delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_status_badge(status: str, label: Optional[str] = None):
    """Render a colored status badge."""
    text = label or status
    status_lower = status.lower()
    if status_lower in ['success', 'active', 'good', 'optimal', 'ready']:
        bg = "#d1fae5"
        color = "#065f46"
    elif status_lower in ['warning', 'caution', 'medium', 'pending']:
        bg = "#fef3c7"
        color = "#92400e"
    elif status_lower in ['danger', 'error', 'failed', 'high risk']:
        bg = "#fee2e2"
        color = "#991b1b"
    else:
        bg = "#e0f2fe"
        color = "#075985"

    return f'<span style="background-color: {bg}; color: {color}; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">{text}</span>'

def render_footer():
    """Render a clean, professional footer."""
    st.markdown(f"""
    <div style="margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid #E1E8ED; display: flex; justify-content: space-between; align-items: center; color: {COLORS['text_muted']}; font-size: 0.85rem;">
        <div>
            <strong>DemandWise</strong> — Intelligent Food Demand Forecasting Platform
        </div>
        <div>
            Enterprise Edition v1.2.0 • Local Secure Deployment
        </div>
    </div>
    """, unsafe_allow_html=True)
