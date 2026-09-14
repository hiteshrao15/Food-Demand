"""
DemandWise - Advanced Utility Functions
Robust helpers for mathematical, statistical, formatting, and file operations.
"""
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import json
import pandas as pd
import numpy as np

def format_number(val: Any) -> str:
    """Format numerical values cleanly for UI presentation."""
    if val is None:
        return "N/A"
    try:
        if isinstance(val, (int, float)):
            if np.isnan(val):
                return "N/A"
            if val >= 1_000_000:
                return f"{val/1_000_000:.1f}M"
            if val >= 10_000:
                return f"{val/1_000:.1f}k"
            if isinstance(val, float):
                return f"{val:.1f}"
            return f"{int(val):,}"
    except (ValueError, TypeError):
        pass
    return str(val)

def ensure_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float with reliable fallback."""
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def calculate_safety_buffer(predicted_demand: float, buffer_percentage: float = 0.10) -> Dict[str, int]:
    """
    Calculate optimal preparation buffer to minimize waste while preventing stockouts.
    Returns recommended prep quantity and safe upper/lower bounds.
    """
    base = max(0.0, float(predicted_demand))

    # Handle int/float passed as e.g. 10 instead of 0.10
    if buffer_percentage > 1.0:
        buffer_percentage = buffer_percentage / 100.0

    safety_stock = base * buffer_percentage
    return {
        'recommended_prep': int(np.ceil(base + safety_stock)),
        'lower_bound_95': int(max(0, np.floor(base - (1.96 * np.sqrt(max(1.0, base)))))),
        'upper_bound_95': int(np.ceil(base + (1.96 * np.sqrt(max(1.0, base))))),
        'safety_units': int(np.ceil(safety_stock))
    }

def get_day_name(d: Any) -> str:
    """Get day of week name from string or date object."""
    try:
        if isinstance(d, str):
            d = pd.to_datetime(d)
        return d.strftime('%A')
    except Exception:
        return "Unknown"

def dict_to_json(data: Dict, filepath: str) -> bool:
    """Save dictionary to a structured JSON file safely."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=str)
        return True
    except Exception:
        return False

def json_to_dict(filepath: str) -> Dict:
    """Load JSON file into a dictionary safely."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
