import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AnalyticsEngine:
    """Provides analytical transformations on historical demand datasets."""

    @staticmethod
    def get_dashboard_kpis(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate high-level Key Performance Indicators for the dashboard."""
        if df is None or df.empty:
            return {}

        try:
            total_orders = float(df['demand'].sum())
            total_days = df['date'].nunique()
            avg_daily_demand = total_orders / total_days if total_days > 0 else 0

            # Highest demand item overall
            item_totals = df.groupby('food_item')['demand'].sum()
            highest_item = item_totals.idxmax() if not item_totals.empty else "N/A"

            # Most recent demand trend
            recent_days = min(7, total_days)
            latest_date = df['date'].max()
            recent_df = df[df['date'] >= (latest_date - pd.Timedelta(days=recent_days))]
            recent_avg = recent_df['demand'].sum() / recent_days if recent_days > 0 else 0

            trend_percent = 0.0
            if avg_daily_demand > 0:
                trend_percent = ((recent_avg - avg_daily_demand) / avg_daily_demand) * 100

            return {
                "total_orders": total_orders,
                "avg_daily_demand": avg_daily_demand,
                "unique_items": df['food_item'].nunique(),
                "highest_item": highest_item,
                "recent_avg": recent_avg,
                "trend_percent": trend_percent,
                "latest_data_date": latest_date
            }
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}

    @staticmethod
    def get_item_performance(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate aggregate performance by food item."""
        if df is None or df.empty:
            return pd.DataFrame()

        try:
            agg_df = df.groupby('food_item').agg({
                'demand': ['sum', 'mean', 'max', 'min', 'std']
            }).reset_index()

            # Flatten multi-level columns
            agg_df.columns = ['Food Item', 'Total Demand', 'Average Demand', 'Max Demand (Day)', 'Min Demand (Day)', 'Volatility (StdDev)']

            # Sort by total demand
            return agg_df.sort_values(by='Total Demand', ascending=False).round(1)
        except Exception as e:
            logger.error(f"Error calculating item performance: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_trend_data(df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
        """Aggregate total demand over time. freq: 'D' (daily), 'W' (weekly), 'M' (monthly)."""
        if df is None or df.empty:
            return pd.DataFrame()

        try:
            # Group by date based on frequency
            trend_df = df.groupby(pd.Grouper(key='date', freq=freq))['demand'].sum().reset_index()
            return trend_df
        except Exception as e:
            logger.error(f"Error calculating trend data: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_calendar_patterns(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Extract average demand by Day of Week and Holiday vs Non-Holiday."""
        if df is None or df.empty:
            return pd.DataFrame(), pd.DataFrame()

        try:
            # 1. Day of week average
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['dow_name'] = df['date'].dt.dayofweek.map(lambda x: day_names[x])
            dow_avg = df.groupby('dow_name')['demand'].mean().reindex(day_names).reset_index()
            dow_avg.columns = ['Day of Week', 'Average Demand']

            # 2. Holiday vs Non-Holiday average
            if 'holiday' in df.columns:
                df['holiday_label'] = df['holiday'].map({0: 'Regular Day', 1: 'Holiday'})
                hol_avg = df.groupby('holiday_label')['demand'].mean().reset_index()
                hol_avg.columns = ['Day Type', 'Average Demand']
            else:
                hol_avg = pd.DataFrame(columns=['Day Type', 'Average Demand'])

            return dow_avg, hol_avg
        except Exception as e:
            logger.error(f"Error calculating calendar patterns: {e}")
            return pd.DataFrame(), pd.DataFrame()
