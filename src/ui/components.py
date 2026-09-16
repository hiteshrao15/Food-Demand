"""
DemandWise - Premium UI Components Library
Reusable, polished Streamlit components with enterprise-grade styling and animations.
"""
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from textwrap import dedent
from src.styles.theme import COLORS, FONTS


def _render_html(markup: str):
    """Render generated HTML without indentation being parsed as a code block."""
    normalized = "\n".join(line.strip() for line in dedent(markup).splitlines()).strip()
    st.markdown(normalized, unsafe_allow_html=True)


def render_html(markup: str):
    """Render a page-level HTML block with Markdown-safe indentation."""
    _render_html(markup)

# ==================== PAGE STRUCTURE ====================

def render_top_bar(page_title: str, page_icon: str = "📊", subtitle: Optional[str] = None, 
                   action_button: Optional[Tuple[str, str]] = None):
    """
    Render responsive top application bar with title, subtitle, and optional action.
    
    Args:
        page_title: Page title
        page_icon: Emoji icon for the page
        subtitle: Optional contextual subtitle
        action_button: Tuple of (button_label, button_key) for primary action
    """
    col1, col2 = st.columns([1, 0.2]) if action_button else (st.columns(1)[0], None)
    
    with col1:
        header_html = f"""
        <div style="margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid {COLORS['border_dark']};">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">{page_icon}</span>
                <h1 style="margin: 0; font-size: 2rem; font-weight: 700; color: {COLORS['text_primary']};">
                    {page_title}
                </h1>
            </div>
            {f'<p style="margin: 0.5rem 0 0 0; color: {COLORS["text_secondary"]}">{subtitle}</p>' if subtitle else ''}
        </div>
        """
        _render_html(header_html)
    
    if col2 and action_button:
        with col2:
            st.write("")  # Spacer
            st.write("")

# ==================== CARDS ====================

def render_kpi_card(label: str, value: Any, delta: Optional[str] = None, 
                    delta_type: str = "neutral", icon: str = "📊", color_accent: str = "primary"):
    """
    Render animated KPI card with optional delta indicator.
    
    Args:
        label: KPI label (uppercase, concise)
        value: Main value to display
        delta: Optional change indicator (e.g., "+15%", "-8")
        delta_type: "positive", "negative", or "neutral"
        icon: Emoji icon
        color_accent: Color variant for accent
    """
    delta_color_map = {
        "positive": COLORS['success'],
        "negative": COLORS['danger'],
        "neutral": COLORS['text_muted'],
    }
    delta_color = delta_color_map.get(delta_type, COLORS['text_muted'])
    delta_arrow = {"positive": "↑", "negative": "↓", "neutral": "•"}.get(delta_type, "•")
    
    delta_html = (
        f'<div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.5rem; '
        f'color: {delta_color};">{delta_arrow} {delta}</div>'
        if delta else ""
    )
    
    kpi_html = f"""
    <div class="kpi-card" style="position: relative; padding: 1.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
            <div class="kpi-label">{label}</div>
            <span style="font-size: 1.5rem;">{icon}</span>
        </div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    _render_html(kpi_html)

def render_data_card(title: str, content: str, icon: Optional[str] = None, 
                     footer: Optional[str] = None, color: str = "primary"):
    """Render styled information/data card."""
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 12px;">{icon}</span>' if icon else ""
    footer_html = f"""
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid {COLORS['border_dark']}; 
                    font-size: 0.8rem; color: {COLORS['text_muted']};">{footer}</div>
    """ if footer else ""
    
    card_html = f"""
    <div class="card" style="border-left: 4px solid {COLORS['primary']};">
        <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
            {icon_html}
            <h3 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: {COLORS['text_primary']};">
                {title}
            </h3>
        </div>
        <div style="color: {COLORS['text_secondary']}; line-height: 1.5; font-size: 0.95rem;">
            {content}
        </div>
        {footer_html}
    </div>
    """
    _render_html(card_html)

def render_status_card(title: str, status: str, items: Dict[str, str]):
    """
    Render a status overview card with key-value pairs.
    
    Args:
        title: Card title
        status: Overall status ("success", "warning", "danger")
        items: Dict of label -> value pairs
    """
    status_colors = {
        "success": (COLORS['success'], "✓"),
        "warning": (COLORS['warning'], "⚠"),
        "danger": (COLORS['danger'], "✕"),
    }
    status_color, status_icon = status_colors.get(status, (COLORS['text_muted'], "•"))
    
    items_html = "".join([
        f"""
        <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; 
                    border-bottom: 1px solid {COLORS['border_subtle']};">
            <span style="color: {COLORS['text_secondary']};">{label}</span>
            <span style="color: {COLORS['text_primary']}; font-weight: 500;">{value}</span>
        </div>
        """ for label, value in items.items()
    ])
    
    card_html = f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: {COLORS['text_primary']};">{title}</h3>
            <span style="font-size: 1.5rem; color: {status_color};">{status_icon}</span>
        </div>
        {items_html}
    </div>
    """
    _render_html(card_html)

