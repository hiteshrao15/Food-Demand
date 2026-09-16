"""
DemandWise - Premium Food Demand Prediction Platform
Main Streamlit Application Entry Point
Professional, responsive dashboard for intelligent food operations.
"""
import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging

# Import application modules
from src.config import get_config, APP_NAME, APP_TAGLINE
from src.analytics.engine import AnalyticsEngine
from src.state import (
    clear_caches,
    dataset_summary,
    get_database,
    get_dataset_source_label,
    get_model_metadata,
    get_predictor,
    init_state_defaults,
    is_sample_mode,
    load_active_dataset,
    render_data_source_banner,
    trained_display,
)
from src.utils.logger import get_logger, setup_logging
from src.ui.components import (
    render_top_bar, render_kpi_card,
    section_header, divider, empty_state, render_footer,
    error_state, render_html,
)
from src.styles.theme import get_custom_css, COLORS
from src.ui.refinements import get_refinement_css

# Setup
setup_logging()
logger = get_logger(__name__)
config = get_config()

# Page Config
st.set_page_config(
    page_title=f"{APP_NAME} — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium theme
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Apply advanced refinements
st.markdown(get_refinement_css(), unsafe_allow_html=True)

# Session State Initialization
def initialize_session():
    """Initialize all session state variables."""
    init_state_defaults()
    defaults = {
        'data_loaded': False,
        'model_loaded': False,
        'db_initialized': False,
        'selected_page': 'Overview',
        'theme': 'dark',
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    if 'selected_model' not in st.session_state:
        st.session_state['selected_model'] = config['models'].get('default', 'rf')


initialize_session()

# ========== SHARED LOADERS (version-keyed so activation invalidates caches) ==========

@st.cache_data(show_spinner=False)
def load_historical_data(_version: int):
    """Load the active dataset (file, uploaded, or explicit sample fallback)."""
    try:
        df, _label, _sample = load_active_dataset()
        return df
    except Exception as e:
        logger.error(f"Data load failed: {e}", exc_info=True)
        return None


@st.cache_resource(show_spinner=False)
def load_predictor(_version: int, model_type: str):
    """Load predictor for the selected model (None when unavailable)."""
    try:
        return get_predictor(model_type)
    except Exception as e:
        logger.error(f"Predictor load failed: {e}", exc_info=True)
    return None


@st.cache_resource(show_spinner=False)
def load_database(_version: int):
    """Initialize database connection (None when unavailable)."""
    try:
        return get_database()
    except Exception as e:
        logger.error(f"Database init failed: {e}", exc_info=True)
    return None


def _dataset_version() -> int:
    try:
        return int(st.session_state.get("dataset_version", 0))
    except Exception:
        return 0


# ========== SIDEBAR NAVIGATION (REFINED) ==========

with st.sidebar:
    # Enhanced CSS for sidebar
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F1419 0%, #1A1F2E 100%);
    }

    /* The app owns navigation; hide Streamlit's generated pages list. */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    .nav-button {
        transition: all 250ms cubic-bezier(0.23, 1, 0.32, 1) !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin-bottom: 6px !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        border: 1px solid transparent !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }

    .nav-button:hover {
        background: rgba(30, 136, 229, 0.15) !important;
        border-color: rgba(30, 136, 229, 0.3) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.1) !important;
    }

    .status-card {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        transition: all 200ms ease;
    }

    .status-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.12);
    }
    </style>
    """, unsafe_allow_html=True)

    # Premium Branding Section
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1rem 1.5rem 1rem;
                background: linear-gradient(135deg, rgba(30, 136, 229, 0.08), rgba(244, 161, 29, 0.05));
                border-radius: 12px; margin-bottom: 2rem; border: 1px solid rgba(30, 136, 229, 0.15);">
        <div style="font-size: 3rem; margin-bottom: 0.75rem;">🍽️</div>
        <h2 style="margin: 0 0 0.5rem 0; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px;
                   background: linear-gradient(135deg, #42A5F5 0%, #F4A11D 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
            DemandWise
        </h2>
        <p style="margin: 0; font-size: 0.85rem; color: #B3BAC2; font-weight: 500; letter-spacing: 0.5px;">
            INTELLIGENT OPERATIONS
        </p>
        <div style="margin-top: 0.75rem; font-size: 0.75rem; color: #6B7280;">
            Predict • Optimize • Reduce Waste
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Navigation Section
    st.markdown("""
    <div style="padding-bottom: 0.5rem; margin-bottom: 1.5rem;">
        <div style="font-size: 0.7rem; text-transform: uppercase; color: #6B7280; font-weight: 700;
                    letter-spacing: 1px; margin-bottom: 1rem; padding: 0 8px;">
            📍 Navigation
        </div>
    """, unsafe_allow_html=True)

    nav_options = [
        ("📊", "Overview", "Dashboard"),
        ("🔮", "Forecast", "Demand Prediction"),
        ("📈", "Analytics", "Explore Trends"),
        ("📂", "Data", "Data Management"),
        ("⚙️", "Model", "Model Performance"),
        ("🎯", "Explain", "Explainability"),
        ("📋", "History", "Past Forecasts"),
        ("⚙️", "Settings", "Preferences"),
    ]

    for icon, page, _label in nav_options:
        col1, col2 = st.columns([0.5, 3.5])
        with col1:
            st.markdown(f"<div style='font-size: 1.3rem; line-height: 1;' aria-hidden='true'>{icon}</div>", unsafe_allow_html=True)
        with col2:
            if st.button(page, key=f"nav_{page}", use_container_width=True,
                         help=f"Go to {page}"):
                st.session_state.selected_page = page
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # System Status Section
    st.markdown(f"""
    <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid {COLORS['border_dark']};">
        <div style="font-size: 0.7rem; text-transform: uppercase; color: #6B7280; font-weight: 700;
                    letter-spacing: 1px; margin-bottom: 1rem; padding: 0 8px;">
            ⚡ System Status (live)
        </div>
    """, unsafe_allow_html=True)

    _version = _dataset_version()
    _predictor = load_predictor(_version, st.session_state.get('selected_model', 'rf'))
    model_ready = _predictor is not None and _predictor.is_ready()
    metadata = get_model_metadata()

    # Model Status Card (live values, text + color, never color-only)
    model_color = COLORS['success'] if model_ready else COLORS['warning']
    model_bg = "rgba(16, 185, 129, 0.08)" if model_ready else "rgba(245, 158, 11, 0.08)"
    model_border = "rgba(16, 185, 129, 0.2)" if model_ready else "rgba(245, 158, 11, 0.2)"
    model_text = "✓ Ready" if model_ready else "⚠ Unavailable"
    model_detail = "Unknown model"
    if model_ready:
        model_name = getattr(_predictor, 'model_type', '?').upper()
        trained = trained_display(metadata)
        model_detail = f"{model_name} • {trained}"

    st.markdown(f"""
    <div class="status-card" style="background: {model_bg}; border-color: {model_border};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; color: #6B7280; font-weight: 600; margin-bottom: 0.25rem;">
                    Model
                </div>
                <div style="font-weight: 600; color: {model_color}; font-size: 0.9rem;">
                    {model_text}
                </div>
            </div>
            <div style="font-size: 1.2rem;" aria-hidden="true">🤖</div>
        </div>
        <div style="font-size: 0.75rem; color: #B3BAC2; margin-top: 0.5rem;">
            {model_detail}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Data Status Card (live values)
    _df = load_historical_data(_version)
    data_ready = _df is not None and not _df.empty
    data_color = COLORS['success'] if data_ready else COLORS['warning']
    data_bg = "rgba(16, 185, 129, 0.08)" if data_ready else "rgba(245, 158, 11, 0.08)"
    data_border = "rgba(16, 185, 129, 0.2)" if data_ready else "rgba(245, 158, 11, 0.2)"
    if data_ready:
        summary = dataset_summary(_df)
        data_detail = f"{summary['records']:,} records • {summary['items']} items"
        if is_sample_mode():
            data_detail += " • sample"
    else:
        data_detail = 'No data'

    st.markdown(f"""
    <div class="status-card" style="background: {data_bg}; border-color: {data_border};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; color: #6B7280; font-weight: 600; margin-bottom: 0.25rem;">
                    Data
                </div>
                <div style="font-weight: 600; color: {data_color}; font-size: 0.9rem;">
                    {'✓ Loaded' if data_ready else '⚠ No data'}
                </div>
            </div>
            <div style="font-size: 1.2rem;" aria-hidden="true">📊</div>
        </div>
        <div style="font-size: 0.75rem; color: #B3BAC2; margin-top: 0.5rem;">
            {data_detail}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    </div>
    <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid {COLORS['border_dark']};
                text-align: center;">
        <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600; margin-bottom: 0.5rem;">
            DemandWise v{config['app'].get('version', '1.2.0')}
        </div>
        <div style="font-size: 0.7rem; color: #3D4556; letter-spacing: 0.5px;">
            Premium Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

# ========== MAIN CONTENT AREA ==========

def _recent_window_stats(df: pd.DataFrame, days: int = 30):
    """Compute current vs previous window totals for honest KPI deltas."""
    dates = pd.to_datetime(df['date'])
    max_date = dates.max()
    cur_mask = dates >= (max_date - pd.Timedelta(days=days - 1))
    prev_mask = (dates < (max_date - pd.Timedelta(days=days - 1))) & (
        dates >= (max_date - pd.Timedelta(days=2 * days - 1)))
    cur_total = float(df.loc[cur_mask, 'demand'].sum())
    prev_total = float(df.loc[prev_mask, 'demand'].sum())
    delta_pct = ((cur_total - prev_total) / prev_total * 100) if prev_total > 0 else 0.0
    # Per-item totals in the current window for the ranking table.
    cur_items = df.loc[cur_mask].groupby('food_item')['demand'].sum().sort_values(ascending=False)
    avg_daily = cur_total / days if days else 0.0
    return {
        'max_date': max_date, 'cur_total': cur_total, 'prev_total': prev_total,
        'delta_pct': delta_pct, 'cur_items': cur_items, 'avg_daily': avg_daily,
    }


def _weekend_uplift(df: pd.DataFrame) -> float:
    """Weekend vs weekday average demand uplift in percent (real data)."""
    try:
        work = df.copy()
        work['dow'] = pd.to_datetime(work['date']).dt.dayofweek
        weekend = work[work['dow'] >= 5]['demand'].mean()
        weekday = work[work['dow'] < 5]['demand'].mean()
        if weekday and weekday > 0:
            return float((weekend - weekday) / weekday * 100)
    except Exception as e:
        logger.warning(f"Weekend uplift calc failed: {e}")
    return 0.0


def _holiday_uplift(df: pd.DataFrame) -> float:
    """Holiday vs regular-day average demand uplift in percent (real data)."""
    try:
        if 'holiday' not in df.columns:
            return 0.0
        hol = df[df['holiday'] == 1]['demand'].mean()
        reg = df[df['holiday'] == 0]['demand'].mean()
        if reg and reg > 0 and pd.notna(hol):
            return float((hol - reg) / reg * 100)
    except Exception as e:
        logger.warning(f"Holiday uplift calc failed: {e}")
    return 0.0


def _build_prep_plan(df: pd.DataFrame, predictor, safety_pct: float):
    """Predict next-day demand per item with real intervals (no leakage)."""
    max_date = pd.to_datetime(df['date']).max()
    next_date = (max_date + pd.Timedelta(days=1)).date()
    rows = []
    for item in sorted(df['food_item'].unique()):
        try:
            result = predictor.predict_with_context(
                food_item=item,
                date=str(next_date),
                holiday=0,
                historical_df=df,
                safety_buffer_pct=safety_pct / 100.0,
            )
            width = result['uncertainty_upper'] - result['uncertainty_lower']
            rel_width = (width / result['predicted_demand'] * 100) if result['predicted_demand'] > 0 else 0
            status = "✓ Ready" if rel_width <= 60 else "⚠ Wide interval"
            rows.append({
                'Food Item': item,
                'Predicted': result['predicted_demand'],
                'Recommended': result['recommended_prep'],
                'Interval': f"{result['uncertainty_lower']:.0f}–{result['uncertainty_upper']:.0f}",
                'Status': status,
            })
        except Exception as e:
            logger.warning(f"Prep-plan prediction failed for {item}: {e}")
            rows.append({
                'Food Item': item, 'Predicted': None, 'Recommended': None,
                'Interval': 'Unavailable', 'Status': '⚠ No prediction',
            })
    plan_df = pd.DataFrame(rows)
    return next_date, plan_df


def render_overview_dashboard():
    """Render the overview dashboard from live data and model outputs."""

    version = _dataset_version()
    df = load_historical_data(version)
    predictor = load_predictor(version, st.session_state.get('selected_model', 'rf'))
    metadata = get_model_metadata()

    # Header
    org = st.session_state.get('org_name', 'Restaurant Manager')
    current_hour = datetime.now().hour
    greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 18 else "Good evening"

    render_top_bar(
        page_title=f"{greeting}, {org}",
        page_icon="🍽️",
        subtitle=APP_TAGLINE + " Monitor demand, preparation needs, and model health.",
    )
    render_data_source_banner()

    if df is None or df.empty:
        empty_state(
            "📭",
            "No data yet",
            "Upload a CSV in Data Management or activate the labelled sample dataset to see live metrics, trends, and preparation plans.",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📂 Go to Data Management", use_container_width=True, type="primary"):
                st.session_state.selected_page = "Data"
                st.rerun()
        with c2:
            if st.button("📈 Learn how forecasting works", use_container_width=True):
                st.session_state.selected_page = "Forecast"
                st.rerun()
        divider()
        render_footer()
        return

    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        logger.error(f"Date parsing failed on active dataset: {e}", exc_info=True)
        error_state("❌", "Data Error", "The active dataset has unreadable dates. Please re-upload it in Data Management.")
        return

    stats = _recent_window_stats(df, days=30)
    weekend_uplift = _weekend_uplift(df)
    holiday_uplift = _holiday_uplift(df)

    # ========== KPI ROW (all live) ==========
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.5rem;">
        <h3 style="font-size: 1.5rem; font-weight: 700; margin: 0 0 1.5rem 0; letter-spacing: -0.5px;">
            📊 Last 30 Days — Key Metrics (live)
        </h3>
    </div>
    """, unsafe_allow_html=True)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4, gap="large")
    delta_txt = f"{stats['delta_pct']:+.1f}% vs prior 30d"
    delta_type = "positive" if stats['delta_pct'] >= 0 else "negative"

    with kpi_col1:
        render_kpi_card("Total Demand (30d)", f"{stats['cur_total']:,.0f} units",
                        delta=delta_txt, delta_type=delta_type, icon="📦")
    with kpi_col2:
        render_kpi_card("Avg Daily Demand", f"{stats['avg_daily']:,.0f} units",
                        delta=f"{len(df):,} records total", delta_type="neutral", icon="📊")
    with kpi_col3:
        top_name = stats['cur_items'].index[0] if len(stats['cur_items']) else "—"
        top_val = stats['cur_items'].iloc[0] if len(stats['cur_items']) else 0
        render_kpi_card("Top Item (30d)", f"{top_name}",
                        delta=f"{top_val:,.0f} units", delta_type="neutral", icon="🏆")
    with kpi_col4:
        render_kpi_card("Weekend Uplift", f"{weekend_uplift:+.1f}%",
                        delta="weekend vs weekday avg", delta_type="neutral", icon="📅")

    # Quick actions that visibly do what they say.
    act1, act2, act3 = st.columns(3)
    with act1:
        if st.button("🔮 New forecast", use_container_width=True, type="primary"):
            st.session_state.selected_page = "Forecast"
            st.rerun()
    with act2:
        if st.button("📈 Explore analytics", use_container_width=True):
            st.session_state.selected_page = "Analytics"
            st.rerun()
    with act3:
        if st.button("📂 Manage data", use_container_width=True):
            st.session_state.selected_page = "Data"
            st.rerun()

    # ========== CHARTS ROW (live, no invented forecast line) ==========
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 0.5rem;">
        <h3 style="font-size: 1.5rem; font-weight: 700; margin: 0 0 1.5rem 0; letter-spacing: -0.5px;">
            📈 Demand Trends & Insights (live)
        </h3>
    </div>
    """, unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns([2, 1], gap="large")

    with chart_col1:
        st.markdown(f"""
        <div style="background: {COLORS['surface_dark']}; border: 1.5px solid {COLORS['border_dark']};
                    border-radius: 14px; padding: 1.75rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)

        daily = df.groupby(pd.Grouper(key='date', freq='D'))['demand'].sum().reset_index()
        daily = daily.sort_values('date').tail(60)
        daily['rolling_7'] = daily['demand'].rolling(7, min_periods=1).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily['date'], y=daily['demand'], mode='lines+markers', name='Actual daily demand',
            line=dict(color=COLORS['accent_saffron'], width=3), marker=dict(size=6),
            hovertemplate='<b>Actual</b>: %{y:,.0f} units<br>%{x|%Y-%m-%d}<extra></extra>'))
        fig.add_trace(go.Scatter(
            x=daily['date'], y=daily['rolling_7'], mode='lines', name='7-day rolling avg',
            line=dict(color=COLORS['primary'], width=2, dash='dash'),
            hovertemplate='<b>7-day avg</b>: %{y:,.0f} units<br>%{x|%Y-%m-%d}<extra></extra>'))
        fig.update_layout(
            title="Daily Demand — Last 60 Days (actuals + 7-day average)",
            xaxis_title="Date", yaxis_title="Units", hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
            font=dict(family="Inter, sans-serif", color=COLORS['text_primary'], size=11),
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'),
            margin=dict(l=40, r=20, t=40, b=40), height=350)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.caption("Actual historical demand only. Forecasts appear on the Forecast page with honest prediction intervals.")
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown("<h4 style='margin-bottom: 1rem;'>Top Items (last 30 days, live)</h4>", unsafe_allow_html=True)
        if len(stats['cur_items']):
            peak = float(stats['cur_items'].max()) or 1.0
            for item, demand in stats['cur_items'].head(5).items():
                pct = max(4.0, float(demand) / peak * 100)
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                        <span style="color: {COLORS['text_secondary']}; font-weight: 500;">{item}</span>
                        <span style="color: {COLORS['primary']}; font-weight: 600;">{demand:,.0f}</span>
                    </div>
                    <div style="height: 6px; background: {COLORS['border_subtle']}; border-radius: 3px; overflow: hidden;"
                         role="img" aria-label="{item}: {demand:,.0f} units">
                        <div style="height: 100%; background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['accent_saffron']});
                                    width: {pct:.0f}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Not enough recent data for an item ranking yet.")

    # ========== PREPARATION PLAN (live predictions, leakage-safe) ==========
    divider()
    safety_pct = float(st.session_state.get('safety_buffer_pct', config['prediction'].get('safety_buffer', 10)))
    if predictor is None or not predictor.is_ready():
        error_state("⚠", "Model unavailable",
                    "No trained model is loaded, so preparation recommendations cannot be computed. "
                    "Train or select a model on the Model page — historical trends above remain available.")
        if st.button("⚙️ Open Model Performance", type="primary"):
            st.session_state.selected_page = "Model"
            st.rerun()
    else:
        next_date, plan_df = _build_prep_plan(df, predictor, safety_pct)
        st.markdown(f"<h3 style='margin-bottom: 0.25rem;'>Preparation Plan — {next_date} (live forecast)</h3>", unsafe_allow_html=True)
        st.caption(f"Safety buffer {safety_pct:.0f}% • 95% prediction intervals show uncertainty, not accuracy • "
                   f"Model: {metadata.get('best_model_name', predictor.model_type.upper())} • {trained_display(metadata)}")

        prep_col1, prep_col2 = st.columns([3, 1])
        with prep_col1:
            table_rows = []
            for _, row in plan_df.iterrows():
                badge = ('<span class="badge badge-success">✓ Ready</span>'
                         if str(row['Status']).startswith('✓')
                         else '<span class="badge badge-warning">⚠ Wide interval</span>'
                         if 'Wide' in str(row['Status']) else
                         '<span class="badge badge-warning">⚠ Unavailable</span>')
                pred_txt = f"{row['Predicted']:.0f}" if pd.notna(row['Predicted']) else "—"
                rec_txt = f"{row['Recommended']:.0f}" if pd.notna(row['Recommended']) else "—"
                table_rows.append(f"""
                    <tr style="border-bottom: 1px solid {COLORS['border_subtle']};">
                        <td style="padding: 0.75rem;">{row['Food Item']}</td>
                        <td style="text-align: center; padding: 0.75rem; color: {COLORS['accent_saffron']}; font-weight: 600;">{pred_txt}</td>
                        <td style="text-align: center; padding: 0.75rem; color: {COLORS['primary']}; font-weight: 600;">{rec_txt}</td>
                        <td style="text-align: center; padding: 0.75rem; font-size: 0.8rem;">{row['Interval']}</td>
                        <td style="text-align: center; padding: 0.75rem;">{badge}</td>
                    </tr>
                """)
            render_html(f"""
            <div style="background: {COLORS['surface_dark']}; border: 1px solid {COLORS['border_dark']};
                        border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div style="overflow-x: auto;">
                <table style="width: 100%; min-width: 620px; border-collapse: collapse; color: {COLORS['text_primary']}; font-size: 0.9rem;">
                    <tr style="border-bottom: 1px solid {COLORS['border_dark']};">
                        <th style="text-align: left; padding: 0.75rem; color: {COLORS['text_secondary']}; font-weight: 600;">Item</th>
                        <th style="text-align: center; padding: 0.75rem; color: {COLORS['text_secondary']}; font-weight: 600;">Predicted</th>
                        <th style="text-align: center; padding: 0.75rem; color: {COLORS['text_secondary']}; font-weight: 600;">Prep (+buffer)</th>
                        <th style="text-align: center; padding: 0.75rem; color: {COLORS['text_secondary']}; font-weight: 600;">95% Interval</th>
                        <th style="text-align: center; padding: 0.75rem; color: {COLORS['text_secondary']}; font-weight: 600;">Status</th>
                    </tr>
                    {''.join(table_rows)}
                </table>
                </div>
            </div>
            """)
            csv = plan_df.to_csv(index=False)
            st.download_button("📥 Download preparation plan (CSV)", data=csv,
                               file_name=f"prep_plan_{next_date}.csv", mime="text/csv",
                               use_container_width=True)
        with prep_col2:
            st.markdown("<h4 style='margin-bottom: 1rem;'>Quick Stats (live)</h4>", unsafe_allow_html=True)
            total_prep = plan_df['Recommended'].sum() if plan_df['Recommended'].notna().any() else 0
            wide = int((plan_df['Status'] == '⚠ Wide interval').sum())
            ok_txt = "No wide intervals" if wide == 0 else f"{wide} wide interval(s)"
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid {COLORS['success']};
                        padding: 0.75rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: {COLORS['success']}; font-size: 0.85rem;">✓ {ok_txt}</div>
                <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">
                    Intervals wider than ±30% of prediction are flagged
                </div>
            </div>
            <div style="background: rgba(30, 136, 229, 0.1); border-left: 3px solid {COLORS['primary']};
                        padding: 0.75rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: {COLORS['primary']}; font-size: 0.85rem;">{total_prep:,.0f} Units Total</div>
                <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">
                    Recommended preparation for {next_date}
                </div>
            </div>
            <div style="background: rgba(244, 161, 29, 0.1); border-left: 3px solid {COLORS['accent_saffron']};
                        padding: 0.75rem; border-radius: 6px;">
                <div style="font-weight: 600; color: {COLORS['accent_saffron']}; font-size: 0.85rem;">{safety_pct:.0f}% Buffer</div>
                <div style="font-size: 0.75rem; color: {COLORS['text_secondary']}; margin-top: 0.25rem;">
                    Adjust in Forecast or Settings
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ========== OPERATIONAL INSIGHTS (live, no invented claims) ==========
    divider()
    st.markdown("<h3 style='margin-bottom: 1rem;'>Operational Insights (live)</h3>", unsafe_allow_html=True)
    kpis = AnalyticsEngine.get_dashboard_kpis(df)
    insights_col1, insights_col2, insights_col3 = st.columns(3)
    with insights_col1:
        st.markdown(f"""
        <div class="card" style="border-left: 4px solid {COLORS['success']};">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">📈 Demand pattern</h3>
            <div style="color: {COLORS['text_secondary']}; font-size: 0.95rem; line-height: 1.5;">
                Weekends average <b>{weekend_uplift:+.1f}%</b> vs weekdays; holidays average
                <b>{holiday_uplift:+.1f}%</b> vs regular days (computed from the active dataset).
            </div>
        </div>
        """, unsafe_allow_html=True)
    with insights_col2:
        hi_item = kpis.get('highest_item', '—')
        st.markdown(f"""
        <div class="card" style="border-left: 4px solid {COLORS['primary']};">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">📊 Highest-volume item</h3>
            <div style="color: {COLORS['text_secondary']}; font-size: 0.95rem; line-height: 1.5;">
                <b>{hi_item}</b> leads total historical demand. Prioritise its prep line and
                review its interval on high-uplift days.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with insights_col3:
        if metadata and metadata.get('mae') is not None:
            content = (f"Backtest error: <b>MAE {metadata['mae']:.1f}</b> units, "
                       f"<b>R² {metadata.get('r2', 0):.3f}</b> ({metadata.get('best_model_name', 'model')}). "
                       f"{trained_display(metadata)}. Intervals above express uncertainty — not a guarantee.")
        else:
            content = ("No training metrics found yet (missing model_metadata.json). "
                       "Retrain on the Model page to establish a measured baseline.")
        st.markdown(f"""
        <div class="card" style="border-left: 4px solid {COLORS['accent_saffron']};">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">🎯 Model health (measured)</h3>
            <div style="color: {COLORS['text_secondary']}; font-size: 0.95rem; line-height: 1.5;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # History teaser (live count)
    db = load_database(version)
    if db is not None:
        try:
            summary_hist = db.get_history_summary()
            if summary_hist['count'] > 0:
                st.info(f"📋 {summary_hist['count']} forecast(s) saved in History "
                        f"(avg predicted {summary_hist['avg_predicted']:.0f} units across "
                        f"{summary_hist['distinct_items']} items).")
        except Exception as e:
            logger.warning(f"History teaser failed: {e}")

    # Footer
    divider()
    render_footer()


# ========== PAGE ROUTING ==========

def render_selected_page():
    """Render the page selected from the custom DemandWise navigation."""
    if st.session_state.selected_page == "Overview":
        render_overview_dashboard()
        return

    page_files = {
        "Forecast": "predict.py",
        "Analytics": "analytics.py",
        "Data": "data_management.py",
        "Model": "model_performance.py",
        "Explain": "explainability.py",
        "History": "predict_history.py",
        "Settings": "settings.py",
    }
    page_path = Path(__file__).parent / "pages" / page_files[st.session_state.selected_page]
    import runpy
    try:
        runpy.run_path(str(page_path), run_name="__demandwise_page__")
    except Exception as e:
        logger.error(f"Page '{st.session_state.selected_page}' failed: {e}", exc_info=True)
        error_state("⚠", "Page failed to load",
                    "Something went wrong opening this page. Your data is safe — please try again or return to Overview.")
        if st.button("← Back to Overview"):
            st.session_state.selected_page = "Overview"
            st.rerun()


render_selected_page()
