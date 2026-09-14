"""
Model evaluation metrics for time-series forecasting.
Provides both sklearn-based and native NumPy implementations.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Union, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Check if scikit-learn is available
try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class ModelEvaluator:
    """
    Calculates model performance metrics for time-series forecasting.
    All metrics follow the convention: lower is better for errors, higher is better for R².
    """

    @staticmethod
    def calculate_metrics(
        y_true: Union[np.ndarray, pd.Series, list],
        y_pred: Union[np.ndarray, pd.Series, list],
        sample_weights: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Calculates comprehensive regression metrics.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            sample_weights: Optional weights for weighted metrics

        Returns:
            Dict with mae, mse, rmse, r2, mape (if calculable)
        """
        y_true = np.asarray(y_true, dtype=np.float64).flatten()
        y_pred = np.asarray(y_pred, dtype=np.float64).flatten()

        # Validate shapes
        if len(y_true) != len(y_pred):
            raise ValueError(f"Shape mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")

        if len(y_true) == 0:
            return {"mae": 0.0, "mse": 0.0, "rmse": 0.0, "r2": 0.0}

        if HAS_SKLEARN:
            mae = float(mean_absolute_error(y_true, y_pred, sample_weight=sample_weights))
            mse = float(mean_squared_error(y_true, y_pred, sample_weight=sample_weights))
            rmse = float(np.sqrt(mse))
            r2 = float(r2_score(y_true, y_pred, sample_weight=sample_weights))

            # MAPE - handle division by zero
            try:
                mape = float(mean_absolute_percentage_error(y_true, y_pred))
            except Exception:
                mape = float('inf')
        else:
            # Native high-precision computation
            errors = y_true - y_pred
            mae = float(np.mean(np.abs(errors)))
            mse = float(np.mean(errors ** 2))
            rmse = float(np.sqrt(mse))

            # R-squared calculation
            ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
            ss_res = float(np.sum(errors ** 2))
            r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

            # MAPE calculation
            non_zero_mask = y_true != 0
            if non_zero_mask.any():
                mape = float(np.mean(np.abs(errors[non_zero_mask] / y_true[non_zero_mask])) * 100)
            else:
                mape = float('inf')

        return {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 6),
            "mape": round(mape, 2) if mape != float('inf') else None
        }

    @staticmethod
    def calculate_metrics_by_horizon(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        horizons: np.ndarray
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate metrics grouped by forecast horizon.

        Args:
            y_true: Actual values
            y_pred: Predicted values
            horizons: Horizon (days ahead) for each prediction

        Returns:
            Dict mapping horizon -> metrics dict
        """
        results = {}
        unique_horizons = np.unique(horizons)

        for h in unique_horizons:
            mask = horizons == h
            results[int(h)] = ModelEvaluator.calculate_metrics(
                y_true[mask],
                y_pred[mask]
            )

        return results

    @staticmethod
    def compare_models(results_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Converts model results dictionary into a structured comparison DataFrame.

        Args:
            results_dict: Dict mapping model_key -> metrics dict

        Returns:
            DataFrame sorted by MAE (best first)
        """
        rows = []
        name_map = {
            'lr': 'Linear Regression',
            'rf': 'Random Forest',
            'dl': 'Deep Learning',
            'baseline': 'Baseline (7-day MA)'
        }

        for key, metrics in results_dict.items():
            model_name = metrics.get('model_name', name_map.get(key, key))
            rows.append({
                'Model': model_name,
                'Model_Key': key,
                'MAE': metrics.get('mae', 0.0),
                'MSE': metrics.get('mse', 0.0),
                'RMSE': metrics.get('rmse', 0.0),
                'R2': metrics.get('r2', 0.0),
                'MAPE': metrics.get('mape', None)
            })

        df = pd.DataFrame(rows)

        if not df.empty and 'MAE' in df.columns:
            df = df.sort_values(by='MAE', ascending=True).reset_index(drop=True)

        return df

    @staticmethod
    def interpret_r2(r2: float) -> str:
        """
        Provide human-readable interpretation of R² score.

        Args:
            r2: R-squared value

        Returns:
            Interpretation string
        """
        if r2 >= 0.9:
            return "Excellent - model explains >90% of variance"
        elif r2 >= 0.8:
            return "Good - model explains >80% of variance"
        elif r2 >= 0.7:
            return "Acceptable - model explains >70% of variance"
        elif r2 >= 0.5:
            return "Fair - model explains >50% of variance"
        elif r2 >= 0.0:
            return "Poor - model explains <50% of variance"
        else:
            return "Invalid - model performs worse than mean baseline"

    @staticmethod
    def interpret_mae(mae: float, avg_demand: float) -> str:
        """
        Provide interpretation of MAE relative to average demand.

        Args:
            mae: Mean absolute error
            avg_demand: Average demand in the dataset

        Returns:
            Interpretation string
        """
        if avg_demand == 0:
            return "Cannot interpret MAE (zero average demand)"

        pct_error = (mae / avg_demand) * 100

        if pct_error <= 5:
            return f"Excellent - error is {pct_error:.1f}% of average demand"
        elif pct_error <= 10:
            return f"Good - error is {pct_error:.1f}% of average demand"
        elif pct_error <= 20:
            return f"Acceptable - error is {pct_error:.1f}% of average demand"
        else:
            return f"High error - {pct_error:.1f}% of average demand"
