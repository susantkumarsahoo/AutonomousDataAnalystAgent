"""
Analysis Dashboard Module
Provides lazy-loaded tabs for various data analysis views
"""
import os
import sys
import time
from typing import Optional, Dict, Any
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.configs.config import DatasetNotFoundError, get_dataset_path
from ml_project.frontend_api.streamlit_analysis_tab1 import streamlit_analysis_tab1
from ml_project.frontend_api.steramlit_analysis_tab2 import streamlit_analysis_tab2
from ml_project.frontend_api.streamlit_analysis_tab3 import streamlit_analysis_tab3
from ml_project.frontend_api.streamlit_analysis_tab4 import streamlit_analysis_tab4


# ============================================================
# CONFIGURATION & SETUP
# ============================================================

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

# Initialize logger
logger = get_logger(__name__)




# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_config_and_dataset() -> tuple[Dict[str, Any], Optional[str]]:
    """
    Load configuration and get dataset path.
    
    Returns:
        tuple: (config dict, dataset_path str or None)
    """
    try:
        config = read_yaml("ml_project/configs/ml_project_config.yaml")
        dataset_path = get_dataset_path("data/raw_path")
        logger.info(f"Dataset found at: {dataset_path}")
        return config, dataset_path
    except DatasetNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        return {}, None
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return {}, None


def initialize_session_state() -> None:
    """Initialize all session state variables for tab loading."""
    tab_keys = [
        'force_load_tab1', 'force_load_tab2', 'force_load_tab3', 
        'force_load_tab4', 'force_load_tab5', 'force_load_tab6', 
        'force_load_tab7'
    ]
    
    for key in tab_keys:
        if key not in st.session_state:
            st.session_state[key] = False
    
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0


def clean_dashboard_name(dashboard_type: str) -> str:
    """
    Remove emojis and special characters from dashboard type for logging.
    
    Args:
        dashboard_type: Dashboard name that may contain emojis
        
    Returns:
        Cleaned dashboard name string
    """
    return dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()


def render_tab_loader(
    tab_key: str, 
    tab_name: str, 
    tab_function: Optional[callable] = None,
    dataset_path: Optional[str] = None
) -> None:
    """
    Render a lazy-loaded tab with consistent UI.
    
    Args:
        tab_key: Session state key for this tab
        tab_name: Display name for the tab
        tab_function: Function to call when loading the tab (optional)
        dataset_path: Path to dataset (optional)
    """
    session_key = f'force_load_{tab_key}'
    button_key = f'load_{tab_key}'
    
    if st.session_state.get(session_key, False) or \
       st.button(f"🔄 Load {tab_name}", key=button_key, use_container_width=True):
        st.session_state[session_key] = True
        
        if tab_function is not None:
            with st.spinner(f"Loading {tab_name}..."):
                try:
                    tab_function(dataset_path, logger)
                except Exception as e:
                    error_msg = str(CustomException(e, sys))
                    logger.error(f"Error loading {tab_name}: {error_msg}")
                    st.error(f"❌ Failed to load {tab_name}")
                    with st.expander("Show error details"):
                        st.code(error_msg)
        else:
            st.success("🛠️ This section is under development.")
    else:
        st.info("👆 Click the button above to load this tab's content")
        st.caption("💡 Data will only be fetched when you load this tab")


def render_under_development_placeholder(dashboard_type: str) -> None:
    """
    Render placeholder content for dashboards under development.
    
    Args:
        dashboard_type: Name of the dashboard
    """
    dashboard_clean = clean_dashboard_name(dashboard_type)
    st.info(f"🚧 {dashboard_type} is under development. Coming soon!")
    logger.info("Dashboard under development | type=%s", dashboard_clean)

    with st.expander("📋 Planned Features"):
        st.markdown(f"""
        ### {dashboard_type}

        This dashboard will include:
        - 📊 Advanced analytics features
        - 📈 Interactive visualizations
        - ⚡ Real-time data processing
        - 🤖 Machine learning models
        - 📤 Export capabilities

        **Status:** In Development  
        **Expected Release:** Q2 2025
        """)


