"""
DemandWise - Automated Test Suite
Verifies core functionality without requiring external dependencies like scikit-learn.
"""
import sys
from pathlib import Path

# Ensure project root is in Python path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from src.config import DEFAULT_DATASET_PATH, FEATURE_COLUMNS
from src.data.loader import DataLoader, DataValidator
from src.data.preprocessor import FeatureEngineer
from src.ml.evaluator import ModelEvaluator
from src.ml.models import get_model, NativeLinearRegression, NativeRandomForestRegressor, NativeNeuralNetwork
from src.ml.predictor import DemandPredictor
from src.utils.helpers import format_number, ensure_float
from src.database.db import DatabaseManager

def test_demo_data_generation():
    print("Testing: Demo data generation...")
    df = DataLoader.generate_demo_dataset()
    assert len(df) > 0
    assert 'date' in df.columns
    assert 'food_item' in df.columns
    assert 'demand' in df.columns
    assert df['demand'].min() >= 0
    print("✅ Demo data generation passed.")

def test_data_validation():
    print("Testing: Data validation...")
    valid_df = pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'food_item': ['Pizza', 'Burger'],
        'demand': [80, 100],
        'holiday': [0, 1]
    })
    is_valid, errors = DataValidator.validate_dataframe(valid_df)
    assert is_valid
    assert len(errors) == 0

    invalid_df = pd.DataFrame({
        'date': ['bad-date', '2024-01-02'],
        'food_item': ['Pizza', 'Burger'],
        'demand': [-5, 100],  # Negative demand
        'holiday': [0, 2]  # Invalid holiday value
    })
    is_valid, errors = DataValidator.validate_dataframe(invalid_df)
    assert not is_valid
    assert len(errors) > 0
    print("✅ Data validation passed.")

def test_feature_engineering():
    print("Testing: Feature engineering...")
    df = DataLoader.generate_demo_dataset()
    df_engineered, le = FeatureEngineer.create_features(df)

    for col in FEATURE_COLUMNS:
        assert col in df_engineered.columns

    assert not df_engineered.isnull().any().any()
    # Lag features are filled with rolling mean for first 7 rows, check later row where lag has historical data
    # Get row at index 100 (well past the first 7 rows for each food item)
    assert df_engineered['demand_lag_7'].iloc[100] != df_engineered['demand'].iloc[100]
    print("✅ Feature engineering passed.")

def test_model_training_and_evaluation():
    print("Testing: Model training and evaluation...")
    # Generate and preprocess
    df = DataLoader.generate_demo_dataset()
    df_eng, le = FeatureEngineer.create_features(df)
    scaler = FeatureEngineer.get_scaler()
    scaler.fit(df_eng[FEATURE_COLUMNS])

    X = df_eng[FEATURE_COLUMNS].values
    y = df_eng['demand'].values

    # Split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Test Native Models
    for model_type in ['lr', 'rf', 'dl']:
        model = get_model(model_type)
        if model_type == 'dl':
            model.fit(scaler.transform(X_train), y_train)
            preds = model.predict(scaler.transform(X_test))
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)

        metrics = ModelEvaluator.calculate_metrics(y_test, preds)
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] >= 0
        assert not np.isnan(metrics['mae'])
    print("✅ Model training and evaluation passed.")

def test_predictor_and_explainer():
    print("Testing: Predictor and explainer logic...")

    # Ensure DemandPredictor can be used even when uncertainty estimator/artifacts
    # aren't present (e.g., in unit tests).
    # Train a simple model first
    df = DataLoader.generate_demo_dataset()
    df_eng, le = FeatureEngineer.create_features(df)
    scaler = FeatureEngineer.get_scaler()
    scaler.fit(df_eng[FEATURE_COLUMNS])

    model = get_model('rf')
    model.fit(df_eng[FEATURE_COLUMNS].values, df_eng['demand'].values)

    # Manually mock predictor to use the trained model
    predictor = DemandPredictor.__new__(DemandPredictor)
    predictor.model = model
    predictor.model_type = 'rf'
    predictor.scaler = scaler
    predictor.label_encoder = le
    predictor.feature_columns = FEATURE_COLUMNS
    predictor.uncertainty_estimator = None  # No uncertainty estimator in test
    predictor.metadata = {'best_model_name': 'Random Forest', 'version_id': 'test'}

    result = predictor.predict_with_context('Pizza', '2024-03-01', 0, df)
    assert 'predicted_demand' in result
    assert result['predicted_demand'] >= 0
    assert 'feature_df' in result

    # Test Explainer
    from src.xai.explainer import DemandExplainer
    explainer = DemandExplainer(model, 'rf')
    explanation = explainer.explain_prediction(result['feature_df'])

    assert 'contributions' in explanation
    assert 'summary' in explanation
    assert len(explanation['contributions']) > 0
    print("✅ Predictor and explainer passed.")

def test_helpers():
    print("Testing: Helper functions...")
    assert format_number(15000) == "15.0k"
    assert format_number(500) == "500"
    assert ensure_float("abc") == 0.0
    print("✅ Helper functions passed.")

def run_all_tests():
    print("="*50)
    print("Running DemandWise Test Suite")
    print("="*50)

    test_demo_data_generation()
    test_data_validation()
    test_feature_engineering()
    test_model_training_and_evaluation()
    test_predictor_and_explainer()
    test_helpers()

    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    run_all_tests()