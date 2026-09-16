"""
DemandWise - Data Management Page
Guided workflow: choose source, provide data, validate with friendly
messages, review, and activate. Activation persists to the configured
dataset file and invalidates caches so every page uses the new data.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.data.loader import DataLoader
from src.state import (
    activate_dataset,
    dataset_summary,
    is_sample_mode,
    load_active_dataset,
    normalize_upload,
    render_data_source_banner,
    use_sample_dataset,
    validate_upload,
)
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, render_kpi_card,
    section_header, divider, error_state, success_state, render_footer, render_html,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

st.markdown(get_custom_css(), unsafe_allow_html=True)

config = get_config()
MIN_HISTORY = int(config['data'].get('min_history_days', 30))

# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Data Management",
    page_icon="📂",
    subtitle="Upload, validate, review, and activate your food demand dataset.",
)
render_data_source_banner()

# Current active dataset status (live)
active_df, active_label, active_sample = load_active_dataset()
if active_df is not None and not active_df.empty:
    summary = dataset_summary(active_df)
    st.markdown(f"""
    <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem;">
        <b>Active dataset:</b> {active_label} — {summary['records']:,} records, {summary['items']} items
        {f"({summary['min_date']} → {summary['max_date']})" if summary.get('min_date') else ""}
        {' • <b>sample mode</b>' if active_sample else ""}
    </div>
    """, unsafe_allow_html=True)

# ========== MULTI-STEP WORKFLOW ==========

if 'data_step' not in st.session_state:
    st.session_state.data_step = 1

st.markdown(f"""
<style>
    .step-indicator {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid {COLORS['border_dark']};
    }}
    .step {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: {COLORS['text_secondary']};
        font-weight: 500;
        font-size: 0.9rem;
    }}
    .step.active {{ color: {COLORS['primary']}; }}
    .step-number {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: 2px solid currentColor;
        font-weight: 600;
        font-size: 0.9rem;
    }}
    .step.active .step-number {{
        background: {COLORS['primary']};
        color: white;
        border-color: {COLORS['primary']};
    }}
</style>

<div class="step-indicator">
    <div class="step{' active' if st.session_state.data_step == 1 else ''}">
        <div class="step-number">1</div><span>Choose Source</span>
    </div>
    <div class="step{' active' if st.session_state.data_step == 2 else ''}">
        <div class="step-number">2</div><span>Provide Data</span>
    </div>
    <div class="step{' active' if st.session_state.data_step == 3 else ''}">
        <div class="step-number">3</div><span>Validate</span>
    </div>
    <div class="step{' active' if st.session_state.data_step == 4 else ''}">
        <div class="step-number">4</div><span>Review &amp; Activate</span>
    </div>
