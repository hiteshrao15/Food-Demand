"""
DemandWise - Food Demand Prediction Platform
Main Streamlit Application Entry Point

Professional UI for predicting food demand using Machine Learning.
"""
import pandas as pd
from src.config import get_config, APP_NAME, APP_TAGLINE, DEFAULT_DATASET_PATH
import streamlit as st
from pathlib import Path
import logging
from src.data.loader import DataLoader
from src.ml.predictor import DemandPredictor
from src.analytics.engine import AnalyticsEngine
from src.database.db import DatabaseManager
from src.utils.logger import get_logger, setup_logging
from src.ui.components import (
    render_header, render_kpi_card, render_card, render_footer,
    render_status_badge
)
from src.ui.feedback import show_empty_state, show_error_state, show_success_state
from src.styles.theme import get_custom_css

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load configuration
config = get_config()

# Configure Streamlit page
st.set_page_config(
    page_title=config['app']['name'],
    page_icon="📊",
    layout="wide" if config['ui']['wide_mode'] else "centered",
    initial_sidebar_state="expanded" if not config['ui']['sidebar_collapsed'] else "collapsed"
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize session state for data and model management
def initialize_session_state():
    """Initialize session state variables."""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
        st.session_state.df = None
        st.session_state.data_version = None

    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
        st.session_state.predictor = None
        st.session_state.model_version = None

    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False
        st.session_state.db = None

def get_database():
    """Get or initialize database connection."""
    if not st.session_state.db_initialized:
        st.session_state.db = DatabaseManager()
        st.session_state.db_initialized = True
    return st.session_state.db

def get_predictor(model_type=None):
    """Get or initialize demand predictor."""
    if model_type is None:
        model_type = config['models']['default']

    # Reload if model type changed or not loaded
    if (not st.session_state.model_loaded or
        st.session_state.get('model_type') != model_type or
        st.session_state.predictor is None):
        try:
            predictor = DemandPredictor(model_type=model_type)
            if predictor.is_ready():
                st.session_state.predictor = predictor
                st.session_state.model_loaded = True
                st.session_state.model_type = model_type
                st.session_state.model_version = predictor.metadata.get('version_id')
                logger.info(f"Predictor initialized with {model_type} model")
            else:
                st.session_state.model_loaded = False
                st.session_state.predictor = None
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {e}")
            st.session_state.model_loaded = False
            st.session_state.predictor = None

    return st.session_state.predictor

def load_data(source_type, uploaded_file=None):
    """Load data based on source type."""
    try:
        if source_type == "demo":
            if DEFAULT_DATASET_PATH.exists():
                df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
            else:
                df = DataLoader.generate_demo_dataset()
                df.to_csv(DEFAULT_DATASET_PATH, index=False)
            st.session_state.data_version = "demo"

        elif source_type == "upload" and uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.session_state.data_version = f"upload_{uploaded_file.name}"

        elif source_type == "template":
            # Create empty template with required columns
            df = pd.DataFrame(columns=['date', 'food_item', 'demand', 'holiday'])
            st.session_state.data_version = "template"

        else:
            return None, "Invalid data source"

        # Validate data
        is_valid, errors = DataLoader.validate_dataframe(df)
        if not is_valid:
            return None, f"Data validation failed: {'; '.join(errors)}"

        st.session_state.df = df
        st.session_state.data_loaded = True
        st.session_state.data_source = source_type

        # Clear model cache when data changes
        st.session_state.model_loaded = False
        st.session_state.predictor = None

        logger.info(f"Data loaded successfully: {len(df)} rows from {source_type}")
        return df, None

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None, f"Failed to load data: {str(e)}"

# Initialize session state
initialize_session_state()

# Sidebar Navigation
with st.sidebar:
    st.markdown(f"## {APP_NAME}")
    st.markdown(f"*{APP_TAGLINE}*")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Dashboard", "Predict Demand", "Analytics", "Explainability", "Model Performance", "Data Management", "Settings"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### System Status")

    # Data status
    if st.session_state.data_loaded:
        render_status_badge("success", f"Data Loaded ({len(st.session_state.df)} rows)")
    else:
        render_status_badge("warning", "No Data Loaded")

    # Model status
    predictor = get_predictor()
    if predictor and predictor.is_ready():
        model_name = predictor.metadata.get('best_model_name', 'Unknown')
        render_status_badge("success", f"Model Ready ({model_name})")
    else:
        render_status_badge("error", "Model Not Trained")

    st.divider()
    st.markdown("### About")
    st.caption("DemandWise helps food service operations predict customer demand and optimize preparation.")

# Main content based on page selection
if page == "Dashboard":
    render_header("Dashboard", "Your operational overview and predictive insights.", badge="Live")

    # Load data if not already loaded
    if not st.session_state.data_loaded:
        with st.spinner("Loading demo data..."):
            df, error = load_data("demo")
            if error:
                show_error_state("Data Load Error", error)
                st.stop()

    df = st.session_state.df

    if df is not None and not df.empty:
        # Calculate KPIs
        kpis = AnalyticsEngine.get_dashboard_kpis(df)

        # Display KPI cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_kpi_card("Total Orders", f"{kpis.get('total_orders', 0):.0f}",
                          delta=f"{kpis.get('trend_percent', 0):.1f}%", icon="📦")
        with col2:
            render_kpi_card("Daily Avg", f"{kpis.get('avg_daily_demand', 0):.1f}", icon="📅")
        with col3:
            render_kpi_card("Unique Items", f"{kpis.get('unique_items', 0)}", icon="🍕")
        with col4:
            render_kpi_card("Top Item", kpis.get('highest_item', 'N/A'), icon="🏆")

        st.divider()

        # Model Status
        col1, col2 = st.columns(2)

        with col1:
            predictor = get_predictor()
            if predictor and predictor.is_ready():
                model_info = predictor.metadata
                render_card(
                    "Active Model",
                    f"**{model_info.get('best_model_name', 'Random Forest')}**<br>"
                    f"MAE: {model_info.get('mae', 0):.2f} orders<br>"
                    f"R²: {model_info.get('r2', 0):.4f}",
                    icon="🤖",
                    color="info"
                )
            else:
                render_card(
                    "Active Model",
                    "Model not trained<br>Please train models first",
                    icon="🤖",
                    color="warning"
                )

        with col2:
            st.subheader("📈 Recent Trend")
            recent_data = df.groupby('date')['demand'].sum().tail(30)
            st.line_chart(recent_data)

        render_footer()
    else:
        show_empty_state(
            "📊",
            "No Data Available",
            "Please upload a dataset or load demo data to start predicting demand.",
            "📥 Load Demo Data",
            "load_demo"
        )
        if st.button("Load Demo Data", key="load_demo_btn"):
            df, error = load_data("demo")
            if error:
                show_error_state("Data Load Error", error)
            else:
                show_success_state("Data Loaded", f"Loaded {len(df)} rows of demo data")
                st.rerun()

elif page == "Predict Demand":
    st.switch_page("pages/predict.py")

elif page == "Analytics":
    st.switch_page("pages/analytics.py")

elif page == "Explainability":
    st.switch_page("pages/explainability.py")

elif page == "Model Performance":
    st.switch_page("pages/model_performance.py")

elif page == "Data Management":
    st.switch_page("pages/data_management.py")

elif page == "Settings":
    st.switch_page("pages/settings.py")

# Footer
st.divider()
st.caption(f"{APP_NAME} v{config['app']['version']} | Built with Streamlit & Machine Learning | © 2026")
