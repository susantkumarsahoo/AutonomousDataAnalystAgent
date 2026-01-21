import os
import io
import sys
import time
import requests
import pandas as pd
import numpy as np
from io import BytesIO
from pathlib import Path
from typing import Optional
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.utils.helper import read_yaml
from ml_project.frontend_api.streamlit_cache_data import fetch_close_power_outage_duration
from ml_project.frontend_api.streamlit_analysis_helper import close_power_outage_duration


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]


from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")


# streamlit run main.py


# ========================================
# SECTION 7: POWER OUTAGE DURATION
# ======================================== 

st.header("X-Dashboard Shift wise Power Outage Duration Hour Analysis")


try:
    dataset_path = get_dataset_path("data/raw")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")

    API_URL = "http://localhost:8000"
    FASTAPI_URL = "http://localhost:8000"
    FLASK_URL = "http://localhost:5000"

