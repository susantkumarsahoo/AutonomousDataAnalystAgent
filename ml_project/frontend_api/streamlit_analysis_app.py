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
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.configs.config import DatasetNotFoundError, get_dataset_path
from ml_project.frontend_api.streamlit_analysis_tab1 import streamlit_analysis_tab1
from ml_project.frontend_api.steramlit_analysis_tab2 import streamlit_analysis_tab2
from ml_project.frontend_api.streamlit_analysis_tab3 import streamlit_analysis_tab3
from ml_project.frontend_api.streamlit_analysis_tab4 import streamlit_analysis_tab4


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

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

def analysis_dashboard(dashboard_type: str, dataset_path: Optional[str] = None,
                       uploaded_file: Optional[object] = None,
) -> None:
    """
    Render the selected dashboard with lazy tab loading.

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
            
            # Initialize session state for active tab if not exists
            if 'active_tab' not in st.session_state:
                st.session_state.active_tab = 0
            
            # Create tabs
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
                [
                    "📈 Complaint Overview",
                    "📋 Data Table Reports",
                    "💼 Financial Year Report",
                    "📊 PPT / Executive Reports",
                    "🗂️ Raw Data Reports",
                    "🔍 Dataset Information",
                    "📉 Visual Analytics",
                ]
            )

            # Map tabs to their indices
            tabs = [tab1, tab2, tab3, tab4, tab5, tab6, tab7]
            
            # Detect active tab by checking which one has content
            # Streamlit doesn't have built-in tab detection, so we use buttons/radio
            # Alternative approach: Use radio buttons or selectbox for explicit tab selection
            
            # ----------------------------------------------
            # LAZY LOADING IMPLEMENTATION
            # ----------------------------------------------
            
            # TAB 1: COMPLAINT OVERVIEW
            with tab1:
                if st.session_state.get('force_load_tab1', False) or \
                   st.button("🔄 Load Complaint Overview", key="load_tab1"):
                    st.session_state.force_load_tab1 = True
                    with st.spinner("Loading Complaint Overview..."):
                        streamlit_analysis_tab1(tab1, dataset_path, logger)
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 2: DATA TABLE REPORTS
            with tab2:
                if st.session_state.get('force_load_tab2', False) or \
                   st.button("🔄 Load Data Table Reports", key="load_tab2"):
                    st.session_state.force_load_tab2 = True
                    with st.spinner("Loading Data Table Reports..."):
                        streamlit_analysis_tab2(tab2, dataset_path, logger)
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 3: FINANCIAL YEAR REPORT
            with tab3:
                if st.session_state.get('force_load_tab3', False) or \
                   st.button("🔄 Load Financial Year Report", key="load_tab3"):
                    st.session_state.force_load_tab3 = True
                    with st.spinner("Loading Financial Year Report..."):
                        streamlit_analysis_tab3(tab3, dataset_path, logger)
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 4: PPT / EXECUTIVE REPORTS
            with tab4:
                if st.session_state.get('force_load_tab4', False) or \
                   st.button("🔄 Load PPT / Executive Reports", key="load_tab4"):
                    st.session_state.force_load_tab4 = True
                    with st.spinner("Loading PPT / Executive Reports..."):
                        streamlit_analysis_tab4(tab4, dataset_path, logger)
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 5: RAW DATA REPORTS
            with tab5:
                if st.session_state.get('force_load_tab5', False) or \
                   st.button("🔄 Load Raw Data Reports", key="load_tab5"):
                    st.session_state.force_load_tab5 = True
                    st.success("🛠️ This project is under development.")
                    # Add your tab5 logic here when ready
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 6: DATASET INFORMATION
            with tab6:
                if st.session_state.get('force_load_tab6', False) or \
                   st.button("🔄 Load Dataset Information", key="load_tab6"):
                    st.session_state.force_load_tab6 = True
                    st.success("🛠️ This project is under development.")
                    # Add your tab6 logic here when ready
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")

            # TAB 7: VISUAL ANALYTICS
            with tab7:
                if st.session_state.get('force_load_tab7', False) or \
                   st.button("🔄 Load Visual Analytics", key="load_tab7"):
                    st.session_state.force_load_tab7 = True
                    st.success("🛠️ This project is under development.")
                    # Add your tab7 logic here when ready
                else:
                    st.info("👆 Click the button above to load this tab's content")
                    st.caption("💡 Data will only be fetched when you load this tab")


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