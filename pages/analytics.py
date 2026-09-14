"""
DemandWise - Analytics Dashboard
Professional visualizations and insights from historical demand data.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DEFAULT_DATASET_PATH
from src.data.loader import DataLoader
from src.analytics.engine import AnalyticsEngine
from src.styles.theme import get_custom_css, get_plotly_theme, COLORS
from src.ui.components import render_header, render_kpi_card, render_footer

st.set_page_config(page_title="Analytics | DemandWise", page_icon="📈", layout="wide")

# Apply professional theme
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Get shared Plotly theme
plotly_theme = get_plotly_theme()


def apply_plotly_layout(fig, title: str = "", height: int = 420, xaxis_title: str = "", yaxis_title: str = ""):
    """Apply consistent professional styling to any Plotly figure."""
    layout = plotly_theme['layout']
    fig.update_layout(
        title=dict(
            text=title,
            font=layout['title']['font'],
            x=0.02,
            xanchor='left'
        ),
        font=layout['font'],
        paper_bgcolor=layout['paper_bgcolor'],
        plot_bgcolor=layout['plot_bgcolor'],
        height=height,
        xaxis=dict(
            title=xaxis_title,
            gridcolor=layout['xaxis']['gridcolor'],
            linecolor=layout['xaxis']['linecolor'],
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            title=yaxis_title,
            gridcolor=layout['yaxis']['gridcolor'],
            linecolor=layout['yaxis']['linecolor'],
            showgrid=True,
            zeroline=False,
        ),
        legend=dict(
            bgcolor=COLORS['surface'],
            bordercolor=COLORS['border'],
            borderwidth=1,
        ),
        margin=dict(l=60, r=30, t=60, b=60),
        hovermode='x unified',
    )
    return fig


# ─── Load Data ────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    if DEFAULT_DATASET_PATH.exists():
        df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
    else:
        df = DataLoader.generate_demo_dataset()
        df.to_csv(DEFAULT_DATASET_PATH, index=False)
    return df

df = load_data()

if df is None or df.empty:
    st.warning("No data available. Please upload data first.")
    st.stop()

# ─── Sidebar Filters ──────────────────────────────────────────────────────────

st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=[df['date'].min().date(), df['date'].max().date()],
    min_value=df['date'].min().date(),
    max_value=df['date'].max().date()
)

if len(date_range) == 2:
    filtered_df = df[
        (df['date'] >= pd.Timestamp(date_range[0])) &
        (df['date'] <= pd.Timestamp(date_range[1]))
    ]
else:
    filtered_df = df

selected_items = st.sidebar.multiselect(
    "Food Items",
    options=sorted(df['food_item'].unique()),
    default=sorted(df['food_item'].unique()),
    help="Select food items to analyze"
)

if selected_items:
    filtered_df = filtered_df[filtered_df['food_item'].isin(selected_items)]

# ─── Page Header ──────────────────────────────────────────────────────────────

render_header(
    title="Demand Analytics",
    subtitle="Explore historical trends, item performance, and seasonal patterns in your demand data.",
    icon="📈",
    badge="Insights"
)

# ─── KPI Cards ────────────────────────────────────────────────────────────────

total_orders = int(filtered_df['demand'].sum())
avg_daily = filtered_df.groupby('date')['demand'].sum().mean()
unique_items = filtered_df['food_item'].nunique()
best_item = filtered_df.groupby('food_item')['demand'].sum().idxmax()

# Compute month-over-month delta for total demand (for KPI context)
filtered_df['month'] = filtered_df['date'].dt.to_period('M')
monthly_totals = filtered_df.groupby('month')['demand'].sum().sort_index()
if len(monthly_totals) >= 2:
    last_month = monthly_totals.iloc[-1]
    prev_month = monthly_totals.iloc[-2]
    mom_pct = ((last_month - prev_month) / prev_month * 100) if prev_month != 0 else 0
    mom_delta = f"{abs(mom_pct):.1f}% vs prev month"
    mom_type = "positive" if mom_pct >= 0 else "negative"
else:
    mom_delta = None
    mom_type = "neutral"

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi_card(
        label="Total Orders",
        value=f"{total_orders:,}",
        delta=mom_delta,
        delta_type=mom_type,
        icon="📦"
    )

with col2:
    render_kpi_card(
        label="Avg Daily Demand",
        value=f"{avg_daily:.0f}",
        icon="📊"
    )

with col3:
    render_kpi_card(
        label="Active Items",
        value=str(unique_items),
        icon="🍽️"
    )

with col4:
    render_kpi_card(
        label="Top Performer",
        value=best_item,
        icon="🏆"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─── Tabbed Analytics Views ───────────────────────────────────────────────────

tab_trends, tab_items, tab_calendar = st.tabs([
    "  Trends  ",
    "  Item Performance  ",
    "  Calendar Patterns  "
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — TRENDS
# ═══════════════════════════════════════════════════════════════
with tab_trends:
    st.markdown("### Demand Over Time")

    freq_col, spacer = st.columns([1, 3])
    with freq_col:
        freq = st.selectbox(
            "Aggregation Frequency",
            ["Daily", "Weekly", "Monthly"],
            index=0,
            key="trend_freq"
        )

    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    trend_df = AnalyticsEngine.get_trend_data(filtered_df, freq_map[freq])

    # Line chart — demand trend
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df['date'],
        y=trend_df['demand'],
        mode='lines+markers',
        name='Total Demand',
        line=dict(color=COLORS['primary'], width=2.5),
        marker=dict(size=5, color=COLORS['primary']),
        fill='tozeroy',
        fillcolor=f"rgba(46,134,171,0.08)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Demand: <b>%{y:,}</b><extra></extra>"
    ))
    fig_trend = apply_plotly_layout(
        fig_trend,
        title=f"{freq} Total Demand Over Time",
        height=420,
        xaxis_title="Date",
        yaxis_title="Total Demand"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Month-over-Month Comparison ──────────────────────────────
    st.markdown("### Month-over-Month Comparison")

    mom_df = (
        filtered_df
        .groupby(filtered_df['date'].dt.to_period('M'))['demand']
        .sum()
        .reset_index()
    )
    mom_df.columns = ['month', 'total_demand']
    mom_df['month_str'] = mom_df['month'].astype(str)
    mom_df['pct_change'] = mom_df['total_demand'].pct_change() * 100

    col_mom1, col_mom2 = st.columns(2)

    with col_mom1:
        fig_mom_bar = go.Figure(data=[
            go.Bar(
                x=mom_df['month_str'],
                y=mom_df['total_demand'],
                marker_color=[
                    COLORS['success'] if (i > 0 and mom_df['total_demand'].iloc[i] >= mom_df['total_demand'].iloc[i - 1])
                    else COLORS['danger'] if i > 0
                    else COLORS['primary']
                    for i in range(len(mom_df))
                ],
                hovertemplate="<b>%{x}</b><br>Total Demand: <b>%{y:,}</b><extra></extra>"
            )
        ])
        fig_mom_bar = apply_plotly_layout(
            fig_mom_bar,
            title="Monthly Total Demand",
            height=380,
            xaxis_title="Month",
            yaxis_title="Total Demand"
        )
        fig_mom_bar.update_layout(hovermode='x')
        st.plotly_chart(fig_mom_bar, use_container_width=True)

    with col_mom2:
        mom_change_df = mom_df.dropna(subset=['pct_change'])
        bar_colors = [
            COLORS['success'] if v >= 0 else COLORS['danger']
            for v in mom_change_df['pct_change']
        ]
        fig_mom_pct = go.Figure(data=[
            go.Bar(
                x=mom_change_df['month_str'],
                y=mom_change_df['pct_change'],
                marker_color=bar_colors,
                hovertemplate="<b>%{x}</b><br>Change: <b>%{y:+.1f}%</b><extra></extra>"
            )
        ])
        fig_mom_pct.add_hline(y=0, line_color=COLORS['border'], line_width=1.5)
        fig_mom_pct = apply_plotly_layout(
            fig_mom_pct,
            title="Month-over-Month Change (%)",
            height=380,
            xaxis_title="Month",
            yaxis_title="Change (%)"
        )
        fig_mom_pct.update_layout(hovermode='x')
        st.plotly_chart(fig_mom_pct, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 2 — ITEM PERFORMANCE
# ═══════════════════════════════════════════════════════════════
with tab_items:
    st.markdown("### Item Performance Overview")

    performance_df = AnalyticsEngine.get_item_performance(filtered_df)

    # Sorted bar chart by total demand
    perf_sorted = performance_df.sort_values('Total Demand', ascending=True)
    colorscale_vals = perf_sorted['Total Demand'].tolist()
    max_val = max(colorscale_vals) if colorscale_vals else 1

    bar_colors = [
        f"rgba(46,134,171,{0.4 + 0.6 * (v / max_val)})"
        for v in colorscale_vals
    ]

    fig_items = go.Figure(data=[
        go.Bar(
            x=perf_sorted['Total Demand'],
            y=perf_sorted['Food Item'],
            orientation='h',
            marker_color=bar_colors,
            marker_line_color=COLORS['primary'],
            marker_line_width=0.8,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Total Demand: <b>%{x:,}</b><extra></extra>"
            )
        )
    ])
    fig_items = apply_plotly_layout(
        fig_items,
        title="Total Demand by Food Item",
        height=max(380, len(perf_sorted) * 36),
        xaxis_title="Total Demand",
        yaxis_title="Food Item"
    )
    fig_items.update_layout(hovermode='y unified')
    st.plotly_chart(fig_items, use_container_width=True)

    # Scatter: average vs volatility
    st.markdown("### Demand Stability Analysis")
    st.caption("Items in the top-left have high average demand with low variability — ideal for supply planning.")

    fig_scatter = go.Figure(data=[
        go.Scatter(
            x=performance_df['Volatility (StdDev)'],
            y=performance_df['Average Demand'],
            mode='markers+text',
            text=performance_df['Food Item'],
            textposition='top center',
            marker=dict(
                size=14,
                color=performance_df['Total Demand'],
                colorscale=[
                    [0, COLORS['primary_light']],
                    [1, COLORS['primary_dark']]
                ],
                showscale=True,
                colorbar=dict(title="Total Demand"),
                line=dict(color='white', width=1.5)
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Avg Demand: <b>%{y:.1f}</b><br>"
                "Volatility: <b>%{x:.1f}</b><extra></extra>"
            )
        )
    ])
    fig_scatter = apply_plotly_layout(
        fig_scatter,
        title="Average Demand vs. Demand Volatility",
        height=450,
        xaxis_title="Volatility (Std Dev)",
        yaxis_title="Average Daily Demand"
    )
    fig_scatter.update_layout(hovermode='closest')
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Performance ranking table
    st.markdown("### Performance Ranking")
    st.dataframe(
        performance_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Food Item": st.column_config.TextColumn("Food Item", width="medium"),
            "Total Demand": st.column_config.NumberColumn("Total Demand", format="%d"),
            "Average Demand": st.column_config.NumberColumn("Avg Demand", format="%.1f"),
            "Max Demand (Day)": st.column_config.NumberColumn("Peak Day", format="%d"),
            "Min Demand (Day)": st.column_config.NumberColumn("Lowest Day", format="%d"),
            "Volatility (StdDev)": st.column_config.NumberColumn("Volatility", format="%.1f"),
        }
    )

# ═══════════════════════════════════════════════════════════════
# TAB 3 — CALENDAR PATTERNS
# ═══════════════════════════════════════════════════════════════
with tab_calendar:
    st.markdown("### Day-of-Week & Seasonal Patterns")

    dow_avg, hol_avg = AnalyticsEngine.get_calendar_patterns(filtered_df)

    col_cal1, col_cal2 = st.columns(2)

    with col_cal1:
        dow_colors = [
            COLORS['primary'] if v == dow_avg['Average Demand'].max()
            else COLORS['primary_light']
            for v in dow_avg['Average Demand']
        ]
        fig_dow = go.Figure(data=[
            go.Bar(
                x=dow_avg['Day of Week'],
                y=dow_avg['Average Demand'],
                marker_color=dow_colors,
                marker_line_color=COLORS['primary_dark'],
                marker_line_width=0.8,
                hovertemplate="<b>%{x}</b><br>Avg Demand: <b>%{y:.1f}</b><extra></extra>"
            )
        ])
        fig_dow = apply_plotly_layout(
            fig_dow,
            title="Average Demand by Day of Week",
            height=380,
            xaxis_title="Day of Week",
            yaxis_title="Average Demand"
        )
        fig_dow.update_layout(hovermode='x')
        st.plotly_chart(fig_dow, use_container_width=True)

    with col_cal2:
        # Monthly seasonality
        seasonal_df = (
            filtered_df
            .groupby(filtered_df['date'].dt.month)['demand']
            .mean()
            .reset_index()
        )
        seasonal_df.columns = ['month_num', 'avg_demand']
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        seasonal_df['month_name'] = seasonal_df['month_num'].apply(
            lambda m: month_names[m - 1]
        )

        sea_colors = [
            COLORS['secondary'] if v == seasonal_df['avg_demand'].max()
            else COLORS['primary_light']
            for v in seasonal_df['avg_demand']
        ]

        fig_seasonal = go.Figure(data=[
            go.Bar(
                x=seasonal_df['month_name'],
                y=seasonal_df['avg_demand'],
                marker_color=sea_colors,
                marker_line_color=COLORS['primary_dark'],
                marker_line_width=0.8,
                hovertemplate="<b>%{x}</b><br>Avg Demand: <b>%{y:.1f}</b><extra></extra>"
            )
        ])
        fig_seasonal = apply_plotly_layout(
            fig_seasonal,
            title="Average Demand by Month",
            height=380,
            xaxis_title="Month",
            yaxis_title="Average Demand"
        )
        fig_seasonal.update_layout(hovermode='x')
        st.plotly_chart(fig_seasonal, use_container_width=True)

    # Holiday vs Non-Holiday
    st.markdown("### Holiday Impact Analysis")

    if 'holiday' in filtered_df.columns:
        holiday_labels = {0: "Regular Day", 1: "Holiday"}
        filtered_df = filtered_df.copy()
        filtered_df['holiday_label'] = filtered_df['holiday'].map(holiday_labels)

        col_hol1, col_hol2 = st.columns(2)

        with col_hol1:
            holiday_summary = filtered_df.groupby('holiday_label')['demand'].sum().reset_index()
            fig_holiday = go.Figure(data=[
                go.Pie(
                    labels=holiday_summary['holiday_label'],
                    values=holiday_summary['demand'],
                    hole=0.45,
                    marker=dict(
                        colors=[COLORS['primary'], COLORS['secondary']],
                        line=dict(color='white', width=2)
                    ),
                    hovertemplate="<b>%{label}</b><br>Total Demand: <b>%{value:,}</b><br>Share: <b>%{percent}</b><extra></extra>"
                )
            ])
            fig_holiday.update_layout(
                title=dict(
                    text="Demand Split: Regular vs. Holiday",
                    font=plotly_theme['layout']['title']['font'],
                    x=0.02,
                    xanchor='left'
                ),
                font=plotly_theme['layout']['font'],
                paper_bgcolor=COLORS['surface'],
                height=380,
                legend=dict(
                    bgcolor=COLORS['surface'],
                    bordercolor=COLORS['border'],
                    borderwidth=1,
                ),
                margin=dict(l=30, r=30, t=60, b=30)
            )
            st.plotly_chart(fig_holiday, use_container_width=True)

        with col_hol2:
            if not hol_avg.empty:
                hol_bar_colors = [
                    COLORS['secondary'] if label == "Holiday" else COLORS['primary']
                    for label in hol_avg['Day Type']
                ]
                fig_hol_bar = go.Figure(data=[
                    go.Bar(
                        x=hol_avg['Day Type'],
                        y=hol_avg['Average Demand'],
                        marker_color=hol_bar_colors,
                        marker_line_color=COLORS['primary_dark'],
                        marker_line_width=0.8,
                        hovertemplate="<b>%{x}</b><br>Avg Demand: <b>%{y:.1f}</b><extra></extra>"
                    )
                ])
                fig_hol_bar = apply_plotly_layout(
                    fig_hol_bar,
                    title="Average Demand: Regular vs. Holiday",
                    height=380,
                    xaxis_title="Day Type",
                    yaxis_title="Average Demand"
                )
                fig_hol_bar.update_layout(hovermode='x')
                st.plotly_chart(fig_hol_bar, use_container_width=True)
            else:
                st.info("No holiday data available for the selected filters.")
    else:
        st.info("Holiday data not available in the dataset.")

# ─── Raw Data Expander ────────────────────────────────────────────────────────

st.divider()
st.markdown("### Data Summary")

with st.expander("View Raw Data"):
    st.dataframe(
        filtered_df.drop(columns=['month', 'holiday_label'], errors='ignore'),
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "food_item": st.column_config.TextColumn("Food Item"),
            "demand": st.column_config.NumberColumn("Demand"),
            "holiday": st.column_config.CheckboxColumn("Holiday")
        }
    )

st.caption(
    f"Analyzing {len(filtered_df):,} data points "
    f"from {filtered_df['date'].min().date()} to {filtered_df['date'].max().date()}"
)

# ─── Footer ───────────────────────────────────────────────────────────────────

render_footer()
