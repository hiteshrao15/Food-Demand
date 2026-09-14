"""
Model retraining pipeline with time-series-safe evaluation.
CRITICAL: Uses chronological split and proper feature engineering to prevent data leakage.
"""
import pickle
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
from datetime import datetime
import json
import hashlib

from src.config import MODELS_DIR, FEATURE_COLUMNS, RANDOM_STATE
from src.ml.models import get_model
from src.ml.evaluator import ModelEvaluator
from src.utils.logger import get_logger

logger = get_logger(__name__)


def safe_save_artifact(obj: Any, filepath: str):
    """Safely pickle and save an artifact to disk."""
    try:
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        logger.error(f"Failed to save artifact to {filepath}: {e}")
        raise e


def compute_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()[:16]


class TimeSeriesSplit:
    """
    Chronological train/test split for time-series forecasting.
    Guarantees no data leakage by training on past, testing on future.
    """

    @staticmethod
    def split(
        df: pd.DataFrame,
        test_size: float = 0.2,
        date_column: str = 'date'
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data chronologically.

        Args:
            df: DataFrame sorted by date
            test_size: Fraction of data to use for testing (0.0-1.0)
            date_column: Name of date column

        Returns:
            Tuple of (train_df, test_df)
        """
        # Ensure sorted by date
        df_sorted = df.sort_values(date_column).reset_index(drop=True)

        # Calculate split point
        split_idx = int(len(df_sorted) * (1 - test_size))

        train_df = df_sorted.iloc[:split_idx].copy()
        test_df = df_sorted.iloc[split_idx:].copy()

        logger.info(f"Chronological split: {len(train_df)} train, {len(test_df)} test")
        logger.info(f"Train period: {train_df[date_column].min()} to {train_df[date_column].max()}")
        logger.info(f"Test period: {test_df[date_column].min()} to {test_df[date_column].max()}")

        return train_df, test_df

    @staticmethod
    def rolling_origin_split(
        df: pd.DataFrame,
        n_splits: int = 5,
        min_train_size: int = 100,
        date_column: str = 'date'
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Generate multiple train/test splits for rolling-origin backtesting.

        Args:
            df: DataFrame sorted by date
            n_splits: Number of splits to generate
            min_train_size: Minimum training set size
            date_column: Name of date column

        Returns:
            List of (train_df, test_df) tuples
        """
        df_sorted = df.sort_values(date_column).reset_index(drop=True)
        total_size = len(df_sorted)
        test_size = (total_size - min_train_size) // n_splits

        splits = []
        for i in range(n_splits):
            train_end = min_train_size + i * test_size
            test_end = min(train_end + test_size, total_size)

            train_df = df_sorted.iloc[:train_end].copy()
            test_df = df_sorted.iloc[train_end:test_end].copy()

            splits.append((train_df, test_df))

        return splits


class BaselineForecaster:
    """
    Simple baseline forecasters for comparison.
    ML models should outperform these to be considered useful.
    """

    @staticmethod
    def naive_forecast(historical_df: pd.DataFrame, food_item: str, horizon_days: int = 1) -> float:
        """Use last observed value as forecast."""
        item_data = historical_df[historical_df['food_item'] == food_item].sort_values('date')
        if len(item_data) == 0:
            return 0.0
        return float(item_data['demand'].iloc[-1])

    @staticmethod
    def seasonal_naive_forecast(
        historical_df: pd.DataFrame,
        food_item: str,
        day_of_week: int,
        horizon_days: int = 1
    ) -> float:
        """Use last same-day-of-week value as forecast."""
        item_data = historical_df[historical_df['food_item'] == food_item].sort_values('date')
        same_day_data = item_data[item_data['date'].dt.dayofweek == day_of_week]

        if len(same_day_data) == 0:
            return BaselineForecaster.naive_forecast(historical_df, food_item, horizon_days)

        return float(same_day_data['demand'].iloc[-1])

    @staticmethod
    def moving_average_forecast(
        historical_df: pd.DataFrame,
        food_item: str,
        window: int = 7
    ) -> float:
        """Use moving average as forecast."""
        item_data = historical_df[historical_df['food_item'] == food_item].sort_values('date')
        if len(item_data) == 0:
            return 0.0

        recent = item_data['demand'].tail(window)
        return float(recent.mean())


class UncertaintyEstimator:
    """
    Empirical uncertainty estimation from backtest residuals.
    Provides prediction intervals based on historical forecast errors.
    """

    def __init__(self):
        self.residuals_by_horizon = {}
        self.global_residuals = []
        self.coverage_level = 0.95  # 95% prediction interval

    def fit(self, y_true: np.ndarray, y_pred: np.ndarray, horizons: Optional[np.ndarray] = None):
        """
        Fit uncertainty estimator from backtest residuals.

        Args:
            y_true: True values
            y_pred: Predicted values
            horizons: Optional forecast horizon for each prediction
        """
        residuals = y_true - y_pred
        self.global_residuals = residuals

        if horizons is not None:
            unique_horizons = np.unique(horizons)
            for h in unique_horizons:
                mask = horizons == h
                self.residuals_by_horizon[h] = residuals[mask]

    def get_interval(
        self,
        point_prediction: float,
        horizon: Optional[int] = None
    ) -> Tuple[float, float, float, str]:
        """
        Get prediction interval for a point prediction.

        Args:
            point_prediction: The point forecast
            horizon: Optional forecast horizon

        Returns:
            Tuple of (lower_bound, upper_bound, interval_width, method_description)
        """
        if len(self.global_residuals) == 0:
            # No residual data - return wide interval with warning
            width = point_prediction * 0.5  # 50% of prediction
            return (
                max(0, point_prediction - width),
                point_prediction + width,
                width * 2,
                "Uncertainty estimate unavailable - using fallback 50% range"
            )

        # Use residuals from specific horizon if available
        if horizon is not None and horizon in self.residuals_by_horizon:
            residuals = self.residuals_by_horizon[horizon]
        else:
            residuals = self.global_residuals

        # Compute empirical quantiles
        alpha = 1 - self.coverage_level
        lower_quantile = alpha / 2  # 0.025 for 95% interval
        upper_quantile = 1 - alpha / 2  # 0.975 for 95% interval

        lower_error = np.percentile(residuals, lower_quantile * 100)
        upper_error = np.percentile(residuals, upper_quantile * 100)

        lower_bound = max(0, point_prediction + lower_error)
        upper_bound = point_prediction + upper_error
        interval_width = upper_bound - lower_bound

        method = f"Empirical {int(self.coverage_level*100)}% prediction interval from {len(residuals)} backtest residuals"

        return lower_bound, upper_bound, interval_width, method


class ModelRetrainer:
    """Manages the full end-to-end model retraining pipeline with time-series safety."""

    @staticmethod
    def retrain_and_save(
        df: pd.DataFrame,
        label_encoder,
        scaler,
        test_size: float = 0.2,
        use_rolling_origin: bool = False
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Trains models, evaluates, and saves artifacts for the best and all models.
        Uses CHRONOLOGICAL split to prevent data leakage.

        Args:
            df: Feature-engineered DataFrame
            label_encoder: Fitted label encoder
            scaler: Fitted scaler (will be refitted on train data only)
            test_size: Fraction of data for testing
            use_rolling_origin: If True, use rolling-origin backtesting

        Returns:
            Tuple[str, Dict[str, Any], Dict[str, Any]]:
            (best_model_key, best_model_metrics, all_model_results_metrics_only)
        """
        # 1. Chronological Train/Test Split
        logger.info("Performing chronological train/test split...")
        train_df, test_df = TimeSeriesSplit.split(df, test_size=test_size)

        # 2. Prepare Data
        X_train = train_df[FEATURE_COLUMNS].copy()
        y_train = train_df['demand'].copy()
        X_test = test_df[FEATURE_COLUMNS].copy()
        y_test = test_df['demand'].copy()

        # 3. Fit Scaler on TRAINING DATA ONLY (critical for no leakage)
        logger.info("Fitting scaler on training data only...")
        scaler = type(scaler)()  # Create new instance
        scaler.fit(X_train)

        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        logger.info(f"Features: {len(FEATURE_COLUMNS)}")

        # 4. Train Baseline Model for Comparison
        logger.info("Computing baseline forecasts...")
        baseline_preds = []
        baseline_true = []

        for idx, row in test_df.iterrows():
            food_item = row['food_item']
            pred_date = pd.to_datetime(row['date'])

            # Use data from before test period for baseline
            history = train_df[train_df['food_item'] == food_item]

            if len(history) > 0:
                baseline_pred = BaselineForecaster.moving_average_forecast(
                    train_df, food_item, window=7
                )
            else:
                baseline_pred = train_df['demand'].mean()

            baseline_preds.append(baseline_pred)
            baseline_true.append(row['demand'])

        baseline_metrics = ModelEvaluator.calculate_metrics(
            np.array(baseline_true),
            np.array(baseline_preds)
        )
        baseline_metrics['model_name'] = 'Moving Average (7-day)'
        logger.info(f"Baseline MAE: {baseline_metrics['mae']:.2f}")

        # 5. Train ML Models
        final_results = {}

        model_configs = {
            'lr': {'train_X': X_train, 'train_y': y_train, 'test_X': X_test},
            'rf': {'train_X': X_train, 'train_y': y_train, 'test_X': X_test},
            'dl': {'train_X': X_train_scaled, 'train_y': y_train, 'test_X': X_test_scaled}
        }

        for model_key in ['lr', 'rf', 'dl']:
            try:
                logger.info(f"Training {model_key.upper()} model...")
                model = get_model(model_key)

                config = model_configs[model_key]
                model.fit(config['train_X'], config['train_y'])

                predictions = model.predict(config['test_X'])

                metrics = ModelEvaluator.calculate_metrics(y_test, predictions.flatten())
                metrics['model_obj'] = model
                metrics['model_name'] = {
                    'lr': 'Linear Regression',
                    'rf': 'Random Forest',
                    'dl': 'Deep Learning'
                }.get(model_key, model_key)

                final_results[model_key] = metrics
                logger.info(f"{model_key.upper()} - MAE: {metrics['mae']:.2f}, R²: {metrics['r2']:.4f}")

                # Save individual model
                model_path = MODELS_DIR / f"{model_key}_model.pkl"
                safe_save_artifact(model, str(model_path))

            except Exception as e:
                logger.error(f"Failed to train {model_key.upper()}: {str(e)}")

        if not final_results:
            error_msg = "Model retraining failed; no models trained successfully."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        # 6. Fit Uncertainty Estimator on Best Model's Residuals
        best_model_key = min(final_results, key=lambda k: final_results[k]['mae'])
        best_model = final_results[best_model_key]['model_obj']

        # Get predictions for uncertainty estimation
        if best_model_key == 'dl':
            best_preds = best_model.predict(X_test_scaled)
        else:
            best_preds = best_model.predict(X_test)

        uncertainty_estimator = UncertaintyEstimator()
        uncertainty_estimator.fit(
            y_test.values,
            best_preds.flatten()
        )

        # Save uncertainty estimator
        safe_save_artifact(uncertainty_estimator, str(MODELS_DIR / "uncertainty_estimator.pkl"))

        # 7. Save All Artifacts
        logger.info("Saving model artifacts...")
        safe_save_artifact(label_encoder, str(MODELS_DIR / "label_encoder.pkl"))
        safe_save_artifact(scaler, str(MODELS_DIR / "scaler.pkl"))
        safe_save_artifact(FEATURE_COLUMNS, str(MODELS_DIR / "feature_columns.pkl"))
        safe_save_artifact(best_model, str(MODELS_DIR / "best_model.pkl"))

        # 8. Prepare Results
        metrics_results = {}
        for k, metrics_dict in final_results.items():
            metrics_results[k] = {mk: mv for mk, mv in metrics_dict.items() if mk not in ['model_obj', 'model_name']}
            metrics_results[k]['model_name'] = metrics_dict.get('model_name', k)

        # Add baseline to results
        metrics_results['baseline'] = baseline_metrics

        best_metrics = {mk: mv for mk, mv in final_results[best_model_key].items() if mk != 'model_obj'}
        best_metrics['model_name'] = final_results[best_model_key].get('model_name', best_model_key)

        # 9. Save Comparison and Metadata
        try:
            comp_df = ModelEvaluator.compare_models(metrics_results)
            comp_df.to_csv(MODELS_DIR / "model_comparison.csv", index=False)

            # Compute artifact checksums
            checksums = {}
            for artifact_name in ['best_model.pkl', 'scaler.pkl', 'label_encoder.pkl']:
                artifact_path = MODELS_DIR / artifact_name
                if artifact_path.exists():
                    checksums[artifact_name] = compute_checksum(str(artifact_path))

            metadata = {
                "best_model_name": best_metrics['model_name'],
                "best_model_key": best_model_key,
                "metrics": best_metrics,
                "baseline_metrics": baseline_metrics,
                "timestamp": datetime.now().isoformat(),
                "rows_trained": len(X_train),
                "rows_validated": len(X_test),
                "feature_count": len(FEATURE_COLUMNS),
                "feature_columns": FEATURE_COLUMNS,
                "version_id": f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "split_method": "chronological",
                "train_period": {
                    "start": str(train_df['date'].min()),
                    "end": str(train_df['date'].max())
                },
                "test_period": {
                    "start": str(test_df['date'].min()),
                    "end": str(test_df['date'].max())
                },
                "artifact_checksums": checksums,
                "library_versions": {
                    "pandas": pd.__version__,
                    "numpy": np.__version__,
                }
            }

            with open(MODELS_DIR / "model_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2, default=str)

        except Exception as e_meta:
            logger.warning(f"Could not write metadata/comparison CSV: {e_meta}")

        logger.info(f"✅ Training complete. Best model: {best_model_key.upper()} (MAE: {best_metrics['mae']:.2f})")

        return best_model_key, best_metrics, metrics_results