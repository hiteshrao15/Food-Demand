"""
DemandWise - Settings Page
Preferences that actually persist (session) and wire into Forecast,
Overview and Model pages — plus honest live system information.
"""
import streamlit as st
import pandas as pd
import shutil
from datetime import datetime
from importlib import metadata as importlib_metadata
import platform
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import BASE_DIR, get_config, resolve_dataset_path, resolve_database_path
from src.state import dataset_summary, get_model_metadata, load_active_dataset, render_data_source_banner
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import render_top_bar, section_header, divider, render_footer
from src.utils.logger import get_logger

logger = get_logger(__name__)
st.markdown(get_custom_css(), unsafe_allow_html=True)
config = get_config()

# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Settings",
    page_icon="⚙️",
    subtitle="Preferences apply immediately across Forecast, Overview and Model pages (this session).",
)
render_data_source_banner()

# Session-backed defaults so every control does what it says.
st.session_state.setdefault('org_name', 'My Restaurant')
st.session_state.setdefault('timezone', 'UTC')
st.session_state.setdefault('theme_choice', 'Dark (Recommended)')
st.session_state.setdefault('notify_high', True)
st.session_state.setdefault('notify_model', True)
st.session_state.setdefault('notify_quality', True)
st.session_state.setdefault('safety_buffer_pct', float(config['prediction'].get('safety_buffer', 10)))
st.session_state.setdefault('forecast_horizon', 1)
st.session_state.setdefault('interval_alert_pct', 60)
st.session_state.setdefault('auto_retrain', False)
st.session_state.setdefault('retrain_schedule', 'Weekly')
st.session_state.setdefault('retrain_test_size', 20)
st.session_state.setdefault('min_r2', 0.85)
st.session_state.setdefault('max_mae', 15)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 General", "🔮 Forecast", "💾 Data", "📊 Model", "ℹ️ About"])

# ========== TAB 1: GENERAL ==========

with tab1:
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>General Preferences</h3>", unsafe_allow_html=True)
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Restaurant/Organization Name</label>", unsafe_allow_html=True)
    org_name = st.text_input("Organization Name", value=st.session_state['org_name'], label_visibility="collapsed", key="set_org")
    st.markdown("")
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Timezone (display only)</label>", unsafe_allow_html=True)
    timezone = st.selectbox("Timezone", ["UTC", "EST", "CST", "MST", "PST", "IST", "JST"],
                            index=["UTC", "EST", "CST", "MST", "PST", "IST", "JST"].index(st.session_state['timezone'])
                            if st.session_state['timezone'] in ["UTC", "EST", "CST", "MST", "PST", "IST", "JST"] else 0,
                            label_visibility="collapsed", key="set_tz")
    st.markdown("")
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Theme</label>", unsafe_allow_html=True)
    theme = st.radio("Theme", options=["Dark (Recommended)", "Light", "Auto"], horizontal=True,
                     index=["Dark (Recommended)", "Light", "Auto"].index(st.session_state['theme_choice']),
                     label_visibility="collapsed", key="set_theme")
    st.caption("DemandWise ships with a dark premium design system; Light/Auto are stored as your preference for a future theme.")
    st.markdown("<h4 style='margin-top: 2rem; margin-bottom: 1rem;'>Notifications (session reminders)</h4>", unsafe_allow_html=True)
    notify_high = st.checkbox("Alert when demand is unusually high", value=st.session_state['notify_high'], key="set_nh")
    notify_model = st.checkbox("Notify when model retraining completes", value=st.session_state['notify_model'], key="set_nm")
    notify_low = st.checkbox("Alert on data quality issues", value=st.session_state['notify_quality'], key="set_nq")
    divider()
    if st.button("✓ Save General Settings", type="primary", use_container_width=True, key="save_general"):
        st.session_state['org_name'] = org_name
        st.session_state['timezone'] = timezone
        st.session_state['theme_choice'] = theme
        st.session_state['notify_high'] = notify_high
        st.session_state['notify_model'] = notify_model
        st.session_state['notify_quality'] = notify_low
        st.success(f"✓ General settings saved — greeting now uses “{org_name}”. Applies across all pages.")