# ============================================================
# MAIN DASHBOARD FUNCTION
# ============================================================

def analysis_dashboard(
    dashboard_type: str, 
    dataset_path: Optional[str] = None,
    uploaded_file: Optional[object] = None,
) -> None:
    """
    Render the selected dashboard with lazy tab loading.

    Args:
        dashboard_type: Selected dashboard option
        dataset_path: Path to the default dataset
        uploaded_file: Optional user-uploaded file
    """
    try:
        # Log dashboard rendering
        dashboard_clean = clean_dashboard_name(dashboard_type)
        logger.info("Rendering analysis dashboard | type=%s", dashboard_clean)
        
        # Initialize session state
        initialize_session_state()
        
        # If dataset_path not provided, try to get it from config
        if dataset_path is None:
            _, dataset_path = get_config_and_dataset()
            if dataset_path is None:
                st.warning("⚠️ Dataset not found. Some features may be limited.")
        
        # Page Title
        st.title(dashboard_type)

        # ==================================================
        # ANALYSIS DASHBOARD
        # ==================================================
        if "Analysis Dashboard" in dashboard_type:
            
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

            st.markdown("""
                <style>
                div.stButton > button:first-child {
                    background-image: linear-gradient(to right, #667eea, #764ba2); /* purple-indigo gradient */
                    color: white;
                    border-radius: 10px;
                    height: 3em;
                    width: 100%;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    transition: 0.3s;
                }
                div.stButton > button:hover {
                    background-image: linear-gradient(to right, #f093fb, #f5576c); /* pink-coral gradient */
                    color: white;
                    transform: scale(1.05);
                }
                </style>
            """, unsafe_allow_html=True)



            # ----------------------------------------------
            # TAB 1: COMPLAINT OVERVIEW
            # ----------------------------------------------
            with tab1:
                render_tab_loader(
                    tab_key='tab1',
                    tab_name='Complaint Overview',
                    tab_function=lambda dp, lg: streamlit_analysis_tab1(tab1, dp, lg),
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 2: DATA TABLE REPORTS
            # ----------------------------------------------
            with tab2:
                render_tab_loader(
                    tab_key='tab2',
                    tab_name='Data Table Reports',
                    tab_function=lambda dp, lg: streamlit_analysis_tab2(tab2, dp, lg),
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 3: FINANCIAL YEAR REPORT
            # ----------------------------------------------
            with tab3:
                render_tab_loader(
                    tab_key='tab3',
                    tab_name='Financial Year Report',
                    tab_function=lambda dp, lg: streamlit_analysis_tab3(tab3, dp, lg),
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 4: PPT / EXECUTIVE REPORTS
            # ----------------------------------------------
            with tab4:
                render_tab_loader(
                    tab_key='tab4',
                    tab_name='PPT / Executive Reports',
                    tab_function=lambda dp, lg: streamlit_analysis_tab4(tab4, dp, lg),
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 5: RAW DATA REPORTS
            # ----------------------------------------------
            with tab5:
                render_tab_loader(
                    tab_key='tab5',
                    tab_name='Raw Data Reports',
                    tab_function=None,  # Not implemented yet
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 6: DATASET INFORMATION
            # ----------------------------------------------
            with tab6:
                render_tab_loader(
                    tab_key='tab6',
                    tab_name='Dataset Information',
                    tab_function=None,  # Not implemented yet
                    dataset_path=dataset_path
                )

            # ----------------------------------------------
            # TAB 7: VISUAL ANALYTICS
            # ----------------------------------------------
            with tab7:
                render_tab_loader(
                    tab_key='tab7',
                    tab_name='Visual Analytics',
                    tab_function=None,  # Not implemented yet
                    dataset_path=dataset_path
                )

        # ==================================================
        # OTHER DASHBOARDS (UNDER DEVELOPMENT)
        # ==================================================
        else:
            render_under_development_placeholder(dashboard_type)

        logger.info("Dashboard rendering completed successfully")

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Dashboard rendering error | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while rendering the dashboard.")
        with st.expander("🔍 Show error details"):
            st.code(error_msg)
            st.caption("Please report this error to the development team.")


