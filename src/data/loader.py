import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from src.config import REQUIRED_COLUMNS, DEFAULT_FOOD_ITEMS
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """Validates food demand datasets against application requirements."""

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate if a DataFrame meets all requirements for demand prediction."""
        errors = []

        if df is None or df.empty:
            return False, ["Dataset is empty or could not be read."]

        # 1. Check required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return False, errors  # Stop here if columns are missing

        # 2. Check for null values in critical columns
        for col in REQUIRED_COLUMNS:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} missing values.")

        # 3. Validate Date column
        try:
            pd.to_datetime(df['date'])
        except Exception:
            errors.append("Column 'date' contains invalid date formats (use YYYY-MM-DD).")

        # 4. Validate Demand column
        if not pd.api.types.is_numeric_dtype(df['demand']):
            errors.append("Column 'demand' must be numeric.")
        elif df['demand'].min() < 0:
            errors.append("Column 'demand' cannot contain negative values.")

        # 5. Validate Holiday column
        if not pd.api.types.is_numeric_dtype(df['holiday']):
            errors.append("Column 'holiday' must be numeric (0 or 1).")
        else:
            invalid_holidays = df[~df['holiday'].isin([0, 1])]
            if not invalid_holidays.empty:
                errors.append("Column 'holiday' must contain only 0 (no) or 1 (yes).")

        return len(errors) == 0, errors

class DataLoader:
    """Handles dataset generation, loading, and initial formatting."""

    @staticmethod
    def generate_demo_dataset(start_date: str = '2024-01-01', end_date: str = '2025-12-31') -> pd.DataFrame:
        """Generates realistic demo dataset mathematically identical to the notebook."""
        np.random.seed(42)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        data = []
        for date in date_range:
            for food in DEFAULT_FOOD_ITEMS:
                # Base demand varies by food item
                base_demand = {'Pizza': 80, 'Burger': 100, 'Pasta': 70, 'Salad': 50,
                              'Sandwich': 90, 'Rice Bowl': 85, 'Noodles': 75, 'Soup': 40}[food]

                # Weekend boost
                weekend_boost = 1.3 if date.dayofweek >= 5 else 1.0

                # Holiday boost (simulate holidays)
                is_holiday = 1 if (date.month == 12 and date.day >= 20) or \
                                 (date.month == 1 and date.day <= 5) or \
                                 (date.month == 7 and date.day <= 7) else 0
                holiday_boost = 1.5 if is_holiday else 1.0

                # Day of week effect
                day_effect = [0.9, 0.95, 1.0, 1.05, 1.15, 1.3, 1.2][date.dayofweek]

                # Calculate demand with randomness
                demand = int(base_demand * weekend_boost * holiday_boost * day_effect *
                            np.random.uniform(0.8, 1.2))

                data.append({
                    'date': date,
                    'food_item': food,
                    'demand': demand,
                    'holiday': is_holiday
                })
        logger.info(f"Generated demo dataset with {len(data)} rows.")
        return pd.DataFrame(data)

    @staticmethod
    def load_csv(filepath: str | Path) -> Optional[pd.DataFrame]:
        """Loads and coerces CSV to proper formats."""
        try:
            df = pd.read_csv(filepath)
            df['date'] = pd.to_datetime(df['date'])
            df['demand'] = pd.to_numeric(df['demand'], errors='coerce')
            df['holiday'] = pd.to_numeric(df['holiday'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV from {filepath}: {e}")
            return None
