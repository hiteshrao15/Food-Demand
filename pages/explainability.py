"""
DemandWise - Forecast Explanations Page
Honest, live explainability: real attributions from the trained model for a
real forecast — never invented factors (no temperature/promotion claims).
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import (
    describe_interval,
    get_model_metadata,
    get_predictor,
    load_active_dataset,
    render_data_source_banner,
)
from src.xai.explainer import DemandExplainer
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, section_header,
    divider, render_footer, empty_state, render_html,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
st.markdown(get_custom_css(), unsafe_allow_html=True)
config = get_config()

# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Forecast Explanations",
    page_icon="🎯",
    subtitle="See exactly which real inputs drove a forecast — with the method honestly labelled.",
)
render_data_source_banner()


def _version() -> int:
    try:
        return int(st.session_state.get("dataset_version", 0))
    except Exception:
        return 0


@st.cache_data(show_spinner=False)
def _load_data(_version: int):
    try:
        df, _label, _sample = load_active_dataset()
        return df
    except Exception as e:
        logger.error(f"Data load failed: {e}", exc_info=True)
        return None


@st.cache_resource(show_spinner=False)
def _load_predictor(_version: int, model_type: str):
    try:
        return get_predictor(model_type)
    except Exception as e:
        logger.error(f"Predictor load failed: {e}", exc_info=True)
        return None


version = _version()
df = _load_data(version)
model_code = st.session_state.get('forecast_model_code', st.session_state.get('selected_model', 'rf'))
predictor = _load_predictor(version, model_code)
metadata = get_model_metadata()

if df is None or df.empty:
    empty_state("📭", "No data available", "Activate a dataset in Data Management to enable explanations.")
    st.stop()
try:
    df['date'] = pd.to_datetime(df['date'])
except Exception as e:
    logger.error(f"Date parsing failed: {e}", exc_info=True)
    st.error("Active dataset dates are unreadable. Please re-upload in Data Management.")
    st.stop()

if predictor is None or not predictor.is_ready():
    empty_state("⚠", "Model unavailable", "Train or select a model on the Model page to enable explanations.")
    if st.button("⚙️ Open Model Performance", type="primary"):
        st.session_state.selected_page = "Model"
        st.rerun()
    st.stop()

supported = set(predictor.get_supported_items())
items = sorted([i for i in df['food_item'].unique() if i in supported])
if not items:
    st.error("None of the active items were seen during training. Retrain on the Model page.")
    st.stop()

# ========== FORECAST SELECTOR (prefilled from Forecast page when available) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Select a Forecast to Explain</h3>", unsafe_allow_html=True)
max_date = pd.to_datetime(df['date']).max().date()
min_date = max_date + timedelta(days=1)
max_horizon = int(config['prediction'].get('max_horizon_days', 365))
limit_date = min_date + timedelta(days=max_horizon - 1)

col1, col2, col3, col4 = st.columns([1.2, 1, 0.8, 0.8])
with col1:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Food Item</label>", unsafe_allow_html=True)
    prefill_food = st.session_state.get('explain_food')
    selected_item = st.selectbox("Food Item", items, index=items.index(prefill_food) if prefill_food in items else 0,
                                 label_visibility="collapsed", key="explain_food_select")
with col2:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Forecast Date</label>", unsafe_allow_html=True)
    prefill_date = pd.to_datetime(st.session_state.get('explain_date', str(min_date))).date()
    prefill_date = min(max(prefill_date, min_date), limit_date)
    forecast_date = st.date_input("Date", value=prefill_date, min_value=min_date, max_value=limit_date,
                                  label_visibility="collapsed", key="explain_date_input")
with col3:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Holiday</label>", unsafe_allow_html=True)
    holiday_flag = st.toggle("Holiday", value=bool(st.session_state.get('explain_holiday', False)),
                             label_visibility="collapsed", key="explain_holiday_toggle",
                             help="Same holiday flag the forecast uses.")
with col4:
    st.markdown("<div style='height:1.9rem;'></div>", unsafe_allow_html=True)
    load_btn = st.button("📊 Load Explanation", type="primary", use_container_width=True, key="load_explanation_btn")

if load_btn:
    st.session_state['show_explanation'] = True
    st.session_state['explain_food'] = selected_item
    st.session_state['explain_date'] = str(forecast_date)
    st.session_state['explain_holiday'] = int(holiday_flag)

# ========== EXPLANATION VIEW (live) ==========

if st.session_state.get('show_explanation'):
    food = st.session_state.get('explain_food', selected_item)
    fdate = st.session_state.get('explain_date', str(forecast_date))
    hol = int(st.session_state.get('explain_holiday', int(holiday_flag)))
    if food not in items:
        food = items[0]

    try:
        with st.spinner("Computing forecast and attributions..."):
            result = predictor.predict_with_context(food_item=food, date=fdate, holiday=hol,
                                                    historical_df=df,
                                                    safety_buffer_pct=float(st.session_state.get('safety_buffer_pct', 10)) / 100.0)
            explainer = DemandExplainer(predictor.model, predictor.model_type)
            explanation = explainer.explain_prediction(result['feature_df'])
    except ValueError as ve:
        st.error(f"Cannot explain this forecast: {ve}")
        st.stop()
    except Exception as e:
        logger.error(f"Explanation failed: {e}", exc_info=True)
        st.error("Explanation failed unexpectedly. Your data is safe — please try again.")
        st.stop()

    method = explanation.get('method', 'Not Available')
    contributions = explanation.get('contributions', []) or []
    interval_txt = describe_interval(result)

    # Summary hero (real numbers only)
    summary_html = f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
                border-radius: 12px; padding: 2rem; color: white; margin-bottom: 2rem;">
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 2rem;">
            <div>
                <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700;">{food}</h3>
                <p style="margin: 0 0 1.5rem 0; opacity: 0.95; font-size: 1rem;">
                    Forecast for {pd.to_datetime(fdate).strftime('%A, %B %d, %Y')}{" • holiday" if hol else ""}
                    ({result['day_of_week']}) • {result['days_of_history']} days of history used</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.25rem;">Predicted Demand</div>
                        <div style="font-size: 2rem; font-weight: 700;">{result['predicted_demand']:.0f} units</div></div>
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.25rem;">95% Interval</div>
                        <div style="font-size: 1.4rem; font-weight: 700;">{result['uncertainty_lower']:.0f}–{result['uncertainty_upper']:.0f}</div></div>
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.25rem;">Recommended Prep</div>
                        <div style="font-size: 2rem; font-weight: 700;">{result['recommended_prep']} units</div></div>
                </div>
            </div>
            <div style="text-align: right;"><div style="font-size: 2.5rem; opacity: 0.9;" aria-hidden="true">✨</div>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">Method: {method}</p></div>
        </div>
    </div>
    """
    render_html(summary_html)
    st.caption(interval_txt + " The method label above tells you exactly how attributions were computed.")
    if "Approximation" in method:
        st.info("ℹ️ SHAP is not installed, so attributions below are a **feature-importance approximation** "
                "(global importance × feature value), not true SHAP values. Install the optional `shap` package for exact attributions.")

    if not contributions:
        empty_state("🔍", "No attributions available",
                    "This model type does not expose feature importance. Explanations need a tree/linear model or SHAP.")
        st.stop()

    divider()
    st.markdown("<h3 style='margin-bottom: 1rem;'>What Drives This Forecast? (live attributions)</h3>", unsafe_allow_html=True)
    driver_col1, driver_col2 = st.columns(2, gap="large")
    with driver_col1:
        st.markdown(f"<h4 style='color: {COLORS['success']}; margin-bottom: 1rem;'>▲ Pushing prediction up</h4>", unsafe_allow_html=True)
        ups = [c for c in contributions if c.get('direction') == 'increase'][:4]
        if not ups:
            st.caption("No upward drivers for this forecast.")
        for c in ups:
            val = c.get('shap_value', c.get('approx_contrib', c.get('impact', 0)))
            st.markdown(f"""
            <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                        border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                    <div><div style="font-size: 0.9rem; color: {COLORS['text_primary']}; font-weight: 600;">{c['feature']}</div>
                    <div style="font-size: 0.8rem; color: {COLORS['text_secondary']};">value {c.get('feature_value', 0):.2f}</div></div>
                    <div style="font-weight: 700; color: {COLORS['success']}; font-size: 0.85rem; white-space: nowrap;">+{abs(float(val)):.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    with driver_col2:
        st.markdown(f"<h4 style='color: {COLORS['warning']}; margin-bottom: 1rem;'>▼ Pulling prediction down</h4>", unsafe_allow_html=True)
        downs = [c for c in contributions if c.get('direction') == 'decrease'][:4]
        if not downs:
            st.caption("No downward drivers for this forecast.")
        for c in downs:
            val = c.get('shap_value', c.get('approx_contrib', c.get('impact', 0)))
            st.markdown(f"""
            <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                        border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                    <div><div style="font-size: 0.9rem; color: {COLORS['text_primary']}; font-weight: 600;">{c['feature']}</div>
                    <div style="font-size: 0.8rem; color: {COLORS['text_secondary']};">value {c.get('feature_value', 0):.2f}</div></div>
                    <div style="font-weight: 700; color: {COLORS['warning']}; font-size: 0.85rem; white-space: nowrap;">−{abs(float(val)):.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    divider()
    st.markdown("<h3 style='margin-bottom: 1rem;'>Attribution Strength</h3>", unsafe_allow_html=True)
    top = contributions[:8]
    fig_importance = go.Figure(data=[go.Bar(
        x=[float(c.get('impact', 0)) for c in top],
        y=[c['feature'] for c in top], orientation='h',
        marker=dict(color=[float(c.get('impact', 0)) for c in top],
                    colorscale=[[0, COLORS['border_dark']], [1, COLORS['accent_saffron']]], showscale=False),
        hovertemplate='<b>%{y}</b><br>Impact: %{x:.2f}<extra></extra>')])
    fig_importance.update_layout(xaxis_title="Attribution magnitude", yaxis_title="",
                                 plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                                 font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                                 xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                                 height=320, margin=dict(l=180, r=20, t=20, b=40))
    st.plotly_chart(fig_importance, use_container_width=True, config={'displayModeBar': False})

    divider()
    st.markdown("<h3 style='margin-bottom: 1rem;'>Explanation in Plain English (from live values)</h3>", unsafe_allow_html=True)
    ups_txt = ", ".join([f"{c['feature']} ({c.get('feature_value', 0):.1f})" for c in (explanation.get('top_positive') or [])[:2]]) or "no single dominant upward input"
    downs_txt = ", ".join([f"{c['feature']} ({c.get('feature_value', 0):.1f})" for c in (explanation.get('top_negative') or [])[:2]]) or "no strong downward input"
    plain = (f"The model predicts <b>{result['predicted_demand']:.0f} units</b> of {food} for "
             f"{pd.to_datetime(fdate).strftime('%A, %B %d')} (95% interval {result['uncertainty_lower']:.0f}–{result['uncertainty_upper']:.0f}). "
             f"Upward pressure comes mainly from: {ups_txt}. Downward pressure comes mainly from: {downs_txt}. "
             f"For context, this item averages {result['historical_item_avg']:.0f} units overall, "
             f"{result['historical_dow_avg']:.0f} on {result['day_of_week']}s, and {result['recent_7day_avg']:.0f} over the last 7 days. "
             f"Attributions were computed with <b>{method}</b>; the interval reflects forecast uncertainty, not model accuracy.")
    st.markdown(f"""<div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 1.5rem; line-height: 1.8;">{plain}</div>""", unsafe_allow_html=True)

    divider()
    st.markdown("<h3 style='margin-bottom: 1rem;'>Prediction Interval</h3>", unsafe_allow_html=True)
    lower, mid, upper = result['uncertainty_lower'], result['predicted_demand'], result['uncertainty_upper']
    fig_interval = go.Figure()
    fig_interval.add_trace(go.Scatter(x=[lower, upper], y=['Range', 'Range'], mode='markers',
                                      marker=dict(size=15, color=[COLORS['warning'], COLORS['warning']]), showlegend=False,
                                      hovertemplate='%{x:.0f} units<extra></extra>'))
    fig_interval.add_trace(go.Scatter(x=[mid], y=['Range'], mode='markers+text',
                                      marker=dict(size=20, color=COLORS['accent_saffron']),
                                      text=[f'{mid:.0f} units (predicted)'], textposition='top center', showlegend=False,
                                      hovertemplate='%{text}<extra></extra>'))
    fig_interval.add_shape(type="line", x0=lower, x1=upper, y0=0, y1=0, line=dict(color=COLORS['primary'], width=3))
    fig_interval.update_layout(title=f"95% Prediction Interval ({lower:.0f} – {upper:.0f} units)",
                               xaxis_title="Units", yaxis_showticklabels=False, plot_bgcolor='rgba(0,0,0,0)',
                               paper_bgcolor=COLORS['surface_dark'],
                               font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                               xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                               height=250, margin=dict(l=40, r=20, t=40, b=40))
    st.plotly_chart(fig_interval, use_container_width=True, config={'displayModeBar': False})

    divider()
    with st.expander("🔬 Technical Details (live)"):
        st.markdown(f"**Method:** {method}\n\n{explanation.get('method_description', '')}")
        detail_rows = []
        for c in contributions:
            detail_rows.append({'Feature': c['feature'], 'Value': round(float(c.get('feature_value', 0)), 3),
                                'Effect': c.get('direction', ''), 'Magnitude': round(float(c.get('impact', 0)), 4),
                                'Signed': round(float(c.get('shap_value', c.get('approx_contrib', 0))), 4)})
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
        st.caption(f"Model: {metadata.get('best_model_name', predictor.model_type.upper())} • "
                   f"Features: {len(result.get('features_dict', {}))} • {interval_txt}")
else:
    if st.session_state.get('explain_food'):
        st.info("Parameters carried over from your last forecast — press **Load Explanation** to compute live attributions.")
    empty_state("🔍", "No Forecast Selected",
                "Choose a food item and forecast date above, then click 'Load Explanation' for live, honestly-labelled attributions.")

divider()
render_footer()
