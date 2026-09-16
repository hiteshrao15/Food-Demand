"""
DemandWise - Prediction History Page
Live activity log backed by SQLite: search, filter, sort, detail view,
CSV export, per-row delete and clear-all with confirmation. Excellent
empty state before the first forecast.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import get_database, load_active_dataset, render_data_source_banner
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, section_header, divider, render_footer, empty_state, error_state,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
st.markdown(get_custom_css(), unsafe_allow_html=True)
config = get_config()

# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Prediction History",
    page_icon="📋",
    subtitle="Every saved forecast, filterable and exportable. Stored locally in SQLite.",
)
render_data_source_banner()

db = get_database()
if db is None:
    error_state("⚠", "History unavailable", "The local database could not be opened. Forecasts cannot be listed right now.")
    st.stop()

# Retention housekeeping (configured, best-effort)
try:
    retention = int(get_config()['database'].get('retention_days', 365) or 365)
    if retention > 0:
        db.cleanup_old_predictions(retention_days=retention)
except Exception as e:
    logger.warning(f"Retention cleanup skipped: {e}")

# ========== FILTERS (all functional) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Filters</h3>", unsafe_allow_html=True)
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4, gap="medium")

with filter_col1:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Search</label>", unsafe_allow_html=True)
    search_term = st.text_input("Search by item, model or date", label_visibility="collapsed",
                               placeholder="e.g., Pizza", key="hist_search")
with filter_col2:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Forecast Date Range</label>", unsafe_allow_html=True)
    date_range = st.date_input("Date Range", value=(datetime.now().date() - timedelta(days=90), datetime.now().date() + timedelta(days=90)),
                               label_visibility="collapsed", key="hist_dates")
with filter_col3:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Food Item</label>", unsafe_allow_html=True)
    try:
        db_items = db.get_history_items()
    except Exception as e:
        logger.warning(f"History items read failed: {e}")
        db_items = []
    try:
        df_active, _, _ = load_active_dataset()
        dataset_items = sorted(df_active['food_item'].unique()) if df_active is not None else []
    except Exception:
        dataset_items = []
    options = ["All items"] + sorted(set(db_items) | set(dataset_items))
    selected_item = st.selectbox("Food Items", options, label_visibility="collapsed", key="hist_item")
with filter_col4:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Sort By</label>", unsafe_allow_html=True)
    sort_by = st.selectbox("Sort By", ["Most Recent", "Oldest First", "Forecast Date ↑", "Forecast Date ↓",
                                       "Highest Demand", "Lowest Demand"],
                           label_visibility="collapsed", key="hist_sort")

c1, c2 = st.columns([1, 5])
with c1:
    if st.button("🔄 Reset Filters", key="hist_reset"):
        for key in ('hist_search', 'hist_dates', 'hist_item', 'hist_sort'):
            st.session_state.pop(key, None)
        st.rerun()

divider()

# ========== QUERY (live) ==========

sort_map = {
    'Most Recent': ("created_at", False), 'Oldest First': ("created_at", True),
    'Forecast Date ↑': ("prediction_date", True), 'Forecast Date ↓': ("prediction_date", False),
    'Highest Demand': ("predicted_demand", False), 'Lowest Demand': ("predicted_demand", True),
}
sort_col, ascending = sort_map.get(sort_by, ("created_at", False))
date_from = date_to = None
try:
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        date_from, date_to = str(date_range[0]), str(date_range[1])
except Exception:
    pass

try:
    history_data = db.get_prediction_history(limit=1000, food_item=None if selected_item == "All items" else selected_item,
                                             search=search_term or None, date_from=date_from, date_to=date_to,
                                             sort_by=sort_col, ascending=ascending)
except Exception as e:
    logger.error(f"History query failed: {e}", exc_info=True)
    error_state("⚠", "Could not load history", "The history query failed. Please try again.")
    st.stop()

# ========== SUMMARY (live) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Summary (live)</h3>", unsafe_allow_html=True)
if history_data.empty:
    empty_state("📭", "No forecasts saved yet",
                "Generate your first forecast on the Forecast page and press Save — it will appear here with filters, sorting, and CSV export. Sample data is never shown as history.")
    if st.button("🔮 Go to Forecast", type="primary"):
        st.session_state.selected_page = "Forecast"
        st.rerun()
    divider()
    render_footer()
    st.stop()

stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
with stats_col1:
    st.metric("Total Forecasts", f"{len(history_data):,}")
with stats_col2:
    st.metric("Average Predicted", f"{history_data['predicted_demand'].mean():.0f} units")
with stats_col3:
    interval_w = None
    if 'lower_bound' in history_data.columns and 'upper_bound' in history_data.columns:
        try:
            interval_w = (history_data['upper_bound'] - history_data['lower_bound']).mean()
        except Exception:
            interval_w = None
    st.metric("Avg Interval Width", f"{interval_w:.0f} units" if interval_w is not None and pd.notna(interval_w) else "—",
              help="Mean 95% prediction-interval width: uncertainty, not accuracy.")
with stats_col4:
    st.metric("Items", f"{history_data['food_item'].nunique()}")

divider()

# ========== HISTORY TABLE (responsive, no clipping) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Forecast History</h3>", unsafe_allow_html=True)
display_df = history_data.copy()
for col in ('created_at', 'prediction_date'):
    if col in display_df.columns:
        try:
            display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d %H:%M' if col == 'created_at' else '%Y-%m-%d')
        except Exception:
            pass
cols = [c for c in ['id', 'created_at', 'food_item', 'prediction_date', 'predicted_demand',
                    'lower_bound', 'upper_bound', 'recommended_prep', 'holiday', 'model_used'] if c in display_df.columns]
st.dataframe(display_df[cols], use_container_width=True, hide_index=True,
             column_config={
                 'id': st.column_config.NumberColumn('ID', width='small'),
                 'created_at': st.column_config.TextColumn('Saved At', width='medium'),
                 'food_item': st.column_config.TextColumn('Item', width='medium'),
                 'prediction_date': st.column_config.TextColumn('For Date', width='small'),
                 'predicted_demand': st.column_config.NumberColumn('Predicted', format='%d'),
                 'lower_bound': st.column_config.NumberColumn('Lower', format='%d'),
                 'upper_bound': st.column_config.NumberColumn('Upper', format='%d'),
                 'recommended_prep': st.column_config.NumberColumn('Prep', format='%d'),
                 'holiday': st.column_config.NumberColumn('Holiday', format='%d'),
                 'model_used': st.column_config.TextColumn('Model', width='medium')})

divider()

# ========== DETAIL VIEW ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Forecast Details</h3>", unsafe_allow_html=True)
ids = history_data['id'].tolist() if 'id' in history_data.columns else []
if ids:
    labels = {int(r['id']): f"#{int(r['id'])} • {r['food_item']} • {r['prediction_date']} • {float(r['predicted_demand']):.0f} units"
              for _, r in history_data.iterrows()}
    chosen = st.selectbox("Select a forecast", ids, format_func=lambda i: labels.get(int(i), str(i)), key="hist_detail")
    recent = history_data[history_data['id'] == chosen].iloc[0]
    detail_col1, detail_col2 = st.columns(2, gap="large")
    with detail_col1:
        st.markdown(f"""
        <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                    border-radius: 12px; padding: 1.5rem;">
            <h4 style="margin: 0 0 1rem 0;">Forecast Details</h4>
            <div style="margin-bottom: 1rem;"><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Food Item</div>
                <div style="font-weight: 600;">{recent['food_item']}</div></div>
            <div style="margin-bottom: 1rem;"><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Forecast Date</div>
                <div style="font-weight: 600;">{recent['prediction_date']}</div></div>
            <div style="margin-bottom: 1rem;"><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Saved</div>
                <div style="font-weight: 600;">{recent.get('created_at', '—')}</div></div>
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Model Used</div>
                <div style="font-weight: 600;">{recent.get('model_used', '—')} • holiday={recent.get('holiday', 0)}</div></div>
        </div>
        """, unsafe_allow_html=True)
    with detail_col2:
        lower = recent.get('lower_bound', None)
        upper = recent.get('upper_bound', None)
        interval_line = f"{float(lower):.0f} – {float(upper):.0f}" if pd.notna(lower) and pd.notna(upper) else "Not stored (older entry)"
        st.markdown(f"""
        <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                    border-radius: 12px; padding: 1.5rem;">
            <h4 style="margin: 0 0 1rem 0;">Predictions</h4>
            <div style="margin-bottom: 1rem;"><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Predicted Demand</div>
                <div style="font-size: 1.75rem; font-weight: 700; color: {COLORS['primary']};">{float(recent['predicted_demand']):.0f} units</div></div>
            <div style="margin-bottom: 1rem;"><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">Recommended Prep</div>
                <div style="font-size: 1.75rem; font-weight: 700; color: {COLORS['accent_saffron']};">{float(recent.get('recommended_prep', 0) or 0):.0f} units</div></div>
            <div><div style="font-size: 0.8rem; color: {COLORS['text_muted']};">95% Interval (uncertainty)</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: {COLORS['success']};">{interval_line}</div></div>
        </div>
        """, unsafe_allow_html=True)
    divider()
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("🎯 Explain Similar", key="hist_explain"):
            st.session_state['explain_food'] = recent['food_item']
            st.session_state['explain_date'] = str(recent['prediction_date'])
            st.session_state['explain_holiday'] = int(recent.get('holiday', 0) or 0)
            st.session_state.selected_page = "Explain"
            st.rerun()
    with action_col2:
        if st.button("🔮 Re-forecast", key="hist_reforecast"):
            st.session_state['forecast_food'] = recent['food_item']
            st.session_state.selected_page = "Forecast"
            st.rerun()
    with action_col3:
        if st.button("🗑️ Delete This", key="hist_delete"):
            st.session_state['confirm_delete_id'] = int(chosen)
    if st.session_state.get('confirm_delete_id') == int(chosen):
        st.warning(f"Delete forecast #{chosen}? This cannot be undone.")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Yes, delete", key="hist_delete_yes", type="primary"):
                if db.delete_prediction(int(chosen)):
                    st.success("✓ Forecast deleted.")
                    st.session_state.pop('confirm_delete_id', None)
                    st.rerun()
                else:
                    st.error("Could not delete this forecast.")
        with d2:
            if st.button("Cancel", key="hist_delete_no"):
                st.session_state.pop('confirm_delete_id', None)
                st.rerun()

divider()

# ========== EXPORT + CLEAR (both do what they say) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Export & Manage</h3>", unsafe_allow_html=True)
export_col1, export_col2 = st.columns(2)
with export_col1:
    st.download_button("📥 Export Filtered History (CSV)", data=history_data.to_csv(index=False),
                       file_name=f"forecast_history_{datetime.now().strftime('%Y%m%d')}.csv",
                       mime="text/csv", use_container_width=True, key="hist_export")
    st.caption(f"Exports the {len(history_data)} filtered row(s) above.")
with export_col2:
    if st.button("🗑️ Clear All History", use_container_width=True, key="hist_clear"):
        st.session_state['confirm_clear_all'] = True
    if st.session_state.get('confirm_clear_all'):
        st.warning("Clear ALL saved forecasts? This cannot be undone.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Yes, clear all", type="primary", key="hist_clear_yes"):
                if db.clear_prediction_history():
                    st.success("✓ History cleared.")
                    st.session_state.pop('confirm_clear_all', None)
                    st.rerun()
                else:
                    st.error("Could not clear history.")
        with cc2:
            if st.button("Cancel", key="hist_clear_no"):
                st.session_state.pop('confirm_clear_all', None)
                st.rerun()

divider()
render_footer()
