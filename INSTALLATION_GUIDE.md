# DemandWise - Installation & Deployment Guide

Professional setup instructions for running DemandWise on your local machine.

## System Requirements

- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.10 or higher
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: 2GB for installation + dependencies
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

## Installation Steps

### 1. Download & Extract Project

```bash
# Navigate to your desired location
cd /path/to/your/workspace

# Extract DemandWise project files
# (or clone from repository if using git)
cd Demand
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**Expected installation time:** 5-15 minutes depending on internet speed

### 4. Verify Installation

```bash
# Check Python version
python --version

# Verify key packages
python -c "import streamlit; import pandas; import numpy; import plotly; print('✅ All dependencies installed!')"
```

## Running the Application

### First-Time Setup

On first run, DemandWise will automatically:
- Create required directories (`data/`, `models/`, `logs/`)
- Generate demo dataset
- Train ML models (this takes 2-5 minutes)

### Start the Application

```bash
streamlit run app.py
```

The application will open automatically in your default browser at `http://localhost:8501`

### First Run Output

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Issue: Port 8501 Already in Use

**Solution:**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

### Issue: Models Not Training

**Solution:**
```bash
# Delete old model artifacts and retrain
rm -rf models/*.pkl models/*.json

# Retrain models
python train_models.py

# This will take 5-10 minutes
```

### Issue: "Database is locked" Error

**Solution:**
```bash
# Close all other instances of DemandWise
# Delete database lock file
rm -f data/demandwise.db-journal

# Restart application
streamlit run app.py
```

## Configuration

### Custom Settings

Edit `src/config.py` to customize:

```python
# Model hyperparameters
RF_N_ESTIMATORS = 100      # Number of trees
RF_MAX_DEPTH = 15          # Max tree depth
DL_EPOCHS = 50             # Neural network epochs

# Data settings
TEST_SPLIT_SIZE = 0.2      # Train/test ratio
RANDOM_STATE = 42          # Reproducibility seed
```

### Streamlit Configuration

Create `.streamlit/config.toml` for advanced options:

```toml
[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "info"

[server]
port = 8501
headless = false
runOnSave = true
```

## Deployment

### Local Network Access

To access DemandWise from another machine on your network:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then access using: `http://<YOUR_IP>:8501`

### Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

**Build and run:**
```bash
docker build -t demandwise .
docker run -p 8501:8501 demandwise
```

## Development

### Running Tests

```bash
# Run comprehensive test suite
python tests/test_core.py

# Run specific test
python -m pytest tests/test_core.py::test_demo_data_generation -v
```

### Training Models Manually

```bash
python train_models.py
```

This will:
- Load/generate demo dataset
- Engineer features
- Train 3 models (Linear Regression, Random Forest, Deep Learning)
- Save best model and artifacts
- Display performance metrics

## Data Management

### Upload Custom Dataset

1. Go to **Data Management** page
2. Select **Upload CSV**
3. File must have columns: `date`, `food_item`, `demand`, `holiday`
4. Click **Save as Default Dataset**

### Dataset Format

```csv
date,food_item,demand,holiday
2024-01-01,Pizza,85,0
2024-01-01,Burger,120,0
2024-01-02,Pizza,95,0
```

### Minimum Data Requirements

- At least 30 days of historical data
- Consistent date format (YYYY-MM-DD)
- Positive integer demand values
- Consistent food item names

## Performance Optimization

### For Large Datasets (10,000+ rows)

```python
# Edit src/config.py
TEST_SPLIT_SIZE = 0.15     # Smaller test set
RF_N_ESTIMATORS = 50       # Fewer trees
DL_EPOCHS = 30             # Fewer epochs
```

### Faster Predictions

```bash
# Use feature importance instead of SHAP
# Edit pages/explainability.py model_type = 'lr'
```

## Support & Documentation

- **User Guide**: See `USAGE_GUIDE.md`
- **Architecture**: See `README.md`
- **API Reference**: See `API_REFERENCE.md`

## Next Steps

1. Start with the **Dashboard** to view sample data
2. Go to **Data Management** to upload your data
3. Use **Predict Demand** to make forecasts
4. Check **Analytics** for historical trends
5. Explore **Explainability** to understand predictions

---

**Last Updated**: 2026-09-13
**Version**: 1.2.0