# ========== TAB 2: FORECAST ==========

with tab2:
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>Forecast Configuration</h3>", unsafe_allow_html=True)
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Default Safety Buffer</label>", unsafe_allow_html=True)
    safety_buffer = st.slider("Safety Buffer %", min_value=0, max_value=30, value=int(st.session_state['safety_buffer_pct']),
                              step=1, label_visibility="collapsed", key="set_buffer")
    st.markdown("<small style='color: gray;'>Used by the Overview prep plan and prefilled on the Forecast page</small>", unsafe_allow_html=True)
    st.markdown("")
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Default Forecast Horizon</label>", unsafe_allow_html=True)
    horizon = st.select_slider("Forecast Days Ahead", options=[1, 3, 7, 14, 30],
                               value=st.session_state['forecast_horizon'], label_visibility="collapsed", key="set_horizon")
    st.markdown("")
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Preferred Model</label>", unsafe_allow_html=True)
    model_options = {"Random Forest (Recommended)": "rf", "Linear Regression": "lr", "Deep Learning": "dl"}
    current_model = st.session_state.get('selected_model', config['models'].get('default', 'rf'))
    model = st.radio("Model Type", options=list(model_options),
                     index=next((i for i, c in enumerate(model_options.values()) if c == current_model), 0),
                     label_visibility="collapsed", key="set_model")
    st.markdown("")
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Wide-Interval Alert Threshold (%)</label>", unsafe_allow_html=True)
    interval_alert = st.slider("Interval Alert %", min_value=20, max_value=150, value=st.session_state['interval_alert_pct'],
                               step=5, label_visibility="collapsed", key="set_interval",
                               help="Overview flags prep rows whose 95% interval width exceeds this share of the prediction.")
    st.markdown("<small style='color: gray;'>Uncertainty flag — not an accuracy score</small>", unsafe_allow_html=True)
    divider()
    if st.button("✓ Save Forecast Settings", type="primary", use_container_width=True, key="save_forecast"):
        st.session_state['safety_buffer_pct'] = float(safety_buffer)
        st.session_state['forecast_horizon'] = int(horizon)
        st.session_state['selected_model'] = model_options[model]
        st.session_state['forecast_model_code'] = model_options[model]
        st.session_state['interval_alert_pct'] = int(interval_alert)
        st.success(f"✓ Forecast settings saved — buffer {safety_buffer}%, horizon {horizon}d, model {model}. The Forecast page picks these up.")

# ========== TAB 3: DATA (live status + working backup/export) ==========

