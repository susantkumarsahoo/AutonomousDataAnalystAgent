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
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.backend_api.fastapi_analysis_helper import*
from ml_project.frontend_api.streamlit_analysis_helper import*
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import(
load_excel_data,

)



config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")
    
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

# ================================================================
# STREAMLIT APP FOR TAB 4
# ================================================================

def streamlit_analysis_tab4(tab4, dataset_path, logger):
    """
    Renders all content for Tab 4 including analysis and reports.
    
    Parameters:
    -----------
    tab4 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:
        with tab4:
            # ========================================
            # Initialize Session State
            # ========================================
            st.header("📊 Text Row Data Analysis")
            st.caption("Analyze text data in the dataset")


            

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 4 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
