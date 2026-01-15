import os
import sys
import time
import io
from io import BytesIO
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
from ml_project.frontend_api.streamlit_analysis_helper import*
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import* 


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")


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
    uploaded_file: Optional[object] = None,) -> None:
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

            # ----------------------------------------------
            # TAB 2: DATA TABLE
            # ----------------------------------------------
            with tab2:
                st.success("🛠️ This project is under development.")

            # ----------------------------------------------
            # TAB 3: SUMMARY
            # ----------------------------------------------
            with tab3:
                st.success("🛠️ This project is under development.")

            # ----------------------------------------------
            # TAB 4: DATASET INFORMATION
            # ----------------------------------------------
            with tab4:
                st.success("🛠️ This project is under development.")

            # ----------------------------------------------
            # TAB 5: VISUALIZATIONS
            # ----------------------------------------------
            with tab5:
                st.success("🛠️ This project is under development.")


    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Dashboard rendering error | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while rendering the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)