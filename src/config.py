"""
Configuration module for Food Demand Prediction Platform (DemandWise).
Centralizes all paths, constants, and hyperparameters.
Now serves as the single source of truth, reading from config.yaml and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.yaml"

# Load configuration from YAML file
def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable overrides."""
    default_config = {
        'app': {
            'name': 'DemandWise',
            'version': '1.2.0',
            'tagline': 'Predict demand. Reduce waste. Prepare smarter.',
            'debug': False
        },
        'ui': {
            'theme': 'auto',
            'sidebar_collapsed': False,
            'wide_mode': True,
            'show_developer_options': False
        },
        'data': {
            'dataset_path': 'data/food_demand_data.csv',
            'template_path': 'data/food_demand_template.csv',
            'min_history_days': 30,
            'recommended_history_days': 365,
            'auto_save_predictions': True,
            'allow_negative_demand': False,
            'require_holiday_column': True
        },
        'models': {
            'default': 'rf',
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 15,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42
            },
            'linear_regression': {
                'fit_intercept': True,
                'normalize': False
            },
            'deep_learning': {
                'epochs': 50,
                'batch_size': 32,
                'learning_rate': 0.001,
                'hidden_layers': [64, 32],
                'dropout': 0.2
            },
            'training': {
                'test_split_size': 0.2,
                'validation_split': 0.1,
                'random_state': 42
            },
            'retraining': {
                'auto_retrain': False,
                'retrain_interval_days': 90
            }
        },
        'prediction': {
            'confidence_percentage': 10,
            'safety_buffer': 10,
            'max_horizon_days': 365,
            'auto_save': True
        },
        'explainability': {
            'method': 'shap',
            'top_factors': 5,
            'show_technical_details': True,
            'cache_explainer': True
        },
        'analytics': {
            'default_date_range_days': 90,
            'default_chart_height': 400,
            'show_trend_lines': True,
            'enable_animations': True,
            'frequencies': ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']
        },
        'database': {
            'path': 'data/demandwise.db',
            'retention_days': 365,
            'auto_cleanup': True
        },
        'logging': {
            'level': 'INFO',
            'path': 'logs/app.log',
            'max_bytes': 10485760,
            'backup_count': 5,
            'console_output': True
        },
        'performance': {
            'enable_data_cache': True,
            'cache_ttl': 3600,
            'enable_parallel': False,
            'memory_limit_mb': 2048
        },
        'experimental': {
            'batch_predictions': False,
            'api_server': False,
            'multi_location': False
        }
    }

    # Load from file if exists
    config = default_config.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Deep merge file config into defaults
                    def deep_merge(base, update):
                        for key, value in update.items():
                            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                                deep_merge(base[key], value)
                            else:
                                base[key] = value
                        return base

                    config = deep_merge(config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")

    # Apply environment variable overrides
    env_mappings = {
        'DEMANDWISE_DEBUG': ('app', 'debug', bool),
        'DEMANDWISE_DATASET_PATH': ('data', 'dataset_path', str),
        'DEMANDWISE_DB_PATH': ('database', 'path', str),
        'DEMANDWISE_LOG_LEVEL': ('logging', 'level', str),
        'DEMANDWISE_MODEL_TYPE': ('models', 'default', str),
        'DEMANDWISE_SAFETY_BUFFER': ('prediction', 'safety_buffer', int),
        'DEMANDWISE_MAX_HORIZON': ('prediction', 'max_horizon_days', int),
    }

    for env_var, (section, key, cast_type) in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            try:
                if cast_type == bool:
                    config[section][key] = value.lower() in ('true', '1', 'yes', 'on')
                elif cast_type == int:
                    config[section][key] = int(value)
                else:
                    config[section][key] = value
            except (ValueError, KeyError):
                pass  # Keep default if conversion fails

    return config

# Load configuration once
_CONFIG = load_config()

# Convenience accessors for backwards compatibility
def get_config() -> Dict[str, Any]:
    """Get the full configuration dictionary."""
    return _CONFIG.copy()

def get_app_config() -> Dict[str, Any]:
    """Get application configuration."""
    return _CONFIG['app']

def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration."""
    return _CONFIG['ui']

def get_data_config() -> Dict[str, Any]:
    """Get data configuration."""
    return _CONFIG['data']

def get_models_config() -> Dict[str, Any]:
    """Get models configuration."""
    return _CONFIG['models']

def get_prediction_config() -> Dict[str, Any]:
    """Get prediction configuration."""
    return _CONFIG['prediction']

def get_explainability_config() -> Dict[str, Any]:
    """Get explainability configuration."""
    return _CONFIG['explainability']

def get_analytics_config() -> Dict[str, Any]:
    """Get analytics configuration."""
    return _CONFIG['analytics']

def get_database_config() -> Dict[str, Any]:
    """Get database configuration."""
    return _CONFIG['database']

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return _CONFIG['logging']

def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration."""
    return _CONFIG['performance']

def get_experimental_config() -> Dict[str, Any]:
    """Get experimental configuration."""
    return _CONFIG['experimental']

# Base directories (keeping for backwards compatibility)
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)


