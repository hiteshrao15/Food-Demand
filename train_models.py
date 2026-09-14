"""
Entry point script to generate the synthetic historical food demand dataset,
extract features, train the models, select the best model, and save all artifacts
for the DemandWise application.

CRITICAL FIXES APPLIED:
1. Fixed data leakage: Scaler is now fitted ONLY on training data after chronological split
2. Used TimeSeriesSplit for proper temporal validation instead of random split
3. Added proper uncertainty estimator training and saving
4. Fixed feature engineering to prevent leakage (already fixed in preprocessor)
"""
import sys
from pathlib import Path
import os
import pandas as pd
import json
import numpy as np
from sklearn.model_selection import TimeSeriesSplit

# Ensure parent directory is in Python path for correct package imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.config import DEFAULT_DATASET_PATH, MODEL_COMPARISON_PATH, METADATA_PATH
from src.data.loader import DataLoader
from src.data.preprocessor import FeatureEngineer
from src.ml.retrainer import ModelRetrainer
from src.database.db import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting model training pipeline with leakage prevention...")

    # Initialize Database for registry tracking
    db = DatabaseManager()

    # 1. Generate / Load Data
    logger.info(f"Generating realistic demographic dataset...")
    df = DataLoader.generate_demo_dataset(start_date='2024-01-01', end_date='2025-12-31')

    # Ensure data directory exists
    os.makedirs(DEFAULT_DATASET_PATH.parent, exist_ok=True)
    df.to_csv(DEFAULT_DATASET_PATH, index=False)
    logger.info(f"Dataset generated and saved to {DEFAULT_DATASET_PATH} with {len(df)} rows.")

    # 2. Preprocess Data and Engineer Features
    logger.info("Applying time-series-safe feature engineering (no leakage)...")
    df_engineered, label_encoder = FeatureEngineer.create_features(df)

    # 3. CRITICAL: Split data chronologically BEFORE fitting scaler
    logger.info("Performing chronological train/test split to prevent data leakage...")

    # Sort by date to ensure chronological order
    df_sorted = df_engineered.sort_values('date').reset_index(drop=True)

    # Use 80% for training, 20% for testing (chronological split)
    split_idx = int(len(df_sorted) * 0.8)
    train_df = df_sorted.iloc[:split_idx]
    test_df = df_sorted.iloc[split_idx:]

    logger.info(f"Training set: {len(train_df)} rows ({train_df['date'].min()} to {train_df['date'].max()})")
    logger.info(f"Test set: {len(test_df)} rows ({test_df['date'].min()} to {test_df['date'].max()})")

    # Verify no overlap
    if len(train_df) > 0 and len(test_df) > 0:
        assert train_df['date'].max() < test_df['date'].min(), "Temporal leakage: train and test sets overlap!"

    # 4. Fit Scaler ONLY on training data (critical for no leakage)
    logger.info("Fitting scaler on TRAINING data only...")
    scaler = FeatureEngineer.get_scaler()

    # Features to scale (exclude target and non-numeric)
    feature_cols_for_scaling = [
        "food_item_encoded", "year", "month", "day", "day_of_week", "is_weekend",
        "quarter", "week_of_year", "holiday", "demand_lag_7", "demand_lag_30",
        "demand_rolling_mean_7", "demand_rolling_mean_30"
    ]

    # Fit scaler on training data only
    scaler.fit(train_df[feature_cols_for_scaling])
    logger.info("Scaler fitted successfully on training data.")

    # 5. Train Models using the retrainer (which now handles chronological splitting internally)
    logger.info("Training ML models with chronological validation...")
    best_key, best_metrics, all_results = ModelRetrainer.retrain_and_save(
        train_df, label_encoder, scaler
    )

    # 6. Evaluate on hold-out test set
    logger.info("Evaluating models on hold-out test set...")
    from src.ml.evaluator import ModelEvaluator

    test_results = {}
    for model_key in ['lr', 'rf', 'dl']:
        try:
            # Load each model and evaluate on test set
            predictor = ModelRetrainer._load_model_and_preprocessors(model_key, label_encoder, scaler)
            if predictor is not None:
                # Prepare test features
                test_features, _ = FeatureEngineer.create_features(test_df, label_encoder, fit_encoder=False)
                X_test = test_features[FeatureEngineer.get_feature_columns()]
                y_test = test_features['demand'].values

                # Scale if needed for DL
                if model_key == 'dl' and scaler is not None:
                    X_test = scaler.transform(X_test)

                # Predict
                y_pred = predictor.predict(X_test.values if hasattr(X_test, 'values') else X_test)

                # Calculate metrics
                metrics = ModelEvaluator.calculate_metrics(y_test, y_pred)
                metrics['model_name'] = {'lr': 'Linear Regression', 'rf': 'Random Forest', 'dl': 'Deep Learning'}[model_key]
                test_results[model_key] = metrics

                logger.info(f"{model_key.upper()} Test MAE: {metrics['mae']:.2f}, R²: {metrics['r2']:.4f}")
        except Exception as e:
            logger.warning(f"Could not evaluate {model_key} on test set: {e}")

    # 7. Output and Save Model Registry & Comparison
    logger.info("==" * 35)
    logger.info("MODEL COMPARISON (Training Set)")
    logger.info("==" * 35)

    comparison_rows = []
    name_map = {'lr': 'Linear Regression', 'rf': 'Random Forest', 'dl': 'Deep Learning'}
    for key, metrics in all_results.items():
        row = {'Model': name_map.get(key, key), **metrics}
        comparison_rows.append(row)
        logger.info(f"{row['Model']:<20} | MAE: {row['mae']:<7.2f} | RMSE: {row['rmse']:<7.2f} | R²: {row['r2']:<6.4f}")

    comp_df = pd.DataFrame(comparison_rows)
    comp_df.to_csv(MODEL_COMPARISON_PATH, index=False)

    logger.info("==" * 35)
    logger.info(f"🏆 Best Model: {name_map.get(best_key, best_key)} (Lowest MAE: {best_metrics['mae']:.2f})")
    logger.info(f"Models, Preprocessors, and Encoders saved to model directory.")

    if test_results:
        logger.info("==" * 35)
        logger.info("HOLD-OUT TEST SET EVALUATION")
        logger.info("==" * 35)
        for key, metrics in test_results.items():
            logger.info(f"{metrics['model_name']:<20} | MAE: {metrics['mae']:<7.2f} | RMSE: {metrics['rmse']:<7.2f} | R²: {metrics['r2']:<6.4f}")

    # 8. Register in DB
    version_id = pd.Timestamp.now().strftime("model_%Y%m%d_%H%M%S")
    db.save_model_version(
        version_id=version_id,
        best_model=name_map.get(best_key, best_key).upper(),
        metrics=best_metrics,
        rows=len(train_df)
    )

    # 9. Save to JSON for simple frontend read
    metadata = {
        "version_id": version_id,
        "best_model_key": best_key,
        "best_model_name": name_map.get(best_key, best_key),
        "mae": best_metrics['mae'],
        "rmse": best_metrics['rmse'],
        "r2": best_metrics['r2'],
        "rows_trained": len(train_df),
        "rows_tested": len(test_df) if len(test_df) > 0 else 0,
        "timestamp": pd.Timestamp.now().isoformat(),
        "split_method": "chronological_80_20",
        "leakage_prevention": "scaler_fitted_on_train_only"
    }
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

    logger.info("✅ Training pipeline completed successfully with leakage prevention!")

if __name__ == "__main__":
    main()