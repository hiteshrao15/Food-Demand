"""
DemandWise - Settings Page
Application configuration and information.
"""
import streamlit as st
import json
from pathlib import Path
import sys
import pandas as pd
import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import APP_NAME, APP_TAGLINE, APP_VERSION, DEFAULT_DATASET_PATH, MODELS_DIR, METADATA_PATH
from src.database.db import DatabaseManager
from src.styles.theme import get_custom_css
from src.ui.components import render_header, render_card, render_kpi_card, render_status_badge, render_footer
from src.ui.feedback import show_error_state

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

render_header("Settings", "Configure and manage your DemandWise application.", badge="Admin", icon="⚙️")

# Create tabs
tab_sys, tab_hist, tab_model = st.tabs(["System Info", "Prediction History", "Model Management"])

with tab_sys:
    st.markdown("### Application Information")

    col1, col2 = st.columns(2)

    with col1:
        render_card(
            "Service Status",
            f"**Application Name:** {APP_NAME}<br>**Version:** {APP_VERSION}<br>**Tagline:** {APP_TAGLINE}",
            icon="📱",
            footer=f"System Health: {render_status_badge('active', 'Online')}"
        )

    with col2:
        render_card(
            "File Locations",
            f"**Data File:** <code>{DEFAULT_DATASET_PATH}</code><br>**Models Directory:** <code>{MODELS_DIR}</code>",
            icon="📁",
            footer=f"Permissions: {render_status_badge('success', 'Read/Write')}"
        )

    st.markdown("### Help & Support")
    with st.expander("Frequently Asked Questions"):
        st.markdown("""
        ### How accurate are the predictions?
        Our models typically achieve R² scores above 0.85, meaning they explain 85%+ of demand variance.
        Actual accuracy depends on data quality and how representative your historical data is.

        ### Can I use my own data?
        Yes! Upload your historical sales data in the Data Management section.
        Ensure your data includes date, food item, demand, and holiday columns.

        ### What happens if my predictions seem off?
        - Check if your historical data is accurate
        - Consider retraining with recent data
        - Review the explainability section
        - Account for special events or external factors not in the model

        ### Is my data secure?
        All data is stored locally on your machine. No data is sent to external servers.
        """)

    with st.expander("Keyboard Shortcuts"):
        st.markdown("""
        - **Ctrl + Enter**: Run current cell/section
        - **Ctrl + S**: Save current state
        - **R**: Refresh page (in some browsers)
        """)

with tab_hist:
    st.markdown("### Prediction History")

    db = DatabaseManager()
    history = db.get_prediction_history(limit=1000)

    render_kpi_card("Total Predictions Saved", f"{len(history)}", icon="💾")

    if not history.empty:
        st.markdown("#### Recent Predictions")
        st.dataframe(
            history.head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "prediction_date": st.column_config.TextColumn("Date"),
                "food_item": st.column_config.TextColumn("Food Item"),
                "predicted_demand": st.column_config.NumberColumn("Demand"),
                "model_used": st.column_config.TextColumn("Model"),
                "created_at": st.column_config.DatetimeColumn("Created", format="MMM DD, HH:mm")
            }
        )

        st.divider()
        if st.button("🗑️ Clear Prediction History", type="secondary"):
            if db.clear_prediction_history():
                st.success("✅ History cleared!")
                st.rerun()
            else:
                show_error_state("Database Error", "Failed to clear history from the database.")
    else:
        st.info("No prediction history available.")

with tab_model:
    st.markdown("### Active Model Configuration")

    model_info = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r') as f:
                model_info = json.load(f)
        except Exception:
            pass

    col1, col2, col3 = st.columns(3)

    with col1:
        render_kpi_card("Active Model", model_info.get('best_model_name', 'Random Forest'), icon="🤖")

    with col2:
        render_kpi_card("Version", model_info.get('version_id', 'N/A')[:15] + "...", icon="🏷️")

    with col3:
        render_kpi_card("Training Rows", f"{model_info.get('rows_trained', 0):,}", icon="📊")

    st.markdown("### Model Retraining")

    col1, col2 = st.columns([2, 1])

    with col1:
        render_card(
            "Retraining Strategy",
            """
            ### When to Retrain?
            Consider retraining your models when:
            - You have **new historical data** (past 30+ days)
            - Demand patterns have **changed significantly**
            - You're seeing **increased prediction errors**
            - New menu items have been **introduced**

            ### What happens during retraining?
            1. Load and preprocess new data
            2. Train Linear Regression, Random Forest, and Deep Learning models
            3. Evaluate all models using MAE, RMSE, R²
            4. Select the best-performing model
            5. Save all artifacts for production use
            """,
            icon="🔄",
            color="warning"
        )

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄 Retrain All Models", type="primary", use_container_width=True):
            with st.spinner("Retraining models... This may take several minutes."):
                try:
                    from src.data.loader import DataLoader
                    from src.data.preprocessor import FeatureEngineer
                    from src.ml.retrainer import ModelRetrainer
                    from src.database.db import DatabaseManager

                    # Load and preprocess data
                    if DEFAULT_DATASET_PATH.exists():
                        df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
                    else:
                        df = DataLoader.generate_demo_dataset()
                        df.to_csv(DEFAULT_DATASET_PATH, index=False)

                    df_engineered, label_encoder = FeatureEngineer.create_features(df)
                    scaler = FeatureEngineer.get_scaler()
                    scaler.fit(df_engineered[
                        ["food_item_encoded", "year", "month", "day", "day_of_week", "is_weekend",
                        "quarter", "week_of_year", "holiday", "demand_lag_7", "demand_lag_30",
                        "demand_rolling_mean_7", "demand_rolling_mean_30"]
                    ])

                    # Retrain
                    best_key, best_metrics, all_results = ModelRetrainer.retrain_and_save(
                        df_engineered, label_encoder, scaler
                    )

                    # Log in database
                    db = DatabaseManager()
                    version_id = f"model_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    db.save_model_version(
                        version_id=version_id,
                        best_model=best_key,
                        metrics=best_metrics,
                        rows=len(df_engineered)
                    )

                    st.success(f"✅ Models retrained successfully! Active model: {best_key}")
                    st.rerun()

                except Exception as e:
                    show_error_state("Retraining Failed", str(e))

render_footer()
