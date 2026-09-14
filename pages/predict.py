"""
DemandWise - Demand Prediction Page
Professional interface for predicting food demand with empirical uncertainty.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DEFAULT_DATASET_PATH, APP_NAME
from src.data.loader import DataLoader
from src.ml.predictor import DemandPredictor
from src.database.db import DatabaseManager
from src.utils.logger import get_logger
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import render_header, render_card, render_kpi_card, render_footer
from src.ui.feedback import show_error_state, show_empty_state

logger = get_logger(__name__)

st.set_page_config(
    page_title="Predict Demand — DemandWise",
    page_icon="Predict",
    layout="wide"
)

st.markdown(get_custom_css(), unsafe_allow_html=True)

render_header(
    title="Predict Food Demand",
    subtitle="Select a food item and date to obtain an AI-powered demand forecast with empirical uncertainty.",
    icon="Forecast",
    badge="AI Model"
)

# Data & model loading

@st.cache_data
def load_historical_data():
    try:
        if DEFAULT_DATASET_PATH.exists():
            df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
        else:
            df = DataLoader.generate_demo_dataset()
            df.to_csv(DEFAULT_DATASET_PATH, index=False)
        return df
    except Exception as exc:
        logger.error(f"Failed to load historical data: {exc}")
        return None

@st.cache_resource
def load_predictor():
    try:
        return DemandPredictor(model_type='rf')
    except Exception as exc:
        logger.error(f"Failed to load predictor: {exc}")
        return None

historical_df = load_historical_data()
predictor = load_predictor()
db = DatabaseManager()

# Guard: data unavailable
if historical_df is None:
    show_error_state(
        title="Data Unavailable",
        message="Could not load historical demand data.",
        resolution="Check that the dataset file exists or that demo data can be generated."
    )
    st.stop()

# Guard: model not ready
if predictor is None or not predictor.is_ready():
    show_error_state(
        title="Model Not Ready",
        message="The prediction model has not been trained yet.",
        resolution="Navigate to Training or run train_models.py to train the model before making predictions."
    )
    st.stop()

# Input controls

food_items = sorted(historical_df['food_item'].unique())

st.markdown("#### Configure Prediction")
col_food, col_date, col_holiday = st.columns([2, 2, 1])

with col_food:
    selected_food = st.selectbox(
        "Food Item",
        food_items,
        help="Select the food item to predict demand for"
    )

with col_date:
    prediction_date = st.date_input(
        "Prediction Date",
        value=datetime.now() + timedelta(days=1),
        min_value=datetime.now().date(),
        help="Select the date for which to predict demand"
    )

with col_holiday:
    st.markdown("<br>", unsafe_allow_html=True)
    is_holiday = st.checkbox(
        "Holiday / Special Event",
        value=False,
        help="Check if the date is a holiday or special occasion"
    )

# Safety buffer configuration
with st.expander("Preparation Settings", expanded=False):
    safety_buffer_pct = st.slider(
        "Safety Buffer (%)",
        min_value=0,
        max_value=30,
        value=10,
        step=5,
        help="Percentage of predicted demand to add as safety stock"
    )
    st.caption("This buffer is added to the prediction to generate preparation recommendations.")

st.markdown("<br>", unsafe_allow_html=True)
predict_clicked = st.button("Generate Forecast", use_container_width=True, type="primary")

# Sparkline: recent demand for selected food

def build_sparkline(df: pd.DataFrame, food_item: str) -> go.Figure:
    """Build a compact Plotly sparkline of the last 30 days of demand."""
    item_df = df[df['food_item'] == food_item].copy()
    if 'date' in item_df.columns:
        item_df['date'] = pd.to_datetime(item_df['date'])
        item_df = item_df.sort_values('date').tail(30)
        x_vals = item_df['date']
    else:
        item_df = item_df.tail(30).reset_index(drop=True)
        x_vals = item_df.index

    demand_col = 'demand' if 'demand' in item_df.columns else item_df.select_dtypes('number').columns[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=item_df[demand_col],
        mode='lines',
        fill='tozeroy',
        line=dict(color=COLORS['primary'], width=2),
        fillcolor="rgba(46, 134, 171, 0.12)",
        hovertemplate="Date: %{x|%b %d}<br>Demand: %{y:.0f}<extra></extra>"
    ))
    fig.update_layout(
        height=160,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, showticklabels=True, tickfont=dict(size=10), color=COLORS['text_muted']),
        yaxis=dict(showgrid=True, gridcolor=COLORS['border'], tickfont=dict(size=10), color=COLORS['text_muted']),
        showlegend=False,
    )
    return fig

st.markdown("#### Recent Demand Trend")
spark_col, _ = st.columns([3, 1])
with spark_col:
    try:
        fig_spark = build_sparkline(historical_df, selected_food)
        st.plotly_chart(fig_spark, use_container_width=True, config={"displayModeBar": False})
        st.caption(f"Last 30 demand records for **{selected_food}**")
    except Exception as exc:
        st.caption(f"Sparkline unavailable: {exc}")

st.divider()

# Prediction

if predict_clicked:
    try:
        with st.spinner("Running prediction model..."):
            result = predictor.predict_with_context(
                food_item=selected_food,
                date=prediction_date.strftime("%Y-%m-%d"),
                holiday=1 if is_holiday else 0,
                historical_df=historical_df,
                safety_buffer_pct=safety_buffer_pct / 100.0
            )

        predicted = int(result['predicted_demand'])
        uncertainty_lower = int(result['uncertainty_lower'])
        uncertainty_upper = int(result['uncertainty_upper'])
        uncertainty_method = result.get('uncertainty_method', 'Empirical prediction interval')

        # Auto-save to history
        try:
            saved = db.save_prediction(
                date=prediction_date.strftime("%Y-%m-%d"),
                food_item=selected_food,
                predicted_demand=result['predicted_demand'],
                model_used=result['model_used'],
                holiday=1 if is_holiday else 0,
                recommended_prep=result.get('recommended_prep', 0)
            )
            if not saved:
                st.warning("Forecast generated. (History save issue - check database logs.)")
                logger.warning("Failed to save prediction to history")
        except Exception as db_exc:
            logger.warning(f"Could not save prediction: {db_exc}")

        logger.info(f"Prediction for {selected_food} on {prediction_date}: {predicted} orders")

        # Primary KPI row
        st.markdown("### Prediction Results")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            render_kpi_card(
                label="Predicted Orders",
                value=f"{predicted:,}",
                delta=f"±{uncertainty_upper - uncertainty_lower} range",
                delta_type="neutral",
                icon="Target"
            )

        with kpi2:
            render_kpi_card(
                label="Recommended Prep",
                value=str(result.get('recommended_prep', predicted)),
                delta=f"+{result.get('safety_units', 0)} buffer",
                delta_type="positive",
                icon="Preparation"
            )

        with kpi3:
            weekend_label = "Weekend" if result['is_weekend'] else "Weekday"
            render_kpi_card(
                label="Day Type",
                value=weekend_label,
                delta="Holiday" if result['holiday'] else "Regular",
                delta_type="neutral",
                icon="Calendar"
            )

        with kpi4:
            render_kpi_card(
                label="Model",
                value=result['model_used'].upper(),
                delta="Active",
                delta_type="positive",
                icon="Model"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Uncertainty interval visual with honest labeling
        is_available = "Unavailable" not in uncertainty_method
        interval_title = "Forecast Range" if is_available else "Forecast Range (Estimate Unavailable)"

        ci_content = f"""
        <div style="display:flex; gap:1.5rem; align-items:center; flex-wrap:wrap;">
            <div style="flex:1; min-width:180px;">
                <div style="font-size:0.78rem; font-weight:600; text-transform:uppercase;
                            letter-spacing:0.05em; color:{COLORS['text_secondary']}; margin-bottom:4px;">
                    Lower Estimate
                </div>
                <div style="font-size:1.6rem; font-weight:700; color:{COLORS['warning']};">{uncertainty_lower:,}</div>
                <div style="font-size:0.78rem; color:{COLORS['text_muted']};">orders</div>
            </div>
            <div style="flex:2; text-align:center;">
                <div style="background: linear-gradient(90deg, {COLORS['warning']}, {COLORS['primary']}, {COLORS['success']});
                            height:8px; border-radius:4px; position:relative; margin:0.5rem 0;">
                </div>
                <div style="font-size:2rem; font-weight:800; color:{COLORS['primary_dark']};">{predicted:,}</div>
                <div style="font-size:0.82rem; color:{COLORS['text_secondary']}; margin-top:2px;">point estimate</div>
            </div>
            <div style="flex:1; min-width:180px; text-align:right;">
                <div style="font-size:0.78rem; font-weight:600; text-transform:uppercase;
                            letter-spacing:0.05em; color:{COLORS['text_secondary']}; margin-bottom:4px;">
                    Upper Estimate
                </div>
                <div style="font-size:1.6rem; font-weight:700; color:{COLORS['success']};">{uncertainty_upper:,}</div>
                <div style="font-size:0.78rem; color:{COLORS['text_muted']};">orders</div>
            </div>
        </div>
        <div style="margin-top:1rem; padding:0.6rem; background:#f8fafc; border-radius:6px; font-size:0.82rem; color:{COLORS['text_muted']};">
            <strong>Method:</strong> {uncertainty_method}
        </div>
        """
        render_card(
            title=interval_title,
            content=ci_content,
            icon="Chart",
            color="primary"
        )

        # Historical context row
        st.markdown("#### Historical Benchmarks")
        h1, h2, h3 = st.columns(3)
        dow_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][prediction_date.weekday()]

        with h1:
            render_kpi_card(
                label="All-Time Average",
                value=f"{result['historical_item_avg']:.1f}",
                delta="historical avg",
                delta_type="neutral",
                icon="Average"
            )
        with h2:
            render_kpi_card(
                label=f"{dow_name} Average",
                value=f"{result['historical_dow_avg']:.1f}",
                delta="same day-of-week avg",
                delta_type="neutral",
                icon="Calendar"
            )
        with h3:
            render_kpi_card(
                label="7-Day Recent Avg",
                value=f"{result['recent_7day_avg']:.1f}",
                delta="recent trend",
                delta_type="neutral",
                icon="Trend"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Interpretation card
        render_card(
            title="Why This Prediction?",
            content=result['interpretation'],
            icon="Insight",
            color="info"
        )

        # Prediction detail card
        detail_content = f"""
        <table style="width:100%; border-collapse:collapse; font-size:0.92rem;">
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']}; width:40%;">Food Item</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{result['food_item']}</td>
            </tr>
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']};">Prediction Date</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{result['date']}</td>
            </tr>
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']};">Model Used</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{result['model_used']}</td>
            </tr>
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']};">Weekend</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{'Yes' if result['is_weekend'] else 'No'}</td>
            </tr>
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']};">Holiday</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{'Yes' if result['holiday'] else 'No'}</td>
            </tr>
            <tr>
                <td style="padding:6px 0; color:{COLORS['text_secondary']};">Days of History</td>
                <td style="padding:6px 0; font-weight:600; color:{COLORS['text_primary']};">{result.get('days_of_history', 'N/A')}</td>
            </tr>
        </table>
        """
        render_card(
            title="Prediction Details",
            content=detail_content,
            icon="Details",
            color="secondary"
        )

    except Exception as exc:
        show_error_state(
            title="Prediction Failed",
            message=f"An error occurred while generating the forecast: {exc}",
            resolution="Ensure the model is trained and the selected inputs are valid, then try again."
        )
        logger.error(f"Prediction error: {exc}", exc_info=True)

st.divider()

# How-to and notes cards

info_col, notes_col = st.columns(2)

with info_col:
    render_card(
        title="How to Use",
        content="""
        <ol style="margin:0; padding-left:1.2rem; line-height:1.9;">
            <li><strong>Select Food Item</strong> - choose the item to forecast</li>
            <li><strong>Pick a Date</strong> - select the target date (today or future)</li>
            <li><strong>Mark Holiday</strong> - tick if the date is a holiday</li>
            <li><strong>Configure Buffer</strong> - adjust preparation safety buffer</li>
            <li><strong>Generate Forecast</strong> - review AI-powered results</li>
            <li><strong>Auto-Saved</strong> - forecasts are stored in prediction history</li>
        </ol>
        """,
        icon="Guide",
        color="primary"
    )

with notes_col:
    render_card(
        title="Important Notes",
        content="""
        <ul style="margin:0; padding-left:1.2rem; line-height:1.9;">
            <li>Predictions are estimates based on historical patterns</li>
            <li>Use the forecast range as a planning guide, not a guarantee</li>
            <li>Actual demand may differ due to local events</li>
            <li>Retrain regularly as new data arrives for better accuracy</li>
            <li>Forecasts use only data available before the target date</li>
        </ul>
        """,
        icon="Notice",
        color="warning"
    )

render_footer()