# ==================== BADGES ====================

def render_status_badge(status: str, label: Optional[str] = None, size: str = "medium") -> str:
    """
    Return HTML badge with semantic color.
    
    Args:
        status: "success", "warning", "danger", "info", "saffron"
        label: Custom label (defaults to status)
        size: "small", "medium", "large"
    
    Returns:
        HTML string for badge
    """
    text = label or status.replace("_", " ").title()
    size_map = {"small": "0.65rem", "medium": "0.75rem", "large": "0.85rem"}
    font_size = size_map.get(size, "0.75rem")
    
    badge_class = f"badge-{status}" if status in ["success", "warning", "danger", "saffron"] else "badge-info"
    
    return f'<span class="badge {badge_class}" style="font-size: {font_size};">{text}</span>'

# ==================== SECTIONS ====================

def section_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """Render section header with optional icon and subtitle."""
    icon_html = f'<span style="font-size: 1.75rem; margin-right: 12px;">{icon}</span>' if icon else ""
    
    header_html = f"""
    <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid {COLORS['border_dark']};">
        <div style="display: flex; align-items: center; gap: 12px;">
            {icon_html}
            <div>
                <h2 style="margin: 0; font-size: 1.5rem; font-weight: 600; color: {COLORS['text_primary']};">
                    {title}
                </h2>
                {f'<p style="margin: 0.25rem 0 0 0; color: {COLORS["text_secondary"]}; font-size: 0.9rem;">{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
    </div>
    """
    _render_html(header_html)

def divider():
    """Render subtle divider."""
    st.markdown(f'<div class="divider-subtle"></div>', unsafe_allow_html=True)

# ==================== STATES ====================

def empty_state(icon: str = "📭", title: str = "No Data", message: str = "", action_text: Optional[str] = None):
    """Render empty state."""
    action_html = f"""
    <div style="margin-top: 1.5rem;">
        <button style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['primary_dark']});
                       color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px;
                       font-weight: 600; cursor: pointer;">
            {action_text}
        </button>
    </div>
    """ if action_text else ""
    
    empty_html = f"""
    <div style="text-align: center; padding: 3rem 2rem; background: rgba(0,0,0,0.2);
                border-radius: 12px; border: 1px solid {COLORS['border_dark']};">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <h3 style="margin: 0 0 0.5rem 0; color: {COLORS['text_primary']};">{title}</h3>
        <p style="margin: 0 0 1rem 0; color: {COLORS['text_secondary']}; max-width: 400px; margin-left: auto; margin-right: auto;">
            {message}
        </p>
        {action_html}
    </div>
    """
    _render_html(empty_html)

