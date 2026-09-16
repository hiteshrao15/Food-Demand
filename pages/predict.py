"""
DemandWise - Forecast Demand Page
Live workflow: configure parameters, generate leakage-safe predictions
with honest prediction intervals, save to history, and export.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import (
    describe_interval,
    get_database,
    get_model_metadata,
    get_predictor,
    is_sample_mode,
    load_active_dataset,
    render_data_source_banner,
    trained_display,
)
from src.utils.logger import get_logger
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, render_kpi_card, render_data_card, section_header,
    divider, error_state, empty_state, render_footer, render_html,
)

logger = get_logger(__name__)
config = get_config()

st.markdown(get_custom_css(), unsafe_allow_html=True)


def _version() -> int:
    try:
        return int(st.session_state.get("dataset_version", 0))
    except Exception:
        return 0


@st.cache_data(show_spinner=False)
def load_historical_data(_version: int):
    try:
        df, _label, _sample = load_active_dataset()
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}", exc_info=True)
        return None


@st.cache_resource(show_spinner=False)
def load_predictor(_version: int, model_type: str):
    try:
        return get_predictor(model_type)
    except Exception as e:
        logger.error(f"Failed to load predictor: {e}", exc_info=True)
        return None


# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Forecast Food Demand",
    page_icon="🔮",
    subtitle="Configure parameters and generate demand forecasts with honest prediction intervals.",
)
render_data_source_banner()

# Load data
version = _version()
historical_df = load_historical_data(version)
model_options = {
    "Random Forest (Recommended)": "rf",
    "Linear Regression (Fast)": "lr",
    "Deep Learning (Experimental)": "dl",
}
default_model = st.session_state.get('forecast_model_code', st.session_state.get('selected_model', 'rf'))
predictor = load_predictor(version, default_model)
db = get_database()
metadata = get_model_metadata()

# Validation checks
if historical_df is None or historical_df.empty:
    empty_state("📭", "No data available",
                "Upload a CSV in Data Management or activate the labelled sample dataset to enable forecasting.")
    if st.button("📂 Go to Data Management", type="primary"):
        st.session_state.selected_page = "Data"
        st.rerun()
    st.stop()

try:
    historical_df['date'] = pd.to_datetime(historical_df['date'])
except Exception as e:
    logger.error(f"Date parsing failed: {e}", exc_info=True)
    error_state("❌", "Data Error", "Active dataset dates are unreadable. Please re-upload in Data Management.")
    st.stop()

if predictor is None or not predictor.is_ready():
    error_state("⚠", "Model Not Ready",
                "No trained model is loaded (missing or incompatible artifacts in models/). "
                "Historical data below is still available. Train a model on the Model page to enable forecasts.")
    if st.button("⚙️ Open Model Performance", type="primary"):
        st.session_state.selected_page = "Model"
        st.rerun()
    st.stop()

supported_items = predictor.get_supported_items()
dataset_items = sorted(historical_df['food_item'].unique())
unsupported = [i for i in dataset_items if i not in supported_items]
if unsupported:
    st.warning(f"⚠️ {len(unsupported)} item(s) in the active data were not in model training "
               f"({', '.join(unsupported[:4])}{'…' if len(unsupported) > 4 else ''}). "
               "They are excluded from forecasting until you retrain on the Model page.")

forecastable_items = [i for i in dataset_items if i in supported_items]
if not forecastable_items:
    error_state("⚠", "No forecastable items",
                "None of the active dataset's items were seen during training. Retrain on the Model page.")
    if st.button("⚙️ Open Model Performance", type="primary"):
        st.session_state.selected_page = "Model"
        st.rerun()
    st.stop()

# ========== MAIN CONTENT ==========

config_col, preview_col = st.columns([1.2, 1.8], gap="large")

# ========== LEFT: FORECAST CONFIGURATION ==========

with config_col:
    section_header(title="Forecast Configuration", subtitle="Select parameters", icon="⚙️")

    st.markdown(f"""
    <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                border-radius: 12px; padding: 1.5rem;">
    """, unsafe_allow_html=True)

    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Food Item <span style='color:{COLORS['danger']};'>*</span></label>", unsafe_allow_html=True)
    prev_food = st.session_state.get('forecast_food')
    selected_food = st.selectbox("Food Item", options=forecastable_items,
                                 index=forecastable_items.index(prev_food) if prev_food in forecastable_items else 0,
                                 help="Only items seen during training can be forecast (prevents unknown-category errors).",
                                 label_visibility="collapsed", key="forecast_food_select")
    st.session_state['forecast_food'] = selected_food
    st.markdown("")

    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Forecast Start Date <span style='color:{COLORS['danger']};'>*</span></label>", unsafe_allow_html=True)
    historical_max_date = pd.to_datetime(historical_df['date']).max().date()
    min_date = historical_max_date + timedelta(days=1)  # strictly after history: no leakage
    max_horizon_days = int(config['prediction'].get('max_horizon_days', 365))
    max_date = min_date + timedelta(days=max_horizon_days - 1)
    default_date = min(max(datetime.now().date() + timedelta(days=1), min_date), max_date)
    forecast_date = st.date_input("Forecast Date", value=default_date, min_value=min_date, max_value=max_date,
                                  help=f"Must be after the last historical date ({historical_max_date}) and within {max_horizon_days} days. Predictions use only data before this date.",
                                  label_visibility="collapsed", key="forecast_date_input")
    st.caption(f"History ends {historical_max_date} • earliest forecastable date {min_date} • up to {max_date}.")
    st.markdown("")

    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Special Event</label>", unsafe_allow_html=True)
    is_holiday = st.toggle("Mark as holiday or special event", value=False,
                           help="Holidays historically shift demand; the model treats this as the holiday flag.",
                           key="forecast_holiday_toggle")
    st.markdown("")

    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.95rem;'>Safety Buffer</label>", unsafe_allow_html=True)
    default_buffer = int(float(st.session_state.get('safety_buffer_pct', config['prediction'].get('safety_buffer', 10))))
    safety_buffer = st.slider("Safety Buffer %", min_value=0, max_value=30, value=default_buffer, step=1,
                              help="Added to the point forecast to produce the preparation recommendation.",
                              label_visibility="collapsed", key="forecast_buffer_slider")
    st.session_state['safety_buffer_pct'] = float(safety_buffer)
    st.markdown(f"<div style='font-size:.8rem;color:{COLORS['text_muted']};margin-top:.5rem;'>Adds <strong>{safety_buffer}%</strong> to preparation recommendation</div>", unsafe_allow_html=True)
    st.markdown("")

    with st.expander("⚙️ Advanced Options"):
        st.markdown("<div style='font-size:.9rem;color:gray;'>Fine-tune the forecast behaviour.</div>", unsafe_allow_html=True)
        horizon = st.select_slider("Forecast Horizon (days ahead)", options=[1, 3, 7, 14, 30],
                                   value=int(st.session_state.get('forecast_horizon', 1)),
                                   help="Generate a batch forecast for consecutive days starting at the forecast date.",
                                   key="forecast_horizon_slider")
        st.session_state['forecast_horizon'] = int(horizon)
        model_label = st.selectbox("Model Type", list(model_options),
                                   index=next((i for i, c in enumerate(model_options.values()) if c == default_model), 0),
                                   key="forecast_model_label", help="Switching reloads artifacts for that model.")
        new_code = model_options[model_label]
        if new_code != default_model:
            st.session_state.forecast_model_code = new_code
            st.session_state.selected_model = new_code
            st.rerun()

    st.markdown("")
    generate = st.button("🔮 Generate Forecast", use_container_width=True, type="primary", key="generate_forecast_btn")

    st.markdown(f"""
    <div style="background: rgba(30, 136, 229, 0.1); border-left: 3px solid {COLORS['info']};
                padding: 0.75rem; border-radius: 6px; margin-top: 1rem; font-size: 0.8rem; color: {COLORS['text_secondary']};">
        💡 <strong>Tip:</strong> Forecasts are most reliable near history (≤7 days ahead). Intervals express
        uncertainty from backtest residuals — not a guarantee or an accuracy score.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ========== RIGHT: FORECAST RESULT ==========

