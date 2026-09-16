"""DemandWise shared application state.

Single source of truth for the *active dataset*, database handle, predictor
cache and sample-mode flag so Forecast, Analytics, Data Management, Model
Performance, Explainability, History and Settings stay coherent.

Design notes
------------
- The active dataset is persisted to the configured dataset path
  (``data.dataset_path`` honoured via :func:`src.config.resolve_dataset_path`)
  so uploads survive restarts and every page reads the same rows.
- ``sample_mode`` is an explicit, clearly-labelled fallback: True when the
  rows in use are the built-in generated demo (or the shipped demo file that
  has never been replaced by a user upload). It is never mixed with user data
  silently — every page shows a banner with the source.
- Streamlit caches are invalidated through ``dataset_version``: activating a
  dataset bumps the version and clears ``st.cache_data`` / ``st.cache_resource``
  so stale frames and predictors cannot linger.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src.config import MODELS_DIR, get_config, resolve_dataset_path
from src.data.loader import DataLoader, DataValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)

SAMPLE_SOURCE_LABEL = "Sample data (built-in demo)"
FILE_SOURCE_LABEL = "Active file dataset"
UPLOADED_SOURCE_LABEL = "Uploaded dataset"


def _session() -> Dict[str, Any]:
    """Access streamlit session state safely outside a Streamlit runtime."""
    try:
        return st.session_state
    except Exception:  # pragma: no cover - non-Streamlit (tests)
        return {}


def init_state_defaults() -> None:
    """Ensure all shared session keys exist with safe defaults."""
    session = _session()
    defaults = {
        "dataset_version": 0,
        "dataset_source": "file",  # file | sample | uploaded
        "sample_mode": False,
        "active_df": None,
        "selected_model": get_config()["models"].get("default", "rf"),
        "safety_buffer_pct": float(get_config()["prediction"].get("safety_buffer", 10)),
        "forecast_horizon": 1,
        "org_name": "My Restaurant",
    }
    for key, value in defaults.items():
        if key not in session:
            try:
                session[key] = value
            except Exception:
                pass


def get_dataset_version() -> int:
    try:
        return int(st.session_state.get("dataset_version", 0))
    except Exception:
        return 0


def is_sample_mode() -> bool:
    try:
        return bool(st.session_state.get("sample_mode", False))
    except Exception:
        return False


def get_dataset_source_label() -> str:
    try:
        source = st.session_state.get("dataset_source", "file")
    except Exception:
        source = "file"
    if source == "sample":
        return SAMPLE_SOURCE_LABEL
    if source == "uploaded":
        return UPLOADED_SOURCE_LABEL
    return FILE_SOURCE_LABEL


def bump_dataset_version() -> int:
    """Increment the dataset version and clear Streamlit caches."""
    try:
        st.session_state["dataset_version"] = get_dataset_version() + 1
        version = st.session_state["dataset_version"]
    except Exception:
        version = 0
    clear_caches()
    return version


def clear_caches() -> None:
    """Safely invalidate Streamlit caches after activation/retraining."""
    for clearer in ("cache_data", "cache_resource"):
        try:
            getattr(st, clearer).clear()
        except Exception as exc:  # e.g. outside runtime
            logger.debug(f"Could not clear {clearer}: {exc}")


def normalize_upload(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise user-supplied frames to the canonical schema.

    Accepts friendly variants (``is_holiday``/``isHoliday``, boolean holiday
    flags, string dates) and coerces them. Raises ValueError with an
    actionable message when the frame cannot be salvaged.
    """
    if df is None or df.empty:
        raise ValueError("The uploaded file contains no data rows.")
    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]
    rename_map = {}
    lowered = {c.lower(): c for c in work.columns}
    if "holiday" not in work.columns:
        for alias in ("is_holiday", "isholiday", "is-holiday", "holiday_flag"):
            if alias in lowered:
                rename_map[lowered[alias]] = "holiday"
                break
    if rename_map:
        work = work.rename(columns=rename_map)
    # Friendly column aliases
    for canonical, aliases in {
        "date": ("ds", "order_date", "datetime"),
        "food_item": ("item", "food", "product", "dish", "menu_item"),
        "demand": ("orders", "quantity", "qty", "sales", "units"),
    }.items():
        if canonical not in work.columns:
            for alias in aliases:
                if alias in lowered:
                    work = work.rename(columns={lowered[alias]: canonical})
                    break
    # Coerce holiday booleans / Yes-No strings
    if "holiday" in work.columns:
        work["holiday"] = work["holiday"].map(
            lambda v: 1 if str(v).strip().lower() in ("1", "true", "t", "yes", "y") else (
                0 if str(v).strip().lower() in ("0", "false", "f", "no", "n", "nan", "") else v
            )
        )
    try:
        work["date"] = pd.to_datetime(work["date"])
        work["demand"] = pd.to_numeric(work["demand"], errors="coerce")
        work["holiday"] = pd.to_numeric(work["holiday"], errors="coerce").fillna(0).astype(int)
        work["food_item"] = work["food_item"].astype(str).str.strip()
    except KeyError as exc:
        raise ValueError(f"Missing required column after normalisation: {exc}") from exc
    work = work.dropna(subset=["date", "food_item", "demand"])
    work = work.sort_values(["food_item", "date"]).reset_index(drop=True)
    return work


