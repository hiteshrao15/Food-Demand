"""
DemandWise - Model Performance Dashboard
Compare and evaluate different ML models.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import MODEL_COMPARISON_PATH, METADATA_PATH, MODELS_DIR
from src.utils.logger import get_logger
from src.styles.theme import get_custom_css, COLORS, get_plotly_theme
from src.ui.components import (
    render_header,
    render_card,
    render_kpi_card,
    render_status_badge,
    render_footer,
)

logger = get_logger(__name__)

st.set_page_config(page_title="Model Performance", page_icon="🤖", layout="wide")

# Apply professional theme
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Page Header ────────────────────────────────────────────────────────────────
render_header(
    title="Model Performance",
    subtitle="Compare and evaluate machine learning models for demand prediction.",
    badge="ML Models",
    icon="🤖",
)

# ── Data Loaders ───────────────────────────────────────────────────────────────
@st.cache_data
def load_comparison_data():
    if MODEL_COMPARISON_PATH.exists():
        df = pd.read_csv(MODEL_COMPARISON_PATH)
        # Normalize column names to standard MAE, MSE, RMSE, R²
        rename_map = {}
        for col in df.columns:
            cl = col.lower()
            if cl == 'mae':
                rename_map[col] = 'MAE'
            elif cl == 'mse':
                rename_map[col] = 'MSE'
            elif cl == 'rmse':
                rename_map[col] = 'RMSE'
            elif cl in ('r2', 'r²', 'r_squared'):
                rename_map[col] = 'R²'
        df = df.rename(columns=rename_map)
        return df
    return pd.DataFrame({
        'Model': ['Linear Regression', 'Random Forest', 'Deep Learning'],
        'MAE':   [10.03, 8.79, 9.97],
        'MSE':   [165.69, 122.32, 166.73],
        'RMSE':  [12.87, 11.06, 12.91],
        'R²':    [0.8763, 0.9088, 0.8757],
    })

@st.cache_data
def load_model_metadata():
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

comparison_df = load_comparison_data()
metadata      = load_model_metadata()
plotly_theme  = get_plotly_theme()

# Derive best model (lowest MAE)
best_model_row = comparison_df.loc[comparison_df['MAE'].idxmin()] if not comparison_df.empty else None
active_model   = metadata.get('best_model_name', best_model_row['Model'] if best_model_row is not None else 'N/A')

# ── KPI Cards ──────────────────────────────────────────────────────────────────
st.markdown("## Performance Overview")

if best_model_row is not None:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        render_kpi_card(
            label="Best Model",
            value=best_model_row['Model'],
            delta="Lowest MAE",
            delta_type="positive",
            icon="🏆",
        )
    with kpi2:
        render_kpi_card(
            label="Best R² Score",
            value=f"{best_model_row['R²']:.4f}",
            delta="Higher is better",
            delta_type="positive",
            icon="📐",
        )
    with kpi3:
        render_kpi_card(
            label="Best RMSE",
            value=f"{best_model_row['RMSE']:.2f}",
            delta="Lower is better",
            delta_type="neutral",
            icon="📉",
        )
    with kpi4:
        train_date = (
            metadata.get('timestamp', 'N/A').split('T')[0]
            if metadata else 'N/A'
        )
        render_kpi_card(
            label="Training Date",
            value=train_date,
            icon="📅",
        )

st.divider()

# ── Metric Comparison Charts ───────────────────────────────────────────────────
st.markdown("## Model Metrics Comparison")

MODEL_COLORS = [COLORS['primary'], COLORS['secondary'], COLORS['success']]

col1, col2 = st.columns(2)

with col1:
    fig_mae = go.Figure(data=[
        go.Bar(
            x=comparison_df['Model'],
            y=comparison_df['MAE'],
            marker=dict(
                color=MODEL_COLORS[:len(comparison_df)],
                line=dict(color='rgba(0,0,0,0.05)', width=1),
            ),
            text=comparison_df['MAE'].round(2),
            textposition='outside',
            textfont=dict(size=12, color=COLORS['text_primary']),
        )
    ])
    fig_mae.update_layout(
        **plotly_theme['layout'],
        title=dict(text="Mean Absolute Error (MAE)", font=dict(size=16)),
        height=380,
        xaxis_title="Model",
        yaxis_title="MAE",
        margin=dict(l=40, r=20, t=60, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_mae, use_container_width=True)

with col2:
    fig_r2 = go.Figure(data=[
        go.Bar(
            x=comparison_df['Model'],
            y=comparison_df['R²'],
            marker=dict(
                color=MODEL_COLORS[:len(comparison_df)],
                line=dict(color='rgba(0,0,0,0.05)', width=1),
            ),
            text=comparison_df['R²'].round(4),
            textposition='outside',
            textfont=dict(size=12, color=COLORS['text_primary']),
        )
    ])
    fig_r2.update_layout(
        **plotly_theme['layout'],
        title=dict(text="R² Score (Higher is Better, max 1.0)", font=dict(size=16)),
        height=380,
        xaxis_title="Model",
        yaxis_title="R²",
        yaxis=dict(range=[0, 1.05], gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_r2, use_container_width=True)

# ── Radar / Spider Chart ────────────────────────────────────────────────────────
st.markdown("## Multi-Metric Radar Comparison")
st.caption(
    "All metrics are normalized to a 0–1 scale. "
    "For error metrics (MAE, MSE, RMSE) higher score = lower error (inverted)."
)

if not comparison_df.empty:
    radar_df = comparison_df.copy()

    # Normalize: error metrics → invert (lower error = higher normalized score)
    for err_col in ['MAE', 'MSE', 'RMSE']:
        col_max = radar_df[err_col].max()
        col_min = radar_df[err_col].min()
        rng = col_max - col_min if col_max != col_min else 1
        radar_df[f'{err_col}_norm'] = 1 - (radar_df[err_col] - col_min) / rng

    # R² → already close to 0-1, just min-max normalize
    r2_max = radar_df['R²'].max()
    r2_min = radar_df['R²'].min()
    r2_rng = r2_max - r2_min if r2_max != r2_min else 1
    radar_df['R2_norm'] = (radar_df['R²'] - r2_min) / r2_rng

    categories = ['MAE Score', 'MSE Score', 'RMSE Score', 'R² Score']

    fig_radar = go.Figure()
    for idx, (_, row) in enumerate(radar_df.iterrows()):
        values = [
            row['MAE_norm'], row['MSE_norm'],
            row['RMSE_norm'], row['R2_norm'],
        ]
        values_closed = values + [values[0]]  # close the polygon

        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories + [categories[0]],
            name=row['Model'],
            fill='toself',
            fillcolor=MODEL_COLORS[idx % len(MODEL_COLORS)] + '33',  # 20% opacity
            line=dict(color=MODEL_COLORS[idx % len(MODEL_COLORS)], width=2),
            marker=dict(color=MODEL_COLORS[idx % len(MODEL_COLORS)], size=6),
        ))

    fig_radar.update_layout(
        **plotly_theme['layout'],
        polar=dict(
            bgcolor=COLORS['background'],
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
                tickfont=dict(size=10, color=COLORS['text_secondary']),
            ),
            angularaxis=dict(
                gridcolor=COLORS['border'],
                linecolor=COLORS['border'],
                tickfont=dict(size=12, color=COLORS['text_primary']),
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        height=450,
        margin=dict(l=80, r=80, t=60, b=80),
        title=dict(text="Model Strengths Across All Metrics (Normalized)", font=dict(size=16)),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# ── Detailed Comparison Table ──────────────────────────────────────────────────
st.markdown("## Detailed Model Comparison")

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Model": st.column_config.TextColumn("Model"),
        "MAE":   st.column_config.NumberColumn("MAE",  format="%.2f",  help="Mean Absolute Error — lower is better"),
        "MSE":   st.column_config.NumberColumn("MSE",  format="%.2f",  help="Mean Squared Error — lower is better"),
        "RMSE":  st.column_config.NumberColumn("RMSE", format="%.2f",  help="Root Mean Squared Error — lower is better"),
        "R²":    st.column_config.NumberColumn("R²",   format="%.4f",  help="R-squared Score — higher is better"),
    },
)

st.divider()

# ── Model Characteristics Tabs ─────────────────────────────────────────────────
st.markdown("## Model Characteristics")

tab1, tab2, tab3 = st.tabs(["Linear Regression", "Random Forest", "Deep Learning"])

MODEL_INFO = {
    "Linear Regression": {
        "icon": "📏",
        "color": "primary",
        "strengths": [
            "Simple and highly interpretable",
            "Fast training and prediction",
            "Works well with linear relationships",
            "Minimal computational requirements",
        ],
        "limitations": [
            "Assumes linear relationships between features",
            "Cannot capture complex non-linear patterns",
            "Sensitive to outliers and collinearity",
        ],
        "df_key": "Linear Regression",
    },
    "Random Forest": {
        "icon": "🌲",
        "color": "success",
        "strengths": [
            "Handles non-linear relationships naturally",
            "Robust to outliers and noisy data",
            "Provides built-in feature importance",
            "Less prone to overfitting than single decision trees",
        ],
        "limitations": [
            "Slower training time vs. linear models",
            "Harder to interpret than linear regression",
            "Larger memory footprint at inference",
        ],
        "df_key": "Random Forest",
    },
    "Deep Learning": {
        "icon": "🧠",
        "color": "secondary",
        "strengths": [
            "Captures complex and hierarchical patterns",
            "Scales well to very large datasets",
            "Can learn rich feature representations automatically",
            "High ceiling for accuracy with sufficient data",
        ],
        "limitations": [
            "Requires substantially larger training datasets",
            "Computationally expensive to train",
            "Black-box nature complicates interpretability",
            "Sensitive to hyperparameter choices",
        ],
        "df_key": "Deep Learning",
    },
}

def _build_list_html(items: list, icon: str) -> str:
    rows = "".join(
        f'<div style="margin-bottom:6px;">'
        f'<span style="margin-right:6px;">{icon}</span>{item}'
        f'</div>'
        for item in items
    )
    return rows

for tab, model_name in zip([tab1, tab2, tab3], MODEL_INFO.keys()):
    info = MODEL_INFO[model_name]
    with tab:
        left, right = st.columns([3, 1])

        with left:
            # Is this the active model?
            is_active = active_model == model_name
            badge_html = render_status_badge("active", "Active Model") if is_active else render_status_badge("info", "Available")
            st.markdown(
                f'<div style="margin-bottom:1rem;">{badge_html}</div>',
                unsafe_allow_html=True,
            )

            strengths_html = _build_list_html(info['strengths'], '✅')
            render_card(
                title="Strengths",
                content=strengths_html,
                icon="💪",
                color=info['color'],
            )

            limits_html = _build_list_html(info['limitations'], '⚠️')
            render_card(
                title="Limitations",
                content=limits_html,
                icon="⚡",
                color="warning",
            )

        with right:
            if not comparison_df.empty:
                model_row = comparison_df[comparison_df['Model'] == info['df_key']]
                if not model_row.empty:
                    st.markdown("**Key Metrics**")
                    st.metric("MAE",  f"{float(model_row['MAE'].iloc[0]):.2f}")
                    st.metric("RMSE", f"{float(model_row['RMSE'].iloc[0]):.2f}")
                    st.metric("R²",   f"{float(model_row['R²'].iloc[0]):.4f}")

st.divider()

# ── Model Training Details ─────────────────────────────────────────────────────
st.markdown("## Model Training Details")

if metadata:
    col1, col2, col3 = st.columns(3)

    with col1:
        active_name = metadata.get('best_model_name', 'Random Forest')
        badge_html  = render_status_badge("active", "Active")
        st.markdown(
            f'<p style="font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.05em;color:{COLORS["text_secondary"]};">Active Model</p>'
            f'<span style="font-size:1.4rem;font-weight:700;color:{COLORS["primary_dark"]};">'
            f'{active_name}</span>&nbsp;&nbsp;{badge_html}',
            unsafe_allow_html=True,
        )

    with col2:
        st.metric("Version ID",    metadata.get('version_id',    'N/A'))

    with col3:
        st.metric("Rows Trained",  metadata.get('rows_trained',  0))

    st.markdown("")  # spacer

    if st.button("Retrain Models", type="secondary"):
        with st.spinner("Training models... This may take a few minutes."):
            try:
                from src.ml.retrainer import ModelRetrainer
                from src.data.preprocessor import FeatureEngineer
                from src.data.loader import DataLoader

                df = DataLoader.load_csv(str(MODELS_DIR.parent / "data" / "food_demand_data.csv"))
                if df is None:
                    df = DataLoader.generate_demo_dataset()

                df_engineered, label_encoder = FeatureEngineer.create_features(df)
                scaler = FeatureEngineer.get_scaler()
                scaler.fit(df_engineered[[
                    "food_item_encoded", "year", "month", "day", "day_of_week",
                    "is_weekend", "quarter", "week_of_year", "holiday",
                    "demand_lag_7", "demand_lag_30",
                    "demand_rolling_mean_7", "demand_rolling_mean_30",
                ]])

                best_key, best_metrics, all_results = ModelRetrainer.retrain_and_save(
                    df_engineered, label_encoder, scaler
                )

                st.success("Models retrained successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Retraining failed: {str(e)}")
                logger.error(f"Retraining error: {e}")
else:
    st.info("No model metadata available. Train models first to see training details here.")

st.divider()

# ── Metric Explainer ───────────────────────────────────────────────────────────
st.markdown("## Understanding Model Metrics")

with st.expander("Learn about evaluation metrics"):
    col_l, col_r = st.columns(2)

    with col_l:
        render_card(
            title="Mean Absolute Error (MAE)",
            content=(
                "The average absolute difference between predicted and actual values.<br><br>"
                "<b>Interpretation:</b> Lower is better &nbsp;|&nbsp; "
                "<b>Range:</b> 0 to ∞<br>"
                "<b>Example:</b> MAE of 8.79 means predictions are off by ~9 orders on average."
            ),
            icon="📏",
            color="primary",
        )
        render_card(
            title="R² Score (Coefficient of Determination)",
            content=(
                "The proportion of variance in the target variable explained by the model.<br><br>"
                "<b>Interpretation:</b> Higher is better &nbsp;|&nbsp; "
                "<b>Range:</b> −∞ to 1.0<br>"
                "<b>Good:</b> &gt; 0.7 &nbsp;|&nbsp; <b>Excellent:</b> &gt; 0.9"
            ),
            icon="📐",
            color="success",
        )

    with col_r:
        render_card(
            title="Root Mean Squared Error (RMSE)",
            content=(
                "The square root of the average squared differences between predictions and actuals.<br><br>"
                "<b>Interpretation:</b> Lower is better &nbsp;|&nbsp; "
                "<b>Range:</b> 0 to ∞<br>"
                "<b>Note:</b> Penalizes large errors more heavily than MAE."
            ),
            icon="📉",
            color="warning",
        )
        render_card(
            title="Mean Squared Error (MSE)",
            content=(
                "The average of the squared differences between predictions and actuals.<br><br>"
                "<b>Interpretation:</b> Lower is better &nbsp;|&nbsp; "
                "<b>Range:</b> 0 to ∞<br>"
                "<b>Note:</b> Useful for comparing models; same units as RMSE²."
            ),
            icon="🔢",
            color="info",
        )

# ── Footer ─────────────────────────────────────────────────────────────────────
render_footer()
