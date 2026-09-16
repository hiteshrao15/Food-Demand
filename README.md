# DemandWise - Food Demand Prediction Platform

**Predict demand. Reduce waste. Prepare smarter.**

A professional Machine Learning-powered web application for predicting food demand in restaurants, cafés, canteens, and food service operations.

---

## Overview

DemandWise helps food businesses answer the critical question: **"How much food should I prepare for a particular day?"**

Using historical demand data and Machine Learning, the system estimates future demand and provides understandable explanations for each prediction.

### Problem Statement

Food service operations face constant challenges with demand prediction:
- Over-preparation leads to food waste and lost revenue
- Under-preparation results in customer dissatisfaction and missed sales
- Manual prediction is time-consuming and often inaccurate
- Lack of transparency in why certain demand levels are expected

DemandWise addresses these challenges with a data-driven, explainable approach.

---

## Features

### Core Functionality
- **Demand Prediction**: Predict food demand for any future date
- **Multiple ML Models**: Linear Regression, Random Forest, and Deep Learning
- **Explainable AI**: Understand *why* predictions are made using SHAP values
- **Historical Analytics**: Explore trends, patterns, and performance metrics
- **Model Comparison**: Compare model performance and select the best approach
- **Data Management**: Upload, validate, and manage your datasets

### User Interface
- **Professional Dashboard**: Clear KPIs and actionable insights
- **Interactive Predictions**: Easy-to-use prediction interface
- **Visual Analytics**: Charts and graphs for trend analysis
- **Prediction History**: Track and review past predictions

---

## Technology Stack

### Machine Learning
- **Linear Regression**: Baseline model with fast inference
- **Random Forest**: Ensemble learning for robust predictions
- **Deep Learning**: Neural network for complex pattern recognition
- **SHAP**: Explainable AI for transparent predictions

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Feature Engineering**: Time-based features, lag features, rolling statistics

### Web Application
- **Streamlit**: Interactive web framework
- **Plotly**: Interactive visualizations
- **SQLite**: Local database for history and metadata

### Development
- **Python 3.10+**: Core programming language
- **Modular Architecture**: Clean separation of concerns
- **Type Hints**: Code clarity and maintainability

---

## Architecture

```
food-demand-prediction/
│
├── app.py                    # Main Streamlit application
├── train_models.py           # Model training script
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
│
├── data/                     # Data storage
│   └── food_demand_data.csv  # Historical demand data
│
├── models/                   # Trained model artifacts
│   ├── lr_model.pkl          # Linear Regression
│   ├── rf_model.pkl          # Random Forest
│   ├── dl_model.pkl          # Deep Learning
│   ├── label_encoder.pkl     # Food item encoder
│   ├── scaler.pkl            # Feature scaler
│   └── feature_columns.pkl   # Feature list
│
├── notebooks/                # Research notebooks
│   └── food_demand_prediction.ipynb
│
├── pages/                    # Streamlit pages
│   ├── predict.py            # Prediction interface
│   ├── analytics.py          # Analytics dashboard
│   ├── explainability.py     # XAI explanations
│   ├── model_performance.py  # Model comparison
│   ├── data_management.py    # Data upload/management
│   └── settings.py           # Application settings
│
└── src/                      # Source code modules
    ├── config.py             # Configuration constants
    ├── data/                 # Data processing
    ├── ml/                   # Machine learning
    ├── xai/                  # Explainable AI
    ├── analytics/            # Analytics engine
    ├── database/             # Database operations
    └── utils/                # Utilities
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup

1. **Clone or download the project**
   ```bash
   cd Demand
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train models (first time setup)**
   ```bash
   python train_models.py
   ```

---

## Running the Application

### Start the Web Application
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Quick Start Guide

1. **Dashboard**: View overall metrics and trends
2. **Predict Demand**: Select food item and date for prediction
3. **Analytics**: Explore historical demand patterns
4. **Explainability**: Understand prediction factors
5. **Model Performance**: Compare ML model metrics
6. **Data Management**: Upload or manage datasets

---

## Dataset Format

### Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| date | Date | Date of demand (YYYY-MM-DD) | 2024-01-15 |
| food_item | String | Name of food item | Pizza |
| demand | Integer | Number of orders/demand | 85 |
| holiday | Integer | Holiday flag (0 or 1) | 0 |

### Sample Data

```csv
date,food_item,demand,holiday
2024-01-01,Pizza,85,0
2024-01-01,Burger,120,0
2024-01-01,Salad,45,0
```

### Data Requirements
- Minimum 30 days of historical data recommended
- Consistent food item names across records
- Accurate demand values (integer counts)
- Holiday flag for special dates

---

## ML Models

### Linear Regression
- **Strengths**: Simple, fast, interpretable
- **Use Case**: Baseline predictions, linear relationships
- **MAE**: ~10.0 orders

### Random Forest (Best Performer)
- **Strengths**: Handles non-linearity, robust to outliers
- **Use Case**: Primary production model
- **MAE**: ~8.8 orders
- **R²**: 0.91

### Deep Learning
- **Strengths**: Captures complex patterns
- **Use Case**: Large datasets, hierarchical features
- **MAE**: ~10.0 orders

### Model Selection

The system automatically selects the best-performing model based on Mean Absolute Error (MAE) on validation data.

---

## Explainable AI (XAI)

DemandWise uses SHAP (SHapley Additive exPlanations) to provide transparency:

### What SHAP Shows
- **Feature Importance**: Which factors matter most
- **Direction**: Positive or negative influence
- **Magnitude**: How much each feature contributes

### Example Explanation
```
Demand is expected to be higher due to:
- Weekend effect: +12 orders
- Recent demand trend: +8 orders
- Historical average: +5 orders

Potential reducing factors:
- Not a holiday: -3 orders
```

---

## Retraining Models

### When to Retrain
- New historical data available (30+ days)
- Demand patterns have changed
- Prediction errors increasing
- New menu items introduced

### How to Retrain

**Option 1: Via UI**
1. Navigate to Settings page
2. Click "Retrain All Models"
3. Wait for training to complete

**Option 2: Via Command Line**
```bash
python train_models.py
```

---

## Project Structure Details

### Source Modules

#### `src/data/`
- `loader.py`: Data loading and generation
- `validator.py`: Data validation logic
- `preprocessor.py`: Feature engineering

#### `src/ml/`
- `models.py`: ML model implementations
- `evaluator.py`: Model evaluation metrics
- `predictor.py`: Prediction pipeline
- `retrainer.py`: Model retraining workflow

#### `src/xai/`
- `explainer.py`: SHAP-based explanations

#### `src/analytics/`
- `engine.py`: Analytics calculations

#### `src/database/`
- `db.py`: SQLite operations

#### `src/utils/`
- `logger.py`: Application logging
- `helpers.py`: Utility functions

---

## Limitations

### Current Limitations
- Single-location predictions (no multi-store support)
- No weather data integration
- No event/festival data integration
- Manual holiday marking required
- No real-time POS integration

### Data Requirements
- Requires historical data for training
- Minimum 30 days recommended for reasonable accuracy
- Quality depends on data accuracy

---

## Future Improvements

### Planned Features
- [ ] Multi-location support
- [ ] Weather data integration
- [ ] Event calendar integration
- [ ] Real-time POS integration
- [ ] Inventory management integration
- [ ] Mobile application
- [ ] User accounts and roles
- [ ] Advanced forecasting horizons

### Technical Improvements
- [ ] Model ensemble approaches
- [ ] Hyperparameter optimization
- [ ] Automated feature selection
- [ ] Cloud database support
- [ ] API endpoints

---

## Contributing

This is an educational/demonstration project. For production use:

1. Add comprehensive error handling
2. Implement user authentication
3. Add data encryption
4. Set up monitoring and logging
5. Implement backup strategies

---

## License

This project is for educational and demonstration purposes.

---

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [Scikit-learn](https://scikit-learn.org/) - Machine learning
- [SHAP](https://shap.readthedocs.io/) - Explainable AI
- [Plotly](https://plotly.com/) - Visualizations
- [Pandas](https://pandas.pydata.org/) - Data analysis

---

**DemandWise** - Making food demand prediction accessible and understandable.
