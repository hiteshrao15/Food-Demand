"""
DemandWise - Model Performance Page
Live model health: measured backtest metrics, real model comparison,
working model switching and retraining on the active dataset.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import (
    clear_caches,
    dataset_summary,
    get_database,
    get_model_comparison,
    get_model_metadata,
    load_active_dataset,
    render_data_source_banner,
    trained_display,
)
from src.data.preprocessor import FeatureEngineer
from src.ml.retrainer import ModelRetrainer
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, render_data_card, section_header,
    divider, error_state, render_footer, render_html,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
st.markdown(get_custom_css(), unsafe_allow_html=True)
config = get_config()

# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Model Performance",
    page_icon="⚙️",
    subtitle="Measured accuracy, honest model comparison, and retraining on your active data.",
)
render_data_source_banner()

version = int(st.session_state.get("dataset_version", 0))
metadata = get_model_metadata()
comparison = get_model_comparison()
db = get_database()
active_model_code = st.session_state.get('selected_model', config['models'].get('default', 'rf'))

MODEL_LABELS = {'rf': 'Random Forest', 'lr': 'Linear Regression', 'dl': 'Deep Learning'}
MODEL_BLURBS = {
    'rf': 'Ensemble of decision trees — usually the most robust choice.',
    'lr': 'Fast linear baseline — transparent and quick.',
    'dl': 'Small neural network — experimental; needs ample history.',
}

# ========== ACTIVE MODEL HERO CARD (live) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Active Model (measured)</h3>", unsafe_allow_html=True)

if metadata and metadata.get('mae') is not None:
    hero_name = metadata.get('best_model_name', MODEL_LABELS.get(active_model_code, active_model_code.upper()))
    mae, rmse, r2 = metadata.get('mae', 0), metadata.get('rmse', 0), metadata.get('r2', 0)
    trained_txt = trained_display(metadata)
    rows_txt = f"{metadata.get('rows_trained', '—')} rows"
    hero_html = f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
                border-radius: 14px; padding: 2rem; margin-bottom: 2rem; color: white;
                box-shadow: 0 8px 24px rgba(30, 136, 229, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem; flex-wrap: wrap;">
            <div>
                <div style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.1em;
                           opacity: 0.9; margin-bottom: 0.5rem; font-weight: 600;">Currently Active (backtest-measured)</div>
                <h2 style="margin: 0 0 0.5rem 0; font-size: 2rem; font-weight: 700; color: white;">{hero_name}</h2>
                <p style="margin: 0 0 1rem 0; opacity: 0.95; font-size: 1rem;">{MODEL_BLURBS.get(metadata.get('best_model_key', ''), 'Trained on your active dataset.')}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 1rem; margin-top: 1.5rem;">
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">MAE (backtest)</div><div style="font-size: 1.5rem; font-weight: 700;">{mae:.1f} units</div></div>
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">RMSE (backtest)</div><div style="font-size: 1.5rem; font-weight: 700;">{rmse:.1f} units</div></div>
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">R² (backtest)</div><div style="font-size: 1.5rem; font-weight: 700;">{r2:.3f}</div></div>
                    <div><div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem;">Training</div><div style="font-size: 1.1rem; font-weight: 700;">{trained_txt} • {rows_txt}</div></div>
                </div>
            </div>
            <div style="font-size: 3rem; opacity: 0.9;" aria-hidden="true">🤖</div>
        </div>
    </div>
    """
    render_html(hero_html)
else:
    error_state("⚠", "No measured metrics yet",
                "model_metadata.json is missing or incomplete (e.g. fresh checkout without training). "
                "Retrain below to establish a measured baseline — no invented scores are shown.")
    hero_name = MODEL_LABELS.get(active_model_code, active_model_code)

# ========== METRICS EXPLANATION (live numbers) ==========

