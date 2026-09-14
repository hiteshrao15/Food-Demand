"""
DemandWise - Explainable AI Interface
Understand why predictions are made using SHAP values and feature attribution.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DEFAULT_DATASET_PATH
from src.data.loader import DataLoader
from src.ml.predictor import DemandPredictor
from src.xai.explainer import DemandExplainer
from src.utils.logger import get_logger
from src.styles.theme import get_custom_css, get_plotly_theme, COLORS
from src.ui.components import (
    render_header,
    render_card,
    render_kpi_card,
    render_status_badge,
    render_footer,
)

logger = get_logger(__name__)

# Configure Streamlit page
st.set_page_config(page_title="Explainability", page_icon="💡", layout="wide")

# Inject professional theme CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Page Header
render_header(
    title="Prediction Explainability",
    subtitle="Understand why the model predicts certain demand levels through interpretable feature attribution.",
    badge="XAI",
    icon="💡"
)


# Load data and predictor
@st.cache_data
def load_data():
    if DEFAULT_DATASET_PATH.exists():
        df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
    else:
        df = DataLoader.generate_demo_dataset()
        df.to_csv(DEFAULT_DATASET_PATH, index=False)
    return df


@st.cache_resource
def load_predictor():
    return DemandPredictor(model_type='rf')


df = load_data()
predictor = load_predictor()

if not predictor.is_ready():
    st.error("❌ Model is not ready. Please train models first.")
    st.stop()

# Sidebar Controls & Educational Information
with st.sidebar:
    st.header("🔧 Explanation Settings")

    model_type = st.selectbox(
        "Explainability Method",
        ["SHAP (Recommended)", "Feature Importance"],
        help="Method to explain the prediction"
    )

    st.markdown(
        f"""
        <div style="background-color: {COLORS['surface']}; padding: 0.85rem; border-radius: 8px; border: 1px solid {COLORS['border']}; font-size: 0.85rem; color: {COLORS['text_secondary']}; margin-bottom: 1.5rem;">
            <b>SHAP values</b> show how much each individual factor pushes demand up or down from base expectation.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Collapsible Educational Section in Sidebar
    with st.expander("🎓 About Explainable AI", expanded=False):
        st.markdown("""
        ### What is Explainable AI (XAI)?
        Explainable AI helps you understand how machine learning models make predictions rather than treating them as a black box.

        **Core Pillars:**
        1. **Feature Importance**: Which factors matter most.
        2. **Direction of Influence**: Whether a factor increases or decreases demand.
        3. **Contribution Magnitude**: The exact quantitative contribution of each factor.

        ---

        ### How SHAP Works
        SHAP (*SHapley Additive exPlanations*) is rooted in cooperative game theory:
        - Quantifies individual feature impact against a baseline expectation.
        - Uncovers non-linear interactions reliably and consistently.
        - Provides both positive and negative attributions.

        ---

        ### Value for Food Service
        - **Trust & Transparency**: Audit automated recommendations before kitchen prep.
        - **Actionable Levers**: Focus on drivers you can actively manage.
        - **Demand Drivers**: Identify hidden seasonal and holiday patterns.
        """)

# Main Content - Query Configuration
st.markdown("### 🔍 Live Explanation Demo")
st.markdown("Configure prediction parameters below to inspect model reasoning.")

with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        food_items = sorted(df['food_item'].unique())
        selected_food = st.selectbox(
            "Food Item",
            food_items,
            index=0,
            help="Select a food item for explanation"
        )

    with col2:
        prediction_date = st.date_input(
            "Prediction Date",
            value=pd.Timestamp.now() + pd.Timedelta(days=1),
            help="Select a date for prediction"
        )

    with col3:
        st.markdown("<div style='margin-top: 1.75rem;'></div>", unsafe_allow_html=True)
        is_holiday = st.checkbox(
            "Holiday / Special Event",
            value=False,
            help="Mark if this date is a holiday"
        )

generate_btn = st.button("🧠 Generate Explanation", type="primary", use_container_width=True)

