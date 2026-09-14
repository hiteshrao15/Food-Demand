"""
DemandWise - Data Management Page
Upload, validate, and manage datasets with proper security and validation.
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config, DEFAULT_DATASET_PATH, SAMPLE_TEMPLATE_PATH
from src.data.loader import DataLoader, DataValidator
from src.utils.logger import get_logger
from src.styles.theme import get_custom_css
from src.ui.components import (
    render_header, render_card, render_kpi_card, render_footer,
    render_status_badge, render_upload_box, render_confirmation_dialog
)
from src.ui.feedback import show_empty_state, show_error_state, show_success_state, show_warning_state

logger = get_logger(__name__)

# Load configuration
config = get_config()

st.set_page_config(page_title="Data Management", page_icon="📂", layout="wide")

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

render_header("Data Management", "Upload, validate, and manage your food demand datasets.", badge="Data", icon="📂")

# Get current data info
def get_current_data_info():
    """Get information about currently loaded data."""
    if 'df' not in st.session_state or st.session_state.df is None:
        return None
    df = st.session_state.df
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'date_range': f"{(pd.to_datetime(df['date']).max() - pd.to_datetime(df['date']).min()).days} days" if 'date' in df.columns and not df['date'].empty else "N/A",
        'items': df['food_item'].nunique() if 'food_item' in df.columns else 0,
        'source': st.session_state.get('data_source', 'unknown')
    }

# Data source selection
st.markdown("### Data Source")

col1, col2 = st.columns([1, 2])

with col1:
    data_source = st.radio(
        "Select Data Source",
        ["Use Demo Data", "Upload CSV", "Create from Scratch"],
        label_visibility="collapsed"
    )

df = None
load_error = None

with col2:
    if data_source == "Use Demo Data":
        current_info = get_current_data_info()
        is_demo = (current_info and current_info['source'] == 'demo') if current_info else False

        render_card(
            "Demo Data",
            "Load a comprehensive synthetic dataset with 2 years of historical data covering 8 food items. Perfect for testing and demonstrating the platform's capabilities.",
            icon="🧪",
            color="info",
            footer=f"Status: {render_status_badge('success' if is_demo else 'secondary', 'Currently Loaded' if is_demo else 'Available')}"
        )

        if st.button("Load Demo Data", type="primary", use_container_width=True):
            with st.spinner("Loading demo data..."):
                df, error = load_data_source("demo")
                if error:
                    load_error = error
                else:
                    show_success_state("Demo Data Loaded", f"Loaded {len(df)} rows of synthetic data")
                    st.rerun()

    elif data_source == "Upload CSV":
        render_card(
            "Upload Data",
            "Upload your own historical demand data as a CSV file. It must contain date, food_item, demand, and holiday columns.",
            icon="📤",
            color="primary"
        )

        # File upload with validation
        uploaded_file = st.file_uploader(
            "Drag and drop your CSV file here",
            type=['csv'],
            help=f"Upload a CSV file with historical demand data (Max size: {config['performance']['memory_limit_mb']}MB)",
            label_visibility="collapsed"
        )

        if uploaded_file:
            # Check file size
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            max_size_mb = config['performance']['memory_limit_mb']

            if file_size_mb > max_size_mb:
                show_error_state(
                    "File Too Large",
                    f"Uploaded file ({file_size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
                )
            else:
                with st.spinner("Validating and processing upload..."):
                    df, error = load_data_source("upload", uploaded_file)
                    if error:
                        load_error = error
                    else:
                        show_success_state(
                            "File Uploaded Successfully",
                            f"Loaded {len(df)} rows from {uploaded_file.name}"
                        )
                        st.rerun()

    elif data_source == "Create from Scratch":
        render_card(
            "Manual Entry",
            "Manually enter data directly into the system. This feature is currently under development.",
            icon="⌨️",
            color="secondary",
            footer=f"Status: {render_status_badge('warning', 'Coming Soon')}"
        )

        # Show template info
        st.info("💡 Tip: You can download a CSV template below to understand the required format, then fill it out locally and upload it.")

# Handle load errors
if load_error:
    show_error_state("Data Load Error", load_error)

# Data validation and overview
current_df = st.session_state.get('df')
if current_df is not None:
    st.divider()
    st.markdown("### Data Quality & Validation")

    # Validate data
    is_valid, errors = DataValidator.validate_dataframe(current_df)

    if is_valid:
        # Calculate data quality metrics
        quality_score = calculate_data_quality_score(current_df)

        col1, col2 = st.columns([1, 2])
        with col1:
            render_kpi_card(
                "Data Quality Score",
                f"{quality_score}/100",
                icon="⭐",
                delta="Optimal" if quality_score > 90 else "Good" if quality_score > 75 else "Needs Improvement",
                delta_type="positive" if quality_score > 90 else ("neutral" if quality_score > 75 else "warning")
            )
        with col2:
            if quality_score >= 90:
                show_success_state("Data Validation", "All checks passed! Data is ready for training and prediction.")
            elif quality_score >= 75:
                show_warning_state("Data Validation", "Data is mostly valid with minor issues that may affect accuracy.")
            else:
                show_error_state("Data Validation", "Data has significant issues that should be addressed before use.")

        with st.expander("View Validation Details", expanded=False):
            if errors:
                st.error("Validation Issues Found:")
                for error in errors:
                    st.write(f"• {error}")
            else:
                st.success("✅ All validation checks passed!")

            # Show data quality breakdown
            st.markdown("**Data Quality Breakdown:**")
            breakdown = get_data_quality_breakdown(current_df)
            for metric, value in breakdown.items():
                st.write(f"• {metric}: {value}")
    else:
        show_error_state("Data Validation Failed", "Please fix the following issues:")
        for error in errors:
            st.write(f"• {error}")

    st.divider()
    st.markdown("### Data Overview")

    current_info = get_current_data_info()
    if current_info:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_kpi_card("Total Rows", f"{current_info['rows']:,}", icon="📋")
        with col2:
            render_kpi_card("Features", f"{current_info['columns']}", icon="📊")
        with col3:
            render_kpi_card("Time Span", current_info['date_range'], icon="🗓️")
        with col4:
            render_kpi_card("Unique Items", f"{current_info['items']}", icon="🍕")

    st.markdown("#### Data Preview")

    # Configure columns for better display
    column_config = {}
    if 'date' in current_df.columns:
        column_config["date"] = st.column_config.DateColumn("Date", format="YYYY-MM-DD")
    if 'food_item' in current_df.columns:
        column_config["food_item"] = st.column_config.TextColumn("Food Item")
    if 'demand' in current_df.columns:
        column_config["demand"] = st.column_config.NumberColumn("Demand", format="%d")
    if 'holiday' in current_df.columns:
        column_config["holiday"] = st.column_config.CheckboxColumn("Holiday")

    st.dataframe(
        current_df.head(20),
        use_container_width=True,
        column_config=column_config
    )

    st.divider()
    st.markdown("### Exploratory Analytics")

    if is_valid:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Demand Distribution")
            if 'demand' in current_df.columns and not current_df['demand'].empty:
                st.dataframe(
                    current_df['demand'].describe().to_frame().T,
                    use_container_width=True
                )
            else:
                st.info("No demand data available for distribution analysis")

        with col2:
            st.markdown("##### Items Frequency")
            if 'food_item' in current_df.columns and not current_df['food_item'].empty:
                item_counts = current_df['food_item'].value_counts().head(10)
                if len(item_counts) > 0:
                    st.bar_chart(item_counts)
                else:
                    st.info("No food item data available")
            else:
                st.info("No food item data available for frequency analysis")

    st.divider()
    st.markdown("### Actions & Templates")

    col1, col2 = st.columns(2)

    with col1:
        render_card(
            "Manage Active Dataset",
            "Save the current dataset as the default source for training and prediction.",
            icon="💾"
        )

        # Show current dataset info
        if current_info:
            st.caption(f"Current dataset: {current_info['rows']} rows from {current_info['source']}")

        # Save as default button
        button_disabled = current_df is None or len(current_df) == 0
        if st.button(
            "💾 Save as Default Dataset",
            use_container_width=True,
            type="primary",
            disabled=button_disabled
        ):
            if current_df is not None and len(current_df) > 0:
                # Show confirmation dialog
                if render_confirmation_dialog(
                    "Save Dataset",
                    f"Are you sure you want to save the current dataset ({len(current_df)} rows) as the default?\nThis will overwrite the existing default dataset.",
                    "Confirm Save",
                    "Cancel"
                ):
                    try:
                        current_df.to_csv(DEFAULT_DATASET_PATH, index=False)
                        show_success_state("Dataset Saved", f"Successfully saved {len(current_df)} rows as default dataset")
                        # Clear any cached data to force reload
                        if 'df' in st.session_state:
                            del st.session_state.df
                        st.rerun()
                    except Exception as e:
                        show_error_state("Save Failed", f"Failed to save dataset: {str(e)}")
            else:
                show_error_state("No Data", "No data available to save")

        # Export data
        if current_df is not None and len(current_df) > 0:
            csv_export = current_df.to_csv(index=False)
            st.download_button(
                label="📤 Export Current Data",
                data=csv_export,
                file_name=f"food_demand_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col2:
        render_card(
            "Download Template",
            "Download an empty CSV template with the required columns pre-populated to ensure correct format.",
            icon="📥"
        )

        # Create and offer template download
        try:
            template_df = DataLoader.generate_template_dataset()
            csv_template = template_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Template",
                data=csv_template,
                file_name="food_demand_template.csv",
                mime="text/csv",
                use_container_width=True,
                help="Download a template with the correct column structure and sample data"
            )

            # Show template preview
            with st.expander("Template Preview", expanded=False):
                st.dataframe(template_df.head(), use_container_width=True)

        except Exception as e:
            show_error_state("Template Generation Failed", f"Could not generate template: {str(e)}")

else:
    show_empty_state(
        "📥",
        "No Data Loaded",
        "Select a data source above to load, upload, or create a dataset.",
        "📥 Load Demo Data",
        "load_demo"
    )

    if st.button("Load Demo Data", key="load_demo_btn_empty"):
        df, error = load_data_source("demo")
        if error:
            show_error_state("Data Load Error", error)
        else:
            show_success_state("Data Loaded", f"Loaded {len(df)} rows of demo data")
            st.rerun()

render_footer()


def load_data_source(source_type, uploaded_file=None):
    """Load data from specified source with validation."""
    try:
        if source_type == "demo":
            if DEFAULT_DATASET_PATH.exists():
                df = DataLoader.load_csv(str(DEFAULT_DATASET_PATH))
            else:
                df = DataLoader.generate_demo_dataset()
                # Ensure directory exists
                DEFAULT_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(DEFAULT_DATASET_PATH, index=False)
            data_version = "demo"

        elif source_type == "upload" and uploaded_file is not None:
            # Reset file pointer
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            data_version = f"upload_{uploaded_file.name}"

        else:
            return None, "Invalid data source specified"

        # Validate data
        is_valid, errors = DataValidator.validate_dataframe(df)
        if not is_valid:
            return None, f"Data validation failed: {'; '.join(errors)}"

        # Additional security checks
        security_issues = validate_upload_security(df, uploaded_file.name if uploaded_file else "demo")
        if security_issues:
            return None, f"Security validation failed: {'; '.join(security_issues)}"

        return df, None

    except Exception as e:
        logger.error(f"Error loading {source_type} data: {e}")
        return None, f"Failed to load data: {str(e)}"


def validate_upload_security(df, filename):
    """Perform security validation on uploaded data."""
    issues = []

    # Check for potential formula injection in column names
    suspicious_prefixes = ['=', '+', '-', '@', '\t', '\r']
    for col in df.columns:
        if isinstance(col, str) and any(col.startswith(prefix) for prefix in suspicious_prefixes):
            issues.append(f"Column name '{col}' appears to contain formula injection risk")

    # Check for extremely large values that might cause memory issues
    if 'demand' in df.columns:
        max_demand = df['demand'].max()
        if pd.notna(max_demand) and max_demand > 1000000:  # 1M units seems unreasonable for food demand
            issues.append(f"Demand values appear unreasonably high (max: {max_demand}), possible data error")

    # Check for unreasonable date ranges
    if 'date' in df.columns:
        try:
            dates = pd.to_datetime(df['date'], errors='coerce')
            if dates.isna().any():
                issues.append("Some date values could not be parsed")
            else:
                date_range = (dates.max() - dates.min()).days
                if date_range > 3650:  # More than 10 years
                    issues.append(f"Date range is very large ({date_range} days), possible data error")
                elif date_range < 0:
                    issues.append("Date range appears to be backwards (end date before start date)")
        except Exception:
            issues.append("Could not validate date column due to parsing errors")

    return issues


def calculate_data_quality_score(df):
    """Calculate a data quality score based on various factors."""
    if df is None or len(df) == 0:
        return 0

    score = 100

    # Penalize for missing values
    total_cells = df.size
    if total_cells > 0:
        missing_pct = (df.isnull().sum().sum() / total_cells) * 100
        score -= missing_pct * 0.5  # Up to 50 points off for missing data

    # Penalize for invalid demand values
    if 'demand' in df.columns:
        negative_count = (df['demand'] < 0).sum()
        if negative_count > 0:
            score -= min(20, (negative_count / len(df)) * 100)  # Up to 20 points off

        # Check for extreme outliers
        q1 = df['demand'].quantile(0.25)
        q3 = df['demand'].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_count = ((df['demand'] < lower_bound) | (df['demand'] > upper_bound)).sum()
            if outlier_count > 0:
                score -= min(15, (outlier_count / len(df)) * 100)  # Up to 15 points off

    # Penalize for invalid holiday values
    if 'holiday' in df.columns:
        invalid_holiday = (~df['holiday'].isin([0, 1])).sum()
        if invalid_holiday > 0:
            score -= min(10, (invalid_holiday / len(df)) * 100)  # Up to 10 points off

    # Bonus for good sample size
    if len(df) >= 365:  # At least one year of data
        score = min(100, score + 5)
    if len(df) >= 730:  # At least two years
        score = min(100, score + 5)

    return max(0, min(100, round(score)))


def get_data_quality_breakdown(df):
    """Get detailed breakdown of data quality metrics."""
    if df is None or len(df) == 0:
        return {"Error": "No data available"}

    breakdown = {}

    # Completeness
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
    breakdown["Completeness"] = f"{completeness:.1f}%"

    # Demand validity (if column exists)
    if 'demand' in df.columns:
        valid_demand = ((df['demand'] >= 0) & df['demand'].notna()).sum()
        demand_validity = (valid_demand / len(df) * 100) if len(df) > 0 else 0
        breakdown["Valid Demand Values"] = f"{demand_validity:.1f}%"

        # Check for realistic values
        realistic_demand = ((df['demand'] >= 0) & (df['demand'] <= 10000) & df['demand'].notna()).sum()
        realistic_pct = (realistic_demand / len(df) * 100) if len(df) > 0 else 0
        breakdown["Realistic Demand Range"] = f"{realistic_pct:.1f}%"

    # Holiday validity (if column exists)
    if 'holiday' in df.columns:
        valid_holiday = df['holiday'].isin([0, 1]).sum()
        holiday_validity = (valid_holiday / len(df) * 100) if len(df) > 0 else 0
        breakdown["Valid Holiday Values"] = f"{holiday_validity:.1f}%"

    # Date validity (if column exists)
    if 'date' in df.columns:
        try:
            valid_dates = pd.to_datetime(df['date'], errors='coerce').notna().sum()
            date_validity = (valid_dates / len(df) * 100) if len(df) > 0 else 0
            breakdown["Valid Dates"] = f"{date_validity:.1f}%"
        except Exception:
            breakdown["Valid Dates"] = "Unable to assess"

    # Duplicates
    total_rows = len(df)
    unique_rows = df.drop_duplicates().shape[0]
    duplicate_pct = ((total_rows - unique_rows) / total_rows * 100) if total_rows > 0 else 0
    breakdown["Unique Rows"] = f"{100 - duplicate_pct:.1f}%"

    return breakdown