def validate_upload(df: pd.DataFrame, min_history_days: int = 30) -> Tuple[bool, List[str], List[str]]:
    """Validate an upload, returning (ok, errors, warnings) with friendly text."""
    errors: List[str] = []
    warnings: List[str] = []
    ok, validator_errors = DataValidator.validate_dataframe(df)
    errors.extend(validator_errors)
    if df is not None and not df.empty and "date" in df.columns:
        try:
            dates = pd.to_datetime(df["date"])
            span_days = (dates.max() - dates.min()).days + 1
            if span_days < min_history_days:
                warnings.append(
                    f"Only {span_days} day(s) of history found; "
                    f"at least {min_history_days} days are recommended for reliable forecasts. "
                    "You can still activate, but intervals will be wider."
                )
            if dates.duplicated().any():
                warnings.append("Duplicate date/item rows detected; the latest upload keeps all rows as provided.")
        except Exception as exc:
            logger.warning(f"Could not assess history span: {exc}")
    if df is not None and "food_item" in df.columns:
        n_items = df["food_item"].nunique()
        if n_items < 1:
            errors.append("No food items found in the 'food_item' column.")
    return (len(errors) == 0, errors, warnings)


@st.cache_data(show_spinner=False)
def _load_dataset_from_disk(_version: int, path_str: str) -> Optional[pd.DataFrame]:
    """Cached disk load keyed by dataset version (invalidated on activation)."""
    path = Path(path_str)
    if not path.exists():
        logger.info(f"Dataset file {path} missing — caller will use sample fallback.")
        return None
    try:
        df = DataLoader.load_csv(str(path))
        if df is not None:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values(["food_item", "date"]).reset_index(drop=True)
        return df
    except Exception as exc:
        logger.error(f"Failed to load dataset from {path}: {exc}", exc_info=True)
        return None


