"""
Production demand predictor with time-series-safe feature construction.
CRITICAL: All features are computed using only data available BEFORE the prediction date.
"""
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import warnings

from src.config import MODELS_DIR, FEATURE_COLUMNS
from src.data.preprocessor import FeatureEngineer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactValidationError(Exception):
    """Raised when model artifacts fail validation."""
    pass


def safe_load_artifact(filepath: Path, expected_type: Optional[type] = None):
    """Safely load pickled artifact with optional type validation."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'rb') as f:
            obj = pickle.load(f)
        if expected_type is not None and not isinstance(obj, expected_type):
            warnings.warn(f"Artifact {filepath} is {type(obj)}, expected {expected_type}")
        return obj
    except Exception as e:
        logger.warning(f"Failed to load {filepath}: {e}")
        return None


class DemandPredictor:
    """
    Production demand predictor with proper time-series handling.

    Loads models, preprocessors, and generates predictions with context.
    All features are computed using ONLY data available before the prediction date.
    """

    def __init__(self, model_type: str = 'rf'):
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.uncertainty_estimator = None
        self.feature_columns = FEATURE_COLUMNS.copy()
        self.metadata = {}
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads required artifacts from the models directory."""
        try:
            # Load metadata first
            import json
            metadata_path = MODELS_DIR / 'model_metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)

            # Validate feature columns match
            if 'feature_columns' in self.metadata:
                saved_features = self.metadata['feature_columns']
                if saved_features != self.feature_columns:
                    logger.warning(
                        f"Feature mismatch: saved={len(saved_features)}, "
                        f"current={len(self.feature_columns)}. Using saved features."
                    )
                    self.feature_columns = saved_features

            # Load model
            model_file_map = {
                'lr': MODELS_DIR / 'lr_model.pkl',
                'rf': MODELS_DIR / 'rf_model.pkl',
                'dl': MODELS_DIR / 'dl_model.pkl'
            }

            model_file = model_file_map.get(self.model_type, MODELS_DIR / 'best_model.pkl')
            self.model = safe_load_artifact(model_file)

            # Load preprocessors
            self.scaler = safe_load_artifact(MODELS_DIR / 'scaler.pkl')
            self.label_encoder = safe_load_artifact(MODELS_DIR / 'label_encoder.pkl')

            # Load uncertainty estimator
            self.uncertainty_estimator = safe_load_artifact(
                MODELS_DIR / 'uncertainty_estimator.pkl'
            )

            if self.model is not None:
                logger.info(f"Model ({self.model_type}) and artifacts loaded successfully.")
            else:
                logger.warning(f"Model artifact not found for type: {self.model_type}")

        except Exception as e:
            logger.error(f"Error loading artifacts: {e}")

    def is_ready(self) -> bool:
        """Check if model and encoders are ready for prediction."""
        return self.model is not None and self.label_encoder is not None

    def get_supported_items(self) -> List[str]:
        """Get list of food items the model was trained on."""
        if self.label_encoder is None:
            return []
        try:
            return list(self.label_encoder.classes_)
        except Exception:
            return []

    def validate_food_item(self, food_item: str) -> Tuple[bool, str]:
        """
        Validate that food item is supported by the model.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.label_encoder is None:
            return False, "Model not loaded"

        supported = self.get_supported_items()
        if food_item not in supported:
            return False, f"'{food_item}' not in trained items. Supported: {', '.join(supported[:5])}..."

        return True, ""

    def validate_prediction_date(
        self,
        pred_date: pd.Timestamp,
        historical_df: pd.DataFrame,
        food_item: str
    ) -> Tuple[bool, str, int]:
        """
        Validate that sufficient historical data exists for prediction.

        Returns:
            Tuple of (is_valid, error_message, days_of_history)
        """
        item_history = historical_df[
            (historical_df['food_item'] == food_item) &
            (historical_df['date'] < pred_date)
        ]

        days_of_history = len(item_history)

        if days_of_history == 0:
            return False, f"No historical data for '{food_item}' before {pred_date.date()}", 0

        if days_of_history < 7:
            logger.warning(
                f"Limited history ({days_of_history} days) for {food_item}. "
                f"Predictions may be less reliable."
            )

        return True, "", days_of_history

    def predict(self, feature_df: pd.DataFrame) -> float:
        """
        Runs prediction on prepared input features DataFrame.

        Args:
            feature_df: DataFrame with columns matching self.feature_columns

        Returns:
            Predicted demand (non-negative)
        """
        if not self.is_ready():
            raise ValueError("Predictor is not ready. Model or encoder missing.")

        # Ensure feature order matches training
        X = feature_df[self.feature_columns].copy()

        if self.model_type == 'dl' and self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            pred = self.model.predict(X_scaled)
        else:
            pred = self.model.predict(X.values if hasattr(X, 'values') else X)

        pred_val = float(np.asarray(pred).flatten()[0])
        return max(0.0, round(pred_val, 1))

    def predict_with_uncertainty(
        self,
        feature_df: pd.DataFrame,
        horizon_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make prediction with uncertainty interval.

        Args:
            feature_df: Feature DataFrame
            horizon_days: Forecast horizon (for horizon-specific uncertainty)

        Returns:
            Dict with prediction, lower_bound, upper_bound, interval_method
        """
        point_prediction = self.predict(feature_df)

        if self.uncertainty_estimator is not None:
            lower, upper, width, method = self.uncertainty_estimator.get_interval(
                point_prediction, horizon=horizon_days
            )
        else:
            # Fallback: use empirical rule with rolling std if available
            rolling_std = feature_df.get('demand_rolling_std_7', [10.0]).iloc[0] if len(feature_df) > 0 else 10.0
            margin = 1.96 * max(rolling_std, point_prediction * 0.15)  # At least 15% margin
            lower = max(0, point_prediction - margin)
            upper = point_prediction + margin
            width = upper - lower
            method = "Approximate 95% interval (backtest residuals unavailable)"

        return {
            'prediction': point_prediction,
            'lower_bound': round(lower, 1),
            'upper_bound': round(upper, 1),
            'interval_width': round(width, 1),
            'interval_method': method
        }

    def predict_with_context(
        self,
        food_item: str,
        date: str,
        holiday: int,
        historical_df: pd.DataFrame,
        safety_buffer_pct: float = 0.10
    ) -> Dict[str, Any]:
        """
        Generate prediction with full context, uncertainty, and recommendations.

        CRITICAL: Features are computed using ONLY data available before the prediction date.

        Args:
            food_item: Name of food item to predict
            date: Prediction date (YYYY-MM-DD)
            holiday: Holiday flag (0 or 1)
            historical_df: Historical demand data
            safety_buffer_pct: Safety buffer percentage (0.10 = 10%)

        Returns:
            Dict with prediction, uncertainty, recommendations, and context
        """
        pred_date = pd.to_datetime(date)

        # Validate inputs
        is_valid, error_msg = self.validate_food_item(food_item)
        if not is_valid:
            raise ValueError(error_msg)

        is_valid, error_msg, days_history = self.validate_prediction_date(
            pred_date, historical_df, food_item
        )
        if not is_valid:
            raise ValueError(error_msg)

        # Filter historical data (CRITICAL: only data BEFORE prediction date)
        item_data = historical_df[
            (historical_df['food_item'] == food_item) &
            (historical_df['date'] < pred_date)
        ].sort_values('date')

        if item_data.empty:
            raise ValueError(f"No historical records found for '{food_item}' before {pred_date.date()}")

        # Build features using time-series-safe method
        feature_df = FeatureEngineer.create_inference_features(
            food_item=food_item,
            pred_date=pred_date,
            holiday=holiday,
            historical_df=historical_df,
            label_encoder=self.label_encoder,
            feature_columns=self.feature_columns
        )

        # Generate prediction with uncertainty
        pred_result = self.predict_with_uncertainty(feature_df)
        predicted_demand = pred_result['prediction']

        # Calculate preparation recommendation with safety buffer
        if safety_buffer_pct > 1.0:
            safety_buffer_pct = safety_buffer_pct / 100.0

        safety_units = int(np.ceil(predicted_demand * safety_buffer_pct))
        recommended_prep = int(np.ceil(predicted_demand + safety_units))

        # Context metrics
        item_avg = float(item_data['demand'].mean())
        item_std = float(item_data['demand'].std()) if len(item_data) > 1 else 0.0

        # Same day-of-week average
        dow_data = item_data[item_data['date'].dt.dayofweek == pred_date.dayofweek]
        dow_avg = float(dow_data['demand'].mean()) if len(dow_data) > 0 else item_avg

        # Recent trends
        recent_7 = item_data['demand'].tail(7) if len(item_data) >= 7 else item_data['demand']
        recent_7_avg = float(recent_7.mean())

        # Generate interpretation
        pct_diff = ((predicted_demand - item_avg) / item_avg * 100) if item_avg > 0 else 0

        if pct_diff > 15:
            trend = "higher"
            driver = "weekend/holiday peak" if pred_date.dayofweek >= 5 or holiday else "seasonal increase"
        elif pct_diff < -15:
            trend = "lower"
            driver = "off-peak period" if pred_date.dayofweek < 5 else "seasonal decrease"
        else:
            trend = "steady"
            driver = "normal demand patterns"

        interpretation = (
            f"Demand projected to be **{abs(pct_diff):.0f}% {trend}** than average "
            f"({item_avg:.1f} orders). Driver: {driver}. "
            f"Based on {days_history} days of history."
        )

        return {
            "food_item": food_item,
            "date": pred_date.strftime("%Y-%m-%d"),
            "day_of_week": pred_date.day_name(),
            "predicted_demand": predicted_demand,
            "uncertainty_lower": pred_result['lower_bound'],
            "uncertainty_upper": pred_result['upper_bound'],
            "uncertainty_method": pred_result['interval_method'],
            "recommended_prep": recommended_prep,
            "safety_buffer_pct": safety_buffer_pct * 100,
            "safety_units": safety_units,
            "model_used": self.metadata.get('best_model_name', self.model_type.upper()),
            "holiday": bool(holiday),
            "is_weekend": bool(pred_date.dayofweek >= 5),
            "historical_item_avg": round(item_avg, 1),
            "historical_item_std": round(item_std, 1),
            "historical_dow_avg": round(dow_avg, 1),
            "recent_7day_avg": round(recent_7_avg, 1),
            "days_of_history": days_history,
            "interpretation": interpretation,
            "feature_df": feature_df,
            "features_dict": feature_df.iloc[0].to_dict() if len(feature_df) > 0 else {}
        }

    def batch_predict(
        self,
        requests: List[Dict[str, Any]],
        historical_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for multiple items/dates.

        Args:
            requests: List of dicts with keys: food_item, date, holiday
            historical_df: Historical demand data

        Returns:
            List of prediction results
        """
        results = []

        for req in requests:
            try:
                result = self.predict_with_context(
                    food_item=req['food_item'],
                    date=req['date'],
                    holiday=req.get('holiday', 0),
                    historical_df=historical_df
                )
                result['status'] = 'success'
                results.append(result)
            except Exception as e:
                results.append({
                    'food_item': req['food_item'],
                    'date': req['date'],
                    'status': 'error',
                    'error': str(e)
                })

        return results
