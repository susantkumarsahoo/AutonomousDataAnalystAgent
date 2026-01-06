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
from ml_project.backend_api.fastapi_analysis_helper import open_complaint_pivot

from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]

API_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

logger = get_logger(__name__)


# =====================================================
# CACHED API FUNCTIONS
# =====================================================

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_open_complaint_pivot():
    """Fetch open complaint pivot data from API - cached"""
    try:
        response = fastapi_api_request_url("/open_complaint_pivot")
        if response is not None and response.status_code == 200:
            response_data = response.json()
            if response_data:
                return pd.DataFrame(response_data), None, response.status_code
            else:
                return None, "No data available", response.status_code
        else:
            status = response.status_code if response else None
            return None, f"API error", status
    except Exception as e:
        logger.error(f"Error fetching open complaint pivot: {e}")
        return None, str(e), None


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_open_close_complaint_pivot():
    """Fetch open/close complaint pivot data from API - cached"""
    try:
        response = fastapi_api_request_url("/open_close_complaint_pivot")
        if response is not None and response.status_code == 200:
            response_data = response.json()
            if response_data:
                return pd.DataFrame(response_data), None, response.status_code
            else:
                return None, "No data available", response.status_code
        else:
            status = response.status_code if response else None
            return None, f"API error", status
    except Exception as e:
        logger.error(f"Error fetching open/close complaint pivot: {e}")
        return None, str(e), None


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_agging_open_pivot():
    """Fetch agging open pivot data from API - cached"""
    try:
        response = fastapi_api_request_url("/agging_open_pivot_dict")
        if response is not None and response.status_code == 200:
            response_data = response.json()
            if response_data:
                return pd.DataFrame(response_data), None, response.status_code
            else:
                return None, "No data available", response.status_code
        else:
            status = response.status_code if response else None
            return None, f"API error", status
    except Exception as e:
        logger.error(f"Error fetching agging open pivot: {e}")
        return None, str(e), None


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_agging_open_close_pivot():
    """Fetch agging open/close pivot data from API - cached"""
    try:
        response = fastapi_api_request_url("/agging_open_close_pivot_dict")
        if response is not None and response.status_code == 200:
            response_data = response.json()
            if response_data:
                return pd.DataFrame(response_data), None, response.status_code
            else:
                return None, "No data available", response.status_code
        else:
            status = response.status_code if response else None
            return None, f"API error", status
    except Exception as e:
        logger.error(f"Error fetching agging open/close pivot: {e}")
        return None, str(e), None


def style_grand_total_dataframe(df_pivot):
    """Apply styling to highlight Grand_Total row"""
    if 'Grand_Total' in df_pivot['COMPLAINT TYPE'].values:
        def highlight_grand_total(row):
            if row['COMPLAINT TYPE'] == 'Grand_Total':
                return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        return df_pivot.style.apply(highlight_grand_total, axis=1)
    else:
        return df_pivot


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
                st.success("🛠️ This project is under development.")
                # Add a header
                st.header("📈 Open-Close Complaints Overview")
                                           
                # Add refresh button
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("🔄 Refresh All", key="refresh_all_btn"):
                        st.cache_data.clear()
                        st.rerun()
                
                st.divider()

                # ========================================
                # SECTION 1: OPEN COMPLAINT PIVOT
                # ========================================
                with st.spinner("Loading data..."):
                    df_pivot, error, status_code = fetch_open_complaint_pivot()

                if error is None and df_pivot is not None:
                    st.subheader("📊 Open Complaints Pivot Table")
                    st.caption("Grand Total row is highlighted in red for easy identification")
                    
                    styled_df = style_grand_total_dataframe(df_pivot)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Complaint overview displayed successfully")
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        st.info("The API service may be experiencing issues. Please try again in a few moments.")
                        logger.error(f"Tab 1: API request failed with status code {status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                        logger.error(f"Tab 1: Error - {error}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()

                # ========================================
                # SECTION 2: OPEN/CLOSE COMPLAINTS PIVOT
                # ========================================
                st.subheader("📊 Open/Close Complaints Pivot Table")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_02, error_02, status_code_02 = fetch_open_close_complaint_pivot()

                if error_02 is None and df_pivot_02 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_02)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaints Pivot Table displayed successfully")
                else:
                    if status_code_02:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_02}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_02}")
                    else:
                        st.error(f"❌ Error: {error_02}")
                        logger.error(f"Tab 1: Error - {error_02}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()
                
                # ========================================
                # SECTION 3: AGGING OPEN COMPLAINTS PIVOT
                # ========================================
                st.header("📊 Agging Open Complaints Pivot Table")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_03, error_03, status_code_03 = fetch_agging_open_pivot()

                if error_03 is None and df_pivot_03 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_03)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open Complaints Pivot Table displayed successfully")
                else:
                    if status_code_03:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_03}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_03}")
                    else:
                        st.error(f"❌ Error: {error_03}")
                        logger.error(f"Tab 1: Error - {error_03}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()
                
                # ========================================
                # SECTION 4: AGGING OPEN/CLOSE COMPLAINTS PIVOT
                # ========================================
                st.header("📊 Agging Open/Close Complaints Pivot Table")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_04, error_04, status_code_04 = fetch_agging_open_close_pivot()

                if error_04 is None and df_pivot_04 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_04)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open/Close Complaints Pivot Table displayed successfully")
                else:
                    if status_code_04:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_04}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_04}")
                    else:
                        st.error(f"❌ Error: {error_04}")
                        logger.error(f"Tab 1: Error - {error_04}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()

            # ----------------------------------------------
            # TAB 2: DATA TABLE
            # ----------------------------------------------
            with tab2:
                st.subheader("Data Table")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 3: SUMMARY
            # ----------------------------------------------
            with tab3:
                st.subheader("Summary")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 4: DATASET INFORMATION
            # ----------------------------------------------
            with tab4:
                st.subheader("Dataset Information")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 5: VISUALIZATIONS
            # ----------------------------------------------
            with tab5:
                st.subheader("Data Visualizations")
                st.warning("🚧 This Project is under development.")

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