def _resolve_relative_to_base(configured_path: Union[str, Path]) -> Path:
    """Resolve a configured path relative to the project base directory.

    Config values such as ``data/food_demand_data.csv`` are relative to the
    repository root (BASE_DIR), not to DATA_DIR. Earlier code joined them onto
    DATA_DIR which produced ``data/data/...`` contradictions. Absolute paths
    and ``~`` are honoured as-is so environment-variable overrides keep working.
    """
    p = Path(configured_path).expanduser()
    if p.is_absolute():
        return p
    return BASE_DIR / p


def resolve_dataset_path(config_dict: Optional[Dict[str, Any]] = None) -> Path:
    """Return the active dataset path honouring config + env overrides."""
    cfg = config_dict if config_dict is not None else _CONFIG
    return _resolve_relative_to_base(cfg['data']['dataset_path'])


def resolve_template_path(config_dict: Optional[Dict[str, Any]] = None) -> Path:
    """Return the CSV template path honouring config + env overrides."""
    cfg = config_dict if config_dict is not None else _CONFIG
    return _resolve_relative_to_base(cfg['data'].get('template_path', 'data/food_demand_template.csv'))


def resolve_database_path(config_dict: Optional[Dict[str, Any]] = None) -> Path:
    """Return the SQLite path honouring config + DEMANDWISE_DB_PATH override."""
    cfg = config_dict if config_dict is not None else _CONFIG
    return _resolve_relative_to_base(cfg['database']['path'])


def reload_config() -> Dict[str, Any]:
    """Reload configuration from disk + environment (useful for tests)."""
    global _CONFIG
    _CONFIG = load_config()
    return get_config()

# File Paths (from config — resolved relative to BASE_DIR, not DATA_DIR)
DEFAULT_DATASET_PATH = _resolve_relative_to_base(_CONFIG['data']['dataset_path'])
SAMPLE_TEMPLATE_PATH = _resolve_relative_to_base(_CONFIG['data']['template_path'])
DATABASE_PATH = _resolve_relative_to_base(_CONFIG['database']['path'])
MODEL_COMPARISON_PATH = MODELS_DIR / "model_comparison.csv"
METADATA_PATH = MODELS_DIR / "model_metadata.json"

# App Branding (from config)
APP_NAME = _CONFIG['app']['name']
APP_TAGLINE = _CONFIG['app']['tagline']
APP_VERSION = _CONFIG['app']['version']

# Target & Feature Specifications
TARGET_COLUMN = "demand"
REQUIRED_COLUMNS = ["date", "food_item", "demand", "holiday"]

# Feature columns - updated to include std features
FEATURE_COLUMNS = [
    "food_item_encoded",
    "year",
    "month",
    "day",
    "day_of_week",
    "is_weekend",
    "quarter",
    "week_of_year",
    "holiday",
    "demand_lag_7",
    "demand_lag_30",
    "demand_rolling_mean_7",
    "demand_rolling_mean_30",
    "demand_rolling_std_7",
    "demand_rolling_std_30"
]

DEFAULT_FOOD_ITEMS = [
    "Pizza",
    "Burger",
    "Pasta",
    "Salad",
    "Sandwich",
    "Rice Bowl",
    "Noodles",
    "Soup"
]

# Model Parameters
RANDOM_STATE = _CONFIG['models']['training']['random_state']
TEST_SPLIT_SIZE = _CONFIG['models']['training']['test_split_size']
RF_N_ESTIMATORS = _CONFIG['models']['random_forest']['n_estimators']
RF_MAX_DEPTH = _CONFIG['models']['random_forest']['max_depth']
DL_EPOCHS = _CONFIG['models']['deep_learning']['epochs']
DL_BATCH_SIZE = _CONFIG['models']['deep_learning']['batch_size']

# Prediction settings
DEFAULT_CONFIDENCE_PERCENTAGE = _CONFIG['prediction']['confidence_percentage']
DEFAULT_SAFETY_BUFFER = _CONFIG['prediction']['safety_buffer']
MAX_HORIZON_DAYS = _CONFIG['prediction']['max_horizon_days']

# Create .env.example file if it doesn't exist
def create_env_example():
    """Create an example environment file."""
    env_example_path = BASE_DIR / ".env.example"
    if not env_example_path.exists():
        env_content = """# DemandWise Environment Variables
# Copy this file to .env and customize as needed

# Application Settings
DEMANDWISE_DEBUG=false

# Data Settings
DEMANDWISE_DATASET_PATH=data/food_demand_data.csv

# Database Settings
DEMANDWISE_DB_PATH=data/demandwise.db

# Logging Settings
DEMANDWISE_LOG_LEVEL=INFO

# Model Settings
DEMANDWISE_MODEL_TYPE=rf

# Prediction Settings
DEMANDWISE_SAFETY_BUFFER=10
DEMANDWISE_MAX_HORIZON=365
"""
        with open(env_example_path, 'w') as f:
            f.write(env_content)

# Create .env.example on import
create_env_example()