import os
import io
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
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_analysis_helper import generate_all_agging_complaint_report


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

def demo_dashboard(
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
        if "Mathematics & Statistical Analysis" in dashboard_type:
           
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
                    "📈 Mathmatic Data Count",
                    "📋 Math Analysis",
                    "📊 Summary",
                    "🔍 Data Strucher",
                    "📊 Math Ploting",
                ]
            )

            # ----------------------------------------------
            # TAB 1: COMPLAINT OVERVIEW
            # ----------------------------------------------

            with tab1:
                st.success("🛠️ This project is under development.")

                st.title("Celebrate with Balloons and Snow")

                # Trigger balloons
                if st.button("Launch Balloons"):
                    st.balloons()  # Celebratory balloons
                    st.success("Balloons launched!")

                # Trigger snow
                if st.button("Make it Snow"):
                    st.snow()  # Celebratory snowfall
                    st.success("Snowfall activated!")

                # Bonus: show after a progress
                st.write("Simulate a task, then celebrate:")
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)

                st.info("Task complete — enjoy the effects!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Celebrate with Balloons after task"):
                        st.balloons()
                with col2:
                    if st.button("Celebrate with Snow after task"):
                        st.snow()




    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Dashboard rendering error | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while rendering the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
