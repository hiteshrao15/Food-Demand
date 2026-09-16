"""
DemandWise - Analytics Page
Live exploration of the active dataset: trends, rankings, calendar
patterns and honest exports. All numbers come from real loaded rows.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import load_active_dataset, render_data_source_banner
from src.styles.theme import get_custom_css, COLORS
from src.ui.components import (
    render_top_bar, render_kpi_card, section_header,
    divider, error_state, empty_state, render_footer,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)
st.markdown(get_custom_css(), unsafe_allow_html=True)
config = get_config()

# ========== DATA LOADER (version-keyed) ==========

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
        logger.error(f"Analytics data load failed: {e}", exc_info=True)
        return None


# ========== PAGE HEADER ==========

render_top_bar(
    page_title="Demand Analytics",
    page_icon="📈",
    subtitle="Live trends and patterns from your active dataset — no demo numbers.",
)
render_data_source_banner()

df = load_historical_data(_version())

if df is None or df.empty:
    empty_state("📭", "No data to analyse",
                "Upload a CSV in Data Management or activate the labelled sample dataset.")
    if st.button("📂 Go to Data Management", type="primary"):
        st.session_state.selected_page = "Data"
        st.rerun()
    st.stop()

try:
    df['date'] = pd.to_datetime(df['date'])
except Exception as e:
    logger.error(f"Date parsing failed: {e}", exc_info=True)
    error_state("❌", "Data Error", "Active dataset dates are unreadable. Please re-upload in Data Management.")
    st.stop()

df['weekday'] = df['date'].dt.day_name()
df['month'] = df['date'].dt.month

# ========== FILTER BAR (functional reset) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Filters</h3>", unsafe_allow_html=True)
filter_row1, filter_row2 = st.columns([1, 1], gap="large")

with filter_row1:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Date Range</label>", unsafe_allow_html=True)
    date_range = st.date_input("Select date range",
                               value=(df['date'].min().date(), df['date'].max().date()),
                               min_value=df['date'].min().date(), max_value=df['date'].max().date(),
                               label_visibility="collapsed", key="analytics_dates")
with filter_row2:
    st.markdown(f"<label style='display:block;margin-bottom:.5rem;font-weight:600;color:{COLORS['text_primary']};font-size:.9rem;'>Food Items</label>", unsafe_allow_html=True)
    all_items = sorted(df['food_item'].unique())
    default_items = all_items[:3] if len(all_items) >= 3 else all_items
    selected_items = st.multiselect("Select food items", options=all_items, default=default_items,
                                    label_visibility="collapsed", key="analytics_items")

col1, col2, col3 = st.columns([1, 1, 8])
with col1:
    if st.button("🔄 Reset", key="analytics_reset"):
        for key in ('analytics_dates', 'analytics_items'):
            st.session_state.pop(key, None)
        st.rerun()

# Normalise date_range (single-date edge case) then filter.
try:
    if isinstance(date_range, (list, tuple)):
        date_start, date_end = (date_range[0], date_range[1]) if len(date_range) == 2 else (date_range[0], date_range[0])
    else:
        date_start = date_end = date_range
except Exception:
    date_start = date_end = df['date'].min().date()

if not selected_items:
    empty_state("🔍", "No items selected", "Select at least one food item to see analytics.")
    st.stop()

filtered_df = df[(df['date'] >= pd.to_datetime(date_start)) & (df['date'] <= pd.to_datetime(date_end)) &
                 (df['food_item'].isin(selected_items))]
with col2:
    st.metric("Records", f"{len(filtered_df):,}")

if filtered_df.empty:
    empty_state("🔍", "No rows match these filters", "Widen the date range or select more items.")
    st.stop()

divider()

# ========== KPI SUMMARY (live) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Overview (live)</h3>", unsafe_allow_html=True)
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    render_kpi_card("Total Demand", f"{filtered_df['demand'].sum():,.0f}", f"{filtered_df['date'].nunique()} days", "neutral", "📦")
with kpi_col2:
    render_kpi_card("Average Daily", f"{filtered_df['demand'].mean():.0f}", "units/day", "neutral", "📊")
with kpi_col3:
    peak_row = filtered_df.loc[filtered_df['demand'].idxmax()]
    render_kpi_card("Peak Day", f"{peak_row['demand']:.0f}", f"{peak_row['food_item']} • {pd.to_datetime(peak_row['date']).date()}", "positive", "📈")
with kpi_col4:
    render_kpi_card("Variability", f"{filtered_df['demand'].std():.0f}", "std dev", "neutral", "📉")

# Honest calendar insight (live, replaces generic tips).
try:
    weekend_avg = filtered_df[pd.to_datetime(filtered_df['date']).dt.dayofweek >= 5]['demand'].mean()
    weekday_avg = filtered_df[pd.to_datetime(filtered_df['date']).dt.dayofweek < 5]['demand'].mean()
    uplift = ((weekend_avg - weekday_avg) / weekday_avg * 100) if weekday_avg else 0
    hol_avg = filtered_df[filtered_df['holiday'] == 1]['demand'].mean() if 'holiday' in filtered_df.columns else float('nan')
    reg_avg = filtered_df[filtered_df['holiday'] == 0]['demand'].mean() if 'holiday' in filtered_df.columns else float('nan')
    hol_uplift = ((hol_avg - reg_avg) / reg_avg * 100) if reg_avg and pd.notna(hol_avg) else 0
    st.info(f"📌 In this selection: weekends average **{uplift:+.1f}%** vs weekdays; "
            f"holidays average **{hol_uplift:+.1f}%** vs regular days.")
except Exception as e:
    logger.warning(f"Calendar insight failed: {e}")

divider()

# ========== CHARTS (live) ==========

st.markdown("<h3 style='margin-bottom: 1rem;'>Visualizations (live)</h3>", unsafe_allow_html=True)
st.markdown("<h4 style='margin-bottom: 1rem;'>Demand Trend Over Time</h4>", unsafe_allow_html=True)
fig_trend = go.Figure()
for item in selected_items:
    item_data = filtered_df[filtered_df['food_item'] == item].sort_values('date')
    fig_trend.add_trace(go.Scatter(x=item_data['date'], y=item_data['demand'], mode='lines+markers', name=item,
                                   line=dict(width=3),
                                   hovertemplate='<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Demand: %{y:.0f}<extra></extra>'))
fig_trend.update_layout(xaxis_title="Date", yaxis_title="Demand (units)", hovermode='x unified',
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                        font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                        yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                        height=350, margin=dict(l=40, r=20, t=40, b=40),
                        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'))
st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
divider()

chart_col1, chart_col2 = st.columns(2, gap="large")
with chart_col1:
    st.markdown("<h4 style='margin-bottom: 1rem;'>Food Items by Total Demand</h4>", unsafe_allow_html=True)
    top_items = filtered_df.groupby('food_item')['demand'].sum().sort_values(ascending=False).head(10)
    fig_ranking = go.Figure(data=[go.Bar(x=top_items.values, y=top_items.index, orientation='h',
                                         marker=dict(color=top_items.values,
                                                     colorscale=[[0, COLORS['primary']], [1, COLORS['accent_saffron']]],
                                                     showscale=False),
                                         hovertemplate='<b>%{y}</b><br>Total: %{x:,.0f} units<extra></extra>')])
    fig_ranking.update_layout(xaxis_title="Total Demand (units)", yaxis_title="", plot_bgcolor='rgba(0,0,0,0)',
                              paper_bgcolor=COLORS['surface_dark'],
                              font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                              xaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                              height=300, margin=dict(l=120, r=20, t=20, b=40))
    st.plotly_chart(fig_ranking, use_container_width=True, config={'displayModeBar': False})

with chart_col2:
    st.markdown("<h4 style='margin-bottom: 1rem;'>Average Demand by Day of Week</h4>", unsafe_allow_html=True)
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_demand = filtered_df.groupby('weekday')['demand'].mean().reindex(weekday_order)
    fig_weekday = go.Figure(data=[go.Bar(x=weekday_demand.index, y=weekday_demand.values,
                                         marker=dict(color=[COLORS['accent_saffron'] if i >= 4 else COLORS['primary']
                                                            for i in range(len(weekday_demand))]),
                                         hovertemplate='<b>%{x}</b><br>Avg: %{y:.0f} units<extra></extra>')])
    fig_weekday.update_layout(xaxis_title="Day of Week", yaxis_title="Average Demand (units)",
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                              font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                              yaxis=dict(showgrid=True, gridwidth=1, gridcolor=COLORS['border_subtle']),
                              height=300, margin=dict(l=40, r=20, t=20, b=40), showlegend=False)
    st.plotly_chart(fig_weekday, use_container_width=True, config={'displayModeBar': False})

divider()
st.markdown("<h4 style='margin-bottom: 1rem;'>Item Contribution to Total Demand</h4>", unsafe_allow_html=True)
item_contribution = filtered_df.groupby('food_item')['demand'].sum().sort_values(ascending=False)
fig_pie = go.Figure(data=[go.Pie(labels=item_contribution.index, values=item_contribution.values,
                                 marker=dict(colors=px.colors.sequential.Blues),
                                 hovertemplate='<b>%{label}</b><br>%{value:,.0f} units (%{percent})<extra></extra>')])
fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor=COLORS['surface_dark'],
                      font=dict(family="Inter, sans-serif", color=COLORS['text_primary']),
                      height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
divider()

# ========== DATA TABLE + EXPORT (one-click, real) ==========

section_header(title="Detailed Data", subtitle=f"{len(filtered_df):,} filtered rows", icon="📋")
display_df = filtered_df[['date', 'food_item', 'demand', 'holiday']].copy().sort_values('date', ascending=False)
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
st.dataframe(display_df, use_container_width=True, hide_index=True,
             column_config={'date': st.column_config.TextColumn('Date', width='small'),
                            'food_item': st.column_config.TextColumn('Food Item', width='medium'),
                            'demand': st.column_config.NumberColumn('Demand (units)', format='%d'),
                            'holiday': st.column_config.NumberColumn('Holiday', format='%d')})
st.download_button("📥 Export Filtered Data (CSV)", data=filtered_df.to_csv(index=False),
                   file_name=f"analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                   mime="text/csv", key="analytics_export")
divider()
render_footer()
