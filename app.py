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

# Constants
API_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"
SAVE_DIR = "data/raw_path"

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

logger = get_logger(__name__)

# ============================================================================
# CACHED FUNCTIONS - Expensive operations cached for performance
# ============================================================================

@st.cache_data(ttl=120, show_spinner=False)
def get_cached_dataset_path():
    """Cache dataset path lookup for 30 seconds"""
    try:
        dataset_path = get_dataset_path("data/raw_path")
        logger.info(f"Dataset found at: {dataset_path}")
        return dataset_path, None
    except DatasetNotFoundError as e:
        logger.info(f"No dataset found: {e}")
        return None, str(e)

@st.cache_data(ttl=30, show_spinner=False)  # Increased TTL to reduce API calls
def check_api_status_cached():
    """Cache API status check for 30 seconds to reduce API calls"""
    try:
        is_connected, api_data = check_api_status()
        return is_connected, api_data
    except Exception as e:
        logger.error("API status check error | error=%s", str(e))
        return False, {"message": str(e), "dataset_path": None, "dataset_available": False}

@st.cache_data(ttl=120, show_spinner=False)  # Increased TTL
def check_fastapi_health():
    """Cache FastAPI health check"""
    try:
        response = fastapi_api_request_url("/healthcheck", timeout=5)
        if response and response.json().get("status") == "healthy":
            logger.info("FastAPI healthcheck successful")
            return "healthy"
        else:
            logger.error("FastAPI healthcheck failed")
            return "down"
    except Exception as e:
        logger.error("FastAPI healthcheck error | error=%s", str(e))
        return "error"

@st.cache_data(ttl=120, show_spinner=False)  # Increased TTL
def check_flask_health():
    """Cache Flask API health check"""
    try:
        response = flask_api_request_url("/healthcheck", timeout=5)
        if response and response.json().get("status") == "healthy":
            logger.info("Flask API healthcheck successful")
            return "healthy"
        else:
            logger.error("Flask API healthcheck failed")
            return "down"
    except Exception as e:
        logger.error("Flask API healthcheck error | error=%s", str(e))
        return "error"

@st.cache_data(show_spinner=False)
def get_files_in_directory(directory):
    """Cache directory file listing"""
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    
    # Dataset tracking
    if 'dataset_path' not in st.session_state:
        st.session_state.dataset_path = None
    
    if 'last_upload_time' not in st.session_state:
        st.session_state.last_upload_time = None
    
    if 'upload_count' not in st.session_state:
        st.session_state.upload_count = 0
    
    # Dashboard state
    if 'selected_dashboard' not in st.session_state:
        st.session_state.selected_dashboard = "📈 Analysis Dashboard"
    
    # API connection state
    if 'api_connected' not in st.session_state:
        st.session_state.api_connected = False
    
    # UI state
    if 'show_success_message' not in st.session_state:
        st.session_state.show_success_message = False
    
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = None
    
    # Error tracking
    if 'error_history' not in st.session_state:
        st.session_state.error_history = []
    
    # NEW: Prevent unnecessary reruns
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
    
    # NEW: Track if we need to rerun
    if 'force_rerun' not in st.session_state:
        st.session_state.force_rerun = False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def add_error_to_history(error_msg):
    """Track errors in session state"""
    st.session_state.error_history.append({
        'timestamp': datetime.now(),
        'error': error_msg
    })
    # Keep only last 10 errors
    if len(st.session_state.error_history) > 10:
        st.session_state.error_history = st.session_state.error_history[-10:]

def clear_all_cache():
    """Clear all cached data"""
    st.cache_data.clear()
    logger.info("All cache cleared")

def get_latest_file_in_directory(directory):
    """Get the most recently created file in directory"""
    files_in_dir = get_files_in_directory(directory)
    
    if not files_in_dir:
        return None
    
    latest_file = max(
        [os.path.join(directory, f) for f in files_in_dir],
        key=os.path.getctime
    )
    return latest_file

# ============================================================================
# MAIN APPLICATION
# ============================================================================

