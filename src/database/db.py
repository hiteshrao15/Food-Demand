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

from src.config import DATA_DIR, resolve_database_path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Schema version for migrations
SCHEMA_VERSION = 2


def get_writable_db_path() -> str:
    """Return a writable SQLite path honouring config + DEMANDWISE_DB_PATH.

    Resolves ``database.path`` from config.yaml relative to the project root
    so environment-variable overrides work and the location never contradicts
    what is documented in config.yaml / .env.example.
    """
    try:
        db_path = resolve_database_path()
    except Exception as exc:  # fail safe to the conventional location
        logger.warning(f"Falling back to default DB path (config resolve failed): {exc}")
        db_path = DATA_DIR / "demandwise.db"

    # Ensure the directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

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
            try:
                cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
            except sqlite3.IntegrityError:
                pass

        # Migration to version 2: store prediction-interval bounds + buffer for honest UI
        if current_version < 2:
            for column in (
                "ALTER TABLE predictions ADD COLUMN lower_bound REAL DEFAULT NULL",
                "ALTER TABLE predictions ADD COLUMN upper_bound REAL DEFAULT NULL",
                "ALTER TABLE predictions ADD COLUMN safety_buffer_pct REAL DEFAULT NULL",
            ):
                try:
                    cursor.execute(column)
                except sqlite3.OperationalError as e:
                    logger.warning(f"Migration step warning: {e}")
            try:
                cursor.execute("INSERT INTO schema_version (version) VALUES (2)")
            except sqlite3.IntegrityError:
                pass

    # -- Prediction History Methods --

    def save_prediction(
        self,
        date: str,
        food_item: str,
        predicted_demand: float,
        model_used: str,
        holiday: int,
        recommended_prep: int = 0,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        safety_buffer_pct: Optional[float] = None,
    ) -> bool:
        """Save a new prediction to history."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    '''INSERT INTO predictions
                       (prediction_date, food_item, predicted_demand, model_used, holiday,
                        recommended_prep, lower_bound, upper_bound, safety_buffer_pct)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (date, food_item, predicted_demand, model_used, holiday,
                     recommended_prep, lower_bound, upper_bound, safety_buffer_pct)
                )
                conn.commit()
            logger.info(f"Saved prediction for {food_item} on {date}")
            return True
        except Exception as e:
            logger.error(f"Failed to save prediction to DB: {e}", exc_info=True)
            return False

    def get_prediction_history(
        self,
        limit: int = 500,
        food_item: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "created_at",
        ascending: bool = False,
    ) -> pd.DataFrame:
        """Retrieve prediction history with useful filters/sorting.

        Args:
            limit: Max rows to return.
            food_item: Exact item name filter (or None/All for no filter).
            search: Case-insensitive substring matched against item/model/date.
            date_from/date_to: 'YYYY-MM-DD' bounds applied to prediction_date.
            sort_by: One of created_at, prediction_date, predicted_demand,
                recommended_prep, food_item.
            ascending: Sort direction.
        """
        allowed_sort = {
            "created_at", "prediction_date", "predicted_demand",
            "recommended_prep", "food_item",
        }
        if sort_by not in allowed_sort:
            sort_by = "created_at"
        direction = "ASC" if ascending else "DESC"
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM predictions WHERE 1=1"
                params: List[Any] = []
                if food_item and food_item not in ("All items", "All Items"):
                    query += " AND food_item = ?"
                    params.append(food_item)
                if date_from:
                    query += " AND date(prediction_date) >= date(?)"
                    params.append(date_from)
                if date_to:
                    query += " AND date(prediction_date) <= date(?)"
                    params.append(date_to)
                if search:
                    query += " AND (lower(food_item) LIKE ? OR lower(model_used) LIKE ? OR prediction_date LIKE ?)"
                    like = f"%{search.lower()}%"
                    params.extend([like, like, f"%{search}%"])
                query += f" ORDER BY {sort_by} {direction} LIMIT ?"
                params.append(int(limit))
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"Failed to get prediction history from DB: {e}", exc_info=True)
            return pd.DataFrame()

    def delete_prediction(self, prediction_id: int) -> bool:
        """Delete a single prediction by id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM predictions WHERE id = ?", (int(prediction_id),))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete prediction {prediction_id}: {e}", exc_info=True)
            return False

    def get_history_items(self) -> List[str]:
        """Return distinct food items present in prediction history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT food_item FROM predictions ORDER BY food_item")
                return [row[0] for row in cursor.fetchall() if row[0]]
        except Exception as e:
            logger.error(f"Failed to list history items: {e}", exc_info=True)
            return []

    def get_history_summary(self) -> Dict[str, Any]:
        """Return aggregate stats over prediction history for summary cards."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*), AVG(predicted_demand), COUNT(DISTINCT food_item) FROM predictions"
                )
                row = cursor.fetchone()
                return {
                    "count": int(row[0] or 0),
                    "avg_predicted": float(row[1]) if row[1] is not None else 0.0,
                    "distinct_items": int(row[2] or 0),
                }
        except Exception as e:
            logger.error(f"Failed to summarise history: {e}", exc_info=True)
            return {"count": 0, "avg_predicted": 0.0, "distinct_items": 0}

    def clear_prediction_history(self) -> bool:
        """Clear all prediction history."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM predictions")
                conn.commit()
            logger.info("Cleared prediction history")
            return True
        except Exception as e:
            logger.error(f"Failed to clear prediction history: {e}", exc_info=True)
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
            logger.error(f"Failed to get active model info from DB: {e}", exc_info=True)
            return None

    def get_model_history(self, limit: int = 20) -> pd.DataFrame:
        """Return model training history (newest first) for the performance page."""
        try:
            with self._get_connection() as conn:
                df = pd.read_sql_query(
                    "SELECT version_id, best_model AS model, mae AS MAE, rmse AS RMSE, "
                    "r2 AS R2, dataset_rows, trained_at, is_active "
                    "FROM model_registry ORDER BY trained_at DESC LIMIT ?",
                    conn,
                    params=(int(limit),),
                )
                return df
        except Exception as e:
            logger.error(f"Failed to get model history: {e}", exc_info=True)
            return pd.DataFrame()

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