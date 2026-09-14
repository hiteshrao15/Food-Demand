"""
SQLite database manager for DemandWise.
Handles prediction history and model registry with persistent storage.
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Any
from pathlib import Path
import os
import json

from src.config import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Schema version for migrations
SCHEMA_VERSION = 1

def get_writable_db_path() -> str:
    """Returns a writable path for SQLite database, using configured data directory."""
    # Use the configured data directory from config.yaml
    db_path = DATA_DIR / "demandwise.db"

    # Ensure the directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return str(db_path)


class DatabaseManager:
    """Manages local SQLite database for settings, prediction history, and dataset metadata."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_writable_db_path()
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_db(self):
        """Create tables if they do not exist and handle schema migrations."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create schema_version table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Check current schema version
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                current_version = result[0] if result[0] is not None else 0

                # Apply migrations if needed
                if current_version < SCHEMA_VERSION:
                    self._apply_migrations(cursor, current_version)
                    conn.commit()

                # Create tables if they don't exist (idempotent)

                # Table for prediction history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prediction_date TEXT NOT NULL,
                        food_item TEXT NOT NULL,
                        actual_date TEXT,
                        predicted_demand REAL NOT NULL,
                        model_used TEXT NOT NULL,
                        holiday INTEGER NOT NULL,
                        recommended_prep INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Table for model registry/history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS model_registry (
                        version_id TEXT PRIMARY KEY,
                        model_types TEXT NOT NULL,
                        best_model TEXT NOT NULL,
                        mae REAL,
                        rmse REAL,
                        r2 REAL,
                        trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        dataset_rows INTEGER,
                        is_active INTEGER DEFAULT 0
                    )
                ''')

                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_predictions_date
                    ON predictions(prediction_date)
                ''')

                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_predictions_food_item
                    ON predictions(food_item)
                ''')

                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_predictions_created_at
                    ON predictions(created_at DESC)
                ''')

                logger.info(f"Database initialized successfully at '{self.db_path}'.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise e

    def _apply_migrations(self, cursor, current_version: int):
        """Apply database schema migrations."""
        logger.info(f"Applying database migrations from version {current_version} to {SCHEMA_VERSION}")

        # Migration from version 0 to 1: Add recommended_prep column
        if current_version < 1:
            try:
                cursor.execute("ALTER TABLE predictions ADD COLUMN recommended_prep INTEGER DEFAULT 0")
                logger.info("Added recommended_prep column to predictions table")
            except sqlite3.OperationalError as e:
                # Column might already exist
                logger.warning(f"Migration step warning: {e}")

            # Record that we applied migration version 1
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")

    # -- Prediction History Methods --

    def save_prediction(self, date: str, food_item: str, predicted_demand: float, model_used: str, holiday: int, recommended_prep: int = 0) -> bool:
        """Save a new prediction to history."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    '''INSERT INTO predictions (prediction_date, food_item, predicted_demand, model_used, holiday, recommended_prep)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (date, food_item, predicted_demand, model_used, holiday, recommended_prep)
                )
                conn.commit()
            logger.info(f"Saved prediction for {food_item} on {date}")
            return True
        except Exception as e:
            logger.error(f"Failed to save prediction to DB: {e}")
            return False

    def get_prediction_history(self, limit: int = 100) -> pd.DataFrame:
        """Retrieve recent prediction history as a DataFrame."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM predictions ORDER BY created_at DESC LIMIT ?"
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
        except Exception as e:
            logger.error(f"Failed to get prediction history from DB: {e}")
            return pd.DataFrame()

    def clear_prediction_history(self) -> bool:
        """Clear all prediction history."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM predictions")
                conn.commit()
            return True
        except Exception:
            return False

    # -- Model Registry Methods --

    def save_model_version(self, version_id: str, best_model: str, metrics: Dict[str, float], rows: int = 0) -> bool:
        """Log a newly trained model version and set it as active."""
        try:
            with self._get_connection() as conn:
                # Deactivate all current versions
                conn.execute("UPDATE model_registry SET is_active = 0")

                # Insert new active version
                conn.execute(
                    '''INSERT INTO model_registry (version_id, model_types, best_model, mae, rmse, r2, dataset_rows, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
                    (version_id, "lr,rf,dl", best_model,
                     metrics.get('mae', 0.0), metrics.get('rmse', 0.0), metrics.get('r2', 0.0), rows)
                )
                conn.commit()
            logger.info(f"Saved model version {version_id} with best model {best_model}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model version to DB: {e}")
            return False

    def get_active_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active model."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM model_registry WHERE is_active = 1 LIMIT 1")
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get active model info from DB: {e}")
            return None

    def cleanup_old_predictions(self, retention_days: int = 365) -> int:
        """Remove prediction records older than retention_days."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """DELETE FROM predictions
                       WHERE datetime(created_at) < datetime('now', '-' || ? || ' days')""",
                    (retention_days,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old prediction records")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old predictions: {e}")
            return 0