def load_active_dataset() -> Tuple[Optional[pd.DataFrame], str, bool]:
    """Load the active dataset for display/prediction.

    Returns (df, source_label, is_sample). Prefers an in-memory activated
    frame, then the configured file, then an explicitly-labelled generated
    sample fallback. Never raises — callers render empty states instead.
    """
    init_state_defaults()
    session = _session()
    active = session.get("active_df") if isinstance(session, dict) or hasattr(session, "get") else None
    try:
        active = st.session_state.get("active_df")
    except Exception:
        pass
    if active is not None and not active.empty:
        try:
            label = get_dataset_source_label()
            return active, label, is_sample_mode()
        except Exception:
            pass
    try:
        dataset_path = resolve_dataset_path()
    except Exception as exc:
        logger.error(f"Could not resolve dataset path: {exc}", exc_info=True)
        dataset_path = Path("data/food_demand_data.csv")
    df = _load_dataset_from_disk(get_dataset_version(), str(dataset_path))
    if df is not None and not df.empty:
        # File-backed data that was never explicitly uploaded is still demo
        # on a clean checkout — label it honestly as sample until replaced.
        try:
            source = st.session_state.get("dataset_source", "file")
            sample = bool(st.session_state.get("sample_mode", source == "file" and _looks_like_shipped_demo(df)))
        except Exception:
            sample = False
        label = get_dataset_source_label() if not sample else SAMPLE_SOURCE_LABEL + " (shipped file)"
        return df, label, sample
    # Explicit sample fallback — clearly labelled, never mixed silently.
    try:
        demo = DataLoader.generate_demo_dataset()
        demo["date"] = pd.to_datetime(demo["date"])
        return demo, SAMPLE_SOURCE_LABEL, True
    except Exception as exc:
        logger.error(f"Sample fallback generation failed: {exc}", exc_info=True)
        return None, "No data available", True


def _looks_like_shipped_demo(df: pd.DataFrame) -> bool:
    """Heuristic: shipped demo covers 2024-01-01..2025-12-31 with 8 default items."""
    try:
        items = set(df["food_item"].unique())
        default = {"Pizza", "Burger", "Pasta", "Salad", "Sandwich", "Rice Bowl", "Noodles", "Soup"}
        return items == default and str(pd.to_datetime(df["date"]).min().date()) == "2024-01-01"
    except Exception:
        return False


def activate_dataset(df: pd.DataFrame, source: str = "uploaded") -> Tuple[bool, str]:
    """Persist an uploaded/sample frame as the active dataset everywhere.

    Writes to the configured dataset path, updates session state, bumps the
    version (clearing caches) and returns (success, message).
    """
    try:
        clean = normalize_upload(df)
    except ValueError as exc:
        return False, str(exc)
    ok, errors, _warnings = validate_upload(clean)
    if not ok:
        return False, "Dataset failed validation: " + "; ".join(errors)
    try:
        dataset_path = resolve_dataset_path()
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        clean.to_csv(dataset_path, index=False)
    except Exception as exc:
        logger.error(f"Failed to persist activated dataset: {exc}", exc_info=True)
        return False, f"Could not save dataset file: {exc}"
    try:
        st.session_state["active_df"] = clean
        st.session_state["dataset_source"] = source
        st.session_state["sample_mode"] = (source == "sample")
    except Exception as exc:
        logger.warning(f"Could not update session state on activation: {exc}")
    bump_dataset_version()
    # Re-read through cache so all pages converge on identical rows.
    try:
        st.session_state["active_df"] = clean
    except Exception:
        pass
    label = "Sample dataset" if source == "sample" else "Dataset"
    return True, f"{label} activated: {len(clean)} records across {clean['food_item'].nunique()} items."


def use_sample_dataset() -> Tuple[bool, str]:
    """Activate the built-in generated demo as an explicit sample mode."""
    try:
        demo = DataLoader.generate_demo_dataset()
        return activate_dataset(demo, source="sample")
    except Exception as exc:
        logger.error(f"Could not activate sample dataset: {exc}", exc_info=True)
        return False, f"Could not load sample data: {exc}"


def get_database():
    """Return a DatabaseManager honouring the configured DB path."""
    from src.database.db import DatabaseManager

    try:
        return DatabaseManager()
    except Exception as exc:
        logger.error(f"Database unavailable: {exc}", exc_info=True)
        return None


