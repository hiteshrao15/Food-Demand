# DemandWise - User Guide

Complete guide to using DemandWise for food demand prediction and analytics.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Making Predictions](#making-predictions)
4. [Analytics & Insights](#analytics--insights)
5. [Understanding Explanations](#understanding-explanations)
6. [Data Management](#data-management)
7. [Best Practices](#best-practices)
8. [FAQ](#faq)

---

## Getting Started

### First Login

After launching DemandWise (`streamlit run app.py`), you'll see:

1. **Dashboard** - Your operational hub with KPIs and trends
2. **Predict Demand** - Make forecasts for specific dates
3. **Analytics** - Explore historical patterns
4. **Explainability** - Understand why predictions happen
5. **Model Performance** - Compare ML models
6. **Data Management** - Upload and manage datasets
7. **Settings** - System configuration and help

### Demo Mode

DemandWise includes sample food service data (8 items, 2 years). Perfect for:
- Learning how the system works
- Testing features without your own data
- Understanding prediction patterns

---

## Dashboard Overview

The Dashboard is your command center showing:

### Key Performance Indicators (KPIs)

| Metric | Meaning |
|--------|---------|
| **Total Orders** | Sum of all demand across all items |
| **Daily Average** | Average daily demand |
| **Unique Items** | Number of food items tracked |
| **Top Item** | Best-performing food item |

### Active Model Card

Shows which ML model is currently predicting:
- **Model Name** (usually "Random Forest")
- **MAE** (Mean Absolute Error) - lower is better
- **R²** (Coefficient) - higher is better

### Recent Trends

30-day trend line showing demand trajectory.

---

## Making Predictions

### Step-by-Step Prediction

**1. Select Food Item**
- Choose from dropdown of available items
- Or upload new items via Data Management

**2. Choose Prediction Date**
- Can predict up to 365 days ahead
- System prevents past dates

**3. Mark Holiday (Optional)**
- Check if date is special occasion
- Holiday boost typically 15-25% higher demand

**4. Click "Predict Demand"**
- System processes in 2-5 seconds
- Shows predicted orders with confidence range

### Understanding Prediction Output

```
Predicted Orders: 95 orders
Confidence Range: ±9 orders (±10%)
Recommended Prep: 104 servings
```

**What this means:**
- Your best estimate is **95 orders**
- System is 95% confident actual will be **86-104 orders**
- Recommend preparing **104 units** to avoid stockouts

### Historical Context

The system shows three reference points:

| Reference | Use Case |
|-----------|----------|
| **Historical Avg** | All-time average for this item |
| **Same Day Avg** | Average for this day of week |
| **Recent 7-Day Avg** | Latest trend indicator |

### Save Predictions

Predictions auto-save to history (visible in Settings tab).

---

## Analytics & Insights

### Trend Analysis

**View demand over time:**
- **Daily**: See day-to-day variations
- **Weekly**: Identify week-to-week patterns
- **Monthly**: Spot seasonal trends

### Day-of-Week Patterns

Which days are busy? Which are slow?

- **Monday-Friday**: Typically steadier, mid-range demand
- **Saturday-Sunday**: Usually 20-40% higher
- **Holidays**: Can spike 30-80% depending on context

### Item Performance

Rank items by total demand:
- See which items drive business
- Identify underperformers
- Plan inventory accordingly

### Holiday Impact

Compare regular days vs. holidays:
- Demand lift percentages
- Which items spike most
- When holidays matter most

### Month-over-Month

Spot growth or decline:
- Is business growing?
- Seasonal patterns?
- Year-over-year changes

---

## Understanding Explanations

### Why Predictions?

Click **Explainability** to see EXACTLY what drives each prediction.

### Top Factors

**Positive Factors** (increase demand):
- "Recent Demand Trend" +12 orders
- "Weekend Effect" +8 orders
- "Holiday Flag" +5 orders

**Negative Factors** (decrease demand):
- "Winter Month" -3 orders
- "Low Historical Average" -2 orders

### Feature Importance

Not all factors matter equally:
- **High importance**: Strongly influences prediction
- **Low importance**: Minimal effect

### Confidence

SHAP values show model's conviction:
- Large values = high confidence
- Small values = uncertain

### Trust Building

Use explanations to:
- ✅ Build confidence in predictions
- ✅ Identify influential factors you can control
- ✅ Spot unusual patterns
- ✅ Make informed business decisions

---

## Data Management

### Upload Your Data

**Step 1: Prepare CSV file**

```csv
date,food_item,demand,holiday
2024-01-01,Pasta,120,0
2024-01-01,Salad,45,1
2024-01-02,Pasta,135,0
```

**Step 2: Go to Data Management**
- Click "Upload CSV"
- Select your file
- System validates automatically

**Step 3: Review & Save**
- Check validation results
- View data preview
- Click "Save as Default Dataset"

**Step 4: Retrain Models**
- Go to Settings
- Click "Retrain All Models"
- Wait 5-10 minutes for training

### Data Requirements

| Column | Format | Example | Notes |
|--------|--------|---------|-------|
| date | YYYY-MM-DD | 2024-01-15 | Required, chronological |
| food_item | Text | Pizza | Case-sensitive, consistent |
| demand | Integer | 85 | Must be ≥ 0 |
| holiday | 0 or 1 | 0 | 0=regular, 1=holiday |

### Minimum Requirements

- **At least 30 days** of history (recommended 365+ days)
- **Daily records** for each food item
- **Consistent item names** (no typos)
- **No future dates** in training data

---

## Best Practices

### For Accurate Predictions

1. **Use complete historical data**
   - More data = better patterns
   - Include full years to capture seasonality

2. **Keep item names consistent**
   - "Margherita Pizza" ≠ "Pizza"
   - Standardize before uploading

3. **Mark holidays accurately**
   - Company holidays, local events
   - Helps model understand demand spikes

4. **Retrain quarterly**
   - Every 90 days with new data
   - Patterns change over time

### For Business Use

1. **Use as a guide, not gospel**
   - Predictions are estimates
   - Account for external factors (weather, events, marketing)

2. **Adjust for known events**
   - Marketing campaign? Expect +20-30%
   - Competitor closed? Expect +10-15%
   - Strike/closure? Expect -50%+

3. **Monitor prediction accuracy**
   - Track actual vs. predicted
   - Adjust prep quantities if systematic bias detected

4. **Share insights with team**
   - Use analytics for staffing decisions
   - Plan inventory based on trends
   - Communicate forecasts to procurement

---

## FAQ

### Q: How accurate are predictions?

**A:** Typically 85-95% accurate (R² > 0.85). Accuracy depends on:
- Data quality and completeness
- How representative historical data is
- Stability of demand patterns
- External factors not in data (weather, events)

### Q: Can I predict multiple items at once?

**A:** Not currently. Use the batch prediction feature (coming soon) or:
1. Predict each item individually
2. Export results for analysis

### Q: How far ahead can I predict?

**A:** System allows up to 365 days ahead, but:
- **7-30 days**: High confidence
- **30-90 days**: Good confidence, seasonal patterns matter
- **90+ days**: Lower confidence, external factors dominate

### Q: What if I have seasonal demand?

**A:** DemandWise automatically learns seasonality from historical data. The model captures:
- Weekly patterns (weekday vs. weekend)
- Monthly patterns (seasonal)
- Holiday effects
- Multi-year trends

### Q: How often should I retrain?

**A:** Retrain when:
- New menu items introduced
- Major demand pattern changes
- Quarterly (every 90 days) minimum
- After significant external events

### Q: Can I use weather data?

**A:** Not directly in current version. Workaround:
1. Create synthetic "weather" column (0-5 scale)
2. Include in training data
3. Mark appropriately for predictions

### Q: Is my data secure?

**A:** Yes! DemandWise:
- Stores data **locally only** (not cloud)
- Never sends data to external servers
- Works completely offline
- Perfect for confidential data

### Q: Can I export predictions?

**A:** Yes! Export formats:
- **CSV**: Full prediction history
- **PDF**: Formatted reports (coming soon)
- **Excel**: Detailed analysis (coming soon)

### Q: What if predictions seem wrong?

**A:** Check:
1. **Data quality**: Outliers, gaps, errors
2. **Item selection**: Right item name?
3. **Holiday flag**: Correctly marked?
4. **External factors**: Events not in data?
5. **Model age**: Last retrained when?

Try retraining with corrected data.

### Q: Can I have multiple users?

**A:** Current version is single-user local. For team use:
- Upcoming: User authentication
- Upcoming: Cloud deployment option
- Workaround: Share same machine access

### Q: How do I report bugs?

**A:** Check the **Settings** page for:
- System logs
- Database status
- Model metadata
- Support contact info

---

## Tips & Tricks

### Speed Up Predictions

- Use **Feature Importance** instead of SHAP for explanations (faster)
- Reduce dataset size to recent 2 years

### Better Insights

- Combine **Analytics** tab with predictions
- Look for patterns in day-of-week charts
- Use holiday analysis to understand demand drivers

### Improve Accuracy

- Upload complete year of data (captures seasonality)
- Correct historical errors before retraining
- Track actual vs. predicted and adjust prep quantities

### Team Communication

- Screenshot predictions for meetings
- Export analytics for reports
- Use explanations to educate team on drivers

---

## Additional Resources

- **Installation Help**: See `INSTALLATION_GUIDE.md`
- **Technical Details**: See `README.md`
- **API Reference**: See `API_REFERENCE.md`
- **Model Details**: See Model Performance tab

---

**Version**: 1.2.0  
**Last Updated**: 2026-09-13  
**Support**: See Settings tab for help resources