divider()
st.markdown("<h3 style='margin-bottom: 1rem;'>Performance Metrics Explained</h3>", unsafe_allow_html=True)
mae_live = f"{metadata.get('mae', '—')}" if metadata else "—"
r2_live = f"{metadata.get('r2', '—')}" if metadata else "—"
metric_col1, metric_col2, metric_col3 = st.columns(3, gap="large")
with metric_col1:
    render_data_card("MAE (Mean Absolute Error)",
                     f"Average miss in units on held-out history. Lower is better. Current backtest: <b>{mae_live}</b>.",
                     icon="📏")
with metric_col2:
    render_data_card("RMSE (Root Mean Square Error)",
                     f"Penalises large misses more. Current backtest: <b>{metadata.get('rmse', '—') if metadata else '—'}</b>.",
                     icon="📊")
with metric_col3:
    render_data_card("R² Score",
                     f"Share of demand variance explained (max 1.0). Current backtest: <b>{r2_live}</b>. This is measured accuracy — different from per-forecast uncertainty intervals.",
                     icon="🎯")
divider()

# ========== MODEL COMPARISON (live CSV) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Model Comparison (measured)</h3>", unsafe_allow_html=True)

if comparison is not None and not comparison.empty and 'MAE' in comparison.columns:
    comp = comparison.copy()
    mae_col = 'MAE' if 'MAE' in comp.columns else 'mae'
    rmse_col = 'RMSE' if 'RMSE' in comp.columns else 'rmse'
    name_col = 'Model' if 'Model' in comp.columns else comp.columns[0]
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Bar(x=comp[name_col], y=comp[mae_col], name='MAE (units)',
                                    marker=dict(color=COLORS['primary']),
                                    hovertemplate='<b>%{x}</b><br>MAE: %{y:.1f} units<extra></extra>'))
    if rmse_col in comp.columns:
        fig_comparison.add_trace(go.Bar(x=comp[name_col], y=comp[rmse_col], name='RMSE (units)',
                                        marker=dict(color=COLORS['accent_saffron']),
                                        hovertemplate='<b>%{x}</b><br>RMSE: %{y:.1f} units<extra></extra>'))
    fig_comparison.update_layout(barmode='group', xaxis_title="Model", yaxis_title="Error (units) — lower is better",
                                 plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                                 font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                                 yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                                 height=350, margin=dict(l=40, r=20, t=20, b=40),
                                 legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'))
    st.plotly_chart(fig_comparison, use_container_width=True, config={'displayModeBar': False})
    st.dataframe(comp, use_container_width=True, hide_index=True)
else:
    st.info("No model comparison table found yet (models/model_comparison.csv). Retrain to generate one from your active data.")

# Model selection cards that actually switch the active model.
st.markdown("<h4 style='margin: 1.5rem 0 1rem 0;'>Use a model</h4>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3, gap="large")
cards = [('rf', '🌲', 'Random Forest', 'Best overall robustness'), ('lr', '⚡', 'Linear Regression', 'Fastest predictions'),
         ('dl', '🧠', 'Deep Learning', 'Experimental')]
for code, emoji, label, blurb in cards:
    with (col1 if code == 'rf' else col2 if code == 'lr' else col3):
        is_active = (active_model_code == code)
        border = f"2px solid {COLORS['primary']}" if is_active else f"1px solid {COLORS['border_dark']}"
        btn_label = "✓ Active" if is_active else f"Use {label}"
        st.markdown(f"""
        <div style="background: {COLORS['surface_dark']}; border: {border};
                    border-radius: 12px; padding: 1.5rem; text-align: center; margin-bottom: 0.75rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;" aria-hidden="true">{emoji}</div>
            <h4 style="margin: 0 0 0.5rem 0; color: {COLORS['text_primary']};">{label}</h4>
            <p style="margin: 0; color: {COLORS['text_secondary']}; font-size: 0.9rem;">{blurb}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(btn_label, key=f"use_model_{code}", use_container_width=True, disabled=is_active):
            st.session_state.selected_model = code
            st.session_state.forecast_model_code = code
            st.success(f"✓ {label} is now the active model for forecasts.")
            st.rerun()

divider()

# ========== RETRAINING SECTION (actually trains) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Model Retraining</h3>", unsafe_allow_html=True)
df, _label, _sample = load_active_dataset()
if df is None or df.empty:
    error_state("📭", "No data to train on", "Activate a dataset in Data Management first.")
else:
    summary = dataset_summary(df)
    trained_txt = trained_display(metadata) if metadata else "never trained in this checkout"
    st.markdown(f"""
    <div style="background: rgba(30, 136, 229, 0.1); border-left: 3px solid {COLORS['info']};
                padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem;">
        <div style="font-weight: 600; color: {COLORS['info']}; margin-bottom: 0.5rem;">💡 {trained_txt} • {summary['records']:,} records • {summary['items']} items</div>
        <p style="margin: 0; color: {COLORS['text_secondary']}; font-size: 0.9rem;">
            Retraining uses a chronological split and fits preprocessing on training data only (no leakage).
            All three models are trained; the lowest-MAE model becomes the measured best. Saved forecasts are kept.
        </p>
    </div>
    """, unsafe_allow_html=True)

    retrain_col1, retrain_col2 = st.columns([2, 1], gap="large")
    with retrain_col1:
        start_retrain = st.button("🔄 Retrain on Active Data", use_container_width=True, type="primary", key="retrain_btn")
    with retrain_col2:
        test_size_pct = st.selectbox("Hold-out size", [10, 20, 30], index=1, help="Share of most-recent history reserved for backtest measurement.",
                                     key="retrain_test_size")

    if start_retrain:
        progress = st.progress(0, text="Engineering time-series-safe features...")
        status = st.empty()
        try:
            status.info("Step 1/3 — engineering features (leakage-safe)...")
            progress.progress(15)
            df_eng, label_encoder = FeatureEngineer.create_features(df)
            scaler = FeatureEngineer.get_scaler()
            status.info("Step 2/3 — training lr / rf / dl with chronological validation (this can take a minute)...")
            progress.progress(40)
            best_key, best_metrics, _all = ModelRetrainer.retrain_and_save(
                df_eng, label_encoder, scaler, test_size=float(test_size_pct) / 100.0)
            progress.progress(85)
            status.info("Step 3/3 — registering version and refreshing caches...")
            if db is not None:
                version_id = pd.Timestamp.now().strftime("model_%Y%m%d_%H%M%S")
                db.save_model_version(version_id=version_id,
                                      best_model=best_metrics.get('model_name', best_key),
                                      metrics=best_metrics, rows=int(len(df_eng)))
            clear_caches()
            progress.progress(100, text="Retraining complete.")
            status.success(f"✓ Retraining complete. Measured best: {best_metrics.get('model_name', best_key)} "
                           f"(MAE {best_metrics.get('mae', 0):.1f}, R² {best_metrics.get('r2', 0):.3f}). Caches refreshed.")
            st.balloons()
        except Exception as e:
            logger.error(f"Retraining failed: {e}", exc_info=True)
            progress.empty()
            status.error("Retraining failed — your previous model and data are untouched. Check logs/app_*.log for details and try again.")

divider()

# ========== TRAINING HISTORY (live DB) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Training History (live)</h3>", unsafe_allow_html=True)
if db is not None:
    try:
        history = db.get_model_history(limit=20)
    except Exception as e:
        logger.error(f"Model history read failed: {e}", exc_info=True)
        history = pd.DataFrame()
    if history is not None and not history.empty:
        show = history.copy()
        if 'is_active' in show.columns:
            show['Status'] = show['is_active'].map(lambda v: '✓ Active' if int(v or 0) == 1 else 'Archived')
            show = show.drop(columns=['is_active'])
        st.dataframe(show, use_container_width=True, hide_index=True,
                     column_config={'MAE': st.column_config.NumberColumn(format='%.1f'),
                                    'RMSE': st.column_config.NumberColumn(format='%.1f'),
                                    'R2': st.column_config.NumberColumn(format='%.3f')})
    else:
        st.info("No training runs recorded in the database yet. Retrain above to create the first entry.")
else:
    st.warning("Database unavailable — training history cannot be shown.")

divider()
render_footer()