with preview_col:
    section_header(title="Forecast Result", subtitle="Live model prediction", icon="📊")

    if generate:
        st.session_state['forecast_generated'] = True
        st.session_state['forecast_params'] = {
            'food': selected_food, 'date': str(forecast_date), 'holiday': int(is_holiday),
            'buffer': float(safety_buffer), 'horizon': int(st.session_state.get('forecast_horizon', 1)),
            'model': st.session_state.get('forecast_model_code', default_model),
        }

    if st.session_state.get('forecast_generated', False):
        params = st.session_state.get('forecast_params', {})
        food = params.get('food', selected_food)
        start = pd.to_datetime(params.get('date', str(forecast_date))).date()
        holiday_flag = int(params.get('holiday', int(is_holiday)))
        buffer_pct = float(params.get('buffer', float(safety_buffer)))
        horizon_days = int(params.get('horizon', 1))

        # Enforce date limits even for replayed params (e.g. dataset changed).
        if start < min_date or start > max_date:
            error_state("⚠", "Forecast date out of range",
                        f"Requested {start} is outside [{min_date}, {max_date}] for the current dataset. Adjust the date and regenerate.")
        elif food not in forecastable_items:
            error_state("⚠", "Item not supported",
                        f"'{food}' was not seen during training. Choose a forecastable item or retrain.")
        else:
            dates = [start + timedelta(days=i) for i in range(horizon_days)]
            results, failures = [], []
            with st.spinner(f"Forecasting {food} for {horizon_days} day(s)..."):
                for d in dates:
                    try:
                        res = predictor.predict_with_context(
                            food_item=food, date=str(d), holiday=holiday_flag,
                            historical_df=historical_df, safety_buffer_pct=buffer_pct / 100.0)
                        results.append(res)
                    except ValueError as ve:
                        failures.append(f"{d}: {ve}")
                        logger.warning(f"Forecast validation for {food} on {d}: {ve}")
                    except Exception as e:
                        failures.append(f"{d}: could not be forecast.")
                        logger.error(f"Forecast failed for {food} on {d}: {e}", exc_info=True)
            if failures and not results:
                error_state("⚠", "Forecast failed", " ".join(failures))
            else:
                if failures:
                    st.warning("⚠️ " + " ".join(failures))
                st.session_state['last_forecast_results'] = results
                first, last = results[0], results[-1]

                kpi1, kpi2 = st.columns(2)
                with kpi1:
                    if horizon_days == 1:
                        render_kpi_card("Predicted Demand", f"{first['predicted_demand']:.0f} units",
                                        delta=f"95% interval {first['uncertainty_lower']:.0f}–{first['uncertainty_upper']:.0f}",
                                        delta_type="neutral", icon="📊")
                    else:
                        total = sum(r['predicted_demand'] for r in results)
                        render_kpi_card(f"Total Predicted ({horizon_days}d)", f"{total:,.0f} units",
                                        delta=f"avg {total / horizon_days:,.0f}/day", delta_type="neutral", icon="📊")
                with kpi2:
                    if horizon_days == 1:
                        render_kpi_card("Recommended Prep", f"{first['recommended_prep']} units",
                                        delta=f"+{buffer_pct:.0f}% buffer", delta_type="positive", icon="👨‍🍳")
                    else:
                        total_prep = sum(r['recommended_prep'] for r in results)
                        render_kpi_card(f"Total Prep ({horizon_days}d)", f"{total_prep:,.0f} units",
                                        delta=f"+{buffer_pct:.0f}% buffer", delta_type="positive", icon="👨‍🍳")
                divider()
                st.markdown("<h4 style='margin-bottom: 1rem;'>Forecast Details (live)</h4>", unsafe_allow_html=True)
                interval_txt = describe_interval(first)
                hist_avg = first['historical_item_avg']
                details_html = f"""
                <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                            border-radius: 12px; padding: 1.5rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600;">Prediction Interval</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['primary']}; margin-top: 0.5rem;">{first['uncertainty_lower']:.0f} – {first['uncertainty_upper']:.0f}</div>
                            <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">{interval_txt}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600;">Measured Model Error</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['success']}; margin-top: 0.5rem;">{(f"MAE {metadata['mae']:.1f}" if metadata.get('mae') is not None else "Not measured")}</div>
                            <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">Backtest accuracy ({trained_display(metadata)}) — distinct from the interval above</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600;">Historical Avg (item)</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['text_primary']}; margin-top: 0.5rem;">{hist_avg:.0f} units</div>
                            <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">{first['days_of_history']} days of history before forecast</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8rem; text-transform: uppercase; color: {COLORS['text_muted']}; font-weight: 600;">Same Weekday Avg</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {COLORS['accent_saffron']}; margin-top: 0.5rem;">{first['historical_dow_avg']:.0f} units</div>
                            <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">{first['day_of_week']} • recent 7d avg {first['recent_7day_avg']:.0f}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: {COLORS['text_secondary']}; margin-top: 1rem;">{first['interpretation']}</div>
                </div>
                """
                render_html(details_html)
                divider()

                if horizon_days == 1:
                    st.markdown("<h4 style='margin-bottom: 1rem;'>Demand Range</h4>", unsafe_allow_html=True)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=[first['uncertainty_lower'], first['predicted_demand'], first['uncertainty_upper']],
                        y=['Lower', 'Expected', 'Upper'], mode='markers+text',
                        marker=dict(size=[15, 25, 15], color=[COLORS['warning'], COLORS['accent_saffron'], COLORS['warning']]),
                        text=[f"{first['uncertainty_lower']:.0f}", f"{first['predicted_demand']:.0f} (predicted)", f"{first['uncertainty_upper']:.0f}"],
                        textposition="top center", hovertemplate='%{text} units<extra></extra>', showlegend=False))
                    fig.add_shape(type="line", x0=first['uncertainty_lower'], x1=first['uncertainty_upper'], y0=1, y1=1,
                                  line=dict(color=COLORS['primary'], width=2))
                    fig.update_layout(title="Predicted Demand Range (95% prediction interval)", xaxis_title="Units",
                                      yaxis_showticklabels=False, plot_bgcolor='rgba(0,0,0,0)',
                                      paper_bgcolor=COLORS['surface_dark'],
                                      font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                                      xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                                      margin=dict(l=40, r=20, t=40, b=40), height=220, hovermode='x')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.markdown(f"<h4 style='margin-bottom: 1rem;'>{horizon_days}-Day Forecast</h4>", unsafe_allow_html=True)
                    batch_df = pd.DataFrame([{
                        'Date': r['date'], 'Predicted': r['predicted_demand'],
                        'Lower': r['uncertainty_lower'], 'Upper': r['uncertainty_upper'],
                        'Prep': r['recommended_prep']} for r in results])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(batch_df['Date']) + list(batch_df['Date'][::-1]),
                        y=list(batch_df['Upper']) + list(batch_df['Lower'][::-1]),
                        fill='toself', fillcolor='rgba(30,136,229,0.15)',
                        line=dict(color='rgba(255,255,255,0)'), name='95% interval', hoverinfo='skip'))
                    fig.add_trace(go.Scatter(x=batch_df['Date'], y=batch_df['Predicted'], mode='lines+markers',
                                             name='Predicted', line=dict(color=COLORS['accent_saffron'], width=3),
                                             hovertemplate='%{x}<br>%{y:.0f} units<extra></extra>'))
                    fig.add_trace(go.Scatter(x=batch_df['Date'], y=batch_df['Prep'], mode='lines+markers',
                                             name='Recommended prep', line=dict(color=COLORS['primary'], width=2, dash='dash'),
                                             hovertemplate='%{x}<br>%{y:.0f} units<extra></extra>'))
                    fig.update_layout(xaxis_title="Date", yaxis_title="Units", hovermode='x unified',
                                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                                      font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                                      margin=dict(l=40, r=20, t=30, b=40), height=300)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    st.dataframe(batch_df, use_container_width=True, hide_index=True,
                                 column_config={'Predicted': st.column_config.NumberColumn(format='%d'),
                                                'Lower': st.column_config.NumberColumn(format='%d'),
                                                'Upper': st.column_config.NumberColumn(format='%d'),
                                                'Prep': st.column_config.NumberColumn(format='%d')})
                divider()
                st.markdown("<h4 style='margin-bottom: 1rem;'>Actions</h4>", unsafe_allow_html=True)
                btn1, btn2, btn3 = st.columns(3)
                with btn1:
                    if st.button("💾 Save Forecast", key="save_forecast_btn"):
                        if db is None:
                            st.error("Database unavailable — forecast was not saved.")
                        else:
                            saved, failed = 0, 0
                            for r in results:
                                ok = db.save_prediction(
                                    date=r['date'], food_item=r['food_item'],
                                    predicted_demand=float(r['predicted_demand']),
                                    model_used=str(r.get('model_used', default_model)),
                                    holiday=int(holiday_flag), recommended_prep=int(r['recommended_prep']),
                                    lower_bound=float(r['uncertainty_lower']), upper_bound=float(r['uncertainty_upper']),
                                    safety_buffer_pct=float(buffer_pct))
                                saved, failed = (saved + 1, failed) if ok else (saved, failed + 1)
                            if saved and not failed:
                                st.success(f"✓ Saved {saved} forecast(s) to History.")
                            elif saved:
                                st.warning(f"Saved {saved}; {failed} failed to save.")
                            else:
                                st.error("Could not save forecasts. Please try again.")
                with btn2:
                    if st.button("🎯 Explain This", key="explain_forecast_btn"):
                        st.session_state['explain_food'] = food
                        st.session_state['explain_date'] = str(dates[0])
                        st.session_state['explain_holiday'] = holiday_flag
                        st.session_state.selected_page = "Explain"
                        st.rerun()
                with btn3:
                    export_df = pd.DataFrame([{
                        'food_item': r['food_item'], 'forecast_date': r['date'],
                        'predicted_demand': r['predicted_demand'], 'lower_bound': r['uncertainty_lower'],
                        'upper_bound': r['uncertainty_upper'], 'recommended_prep': r['recommended_prep'],
                        'model': r.get('model_used', ''), 'holiday': holiday_flag,
                        'interval_method': r.get('uncertainty_method', '')} for r in results])
                    st.download_button("📥 Export CSV", data=export_df.to_csv(index=False),
                                       file_name=f"forecast_{food}_{start}.csv", mime="text/csv",
                                       key="export_forecast_btn")
    else:
        empty_state("🔮", "No Forecast Yet",
                    f"Configure parameters on the left and click 'Generate Forecast' to predict {forecastable_items[0] if forecastable_items else 'demand'} with honest intervals.")

# ========== RELATED INFORMATION ==========

divider()
st.markdown("<h3 style='margin-bottom: 1rem;'>How Forecasts Work</h3>", unsafe_allow_html=True)
info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    render_data_card("Historical Data",
                     "Lag (7/30-day) and rolling features are built only from data before the forecast date — the model never sees the future.",
                     icon="📚")
with info_col2:
    render_data_card("ML Algorithm",
                     f"Active model: {metadata.get('best_model_name', default_model.upper())}. Backtest MAE "
                     f"{metadata.get('mae', '—')} / R² {metadata.get('r2', '—')} measures accuracy on held-out history.",
                     icon="🤖")
with info_col3:
    render_data_card("Prediction Intervals",
                     "Bands are 95% intervals from backtest residuals: the range future demand plausibly falls in. Wider bands mean more uncertainty — not lower accuracy.",
                     icon="📈")
divider()
render_footer()
