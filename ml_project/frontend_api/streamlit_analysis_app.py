import os
import sys
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

logger = get_logger(__name__)


def analysis_dashboard(
    dashboard_type: str,
    dataset_path: str,
    uploaded_file: Optional[object] = None,
) -> None:
    """
    Render the selected dashboard.

    Parameters:
        dashboard_type (str): Selected dashboard option
        dataset_path (str): Path to the default dataset
        uploaded_file (Optional[object]): Optional user-uploaded file
    """
    try:
        # Strip emojis from dashboard_type for logging
        dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
        logger.info("Rendering analysis dashboard | type=%s", dashboard_type_clean)
        
        # Page Title
        st.title(dashboard_type)

        # ==================================================
        # ANALYSIS DASHBOARD
        # ==================================================
        if "Analysis Dashboard" in dashboard_type:
            
            df = None
            try:
                if uploaded_file:
                    logger.info("Loading uploaded file")
                    df = pd.read_excel(uploaded_file)
                elif dataset_path and dataset_path != "Not available":
                    logger.info("Loading default dataset | path=%s", dataset_path)
                    df = pd.read_excel(dataset_path)
                else:
                    st.warning("⚠️ No data available. Please upload a file or check the default dataset path.")
                    logger.warning("No dataset available")
                    return
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                logger.error("Error loading dataset | error=%s", str(e))
                return
            
            if df is None or df.empty:
                st.warning("⚠️ No data available. Please upload a file or check the default dataset path.")
                logger.warning("DataFrame is empty or None")
                return

            logger.info("Dataset loaded successfully | shape=%s", df.shape)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                [
                    "📈 Complaint Overview",
                    "📋 Data Table",
                    "📊 Summary",
                    "🔍 Dataset Information",
                    "📊 Visualizations",
                ]
            )

            # ----------------------------------------------
            # TAB 1: COMPLAINT OVERVIEW
            # ----------------------------------------------
            with tab1:
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 2: DATA TABLE
            # ----------------------------------------------
            with tab2:
                st.warning("🚧 This Project is under development.")
                
                # Preview of data
                if df is not None:
                    if st.button("📊 Show Data Preview", key="show_data_btn"):
                        st.subheader("Data Preview")
                        st.dataframe(df.head(10), use_container_width=True)
                        st.info(f"Showing first 10 rows of {len(df)} total rows")
                        logger.info("Tab 2: Data table displayed")
                else:
                    st.info("No data available to display")

            # ----------------------------------------------
            # TAB 3: SUMMARY
            # ----------------------------------------------
            with tab3:
                st.subheader("Summary")
                st.warning("🚧 This Project is under development.")
                
                # Basic statistics
                if df is not None:
                    st.write("**Dataset Shape:**", df.shape)
                    st.write("**Columns:**", df.columns.tolist())
                    logger.info("Tab 3: Summary displayed")

            # ----------------------------------------------
            # TAB 4: DATASET INFORMATION
            # ----------------------------------------------
            with tab4:
                st.subheader("Dataset Information")
                st.warning("🚧 This Project is under development.")
                
                # Dataset info
                if df is not None:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Rows", len(df))
                        st.metric("Total Columns", len(df.columns))
                    with col2:
                        st.metric("Missing Values", df.isnull().sum().sum())
                        st.metric("Duplicate Rows", df.duplicated().sum())
                    logger.info("Tab 4: Dataset information displayed")

            # ----------------------------------------------
            # TAB 5: VISUALIZATIONS
            # ----------------------------------------------
            with tab5:
                st.subheader("Data Visualizations")
                st.warning("🚧 This Project is under development.")
                logger.info("Tab 5: Visualizations tab opened")

        # ==================================================
        # OTHER DASHBOARDS
        # ==================================================
        else:
            dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
            st.info(f"🚧 {dashboard_type} is under development. Coming soon!")
            logger.info("Dashboard under development | type=%s", dashboard_type_clean)
            
            # Placeholder content
            with st.expander("📋 Planned Features"):
                st.markdown(f"""
                ### {dashboard_type}
                
                This dashboard will include:
                - Advanced analytics features
                - Interactive visualizations
                - Real-time data processing
                - Machine learning models
                - Export capabilities
                
                **Status:** In Development
                **Expected Release:** Q1 2025
                """)
        
        logger.info("Dashboard rendering completed successfully")
        
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Dashboard rendering error | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while rendering the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)           


# streamlit_analysis_app.py
 