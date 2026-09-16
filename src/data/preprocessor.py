"""
Time-series feature engineering for food demand forecasting.
Designed to prevent data leakage with proper temporal ordering.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Conditional imports for production robust fallback
try:
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PurePythonLabelEncoder:
    """Fallback LabelEncoder if scikit-learn is not installed."""
    def __init__(self):
        self.classes_ = []
        self._class_mapping = {}

    def fit(self, y):
        self.classes_ = sorted(list(set(y)))
        self._class_mapping = {c: i for i, c in enumerate(self.classes_)}
        return self

    def transform(self, y):
        return [self._class_mapping.get(item, -1) for item in y]

    def fit_transform(self, y):
        return self.fit(y).transform(y)

    def inverse_transform(self, y):
        inv = {v: k for k, v in self._class_mapping.items()}
        return [inv.get(item, -1) for item in y]


class PurePythonStandardScaler:
    """Fallback StandardScaler if scikit-learn is not installed."""
    def __init__(self):
        self.mean_ = None
        self.scale_ = None
        self.n_features_in_ = None

    def fit(self, X):
        if isinstance(X, pd.DataFrame):
            X = X.values
        X = np.array(X, dtype=float)
        self.mean_ = np.mean(X, axis=0)
        self.scale_ = np.std(X, axis=0)
        # Handle zero variance
        self.scale_[self.scale_ == 0.0] = 1.0
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        if isinstance(X, pd.DataFrame):
            X = X.values
        X_arr = np.array(X, dtype=float)
        return (X_arr - self.mean_) / self.scale_

    def fit_transform(self, X):
        return self.fit(X).transform(X)

    def inverse_transform(self, X):
        if isinstance(X, pd.DataFrame):
            X = X.values
        X_arr = np.array(X, dtype=float)
        return X_arr * self.scale_ + self.mean_


@dataclass
class FeatureEngineerConfig:
    """Configuration for feature engineering."""
    lag_days: Tuple[int, int] = (7, 30)
    rolling_windows: Tuple[int, int] = (7, 30)
    fillna_method: str = "history"  # 'history', 'zero', 'value'


class FeatureEngineer:
    """
    Produces time-series features for ML models.
    CRITICAL: All features must be computed using only data available BEFORE
    the prediction date to prevent data leakage.
    """

    # Required columns for feature engineering input
    REQUIRED_INPUT_COLS = ['date', 'food_item', 'demand', 'holiday']

    # Output feature columns (in order for model compatibility)
    FEATURE_COLUMNS = [
        'food_item_encoded',
        'year',
        'month',
        'day',
        'day_of_week',
        'is_weekend',
        'quarter',
        'week_of_year',
        'holiday',
        'demand_lag_7',
        'demand_lag_30',
        'demand_rolling_mean_7',
        'demand_rolling_mean_30',
        'demand_rolling_std_7',
        'demand_rolling_std_30',
    ]

    # Human-readable feature names for XAI
    FEATURE_NAMES = {
        'food_item_encoded': 'Food Item',
        'year': 'Year',
        'month': 'Month',
        'day': 'Day of Month',
        'day_of_week': 'Day of Week',
        'is_weekend': 'Weekend',
        'quarter': 'Quarter',
        'week_of_year': 'Week of Year',
        'holiday': 'Holiday Flag',
        'demand_lag_7': 'Demand 7 Days Ago',
        'demand_lag_30': 'Demand 30 Days Ago',
        'demand_rolling_mean_7': '7-Day Avg Demand',
        'demand_rolling_mean_30': '30-Day Avg Demand',
        'demand_rolling_std_7': '7-Day Demand Std Dev',
        'demand_rolling_std_30': '30-Day Demand Std Dev',
    }

    def __init__(self, config: Optional[FeatureEngineerConfig] = None):
        self.config = config or FeatureEngineerConfig()

    @staticmethod
    def validate_input(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate that required columns exist and are properly typed."""
        errors = []

        for col in FeatureEngineer.REQUIRED_INPUT_COLS:
            if col not in df.columns:
                errors.append(f"Missing required column: '{col}'")

        if 'date' in df.columns:
            try:
                pd.to_datetime(df['date'])
            except Exception:
                errors.append("'date' column cannot be parsed as datetime")

        if 'demand' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['demand']):
                errors.append("'demand' column must be numeric")
            if (df['demand'] < 0).any():
                errors.append("'demand' column contains negative values")

        if 'holiday' in df.columns:
            unique_vals = set(df['holiday'].dropna().unique())
            if not unique_vals.issubset({0, 1}):
                errors.append("'holiday' column must contain only 0 or 1")

        return len(errors) == 0, errors

    @staticmethod
    def create_features(
        df: pd.DataFrame,
        label_encoder=None,
        fit_encoder: bool = True
    ) -> Tuple[pd.DataFrame, Any]:
        """
        Apply time-series feature engineering transformations.
        CRITICAL: Features are computed using ONLY data available at each row's date.

        Args:
            df: Input DataFrame with columns: date, food_item, demand, holiday
            label_encoder: Optional pre-fitted encoder (for inference)
            fit_encoder: If True, fit new encoder; if False, require fitted encoder

        Returns:
            Tuple of (engineered DataFrame, label_encoder)
        """
        try:
            # Prevent SettingWithCopyWarning
            df = df.copy()

            # Ensure date is datetime
            df['date'] = pd.to_datetime(df['date'])

            # CRITICAL: Sort by food_item and date to ensure proper lag computation
            df = df.sort_values(['food_item', 'date']).reset_index(drop=True)

            # Create time-based features (no leakage - uses only prediction date)
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day'] = df['date'].dt.day
            df['day_of_week'] = df['date'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['quarter'] = df['date'].dt.quarter
            df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)

            # Encode food items
            if fit_encoder:
                if label_encoder is not None:
                    raise ValueError("Cannot fit encoder when fit_encoder=True with existing encoder")
                label_encoder = LabelEncoder() if HAS_SKLEARN else PurePythonLabelEncoder()
                df['food_item_encoded'] = label_encoder.fit_transform(df['food_item'])
            else:
                if label_encoder is None:
                    raise ValueError("Must provide label_encoder when fit_encoder=False")
                df['food_item_encoded'] = label_encoder.transform(df['food_item'])

            # Compute lag features using shift() - guarantees no leakage
            # shift(7) means we look at demand from 7 days BEFORE current date
            df['demand_lag_7'] = df.groupby('food_item')['demand'].shift(7)
            df['demand_lag_30'] = df.groupby('food_item')['demand'].shift(30)

            # Compute rolling statistics with proper offset
            # Rolling mean with min_periods=1 but shifted means we don't include current row
            df['demand_rolling_mean_7'] = df.groupby('food_item')['demand'].transform(
                lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
            )
            df['demand_rolling_mean_30'] = df.groupby('food_item')['demand'].transform(
                lambda x: x.shift(1).rolling(window=30, min_periods=1).mean()
            )

            # Compute rolling standard deviation (useful for uncertainty)
            df['demand_rolling_std_7'] = df.groupby('food_item')['demand'].transform(
                lambda x: x.shift(1).rolling(window=7, min_periods=2).std()
            )
            df['demand_rolling_std_30'] = df.groupby('food_item')['demand'].transform(
                lambda x: x.shift(1).rolling(window=30, min_periods=2).std()
            )

            # Fill NaN values from lag features
            # CRITICAL: Use only historical data up to (but not including) the row.

            # Past-only expanding mean per item (shift(1) ensures we never use the target row)
            item_past_mean = df.groupby('food_item')['demand'].transform(
                lambda x: x.shift(1).expanding(min_periods=1).mean()
            )

            # Fill lag values using rolling means first
            df['demand_lag_7'] = df['demand_lag_7'].fillna(df['demand_rolling_mean_7'])
            df['demand_lag_30'] = df['demand_lag_30'].fillna(df['demand_rolling_mean_30'])

            # If still NaN (e.g., very early history), use past-only expanding mean
            df['demand_lag_7'] = df['demand_lag_7'].fillna(item_past_mean)
            df['demand_lag_30'] = df['demand_lag_30'].fillna(item_past_mean)

            # Fill rolling means with past-only expanding mean if still NaN
            df['demand_rolling_mean_7'] = df['demand_rolling_mean_7'].fillna(item_past_mean)
            df['demand_rolling_mean_30'] = df['demand_rolling_mean_30'].fillna(item_past_mean)

            # Rolling std: if insufficient past history, treat as 0 variance
            df['demand_rolling_std_7'] = df['demand_rolling_std_7'].fillna(0.0)
            df['demand_rolling_std_30'] = df['demand_rolling_std_30'].fillna(0.0)

            # Final safety: if any NaNs remain (e.g., impossible corner cases), fill with 0
            df = df.fillna(0.0)

            return df, label_encoder

        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            raise e

    @staticmethod
    def create_inference_features(
        food_item: str,
        pred_date: pd.Timestamp,
        holiday: int,
        historical_df: pd.DataFrame,
        label_encoder,
        feature_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Create feature row for a single prediction.
        CRITICAL: Uses ONLY data available BEFORE the prediction date.

        Args:
            food_item: Name of food item
            pred_date: Date to predict
            holiday: Holiday flag (0 or 1)
            historical_df: Historical demand data for the food item
            label_encoder: Fitted label encoder
            feature_columns: Ordered list of feature columns

        Returns:
            DataFrame with single row of features matching training format
        """
        feature_columns = feature_columns or FeatureEngineer.FEATURE_COLUMNS

        # Filter to data BEFORE prediction date (critical for no leakage)
        history = historical_df[
            (historical_df['food_item'] == food_item) &
            (historical_df['date'] < pred_date)
        ].sort_values('date')

        # Get food item encoding
        food_encoded = label_encoder.transform([food_item])[0]

        # Build time features from prediction date
        features = {
            "food_item_encoded": food_encoded,
            "year": int(pred_date.year),
            "month": int(pred_date.month),
            "day": int(pred_date.day),
            "day_of_week": int(pred_date.dayofweek),
            "is_weekend": int(1 if pred_date.dayofweek >= 5 else 0),
            "quarter": int(pred_date.quarter),
            "week_of_year": int(pred_date.isocalendar().week),
            "holiday": int(holiday),
        }

        # Compute lag features from history (not including prediction date)
        if len(history) >= 7:
            features["demand_lag_7"] = float(history['demand'].iloc[-7])
        else:
            features["demand_lag_7"] = float(history['demand'].mean()) if len(history) > 0 else 0.0

        if len(history) >= 30:
            features["demand_lag_30"] = float(history['demand'].iloc[-30])
        else:
            features["demand_lag_30"] = float(history['demand'].mean()) if len(history) > 0 else 0.0

        # Compute rolling features from history
        if len(history) >= 1:
            recent_7 = history['demand'].tail(7) if len(history) >= 7 else history['demand']
            recent_30 = history['demand'].tail(30) if len(history) >= 30 else history['demand']

            features["demand_rolling_mean_7"] = float(recent_7.mean())
            features["demand_rolling_mean_30"] = float(recent_30.mean())

            # Std dev with fallback to 0 for small samples
            if len(recent_7) >= 2:
                features["demand_rolling_std_7"] = float(recent_7.std())
            else:
                features["demand_rolling_std_7"] = 0.0

            if len(recent_30) >= 2:
                features["demand_rolling_std_30"] = float(recent_30.std())
            else:
                features["demand_rolling_std_30"] = 0.0
        else:
            # No history available - use zeros/sensible defaults
            avg_demand = 100.0  # Default fallback
            features["demand_rolling_mean_7"] = avg_demand
            features["demand_rolling_mean_30"] = avg_demand
            features["demand_rolling_std_7"] = 0.0
            features["demand_rolling_std_30"] = 0.0

        # Ensure all feature columns are present
        for col in feature_columns:
            if col not in features:
                features[col] = 0.0

        # Create DataFrame in correct column order
        feature_df = pd.DataFrame([features])[feature_columns]

        return feature_df

    @staticmethod
    def get_scaler() -> Any:
        return StandardScaler() if HAS_SKLEARN else PurePythonStandardScaler()

    @staticmethod
    def get_feature_columns() -> List[str]:
        """Return the canonical feature column list."""
        return FeatureEngineer.FEATURE_COLUMNS.copy()

    @staticmethod
    def get_feature_name(column: str) -> str:
        """Get human-readable feature name."""
        return FeatureEngineer.FEATURE_NAMES.get(column, column)