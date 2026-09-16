"""Train DemandWise models without data leakage.

Generates (or reuses) the historical dataset, engineers time-series-safe
features, then delegates to :class:`src.ml.retrainer.ModelRetrainer` which
performs a chronological split, fits the scaler on training data only, trains
lr/rf/dl models, fits the empirical uncertainty estimator and writes all
artifacts + metadata.
"""
import sys
from pathlib import Path

# Ensure project root is importable when run as a script.
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from src.config import DEFAULT_DATASET_PATH, resolve_dataset_path
from src.data.loader import DataLoader
from src.data.preprocessor import FeatureEngineer
from src.database.db import DatabaseManager
from src.ml.retrainer import ModelRetrainer
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main(dataset_path: str | Path | None = None) -> None:
    logger.info("Starting model training pipeline with leakage prevention...")
    db = DatabaseManager()

    target = Path(dataset_path) if dataset_path else resolve_dataset_path()
    if target.exists():
        logger.info(f"Loading existing dataset from {target} ...")
        df = DataLoader.load_csv(str(target))
        if df is None or df.empty:
            logger.warning("Existing dataset unreadable — regenerating demo data.")
            df = DataLoader.generate_demo_dataset(start_date="2024-01-01", end_date="2025-12-31")
            target.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(target, index=False)
    else:
        logger.info("Generating demo dataset ...")
        df = DataLoader.generate_demo_dataset(start_date="2024-01-01", end_date="2025-12-31")
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False)
    logger.info(f"Dataset ready: {len(df)} rows at {target}.")

    logger.info("Applying time-series-safe feature engineering (no leakage)...")
    df_engineered, label_encoder = FeatureEngineer.create_features(df)
    scaler = FeatureEngineer.get_scaler()

    logger.info("Training ML models with chronological validation...")
    best_key, best_metrics, _all_results = ModelRetrainer.retrain_and_save(
        df_engineered, label_encoder, scaler
    )

    name_map = {"lr": "Linear Regression", "rf": "Random Forest", "dl": "Deep Learning"}
    logger.info(f"Best model: {name_map.get(best_key, best_key)} (MAE: {best_metrics['mae']:.2f})")

    version_id = pd.Timestamp.now().strftime("model_%Y%m%d_%H%M%S")
    try:
        db.save_model_version(
            version_id=version_id,
            best_model=name_map.get(best_key, best_key),
            metrics=best_metrics,
            rows=int(len(df_engineered)),
        )
    except Exception as exc:
        logger.warning(f"Could not register model version in DB: {exc}")

    # Keep the legacy top-level path import working for any external callers.
    _ = DEFAULT_DATASET_PATH
    logger.info("Training pipeline completed successfully with leakage prevention!")


if __name__ == "__main__":
    main()