if generate_btn:
    try:
        with st.spinner("Analyzing prediction with model explainer..."):
            # Make prediction and get feature dataframe
            result = predictor.predict_with_context(
                food_item=selected_food,
                date=prediction_date.strftime("%Y-%m-%d"),
                holiday=1 if is_holiday else 0,
                historical_df=df
            )

            feature_df = result['feature_df']

            # Create explainer and generate explanation
            explainer = DemandExplainer(predictor.model, model_type='rf')
            explanation = explainer.explain_prediction(feature_df)

        st.success("✅ Explanation successfully generated.")

        st.divider()

        # Section: High-Level Summary
        st.markdown("### 📊 Prediction Summary & Key Drivers")

        col_left, col_right = st.columns([1.8, 1.2])

        with col_left:
            if explanation['top_positive']:
                pos_items = [
                    f"<div style='margin-bottom: 6px;'><b>{factor['feature']}</b>: "
                    f"<span style='color: {COLORS['success']}; font-weight: 600;'>+{abs(factor['shap_value']):.2f}</span></div>"
                    for factor in explanation['top_positive'][:3]
                ]
                render_card(
                    title="Factors Increasing Demand",
                    content="".join(pos_items),
                    icon="📈",
                    color="success",
                    footer="Top positive contributors pushing prediction upward"
                )

            if explanation['top_negative']:
                neg_items = [
                    f"<div style='margin-bottom: 6px;'><b>{factor['feature']}</b>: "
                    f"<span style='color: {COLORS['danger']}; font-weight: 600;'>-{abs(factor['shap_value']):.2f}</span></div>"
                    for factor in explanation['top_negative'][:3]
                ]
                render_card(
                    title="Factors Decreasing Demand",
                    content="".join(neg_items),
                    icon="📉",
                    color="danger",
                    footer="Top negative dampeners pulling prediction downward"
                )

        with col_right:
            render_kpi_card(
                label="Predicted Demand",
                value=f"{int(result['predicted_demand'])} orders",
                delta=f"{selected_food}",
                delta_type="neutral",
                icon="📦"
            )

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

            render_kpi_card(
                label="Attribution Method",
                value=explanation['method'],
                delta="Random Forest",
                delta_type="neutral",
                icon="🧠"
            )

        st.divider()

        # Section: Feature Contributions Visualizations
        st.markdown("### 📋 Detailed Feature Contributions")

        contributions_df = pd.DataFrame(explanation['contributions'])
        contributions_df['abs_impact'] = contributions_df['impact'].abs()
        top_contribs = contributions_df.sort_values('abs_impact', ascending=False).head(10).copy()

        # Determine signed impacts and bar colors (#06A77D for positive, #C73E1D for negative)
        top_contribs['signed_impact'] = top_contribs.apply(
            lambda r: r['shap_value'] if 'shap_value' in r and pd.notnull(r['shap_value'])
            else (r['impact'] if r['direction'] == 'increase' else -r['impact']),
            axis=1
        )
        top_contribs['color'] = top_contribs['direction'].apply(
            lambda d: COLORS['success'] if d == 'increase' else COLORS['danger']
        )

        # Tabbed visual breakdown
        tab_bar, tab_wf = st.tabs(["📊 Impact Ranking (Bar Chart)", "🌊 Cumulative Impact (Waterfall)"])

        with tab_bar:
            # Horizontal Bar Chart
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=top_contribs['feature'],
                x=top_contribs['signed_impact'],
                orientation='h',
                marker_color=top_contribs['color'],
                text=[f"{v:+.2f}" for v in top_contribs['signed_impact']],
                textposition='auto',
                hovertemplate="<b>%{y}</b><br>Impact: %{x:+.2f} orders<extra></extra>"
            ))

            fig_bar.update_layout(
                title=dict(
                    text="Top 10 Feature Contributions to Prediction",
                    font=dict(family='"Space Grotesk", sans-serif', size=18, color=COLORS['text_primary'])
                ),
                paper_bgcolor=COLORS['surface'],
                plot_bgcolor=COLORS['background'],
                font=dict(family='"Inter", sans-serif', size=12, color=COLORS['text_primary']),
                xaxis=dict(
                    title="Impact on Prediction (Orders)",
                    gridcolor=COLORS['border'],
                    linecolor=COLORS['border'],
                    zeroline=True,
                    zerolinecolor=COLORS['text_muted'],
                    zerolinewidth=1.5
                ),
                yaxis=dict(
                    title="Feature",
                    gridcolor=COLORS['border'],
                    linecolor=COLORS['border'],
                    autorange="reversed"
                ),
                showlegend=False,
                height=480,
                margin=dict(l=60, r=40, t=60, b=50)
            )

            st.plotly_chart(fig_bar, use_container_width=True)

        with tab_wf:
            # Waterfall Chart showing cumulative contribution
            wf_features = top_contribs['feature'].tolist()
            wf_values = top_contribs['signed_impact'].tolist()

            fig_wf = go.Figure(go.Waterfall(
                name="Attribution",
                orientation="v",
                measure=["relative"] * len(wf_features),
                x=wf_features,
                y=wf_values,
                text=[f"{v:+.2f}" for v in wf_values],
                textposition="outside",
                connector={"line": {"color": COLORS['text_muted'], "width": 1.5, "dash": "dot"}},
                increasing={"marker": {"color": COLORS['success']}},
                decreasing={"marker": {"color": COLORS['danger']}}
            ))

            fig_wf.update_layout(
                title=dict(
                    text="Cumulative Feature Contribution Waterfall",
                    font=dict(family='"Space Grotesk", sans-serif', size=18, color=COLORS['text_primary'])
                ),
                paper_bgcolor=COLORS['surface'],
                plot_bgcolor=COLORS['background'],
                font=dict(family='"Inter", sans-serif', size=12, color=COLORS['text_primary']),
                xaxis=dict(
                    title="Features",
                    tickangle=-35,
                    gridcolor=COLORS['border'],
                    linecolor=COLORS['border']
                ),
                yaxis=dict(
                    title="Impact on Demand (Orders)",
                    gridcolor=COLORS['border'],
                    linecolor=COLORS['border'],
                    zeroline=True,
                    zerolinecolor=COLORS['border']
                ),
                height=480,
                margin=dict(l=50, r=30, t=60, b=100)
            )

            st.plotly_chart(fig_wf, use_container_width=True)

        st.divider()

        # Section: Natural Language & Context
        st.markdown("### 📝 Natural Language Explanation")

        explanation_text = explanation.get('summary', 'No summary generated.')
        render_card(
            title="Why This Prediction?",
            content=explanation_text,
            icon="💬",
            color="primary"
        )

        st.markdown("#### 💡 Prediction Context & Key Attributes")
        c1, c2, c3 = st.columns(3)

        with c1:
            render_kpi_card(
                label="Day Type",
                value="Weekend" if result.get('is_weekend') else "Weekday",
                icon="📅"
            )

        with c2:
            render_kpi_card(
                label="Holiday Status",
                value="Yes" if result.get('holiday') else "No",
                delta="Holiday Active" if result.get('holiday') else "Regular Operation",
                delta_type="positive" if result.get('holiday') else "neutral",
                icon="🎉"
            )

        with c3:
            render_kpi_card(
                label="Food Item Type",
                value=str(selected_food),
                icon="🍽️"
            )

        st.divider()

        # Section: Technical Details Expander
        with st.expander("🛠️ Technical Details & Attribution Matrix", expanded=False):
            st.markdown(f"**Attribution Method:** `{explanation['method']}`")
            st.markdown(f"**Base Model Architecture:** `Random Forest Regressor`")
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

            display_cols = ['feature', 'feature_key', 'value', 'shap_value', 'direction', 'impact']
            available_cols = [c for c in display_cols if c in top_contribs.columns]

            st.dataframe(
                top_contribs[available_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "feature": st.column_config.TextColumn("Feature"),
                    "feature_key": st.column_config.TextColumn("Feature Key"),
                    "value": st.column_config.NumberColumn("Input Value", format="%.2f"),
                    "shap_value": st.column_config.NumberColumn("SHAP Value", format="%.4f"),
                    "direction": st.column_config.TextColumn("Direction"),
                    "impact": st.column_config.NumberColumn("Abs Impact", format="%.4f")
                }
            )

    except Exception as e:
        st.error(f"❌ Explanation generation failed: {str(e)}")
        logger.error(f"Explainability error: {e}", exc_info=True)

st.divider()

# Page Footer
render_footer()