def get_predictor(model_type: Optional[str] = None):
    """Return a ready DemandPredictor or None (model-unavailable state)."""
    from src.ml.predictor import DemandPredictor

    try:
        code = model_type or st.session_state.get("selected_model", "rf")
    except Exception:
        code = model_type or "rf"
    try:
        predictor = DemandPredictor(model_type=code)
        if predictor.is_ready():
            return predictor
        logger.warning(f"Predictor '{code}' is not ready (missing artifacts).")
        return None
    except Exception as exc:
        logger.error(f"Predictor load failed for '{code}': {exc}", exc_info=True)
        return None


def get_model_metadata() -> Dict[str, Any]:
    """Read real model metadata written by training; {} when unavailable."""
    path = MODELS_DIR / "model_metadata.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning(f"Could not read model metadata: {exc}")
        return {}


def get_model_comparison() -> pd.DataFrame:
    """Read the real model comparison table; empty frame when unavailable."""
    path = MODELS_DIR / "model_comparison.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        logger.warning(f"Could not read model comparison CSV: {exc}")
        return pd.DataFrame()


def dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute honest summary stats for banners and settings pages."""
    if df is None or df.empty:
        return {"records": 0, "items": 0, "min_date": None, "max_date": None, "span_days": 0}
    try:
        dates = pd.to_datetime(df["date"])
        return {
            "records": int(len(df)),
            "items": int(df["food_item"].nunique()),
            "min_date": dates.min().date(),
            "max_date": dates.max().date(),
            "span_days": int((dates.max() - dates.min()).days + 1),
        }
    except Exception as exc:
        logger.warning(f"Could not summarise dataset: {exc}")
        return {"records": int(len(df)), "items": 0, "min_date": None, "max_date": None, "span_days": 0}


def sample_banner_html() -> str:
    """HTML banner describing the active data source (sample vs operational)."""
    df, label, is_sample = load_active_dataset()
    summary = dataset_summary(df) if df is not None else {"records": 0, "items": 0}
    if is_sample:
        return (
            "<div style='background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);"
            "border-radius:10px;padding:.7rem 1rem;margin-bottom:1rem;font-size:.85rem;'>"
            "⚠️ <b>Sample mode</b> — showing built-in demo data "
            f"({summary['records']} records). Upload &amp; activate your data in "
            "<b>Data</b> to replace it. Sample rows are never mixed with operational data."
            "</div>"
        )
    date_range = ""
    if summary.get("min_date") and summary.get("max_date"):
        date_range = f" • {summary['min_date']} → {summary['max_date']}"
    return (
        "<div style='background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.35);"
        "border-radius:10px;padding:.7rem 1rem;margin-bottom:1rem;font-size:.85rem;'>"
        f"✓ <b>{label}</b> — {summary['records']} records across {summary['items']} items{date_range}."
        "</div>"
    )


def render_data_source_banner() -> None:
    """Streamlit banner: always label sample vs operational data."""
    st.markdown(sample_banner_html(), unsafe_allow_html=True)


def describe_interval(result: Dict[str, Any]) -> str:
    """Honest one-line description of a prediction interval method."""
    method = str(result.get("uncertainty_method") or result.get("interval_method") or "")
    if "backtest residuals" in method or "Empirical" in method:
        return "95% prediction interval from backtest residuals (uncertainty, not accuracy)."
    return "Approximate 95% interval (backtest residuals unavailable) — uncertainty, not accuracy."


def trained_display(metadata: Dict[str, Any]) -> str:
    """Human 'last retrained' text from real metadata, or an honest fallback."""
    ts = metadata.get("timestamp") if metadata else None
    if not ts:
        return "Training date unknown"
    try:
        trained = datetime.fromisoformat(str(ts).replace("Z", ""))
        delta = datetime.now() - trained
        if delta.days <= 0:
            return "Trained today"
        if delta.days == 1:
            return "Trained yesterday"
        return f"Trained {delta.days} days ago ({trained.strftime('%Y-%m-%d')})"
    except Exception:
        return f"Trained {ts}"