def loading_skeleton(height: str = "100px"):
    """Render animated loading skeleton."""
    skeleton_html = f"""
    <style>
        @keyframes shimmer {{
            0% {{ background-position: -1000px 0; }}
            100% {{ background-position: 1000px 0; }}
        }}
        .skeleton {{
            height: {height};
            background: linear-gradient(90deg, {COLORS['surface_dark']} 25%, {COLORS['surface_light']} 50%, {COLORS['surface_dark']} 75%);
            background-size: 200% 100%;
            animation: shimmer 2s infinite;
            border-radius: 8px;
        }}
    </style>
    <div class="skeleton"></div>
    """
    _render_html(skeleton_html)

def error_state(icon: str = "❌", title: str = "Error", message: str = ""):
    """Render error state."""
    error_html = f"""
    <div style="padding: 2rem; background: rgba(239, 68, 68, 0.1); border-radius: 12px;
                border-left: 4px solid {COLORS['danger']};">
        <div style="display: flex; gap: 1rem;">
            <span style="font-size: 1.75rem;">{icon}</span>
            <div>
                <h4 style="margin: 0 0 0.5rem 0; color: {COLORS['danger']};">{title}</h4>
                <p style="margin: 0; color: {COLORS['text_secondary']};">{message}</p>
            </div>
        </div>
    </div>
    """
    _render_html(error_html)

def success_state(icon: str = "✓", title: str = "Success", message: str = ""):
    """Render success state."""
    success_html = f"""
    <div style="padding: 2rem; background: rgba(16, 185, 129, 0.1); border-radius: 12px;
                border-left: 4px solid {COLORS['success']};">
        <div style="display: flex; gap: 1rem;">
            <span style="font-size: 1.75rem; color: {COLORS['success']};">{icon}</span>
            <div>
                <h4 style="margin: 0 0 0.5rem 0; color: {COLORS['success']};">{title}</h4>
                <p style="margin: 0; color: {COLORS['text_secondary']};">{message}</p>
            </div>
        </div>
    </div>
    """
    _render_html(success_html)

# ==================== FORMS ====================

def render_form_group(label: str, required: bool = False, help_text: Optional[str] = None):
    """Render labeled form group header."""
    required_marker = (
        f' <span style="color: {COLORS["danger"]}; font-weight: 600;">*</span>'
        if required else ""
    )
    help_html = f'<small style="color: {COLORS["text_muted"]}; margin-top: 0.25rem;">{help_text}</small>' if help_text else ""
    
    form_html = f"""
    <div style="margin-bottom: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600; 
                      color: {COLORS['text_primary']};">
            {label}{required_marker}
        </label>
        {help_html}
    </div>
    """
    _render_html(form_html)

# ==================== FOOTER ====================

def render_footer():
    """Render professional footer."""
    footer_html = f"""
    <div style="margin-top: 4rem; padding-top: 2rem; padding-bottom: 1rem;
                border-top: 1px solid {COLORS['border_dark']};
                display: flex; justify-content: space-between; align-items: center;
                color: {COLORS['text_muted']}; font-size: 0.85rem;">
        <div>
            <strong>DemandWise</strong> — Intelligent Food Demand Forecasting
        </div>
        <div>
            Enterprise Edition v2.0 • 
            <span style="color: {COLORS['success']};">✓ Local Secure Deployment</span>
        </div>
    </div>
    """
    _render_html(footer_html)

# ==================== UTILITIES ====================

def metric_comparison(label: str, current: Any, previous: Any, 
                      format_func=None, unit: str = ""):
    """Display metric with comparison to previous value."""
    if format_func:
        current_str = format_func(current)
        previous_str = format_func(previous)
    else:
        current_str = str(current)
        previous_str = str(previous)
    
    try:
        change = float(current) - float(previous)
        change_pct = (change / float(previous) * 100) if float(previous) != 0 else 0
        delta_type = "positive" if change >= 0 else "negative"
        delta_text = f"{change:+.1f}% ({change:+.0f} {unit})"
    except:
        delta_text = "N/A"
        delta_type = "neutral"
    
    render_kpi_card(label, f"{current_str} {unit}", delta_text, delta_type)