try:
    # Initialize session state
    initialize_session_state()
    
    # Create data directory if it doesn't exist
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    # Get initial dataset path (only if not already set)
    if st.session_state.dataset_path is None:
        dataset_path, error = get_cached_dataset_path()
        if dataset_path:
            st.session_state.dataset_path = dataset_path
    
    # Use session state dataset path
    dataset_path = st.session_state.dataset_path

    # -------------------------------------------------------------------------
    # Page Configuration
    # -------------------------------------------------------------------------
    st.set_page_config(
        page_title="Twitter Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Header
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
                🧭 XTPSM Insight Engine
            </h2>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------------------------------
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
                🧭 XTPSM Navigation Terminal!
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
        # Dashboard selection with session state
        # FIXED: Use index based on session state to prevent reruns
        dashboard_options = [
            "📈 Analysis Dashboard",
            "📊 Mathematics & Statistical Analysis",
            "🔮 Twitter Flow Prediction",
            "🕒 Time Series Analysis",
            "📝 Sentiment Analysis",
            "🗂️ CRM Database",
            "🤖 AI Chatbot"
        ]
        
        # Get current index
        try:
            current_index = dashboard_options.index(st.session_state.selected_dashboard)
        except ValueError:
            current_index = 0
        
        dashboard_type = st.radio(
            "Select Dashboard",
            dashboard_options,
            index=current_index,
            key='dashboard_selector',
            label_visibility="collapsed",
        )
        
        # FIXED: Only update and log when actually changed
        if dashboard_type != st.session_state.selected_dashboard:
            st.session_state.selected_dashboard = dashboard_type
            # Only log when dashboard actually changes, not on every rerun
            try:
                dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
                logger.info("Dashboard changed to: %s", dashboard_type_clean)
            except:
                logger.info("Dashboard changed")

        st.divider()

        # -------------------------------------------------------------------------
        # Data Source Section
        # -------------------------------------------------------------------------
        st.header("📁 Data Source")
        
        # Display current dataset status
        if dataset_path is None:
            st.warning("⚠️ No dataset currently loaded")
            st.info("👇 Please upload a dataset below to get started")
        else:
            st.success(f"✅ Dataset loaded")
            st.caption(f"📄 {os.path.basename(dataset_path)}")
            
            # Show upload count and time if available
            if st.session_state.last_upload_time:
                time_diff = datetime.now() - st.session_state.last_upload_time
                if time_diff.seconds < 60:
                    st.caption(f"⏱️ Uploaded {time_diff.seconds}s ago")
                else:
                    st.caption(f"⏱️ Uploaded {time_diff.seconds // 60}m ago")
            
            if st.session_state.upload_count > 0:
                st.caption(f"🔄 Total uploads: {st.session_state.upload_count}")
            
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload your data (CSV, Excel, or JSON)",
            type=["csv", "xlsx", "json"],
            help="Upload a new dataset to replace the current one",
            key='file_uploader'
        )

        # Handle file upload
        if uploaded_file is not None:
            # FIXED: Check if this is a new upload to prevent processing on every rerun
            current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            if 'last_uploaded_file_id' not in st.session_state or st.session_state.last_uploaded_file_id != current_file_id:
                with st.spinner("📤 Uploading file..."):
                    try:
                        # Remove previous files
                        for file in os.listdir(SAVE_DIR):
                            file_path_to_remove = os.path.join(SAVE_DIR, file)
                            try:
                                if os.path.isfile(file_path_to_remove):
                                    os.remove(file_path_to_remove)
                                    logger.info("Removed previous file | path=%s", file_path_to_remove)
                            except Exception as e:
                                logger.error("Error removing file | path=%s | error=%s", 
                                           file_path_to_remove, str(e))
                        
                        # Save new file
                        file_path = os.path.join(SAVE_DIR, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Update session state
                        st.session_state.dataset_path = file_path
                        st.session_state.last_upload_time = datetime.now()
                        st.session_state.upload_count += 1
                        st.session_state.show_success_message = True
                        st.session_state.last_uploaded_file_id = current_file_id
                        
                        # Clear cache to force refresh
                        clear_all_cache()

                        logger.info("New file saved | path=%s", file_path)
                        
                        # Show success message
                        st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")
                        st.info("🔄 Click **'Refresh System'** below to update the entire application")
                        
                        # Update dataset_path variable
                        dataset_path = file_path
                    
                    except Exception as e:
                        error_msg = f"Error uploading file: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        add_error_to_history(error_msg)
                        logger.error("File upload error | error=%s", str(e))

        st.divider()

        # -------------------------------------------------------------------------
        # System Refresh Section
        # -------------------------------------------------------------------------
        st.subheader("🔄 System Refresh")
        
        # Show last refresh time
        if st.session_state.last_refresh_time:
            time_since_refresh = datetime.now() - st.session_state.last_refresh_time
            st.caption(f"⏱️ Last refresh: {time_since_refresh.seconds}s ago")

        st.info("Once Reload dataset path and click Refresh System!")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh System", type="primary", use_container_width=True):
                with st.spinner("🔄 Refreshing system..."):
                    try:
                        if not os.path.exists(SAVE_DIR):
                            st.error(f"❌ Directory not found: {SAVE_DIR}")
                            logger.error("SAVE_DIR does not exist | path=%s", SAVE_DIR)
                        else:
                            # Get latest file
                            latest_file = get_latest_file_in_directory(SAVE_DIR)
                            
                            if latest_file:
                                # Update session state
                                st.session_state.dataset_path = latest_file
                                st.session_state.last_refresh_time = datetime.now()
                                
                                # Clear cache
                                clear_all_cache()
                                
                                logger.info("System refreshed | dataset_path=%s", latest_file)
                                st.success(f"✅ System refreshed successfully!")
                                st.info(f"📄 Active dataset: {os.path.basename(latest_file)}")
                                
                                # FIXED: Use st.rerun() properly without triggering on every click
                                st.session_state.force_rerun = True
                                st.rerun()
                            else:
                                st.warning("⚠️ No dataset found in directory. Please upload a file first.")
                                logger.warning("Refresh attempted but no files found in directory")
                    
                    except Exception as e:
                        error_msg = f"Error refreshing system: {str(e)}"
                        st.error(f"❌ {error_msg}")
                        add_error_to_history(error_msg)
                        logger.error("System refresh error | error=%s", str(e), exc_info=True)
        
        with col2:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                clear_all_cache()
                st.success("✅ Cache cleared!")
                st.rerun()

        st.divider()
    
        # -------------------------------------------------------------------------
        # API Status Section
        # -------------------------------------------------------------------------
        st.header("🔌 API Status")
        
        # Check API status with caching
        is_connected, api_data = check_api_status_cached()
        
        # Update session state
        st.session_state.api_connected = is_connected
        
        # Update dataset_path from API if available
        api_dataset_path = api_data.get("dataset_path")
        if api_dataset_path and api_dataset_path != "Not available" and api_dataset_path is not None:
            if api_dataset_path != st.session_state.dataset_path:
                st.session_state.dataset_path = api_dataset_path
                dataset_path = api_dataset_path
        
        # Display API status
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
            # Clear only API-related cache
            check_api_status_cached.clear()
            check_fastapi_health.clear()
            check_flask_health.clear()
            logger.info("API status refresh triggered")
            st.rerun()

        st.divider()

        # -------------------------------------------------------------------------
        # Service Status Section
        # -------------------------------------------------------------------------
        st.subheader("🖥️ Service Status")
        
        col1, col2, col3 = st.columns(3)
        
        # Check FastAPI health
        with col1:
            st.caption("FastAPI")
            fastapi_status = check_fastapi_health()
            if fastapi_status == "healthy":
                st.markdown("🟢 **Healthy**")
            elif fastapi_status == "down":
                st.markdown("🔴 **Down**")
            else:
                st.markdown("🔴 **Error**")
        
        # Check Flask health
        with col2:
            st.caption("Flask API")
            flask_status = check_flask_health()
            if flask_status == "healthy":
                st.markdown("🟢 **Healthy**")
            elif flask_status == "down":
                st.markdown("🔴 **Down**")
            else:
                st.markdown("🔴 **Error**")

        # Streamlit is always active
        with col3:
            st.caption("Streamlit")
            st.markdown("🟢 **Active**")

        st.divider()
    
        # -------------------------------------------------------------------------
        # Dashboard Info
        # -------------------------------------------------------------------------
        with st.expander("ℹ️ Dashboard Info"):
            st.info(
                f"""
                **Version:** 2.1  
                **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
                **API Status:** {"🟢 Connected" if is_connected else "🔴 Disconnected"}  
                **Dataset:** {os.path.basename(dataset_path) if dataset_path else "❌ No dataset"}  
                **Session Uploads:** {st.session_state.upload_count}  
                **Last Refresh:** {st.session_state.last_refresh_time.strftime("%H:%M:%S") if st.session_state.last_refresh_time else "Never"}
                """
            )
            
            # Show error history if any
            if st.session_state.error_history:
                st.warning(f"⚠️ {len(st.session_state.error_history)} errors in this session")
                with st.expander("View Error History"):
                    for idx, err in enumerate(reversed(st.session_state.error_history)):
                        st.text(f"{idx+1}. {err['timestamp'].strftime('%H:%M:%S')} - {err['error'][:100]}...")

    # -------------------------------------------------------------------------
    # MAIN CONTENT
    # -------------------------------------------------------------------------
    
    # Check if API is connected
    if not is_connected:
        st.title("⚠️ API Not Connected")
        st.warning("The FastAPI backend is not running yet. This is normal on first start.")
        
        st.info("""
        ### 📋 Quick Start Guide:
        
        **Step 1:** Upload your dataset using the file uploader in the sidebar  
        **Step 2:** Wait for the API to automatically restart (or manually restart)  
        **Step 3:** Click the **'Refresh API Status'** button in the sidebar  
        **Step 4:** Select a dashboard from the navigation panel  
        
        The system will automatically detect your uploaded file and start the services.
        """)

        st.image("https://via.placeholder.com/300x200.png?text=Upload+Dataset", 
                use_container_width=True)

        if st.button("🔄 Refresh All", type="primary"):
            clear_all_cache()
            st.rerun()
        
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
                🤖 Welcome to the CRM AI Automation Engine!
            </div>
            """,
            unsafe_allow_html=True)

        st.markdown("""
        ### 🚀 Get Started
        
        No dataset is currently loaded. To begin using the AI Engine!
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
            #### 3️⃣ Select AI Report
            Choose a dashboard from the navigation panel to start analyzing
            """)
        
        st.divider()
        
        st.markdown("""
        ### 📊 Available Panels:
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
            # Set environment variable for dataset path
            os.environ['DATASET_PATH'] = dataset_path
            
            # Show celebration only on first successful load
            if st.session_state.show_success_message:
                st.balloons()
                st.session_state.show_success_message = False
            
            # Render the selected dashboard
            # FIXED: Only show spinner and log on actual dashboard changes
            if 'last_rendered_dashboard' not in st.session_state or st.session_state.last_rendered_dashboard != dashboard_type:
                with st.spinner(f"Loading {dashboard_type}..."):
                    analysis_dashboard(dashboard_type, dataset_path, uploaded_file)
                    st.session_state.last_rendered_dashboard = dashboard_type
                    
                    try:
                        dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
                        logger.info("Dashboard rendered successfully | type=%s", dashboard_type_clean)
                    except:
                        logger.info("Dashboard rendered successfully")
            else:
                # Just render without spinner if it's the same dashboard
                analysis_dashboard(dashboard_type, dataset_path, uploaded_file)
        
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            add_error_to_history(error_msg)
            logger.error("Dashboard rendering error | error=%s", error_msg)
            
            st.error("❌ An error occurred while loading the dashboard")
            
            with st.expander("🔍 Show error details"):
                st.code(error_msg)
                
            st.info("""
            **Troubleshooting:**
            - Try refreshing the page
            - Re-upload your dataset
            - Check if the dataset format is correct
            - Clear cache and try again
            - Contact support if the issue persists
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry", type="primary", use_container_width=True):
                    clear_all_cache()
                    st.rerun()
            with col2:
                if st.button("📋 Copy Error", use_container_width=True):
                    st.code(error_msg)
    
except Exception as e:
    error_msg = str(CustomException(e, sys))
    add_error_to_history(error_msg)
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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Page", type="primary", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Cache & Refresh", use_container_width=True):
            clear_all_cache()
            st.rerun()