with tab3:
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>Data Management</h3>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom: 1rem;'>Current Dataset (live)</h4>", unsafe_allow_html=True)
    df, label, sample = load_active_dataset()
    summary = dataset_summary(df) if df is not None else {'records': 0, 'items': 0, 'min_date': None, 'max_date': None}
    try:
        dataset_path = resolve_dataset_path()
        db_path = resolve_database_path()
    except Exception:
        dataset_path, db_path = BASE_DIR / "data/food_demand_data.csv", BASE_DIR / "data/demandwise.db"

    def _file_line(path: Path) -> str:
        try:
            if path.exists():
                size_kb = path.stat().st_size / 1024
                mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                return f"{path} • {size_kb:.0f} KB • updated {mtime}"
            return f"{path} • not present"
        except Exception:
            return str(path)

    st.markdown(f"""
    <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']}; margin-bottom: 0.5rem;">Status</div>
                <div style="font-weight: 600; color: {COLORS['success'] if summary['records'] else COLORS['warning']}; font-size: 1rem;">{"✓ Active" + (" • sample mode" if sample else "") if summary['records'] else "⚠ No data"}</div></div>
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']}; margin-bottom: 0.5rem;">Records / Items</div>
                <div style="font-weight: 600; font-size: 1rem;">{summary['records']:,} / {summary['items']}</div></div>
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']}; margin-bottom: 0.5rem;">History Span</div>
                <div style="font-weight: 600; font-size: 1rem;">{summary.get('min_date', '—')} → {summary.get('max_date', '—')}</div></div>
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']}; margin-bottom: 0.5rem;">Source</div>
                <div style="font-weight: 600; font-size: 1rem;">{label}</div></div>
        </div>
        <div style="margin-top: 1rem; font-size: 0.8rem; color: {COLORS['text_secondary']};">Dataset file: {_file_line(dataset_path)}<br>Database file: {_file_line(db_path)}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='margin: 2rem 0 1rem 0;'>Data Retention</h4>", unsafe_allow_html=True)
    st.info(f"Prediction-history retention is **{config['database'].get('retention_days', 365)} days** from config.yaml "
            "(0 = keep forever). Change it in config.yaml; History cleanup applies it on each visit.")
    st.markdown("<h4 style='margin: 2rem 0 1rem 0;'>Backup & Export (working)</h4>", unsafe_allow_html=True)
    backup_col1, backup_col2 = st.columns(2)
    with backup_col1:
        if st.button("🔄 Backup Now", key="backup_now"):
            try:
                backup_dir = BASE_DIR / "data" / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                made = []
                if dataset_path.exists():
                    dest = backup_dir / f"food_demand_data_{stamp}.csv"
                    shutil.copy2(dataset_path, dest)
                    made.append(dest.name)
                if db_path.exists():
                    dest = backup_dir / f"demandwise_{stamp}.db"
                    shutil.copy2(db_path, dest)
                    made.append(dest.name)
                if made:
                    st.success(f"✓ Backup complete: {', '.join(made)} in data/backups/.")
                else:
                    st.warning("Nothing to back up yet — no dataset or database file found.")
            except Exception as e:
                logger.error(f"Backup failed: {e}", exc_info=True)
                st.error("Backup failed. Check file permissions and try again.")
    with backup_col2:
        if df is not None and not df.empty:
            st.download_button("📥 Export Active Dataset (CSV)", data=df.to_csv(index=False),
                               file_name=f"demandwise_dataset_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", key="export_all_data")
        else:
            st.button("📥 Export Active Dataset (CSV)", disabled=True, key="export_all_disabled")
            st.caption("No data to export yet.")
    divider()
    if st.button("📂 Open Data Management", type="primary", use_container_width=True, key="goto_data"):
        st.session_state.selected_page = "Data"
        st.rerun()

# ========== TAB 4: MODEL ==========

with tab4:
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>Model Configuration</h3>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom: 1rem;'>Automatic Retraining (preference)</h4>", unsafe_allow_html=True)
    auto_retrain = st.checkbox("Enable automatic model retraining reminder", value=st.session_state['auto_retrain'], key="set_ar")
    if auto_retrain:
        schedule = st.select_slider("Frequency", options=["Daily", "Weekly", "Bi-weekly", "Monthly"],
                                    value=st.session_state['retrain_schedule'], label_visibility="collapsed", key="set_sched")
    else:
        schedule = st.session_state['retrain_schedule']
    st.markdown("")
    st.markdown("<h4 style='margin: 2rem 0 1rem 0;'>Validation Settings</h4>", unsafe_allow_html=True)
    test_size = st.slider("Hold-out Size %", min_value=10, max_value=50,
                          value=st.session_state['retrain_test_size'], step=5,
                          label_visibility="collapsed", key="set_ts",
                          help="Prefilled on the Model page retrain control.")
    st.markdown("")
    st.markdown("<h4 style='margin: 2rem 0 1rem 0;'>Quality Guardrails (advisory)</h4>", unsafe_allow_html=True)
    min_r2 = st.slider("Minimum R² Target", min_value=0.5, max_value=0.99, value=st.session_state['min_r2'],
                       step=0.05, label_visibility="collapsed", key="set_r2")
    max_mae = st.number_input("Maximum Acceptable MAE", value=st.session_state['max_mae'], min_value=1,
                              label_visibility="collapsed", key="set_mae")
    meta = get_model_metadata()
    if meta and meta.get('mae') is not None:
        meets = (float(meta.get('r2', 0)) >= float(min_r2)) and (float(meta.get('mae', 0)) <= float(max_mae))
        st.info(f"Current backtest (MAE {meta['mae']:.1f}, R² {meta.get('r2', 0):.3f}) "
                f"{'✓ meets' if meets else '⚠ misses'} your guardrails.")
    divider()
    if st.button("✓ Save Model Settings", type="primary", use_container_width=True, key="save_model"):
        st.session_state['auto_retrain'] = auto_retrain
        st.session_state['retrain_schedule'] = schedule
        st.session_state['retrain_test_size'] = int(test_size)
        st.session_state['min_r2'] = float(min_r2)
        st.session_state['max_mae'] = int(max_mae)
        st.success("✓ Model settings saved and prefilled on the Model page.")

# ========== TAB 5: ABOUT (live versions, no invented URLs) ==========

with tab5:
    st.markdown("<h3 style='margin-bottom: 1.5rem;'>About DemandWise</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
        <h2 style="margin: 0 0 0.5rem 0; font-size: 2rem; font-weight: 700; color: {COLORS['primary']};">DemandWise</h2>
        <p style="margin: 0 0 1.5rem 0; color: {COLORS['text_secondary']}; font-size: 1.1rem;">{config['app'].get('tagline', '')}</p>
        <p style="color: {COLORS['text_secondary']}; line-height: 1.6; margin-bottom: 1rem;">
            DemandWise predicts food demand from your own history with leakage-safe features and honest
            prediction intervals — helping kitchens prepare the right amount and waste less.
        </p>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 2rem;">
            <div><div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600; margin-bottom: 0.5rem;">Version</div>
                <div style="font-weight: 600; font-size: 1.1rem;">v{config['app'].get('version', '1.2.0')}</div></div>
            <div><div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600; margin-bottom: 0.5rem;">Edition</div>
                <div style="font-weight: 600; font-size: 1.1rem;">Premium</div></div>
            <div><div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600; margin-bottom: 0.5rem;">Deployment</div>
                <div style="font-weight: 600; font-size: 1.1rem;">Local/Secure</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def _pkg_version(name: str) -> str:
        try:
            return importlib_metadata.version(name)
        except Exception:
            return "not installed"

    st.markdown("<h4>System Information (live)</h4>", unsafe_allow_html=True)
    sys_info = pd.DataFrame({
        'Property': ['Python', 'Streamlit', 'pandas', 'scikit-learn', 'plotly', 'SHAP (optional)', 'Database', 'Config file'],
        'Value': [platform.python_version(), _pkg_version('streamlit'), _pkg_version('pandas'),
                  _pkg_version('scikit-learn'), _pkg_version('plotly'), _pkg_version('shap'),
                  'Local SQLite', 'config.yaml (+ DEMANDWISE_* env overrides)']})
    st.dataframe(sys_info, use_container_width=True, hide_index=True)
    divider()
    st.markdown("<h4>Guides in this repository</h4>", unsafe_allow_html=True)
    doc_col1, doc_col2, doc_col3 = st.columns(3)
    with doc_col1:
        if st.button("📖 User Guide", key="about_user"):
            st.info("See USER_GUIDE.md in the project folder for operator instructions.")
    with doc_col2:
        if st.button("🛠️ Installation Guide", key="about_install"):
            st.info("See INSTALLATION_GUIDE.md in the project folder for clean-install steps.")
    with doc_col3:
        if st.button("📊 Design System", key="about_design"):
            st.info("See DESIGN_SYSTEM.md for the dark premium theme spec.")

divider()
render_footer()
