import sys
import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import numpy as np
from ml_project.frontend_api.streamlit_analysis_app import analysis_dashboard
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url, check_api_status
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

# Try to get dataset path, but don't fail if it doesn't exist yet
try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    dataset_path = None
    print(f"No dataset found yet: {e}")

API_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

logger = get_logger(__name__)

try:
    # -----------------------------------------------------------------------------
    # Page Configuration
    # -----------------------------------------------------------------------------
    st.set_page_config(
        page_title="Twitter Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(44, 83, 100, 0.5);
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #4ECDC4;
    '>
        <h2 style='
            color: #4ECDC4;
            font-weight: bold;
            margin: 0;
            font-size: 28px;
            letter-spacing: 1px;
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
        '>
            🧭 CRM Navigation Panel TPSM
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #0F2027 0%, #203A43 50%, #2C5364 100%);
            padding: 10px;
            border-radius: 15px;
            box-shadow: 0 8px 20px rgba(44, 83, 100, 0.5);
            text-align: center;
            margin-bottom: 20px;
            border: 2px solid #4ECDC4;
        '>
            <h2 style='
                color: #4ECDC4;
                font-weight: bold;
                margin: 0;
                font-size: 28px;
                letter-spacing: 1px;
                text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
            '>
                🧭 Navigation Panel
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
        dashboard_type = st.radio(
            "Select Dashboard",
            [
                "📈 Analysis Dashboard",
                "📊 Mathematics & Statistical Analysis",
                "🔮 Twitter Flow Prediction",
                "🕒 Time Series Analysis",
                "📝 Sentiment Analysis",
                "🗂️ CRM Database",
                "🤖 AI Chatbot"
            ],
            label_visibility="collapsed",
        )

        st.divider()

        st.header("📁 Data Source")
        
        # Check if dataset exists
        if dataset_path is None:
            st.warning("⚠️ No dataset currently loaded")
            st.info("👇 Please upload a dataset below to get started")
        else:
            st.success(f"✅ Dataset loaded")
            st.caption(f"📄 {os.path.basename(dataset_path)}")
            
        uploaded_file = st.file_uploader(
            "Upload your data (CSV, Excel, or JSON)",
            type=["csv", "xlsx", "json"],
            help="Upload a new dataset to replace the current one"
        )

        # Define save directory
        SAVE_DIR = "data/raw_path"

        # Create directory if it doesn't exist
        os.makedirs(SAVE_DIR, exist_ok=True)

        if uploaded_file is not None:
            try:
                # Remove all previous files in the directory
                for file in os.listdir(SAVE_DIR):
                    file_path_to_remove = os.path.join(SAVE_DIR, file)
                    try:
                        if os.path.isfile(file_path_to_remove):
                            os.remove(file_path_to_remove)
                            logger.info("Removed previous file | path=%s", file_path_to_remove)
                    except Exception as e:
                        logger.error("Error removing file | path=%s | error=%s", file_path_to_remove, str(e))
                
                # Full path where new file will be saved
                file_path = os.path.join(SAVE_DIR, uploaded_file.name)

                # Save new file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Update dataset_path to the newly uploaded file
                dataset_path = file_path

                logger.info("New file saved | path=%s", file_path)
                st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")
                st.info("🔄 Click **'Refresh API Status'** below to update the system")
            
            except Exception as e:
                st.error(f"❌ Error uploading file: {str(e)}")
                logger.error("File upload error | error=%s", str(e))

        st.divider()
    
        st.header("🔌 API Status")
        
        try:
            is_connected, api_data = check_api_status()
        except Exception as e:
            is_connected = False
            api_data = {"message": str(e), "dataset_path": None, "dataset_available": False}
            logger.error("API status check error | error=%s", str(e))
        
        # Update dataset_path from API if available
        api_dataset_path = api_data.get("dataset_path")
        if api_dataset_path and api_dataset_path != "Not available" and api_dataset_path is not None:
            dataset_path = api_dataset_path
        
        if is_connected:
            st.success("✅ API Connected")
            if api_data.get("dataset_available"):
                st.info("📂 Dataset available in API")
            else:
                st.warning("⚠️ No dataset found in API")
        else:
            st.error("❌ API Disconnected")
            st.caption("The API will start once you upload a dataset")
            with st.expander("Show error details"):
                st.code(api_data.get("message", "Unknown error"))
    
        if st.button("🔄 Refresh API Status", use_container_width=True):
            logger.info("API status refresh triggered")
            st.rerun()

        st.divider()

        # API Service Status
        st.subheader("🖥️ Service Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("FastAPI")
            try:
                response = fastapi_api_request_url("/healthcheck", timeout=5)
                if response and response.json().get("status") == "healthy":
                    st.markdown("🟢 **Healthy**")
                    logger.info("FastAPI healthcheck successful")
                else:
                    st.markdown("🔴 **Down**")
                    logger.error("FastAPI healthcheck failed")
            except Exception as e:
                st.markdown("🔴 **Error**")
                logger.error("FastAPI healthcheck error | error=%s", str(e))
        
        with col2:
            st.caption("Flask API")
            try:
                response = flask_api_request_url("/healthcheck", timeout=5)
                if response and response.json().get("status") == "healthy":
                    st.markdown("🟢 **Healthy**")
                    logger.info("Flask API healthcheck successful")
                else:
                    st.markdown("🔴 **Down**")
                    logger.error("Flask API healthcheck failed")
            except Exception as e:
                st.markdown("🔴 **Error**")
                logger.error("Flask API healthcheck error | error=%s", str(e))

        with col3:
            st.caption("Streamlit")
            try:
                st.markdown("🟢 **Active**")
                logger.info("Streamlit healthcheck successful")
            except Exception as e:
                st.markdown("🔴 **Error**")
                logger.error("Streamlit healthcheck error | error=%s", str(e))

        st.divider()
    
        with st.expander("ℹ️ Dashboard Info"):
            st.info(
                f"""
                **Version:** 2.0  
                **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
                **API Status:** {"🟢 Connected" if is_connected else "🔴 Disconnected"}  
                **Dataset:** {os.path.basename(dataset_path) if dataset_path else "❌ No dataset"}
                """
            )

    # -----------------------------------------------------------------------------
    # MAIN CONTENT
    # -----------------------------------------------------------------------------
    
    # Check if API is connected
    if not is_connected:
        st.title("⚠️ API Not Connected")
        st.warning("The FastAPI backend is not running yet. This is normal on first start.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            ### 📋 Quick Start Guide:
            
            **Step 1:** Upload your dataset using the file uploader in the sidebar  
            **Step 2:** Wait for the API to automatically restart (or manually restart)  
            **Step 3:** Click the **'Refresh API Status'** button in the sidebar  
            **Step 4:** Select a dashboard from the navigation panel  
            
            The system will automatically detect your uploaded file and start the services.
            """)
        
        with col2:
            st.image("https://via.placeholder.com/300x200.png?text=Upload+Dataset", use_container_width=True)
        
        logger.warning("API unavailable - waiting for dataset upload and server restart")
    
    # Check if dataset exists
    elif dataset_path is None:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
                        padding: 25px;
                        border-radius: 15px;
                        text-align: center;
                        font-size: 32px;
                        font-weight: bold;
                        color: white;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25);'>
                🤖 Welcome to the CRM AI Agent Automation Engine
            </div>
            """,
            unsafe_allow_html=True)

        
        st.markdown("""
        ### 🚀 Get Started
        
        No dataset is currently loaded. To begin using the AI Engine !
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            #### 1️⃣ Upload Data
            Use the file uploader in the sidebar to upload your CSV, Excel, or JSON file
            """)
        
        with col2:
            st.info("""
            #### 2️⃣ Refresh Status
            Click the 'Refresh API Status' button to update the system
            """)
        
        with col3:
            st.info("""
            #### 3️⃣ Select Dashboard
            Choose a dashboard from the navigation panel to start analyzing
            """)
        
        st.divider()
        
        st.markdown("""
        ### 📊 Available Panel:
        - **Analysis Dashboard** - Comprehensive data overview
        - **Mathematics & Statistical Analysis** - Statistical insights
        - **Twitter Flow Prediction** - Predictive analytics
        - **Time Series Analysis** - Temporal patterns
        - **Sentiment Analysis** - Emotion and sentiment tracking
        - **CRM Database** - Customer relationship management
        - **AI Chatbot** - Interactive AI assistant
        """)
        
        logger.warning("No dataset available - waiting for upload")
    
    # Everything is ready - show the dashboard
    else:
        try:
            # Strip emoji from dashboard_type for logging
            dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
            logger.info("Rendering dashboard | type=%s | dataset=%s", dashboard_type_clean, os.path.basename(dataset_path))
            
            # Celebration for successful load
            st.balloons()
            
            # Set environment variable for dataset path
            os.environ['DATASET_PATH'] = dataset_path
            
            # Render the selected dashboard
            analysis_dashboard(dashboard_type, dataset_path, uploaded_file)
            
            logger.info("Dashboard rendered successfully | type=%s", dashboard_type_clean)
        
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error("Dashboard rendering error | error=%s", error_msg)
            
            st.error("❌ An error occurred while loading the dashboard")
            
            with st.expander("🔍 Show error details"):
                st.code(error_msg)
                
            st.info("""
            **Troubleshooting:**
            - Try refreshing the page
            - Re-upload your dataset
            - Check if the dataset format is correct
            - Contact support if the issue persists
            """)
    
except Exception as e:
    error_msg = str(CustomException(e, sys))
    logger.error("Critical application error | error=%s", error_msg)
    
    st.error("❌ Critical Application Error")
    st.markdown("""
    ### Something went wrong!
    
    Please try the following:
    1. Refresh the page
    2. Clear your browser cache
    3. Restart the application
    4. Check the error details below
    """)
    
    with st.expander("🔍 Error Details"):
        st.code(error_msg)