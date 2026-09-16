"""
Explainable AI (XAI) for food demand predictions.
Provides SHAP-based explanations with proper fallback and honest labeling.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from src.config import FEATURE_COLUMNS
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Human-readable feature name mapping
FEATURE_DISPLAY_NAMES = {
    "food_item_encoded": "Food Item (Category)",
    "year": "Year",
    "month": "Month of Year",
    "day": "Day of Month",
    "day_of_week": "Day of Week",
    "is_weekend": "Weekend",
    "quarter": "Quarter",
    "week_of_year": "Week of Year",
    "holiday": "Holiday Flag",
    "demand_lag_7": "Demand from 7 Days Ago",
    "demand_lag_30": "Demand from 30 Days Ago",
    "demand_rolling_mean_7": "7-Day Rolling Average",
    "demand_rolling_mean_30": "30-Day Rolling Average",
    "demand_rolling_std_7": "7-Day Demand Std Dev",
    "demand_rolling_std_30": "30-Day Demand Std Dev",
}


class DemandExplainer:
    """
    Generates explanations for demand predictions.

    Uses SHAP (SHapley Additive exPlanations) when available for accurate
    feature attribution. Falls back to feature importance when SHAP is not
    available, clearly labeling the method used.

    CRITICAL: This class does NOT claim to provide "SHAP" values when using
    feature importance fallback. The method used is always clearly labeled.
    """

    def __init__(self, model, model_type: str = 'rf'):
        """
        Initialize the explainer.

        Args:
            model: Trained model object
            model_type: Model type ('lr', 'rf', 'dl')
        """
        self.model = model
        self.model_type = model_type
        self._shap_explainer = None
        self._has_shap = self._check_shap_available()

    def _check_shap_available(self) -> bool:
        """Check if SHAP is available and can be used with this model type."""
        try:
            import shap
            return True
        except ImportError:
            logger.info("SHAP not installed. Using feature importance fallback.")
            return False
        except Exception as e:
            logger.warning(f"SHAP import issue: {e}. Using feature importance fallback.")
            return False

    def _init_shap(self):
        """Initialize SHAP explainer with appropriate background sample."""
        if not self._has_shap:
            return

        try:
            import shap

            # Use a small background sample for efficiency
            # This ensures SHAP is both accurate and performant
            background_size = min(100, len(self._background_samples))

            if self.model_type == 'rf':
                self._shap_explainer = shap.TreeExplainer(
                    self.model,
                    feature_perturbation="interventional"
                )
            else:
                # For non-tree models, use KernelExplainer with background
                self._shap_explainer = shap.KernelExplainer(
                    self.model.predict,
                    self._background_samples[:background_size]
                )

            logger.info(f"SHAP explainer initialized for {self.model_type.upper()} model.")

        except Exception as e:
            logger.warning(f"SHAP init failed: {e}. Using feature importance fallback.")
            self._has_shap = False

    def set_background_samples(self, samples: np.ndarray):
        """
        Set background samples for SHAP KernelExplainer.

        Args:
            samples: Feature matrix for background distribution
        """
        self._background_samples = samples

    def _get_shap_values(self, features: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Get SHAP values for given features.

        Returns:
            SHAP values array or None if SHAP unavailable
        """
        if not self._has_shap or self._shap_explainer is None:
            return None

        try:
            prepared = features[FEATURE_COLUMNS]

            if self.model_type == 'rf':
                shap_values = self._shap_explainer.shap_values(prepared)
            else:
                shap_values = self._shap_explainer.shap_values(prepared)

            # Handle list output from SHAP (multi-output)
            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            return shap_values

        except Exception as e:
            logger.error(f"SHAP calculation failed: {e}")
            return None

    def explain_prediction(self, input_features: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate explanation for a single prediction.

        Args:
            input_features: DataFrame with single row of features

        Returns:
            Dict with explanation details
        """
        prepared = input_features[FEATURE_COLUMNS]

        # Try SHAP first if available
        if self._has_shap:
            shap_values = self._get_shap_values(prepared)

            if shap_values is not None:
                return self._format_shap_explanation(prepared, shap_values)

        # Fallback to feature importance
        return self._explain_with_importance(prepared)

    def _format_shap_explanation(
        self,
        features: pd.DataFrame,
        shap_values: np.ndarray
    ) -> Dict[str, Any]:
        """
        Format SHAP values into human-readable explanation.

        Args:
            features: Input features
            shap_values: Computed SHAP values

        Returns:
            Formatted explanation dict
        """
        # Handle multi-dimensional SHAP output
        if shap_values.ndim > 1:
            shap_vals = shap_values[0] if shap_values.shape[0] == 1 else shap_values
        else:
            shap_vals = shap_values

        contributions = []
        for i, col in enumerate(FEATURE_COLUMNS):
            val = float(shap_vals[i]) if i < len(shap_vals) else 0.0
            feature_val = float(features.iloc[0][col])

            contributions.append({
                "feature": FEATURE_DISPLAY_NAMES.get(col, col),
                "feature_key": col,
                "feature_value": feature_val,
                "shap_value": round(val, 4),
                "direction": "increase" if val > 0 else "decrease",
                "impact": round(abs(val), 4)
            })

        # Sort by absolute impact (SHAP)
        contributions.sort(key=lambda x: x["impact"], reverse=True)

        top_positive = [c for c in contributions if c["direction"] == "increase"][:3]
        top_negative = [c for c in contributions if c["direction"] == "decrease"][:3]

        summary = self._generate_summary(top_positive, top_negative)

        return {
            "method": "SHAP (SHapley Additive exPlanations)",
            "method_description": (
                "SHAP values represent the marginal contribution of each feature "
                "to the prediction, averaged over the background dataset. "
                "Positive values increase the prediction, negative values decrease it."
            ),
            "contributions": contributions,
            "top_positive": top_positive,
            "top_negative": top_negative,
            "summary": summary
        }

    def _explain_with_importance(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Fallback explanation using feature importance.

        CRITICAL: This method does NOT claim to provide SHAP values.
        It uses model feature importances with feature values as approximation.
        """
        try:
            # Get feature importances from model
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_)
            else:
                return {
                    "method": "Not Available",
                    "method_description": (
                        "Feature importance is not available for this model type. "
                        "Install scikit-learn and SHAP for full explainability support."
                    ),
                    "contributions": [],
                    "summary": "Explanation not available."
                }

            prepared = features[FEATURE_COLUMNS]

            # Build contributions with importance-based approximation
            # NOTE: This is NOT true SHAP - it's a global importance approximation
            contributions = []
            for i, col in enumerate(FEATURE_COLUMNS):
                importance = float(importances[i]) if i < len(importances) else 0.0
                feature_val = float(prepared.iloc[0][col])

                # Use importance * feature_value as signed contribution
                # This is a heuristic, NOT true SHAP
                contrib_val = importance * feature_val

                contributions.append({
                    "feature": FEATURE_DISPLAY_NAMES.get(col, col),
                    "feature_key": col,
                    "feature_value": feature_val,
                    "importance": round(importance, 4),
                    "approx_contrib": round(contrib_val, 4),
                    "direction": "increase" if contrib_val > 0 else "decrease",
                    "impact": round(abs(contrib_val), 4)
                })

            contributions.sort(key=lambda x: x["impact"], reverse=True)

            top_positive = [c for c in contributions if c["direction"] == "increase"][:3]
            top_negative = [c for c in contributions if c["direction"] == "decrease"][:3]

            return {
                "method": "Feature Importance Approximation",
                "method_description": (
                    "This explanation uses feature importance (model-specific) "
                    "multiplied by feature values as an approximation to SHAP values. "
                    "For accurate feature attribution, install SHAP and use the "
                    "TreeExplainer or KernelExplainer."
                ),
                "contributions": contributions,
                "top_positive": top_positive,
                "top_negative": top_negative,
                "summary": self._generate_summary(top_positive, top_negative)
            }

        except Exception as e:
            logger.error(f"Feature importance explanation failed: {e}")
            return {
                "method": "Not Available",
                "method_description": "Explanation generation failed.",
                "contributions": [],
                "summary": "Explanation not available."
            }

    @staticmethod
    def _generate_summary(positive: List[Dict], negative: List[Dict]) -> str:
        """
        Generate a natural language summary from feature contributions.

        Args:
            positive: List of positive contribution dicts
            negative: List of negative contribution dicts

        Returns:
            Human-readable summary string
        """
        parts = []

        if positive:
            factors = ", ".join([p["feature"] for p in positive[:2]])
            parts.append(
                f"Demand is expected to be higher primarily due to: {factors}."
            )

        if negative:
            factors = ", ".join([n["feature"] for n in negative[:2]])
            parts.append(
                f"Factors reducing demand include: {factors}."
            )

        if not parts:
            return (
                "The prediction is based on historical demand patterns and current "
                "conditions. Check individual feature contributions for details."
            )

        return " ".join(parts)

    def get_feature_rankings(self) -> List[Dict[str, Any]]:
        """
        Get feature importance rankings from the trained model.

        Returns:
            List of features sorted by importance
        """
        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
            elif hasattr(self.model, 'coef_'):
                importances = np.abs(self.model.coef_)
            else:
                return []

            rankings = []
            for i, col in enumerate(FEATURE_COLUMNS):
                if i < len(importances):
                    rankings.append({
                        "feature": FEATURE_DISPLAY_NAMES.get(col, col),
                        "feature_key": col,
                        "importance": float(importances[i]),
                        "rank": i + 1
                    })

            rankings.sort(key=lambda x: x["importance"], reverse=True)

            # Recalculate ranks after sorting
            for i, r in enumerate(rankings):
                r["rank"] = i + 1

            return rankings

        except Exception as e:
            logger.error(f"Failed to get feature rankings: {e}")
            return []