"""DemandWise UI Error Handling and Feedback Components"""
import streamlit as st
from textwrap import dedent

def show_error_state(title: str, message: str, resolution: str = "Please try again or contact support."):
    """Render a comprehensive block for unrecoverable errors."""
    st.error(f"**{title}**\n\n{message}\n\n*Fix:* {resolution}")

def show_empty_state(icon: str, title: str, description: str, action_label: str = None, action_key: str = None) -> bool:
    """Render a polished empty state when there's no data to show."""
    st.markdown(dedent(f"""
    <div style="text-align: center; padding: 4rem 2rem; background: white; border-radius: 12px; border: 1px dashed #ced4da; margin: 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem; color: #adb5bd;">{icon}</div>
        <h3 style="color: #495057; font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;">{title}</h3>
        <p style="color: #6c757d; max-width: 400px; margin: 0 auto 1.5rem auto;">{description}</p>
    </div>
    """).strip(), unsafe_allow_html=True)

    if action_label and action_key:
        cols = st.columns([1, 1, 1])
        with cols[1]:
            return st.button(action_label, key=action_key, use_container_width=True)
    return False

def show_loading_state(message: str = "Loading data..."):
    """Render a loading spinner with standard messaging."""
    return st.spinner(message)