</div>
""", unsafe_allow_html=True)


def reset_workflow():
    for key in ('uploaded_df', 'manual_records', 'data_source', 'validation'):
        st.session_state.pop(key, None)
    st.session_state.data_step = 1


# ========== STEP 1: CHOOSE SOURCE ==========

if st.session_state.data_step == 1:
    section_header(title="Step 1: Choose Data Source",
                   subtitle="Select how you want to provide your demand data", icon="📂")

    source_col1, source_col2, source_col3 = st.columns(3, gap="large")

    with source_col1:
        if st.button("📊 Demo Data", use_container_width=True, help="Use the labelled built-in sample dataset"):
            st.session_state.data_source = "demo"
            st.session_state.data_step = 2
            st.rerun()
        st.markdown(f"<div style='font-size:.85rem;color:{COLORS['text_secondary']};margin-top:.5rem;'>Explore with clearly-labelled sample data</div>", unsafe_allow_html=True)

    with source_col2:
        if st.button("📁 Upload CSV", use_container_width=True, help="Upload your own CSV file"):
            st.session_state.data_source = "csv"
            st.session_state.data_step = 2
            st.rerun()
        st.markdown(f"<div style='font-size:.85rem;color:{COLORS['text_secondary']};margin-top:.5rem;'>Import operational data from a CSV file</div>", unsafe_allow_html=True)

    with source_col3:
        if st.button("✏️ Manual Entry", use_container_width=True, help="Enter records one by one"):
            st.session_state.data_source = "manual"
            st.session_state.data_step = 2
            st.rerun()
        st.markdown(f"<div style='font-size:.85rem;color:{COLORS['text_secondary']};margin-top:.5rem;'>Type in a few records for a quick trial</div>", unsafe_allow_html=True)

    divider()

    with st.expander("📋 CSV Format Requirements", expanded=False):
        st.markdown("""
        Your CSV needs exactly these columns (aliases like **is_holiday** are auto-normalised):

        - **date**: YYYY-MM-DD (e.g. 2024-03-01)
        - **food_item**: item name, consistent spelling (e.g. Pizza)
        - **demand**: non-negative integer units sold
        - **holiday**: 0 (regular day) or 1 (holiday / special event)

        At least 30 days of history across your items is recommended for reliable forecasts.
        """)
        template_df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'food_item': ['Pizza', 'Pizza', 'Burger'],
            'demand': [45, 52, 38],
            'holiday': [1, 0, 0],
        })
        st.download_button("📥 Download CSV Template", data=template_df.to_csv(index=False),
                           file_name="food_demand_template.csv", mime="text/csv")

# ========== STEP 2: DATA INPUT ==========

elif st.session_state.data_step == 2:
    section_header(title="Step 2: Provide Data",
                   subtitle=f"Source: {st.session_state.get('data_source', '—').title()}", icon="📥")

    source = st.session_state.get('data_source')
    df = None

    if source == "demo":
        st.info("The built-in demo dataset is generated locally and will be labelled as **sample data** everywhere — it never mixes with operational data.")
        if st.button("Load demo preview", type="primary"):
            try:
                st.session_state.uploaded_df = DataLoader.generate_demo_dataset()
                st.success(f"✓ Loaded {len(st.session_state.uploaded_df):,} sample records.")
            except Exception as e:
                logger.error(f"Demo generation failed: {e}", exc_info=True)
                st.error("Could not generate the demo dataset. Please try again.")
        df = st.session_state.get('uploaded_df')

    elif source == "csv":
        uploaded_file = st.file_uploader("Upload CSV file", type="csv",
                                         help="Columns: date, food_item, demand, holiday (0/1).")
        if uploaded_file:
            try:
                raw = pd.read_csv(uploaded_file)
                clean = normalize_upload(raw)
                st.session_state.uploaded_df = clean
                st.success(f"✓ Parsed {len(clean):,} records across {clean['food_item'].nunique()} items.")
                if len(raw) != len(clean):
                    st.warning(f"ℹ️ {len(raw) - len(clean)} incomplete row(s) were dropped (missing date/item/demand).")
            except ValueError as ve:
                st.error(f"Could not use this file: {ve}")
            except Exception as e:
                logger.error(f"CSV parse failed: {e}", exc_info=True)
                st.error("Could not read this CSV. Check the format requirements in Step 1.")
        df = st.session_state.get('uploaded_df')
        if df is not None:
            st.markdown("**Preview (first 5 rows)**")
            st.dataframe(df.head(5), use_container_width=True, hide_index=True)

    elif source == "manual":
        st.markdown("#### Add Records Manually")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            entry_date = st.date_input("Date", key="manual_date")
        with col2:
            entry_item = st.text_input("Food Item", placeholder="Pizza", key="manual_item")
        with col3:
            entry_demand = st.number_input("Demand", min_value=0, value=0, key="manual_demand")
        with col4:
            entry_holiday = st.checkbox("Holiday", key="manual_holiday")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ Add Record", use_container_width=True):
                if not entry_item.strip():
                    st.error("Enter a food item name first.")
                else:
                    st.session_state.setdefault('manual_records', []).append({
                        'date': pd.to_datetime(entry_date), 'food_item': entry_item.strip(),
                        'demand': int(entry_demand), 'holiday': int(entry_holiday)})
                    st.success("✓ Record added.")
        with c2:
            if st.button("🗑️ Clear Records", use_container_width=True):
                st.session_state.manual_records = []
                st.session_state.pop('uploaded_df', None)
                st.rerun()
        if st.session_state.get('manual_records'):
            df = pd.DataFrame(st.session_state.manual_records)
            st.session_state.uploaded_df = df
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No manual records yet — add at least a few rows covering different dates.")

    if df is not None and not df.empty:
        st.success(f"✓ Draft ready: {len(df):,} records.")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back"):
                st.session_state.data_step = 1
                st.rerun()
        with col2:
            if st.button("🗑️ Discard Draft"):
                st.session_state.pop('uploaded_df', None)
                st.session_state.pop('manual_records', None)
                st.rerun()
        with col3:
            if st.button("Next: Validate →", type="primary"):
                st.session_state.data_step = 3
                st.rerun()
    else:
        if st.button("← Back"):
            st.session_state.data_step = 1
            st.rerun()

# ========== STEP 3: VALIDATION ==========

elif st.session_state.data_step == 3:
    section_header(title="Step 3: Validation",
                   subtitle="Checking data quality with actionable feedback", icon="✓")

    df = st.session_state.get('uploaded_df')
    if df is None or df.empty:
        error_state("❌", "No Data", "Please provide data first.")
        if st.button("← Back"):
            st.session_state.data_step = 2
            st.rerun()
        st.stop()

    ok, errors, warnings = validate_upload(df, min_history_days=MIN_HISTORY)
    st.session_state['validation'] = {'ok': ok, 'errors': errors, 'warnings': warnings}

    qual_col1, qual_col2, qual_col3, qual_col4 = st.columns(4)
    with qual_col1:
        render_kpi_card("Records", f"{len(df):,}", icon="📊")
    with qual_col2:
        items = df['food_item'].nunique() if 'food_item' in df.columns else 0
        render_kpi_card("Items", str(items), icon="🍕")
    with qual_col3:
        nulls = int(df.isnull().sum().sum())
        render_kpi_card("Missing Values", str(nulls), delta_type="positive" if nulls == 0 else "negative", icon="⚠️")
    with qual_col4:
        render_kpi_card("Status", "✓ Passed" if ok else "✕ Blocked",
                        delta_type="positive" if ok else "negative", icon="✅" if ok else "⛔")

    if errors:
        st.error("**Fix these before activation:**")
        for err in errors:
            st.markdown(f"- {err}")
        st.info("Tip: use the CSV template in Step 1 — it has the exact required columns and holiday coding (0/1).")
    if warnings:
        for warn in warnings:
            st.warning(f"⚠️ {warn}")
    if ok and not warnings:
        st.success("✓ Data looks great — ready for review.")

    st.markdown("**Preview (first 10 rows)**")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back"):
            st.session_state.data_step = 2
            st.rerun()
    with col2:
        if st.button("↺ Start Over"):
            reset_workflow()
            st.rerun()
    with col3:
        if st.button("Next: Review →", type="primary", disabled=not ok):
            st.session_state.data_step = 4
            st.rerun()

# ========== STEP 4: REVIEW & ACTIVATE ==========

elif st.session_state.data_step == 4:
    section_header(title="Step 4: Review & Activate",
                   subtitle="Final review — activation replaces the dataset everywhere", icon="🎯")

    df = st.session_state.get('uploaded_df')
    if df is None or df.empty:
        error_state("❌", "No Data", "Please provide data first.")
        if st.button("← Back to Start"):
            reset_workflow()
            st.rerun()
        st.stop()

    validation = st.session_state.get('validation', {})
    if not validation.get('ok', False):
        ok, errors, _w = validate_upload(df, min_history_days=MIN_HISTORY)
        if not ok:
            error_state("⛔", "Validation Failed", "; ".join(errors))
            if st.button("← Back to Validation"):
                st.session_state.data_step = 3
                st.rerun()
            st.stop()

    summary = dataset_summary(df)
    source = st.session_state.get('data_source', 'csv')
    source_txt = "Sample (labelled demo)" if source == "demo" else ("Manual entry" if source == "manual" else "Uploaded CSV")
    render_html(f"""
    <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
            <div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Total Records</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-top: 0.5rem;">{summary['records']:,}</div>
            </div>
            <div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">Food Items</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-top: 0.5rem;">{summary['items']}</div>
            </div>
            <div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">History Span</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin-top: 0.5rem;">{summary['min_date']} → {summary['max_date']} ({summary['span_days']} days)</div>
            </div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.85rem; color: {COLORS['text_secondary']};">Source: <b>{source_txt}</b> • Activating replaces the active dataset file and refreshes Forecast, Analytics, Overview and the model input.</div>
    </div>
    """)

    st.markdown("**Data Preview (first 10 records)**")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid {COLORS['success']};
                padding: 1rem; border-radius: 6px; margin: 1.5rem 0;">
        <div style="font-weight: 600; color: {COLORS['success']};">✓ Ready to Activate</div>
        <div style="font-size: 0.9rem; color: {COLORS['text_secondary']}; margin-top: 0.5rem;">
            After activation, retrain on the Model page so predictions learn the new patterns
            (existing saved forecasts in History are kept).
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Back"):
            st.session_state.data_step = 3
            st.rerun()
    with col2:
        if st.button("↺ Start Over"):
            reset_workflow()
            st.rerun()
    with col3:
        if st.button("✓ Activate Dataset", type="primary"):
            if source == "demo":
                ok, msg = use_sample_dataset()
            else:
                ok, msg = activate_dataset(df, source="uploaded")
            if ok:
                st.session_state.data_step = 1
                success_state("✓", "Dataset Activated", msg + " Now retrain the model to learn the new patterns.")
                st.balloons()
                st.session_state['just_activated'] = True
            else:
                error_state("❌", "Activation Failed", msg)

    if st.session_state.pop('just_activated', False):
        if st.button("⚙️ Retrain Now on Model Page →", type="primary"):
            st.session_state.selected_page = "Model"
            st.rerun()

divider()
render_footer()
