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
from ml_project.frontend_api.streamlit_analysis_tab4_helper import (
    time_series_complaints_status_stacked,
    get_qrc_value_counts,
    get_complaint_type_value_counts_type,
    agging_all_open_pivot_table,
)
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
# CONFIGURATION
# ================================================================

# Custom CSS for better design
def load_custom_css():
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 2rem;
        }
        
        /* Header styling */
        .custom-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Card styling */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
            margin-bottom: 1rem;
        }
        
        /* Dataframe styling */
        .dataframe-container {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Button styling */
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 5px;
            padding: 0.5rem 2rem;
            border: none;
            font-weight: bold;
        }
        
        .stButton>button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 5px;
            font-weight: bold;
        }
        
        /* Info box styling */
        .info-box {
            background-color: #e7f3ff;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
            margin: 1rem 0;
        }
        
        /* Success box styling */
        .success-box {
            background-color: #e8f5e9;
            padding: 1rem;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
            margin: 1rem 0;
        }
        
        /* Control panel styling */
        .control-panel {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

# ================================================================
# HELPER FUNCTIONS
# ================================================================

@st.cache_data
def load_excel_data(dataset_path: str) -> pd.DataFrame:
    """Load Excel data with caching for performance"""
    try:
        df = pd.read_excel(dataset_path)
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return pd.DataFrame()

def style_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply styling to dataframe for better visualization"""
    return df.style.background_gradient(cmap='RdYlGn_r', subset=pd.IndexSlice[:, df.select_dtypes(include=[np.number]).columns])

def create_download_link(df: pd.DataFrame, filename: str = "filtered_data.csv"):
    """Create a download button for the dataframe"""
    csv = df.to_csv(index=False)
    return csv

# ================================================================
# VISUALIZATION FUNCTIONS - FIXED TO ACCEPT DATAFRAMES
# ================================================================

def create_time_series_chart(df: pd.DataFrame, chart_type: str = "line"):
    """Create time series visualization based on selected chart type"""
    if df.empty:
        st.warning("No data available for time series chart")
        return
    
    # Prepare data - FIXED: pass DataFrame instead of path
    pivot_df = time_series_complaints_status_stacked(df)
    
    if chart_type == "line":
        fig = px.line(pivot_df, x='YEAR', y='Total', 
                      title='Total Complaints Over Years',
                      labels={'Total': 'Number of Complaints', 'YEAR': 'Year'})
    elif chart_type == "bar":
        fig = px.bar(pivot_df, x='YEAR', y='Total',
                     title='Total Complaints by Year',
                     labels={'Total': 'Number of Complaints', 'YEAR': 'Year'})
    elif chart_type == "area":
        fig = px.area(pivot_df, x='YEAR', y='Total',
                      title='Complaint Trends (Area Chart)',
                      labels={'Total': 'Number of Complaints', 'YEAR': 'Year'})
    
    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def create_complaint_type_chart(df: pd.DataFrame, chart_type: str = "bar"):
    """Create complaint type visualization"""
    count_df = get_complaint_type_value_counts_type(df)
    
    if chart_type == "bar":
        fig = px.bar(count_df, x='COMPLAINT TYPE', y='count',
                     title='Top 5 Complaint Types',
                     labels={'count': 'Number of Complaints', 'COMPLAINT TYPE': 'Complaint Type'},
                     color='count',
                     color_continuous_scale='Viridis')
    elif chart_type == "pie":
        fig = px.pie(count_df, names='COMPLAINT TYPE', values='count',
                     title='Complaint Type Distribution',
                     hole=0.4)
    elif chart_type == "horizontal_bar":
        fig = px.bar(count_df, y='COMPLAINT TYPE', x='count',
                     title='Top 5 Complaint Types',
                     labels={'count': 'Number of Complaints', 'COMPLAINT TYPE': 'Complaint Type'},
                     orientation='h',
                     color='count',
                     color_continuous_scale='Blues')
    
    fig.update_layout(
        template='plotly_white',
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

def create_qrc_chart(df: pd.DataFrame):
    """Create Query/Request/Complaint distribution chart"""
    count_df = get_qrc_value_counts(df)
    
    fig = px.pie(count_df, names='QUERY/REQUEST/COMPLAINT', values='count',
                 title='Query/Request/Complaint Distribution',
                 color_discrete_sequence=px.colors.qualitative.Set3)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(template='plotly_white', height=400)
    st.plotly_chart(fig, use_container_width=True)

def create_aging_heatmap(df: pd.DataFrame):
    """Create heatmap for aging complaints - FIXED to accept DataFrame"""
    pivot_df = agging_all_open_pivot_table(df)
    
    # Remove Grand_Total for heatmap
    heatmap_data = pivot_df[pivot_df['COMPLAINT TYPE'] != 'Grand_Total'].copy()
    heatmap_data = heatmap_data.set_index('COMPLAINT TYPE')
    heatmap_data = heatmap_data.drop('Grand_Total', axis=1, errors='ignore')
    
    fig = px.imshow(heatmap_data,
                    labels=dict(x="Age Bucket", y="Complaint Type", color="Count"),
                    title="Complaint Aging Analysis (Heatmap)",
                    color_continuous_scale='RdYlGn_r',
                    aspect='auto')
    
    fig.update_layout(template='plotly_white', height=500)
    st.plotly_chart(fig, use_container_width=True)

def create_monthly_trend_chart(df: pd.DataFrame):
    """Create monthly trend chart"""
    df = df.copy()
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['MONTH_YEAR'] = df['DATE'].dt.to_period('M').astype(str)
    
    monthly_counts = df.groupby('MONTH_YEAR').size().reset_index(name='count')
    
    fig = px.line(monthly_counts, x='MONTH_YEAR', y='count',
                  title='Monthly Complaint Trends',
                  labels={'count': 'Number of Complaints', 'MONTH_YEAR': 'Month-Year'},
                  markers=True)
    
    fig.update_layout(
        template='plotly_white',
        xaxis_tickangle=-45,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# MAIN STREAMLIT APP FOR TAB 4
# ================================================================

def streamlit_analysis_tab4(tab4, dataset_path, logger=None):
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
            # Load custom CSS

            
            # ========================================
            # HEADER SECTION
            # ========================================
            st.markdown("""
                <div class="custom-header">
                    <h1>📊 PPT/Exclusive Analysis Dashboard</h1>
                    <p>Comprehensive analysis and visualization of reports</p>
                </div>
            """, unsafe_allow_html=True)
            
            # ========================================
            # CONTROL PANEL (Previously Sidebar Content)
            # ========================================
            with st.expander("🎛️ Control Panel & Filters", expanded=True):
                st.markdown("### 🎛️ Control Panel")
                
                # Data refresh button
                col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 1, 2])
                with col_refresh1:
                    if st.button("🔄 Refresh Data", use_container_width=True):
                        st.cache_data.clear()
                        st.success("Cache cleared! Data will be refreshed.")
                
                st.markdown("---")
                
                # Create columns for controls
                control_col1, control_col2 = st.columns(2)
                
                with control_col1:
                    st.markdown("### 📊 Visualization Options")
                    
                    # Visualization type selector
                    viz_type = st.selectbox(
                        "Select Primary Chart Type",
                        ["Line Chart", "Bar Chart", "Area Chart"],
                        help="Choose the type of chart for time series data"
                    )
                    
                    # Secondary chart type
                    complaint_viz_type = st.selectbox(
                        "Complaint Type Visualization",
                        ["Bar Chart", "Pie Chart", "Horizontal Bar"],
                        help="Choose visualization for complaint types"
                    )
                
                with control_col2:
                    st.markdown("### 🔍 Data Filters")
                    
                    # Date range filter
                    use_date_filter = st.checkbox("Enable Date Filter", value=False)
                    
                    if use_date_filter:
                        date_range = st.date_input(
                            "Select Date Range",
                            value=(datetime.now() - timedelta(days=365), datetime.now()),
                            help="Filter data by date range"
                        )
                    
                    # Show only open complaints
                    show_only_open = st.checkbox("Show Only Open Complaints", value=False)
                
                st.markdown("---")
                
                # Display options in columns
                display_col1, display_col2 = st.columns(2)
                
                with display_col1:
                    st.markdown("### 📋 Display Options")
                    num_rows = st.slider(
                        "Number of rows to display",
                        min_value=10,
                        max_value=1000,
                        value=100,
                        step=10,
                        help="Select how many rows to show in the dataframe"
                    )
                
                with display_col2:
                    st.markdown("### 🎨 Styling Options")
                    # Dataframe styling option
                    use_styling = st.checkbox("Apply Color Gradient", value=True,
                                             help="Apply color gradient to numeric columns")
                

            
            # ========================================
            # LOAD DATA
            # ========================================
            with st.spinner("Loading data..."):
                df = load_excel_data(dataset_path)
            
            if df.empty:
                st.error("❌ No data available. Please check the dataset path.")
                return
            
            # Apply filters
            filtered_df = df.copy()
            
            if use_date_filter and 'date_range' in locals():
                filtered_df['DATE'] = pd.to_datetime(filtered_df['DATE'])
                filtered_df = filtered_df[
                    (filtered_df['DATE'].dt.date >= date_range[0]) & 
                    (filtered_df['DATE'].dt.date <= date_range[1])
                ]
            
            if show_only_open:
                filtered_df = filtered_df[filtered_df['CLOSED/OPEN'].str.lower().str.strip() == 'open']
            
            # ========================================
            # KEY METRICS
            # ========================================
            st.markdown("### 📈 Key Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_complaints = len(filtered_df)
                st.metric(
                    label="Total Complaints",
                    value=f"{total_complaints:,}",
                    delta=f"{len(df) - total_complaints} filtered" if len(df) != total_complaints else None
                )
            
            with col2:
                if 'CLOSED/OPEN' in filtered_df.columns:
                    open_complaints = len(filtered_df[filtered_df['CLOSED/OPEN'].str.lower().str.strip() == 'open'])
                    st.metric(
                        label="Open Complaints",
                        value=f"{open_complaints:,}",
                        delta=f"{(open_complaints/total_complaints*100):.1f}%"
                    )
            
            with col3:
                if 'COMPLAINT TYPE' in filtered_df.columns:
                    unique_types = filtered_df['COMPLAINT TYPE'].nunique()
                    st.metric(
                        label="Complaint Types",
                        value=f"{unique_types}",
                    )
            
            with col4:
                if 'DATE' in filtered_df.columns:
                    filtered_df['DATE'] = pd.to_datetime(filtered_df['DATE'])
                    avg_age = (datetime.now() - filtered_df['DATE']).dt.days.mean()
                    st.metric(
                        label="Avg Age (Days)",
                        value=f"{avg_age:.0f}",
                    )
            
            st.markdown("---")
            
            # ========================================
            # INTERACTIVE DATAFRAME DISPLAY
            # ========================================
            st.markdown("### 📋 Dataset Overview")
            
            # Display info about the dataset
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="info-box">
                        <strong>Dataset Information:</strong><br>
                        • Rows: {len(filtered_df):,}<br>
                        • Columns: {len(filtered_df.columns)}<br>
                        • Memory: {filtered_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if 'DATE' in filtered_df.columns:
                    min_date = filtered_df['DATE'].min()
                    max_date = filtered_df['DATE'].max()
                    st.markdown(f"""
                        <div class="success-box">
                            <strong>Date Range:</strong><br>
                            • From: {min_date.strftime('%Y-%m-%d')}<br>
                            • To: {max_date.strftime('%Y-%m-%d')}<br>
                            • Duration: {(max_date - min_date).days} days
                        </div>
                    """, unsafe_allow_html=True)
            
            # Dataframe display with optional styling
            st.markdown("#### 🔍 Data Table")
            
            display_df = filtered_df.head(num_rows)
            
            if use_styling:
                # Apply gradient styling to numeric columns only
                numeric_cols = display_df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    styled_df = display_df.style.background_gradient(
                        cmap='RdYlGn_r',
                        subset=numeric_cols
                    )
                    st.dataframe(styled_df, use_container_width=True, height=400)
                else:
                    st.dataframe(display_df, use_container_width=True, height=400)
            else:
                st.dataframe(display_df, use_container_width=True, height=400)
            
            # Download button
            csv = create_download_link(filtered_df)
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv,
                file_name=f"complaint_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown("---")
            
            # ========================================
            # ANALYTICS SECTION
            # ========================================
            
            # Section 1: Time Series Analysis
            st.subheader("📅 Monthly Complaint Trends (Fiscal Year)")
            with st.spinner("Generating time series data..."):
                time_series_df = time_series_complaints_status_stacked(df)
                
                st.dataframe(
                    time_series_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Prepare data for visualization
                # Get month column (usually first column)
                month_col = time_series_df.columns[0]
                status_cols = [col for col in time_series_df.columns if col != month_col]
                
                # Create two columns for visualizations
                st.markdown("---")
                
                # Visualization 1: Multi-line Chart
                st.subheader("📈 Multi-line Trend Analysis")
                
                # Add interactive filters
                col1, col2 = st.columns([3, 1])
                with col2:
                    selected_statuses = st.multiselect(
                        "Select Status to Display",
                        options=status_cols,
                        default=status_cols,
                        key="multiline_filter"
                    )
                
                if selected_statuses:
                    fig1 = go.Figure()
                    
                    # Add traces for each selected status
                    for status in selected_statuses:
                        fig1.add_trace(go.Scatter(
                            x=time_series_df[month_col],
                            y=time_series_df[status],
                            name=status,
                            mode='lines+markers',
                            line=dict(width=2.5),
                            marker=dict(size=6),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                        'Month: %{x}<br>' +
                                        'Count: %{y}<br>' +
                                        '<extra></extra>'
                        ))
                    
                    fig1.update_layout(
                        title={
                            'text': 'Monthly Complaint Trends by Status',
                            'x': 0.5,
                            'xanchor': 'center'
                        },
                        xaxis_title="Month",
                        yaxis_title="Number of Complaints",
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=500,
                        template="plotly_white",
                        xaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='LightGray'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='LightGray'
                        )
                    )
                    
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("⚠️ Please select at least one status to display")
                
                st.markdown("---")
                
                # Visualization 2: Stacked Area Chart
                st.subheader("📊 Stacked Area Chart - Complaint Composition")
                
                # Add interactive filters for stacked area
                col3, col4 = st.columns([3, 1])
                with col4:
                    chart_type = st.radio(
                        "Chart Type",
                        options=["Absolute Count", "Percentage (100%)"],
                        key="area_chart_type"
                    )
                    
                    selected_statuses_area = st.multiselect(
                        "Select Status",
                        options=status_cols,
                        default=status_cols,
                        key="area_filter"
                    )
                
                if selected_statuses_area:
                    fig2 = go.Figure()
                    
                    # Calculate percentage if needed
                    if chart_type == "Percentage (100%)":
                        plot_df = time_series_df.copy()
                        plot_df[selected_statuses_area] = plot_df[selected_statuses_area].div(
                            plot_df[selected_statuses_area].sum(axis=1), axis=0
                        ) * 100
                        yaxis_title = "Percentage (%)"
                        hover_format = '.2f'
                        hover_suffix = '%'
                    else:
                        plot_df = time_series_df
                        yaxis_title = "Number of Complaints"
                        hover_format = ''
                        hover_suffix = ''
                    
                    # Add traces for each selected status
                    for status in selected_statuses_area:
                        fig2.add_trace(go.Scatter(
                            x=plot_df[month_col],
                            y=plot_df[status],
                            name=status,
                            mode='lines',
                            stackgroup='one',
                            fillcolor=None,  # Let Plotly assign colors
                            line=dict(width=0.5),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                        'Month: %{x}<br>' +
                                        'Value: %{y:' + hover_format + '}' + hover_suffix + '<br>' +
                                        '<extra></extra>'
                        ))
                    
                    fig2.update_layout(
                        title={
                            'text': f'Complaint Distribution Over Time ({chart_type})',
                            'x': 0.5,
                            'xanchor': 'center'
                        },
                        xaxis_title="Month",
                        yaxis_title=yaxis_title,
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=500,
                        template="plotly_white",
                        xaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='LightGray'
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='LightGray'
                        )
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Add summary metrics below the chart
                    st.markdown("### 📌 Summary Statistics")
                    metric_cols = st.columns(len(selected_statuses_area))
                    for idx, status in enumerate(selected_statuses_area):
                        with metric_cols[idx]:
                            total = time_series_df[status].sum()
                            avg = time_series_df[status].mean()
                            st.metric(
                                label=status,
                                value=f"{int(total):,}",
                                delta=f"Avg: {avg:.1f}/month"
                            )
                else:
                    st.warning("⚠️ Please select at least one status to display")
            
            st.divider()
            
            # Section 2: Query/Request/Complaint Distribution
            st.subheader("🔍 Query/Request/Complaint Distribution")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                with st.spinner("Analyzing complaint categories..."):
                    qrc_counts = get_qrc_value_counts(df)
                    st.dataframe(
                        qrc_counts,
                        use_container_width=True,
                        hide_index=True
                    )
            
            with col2:
                # Pie chart for QRC distribution
                fig_qrc = px.pie(
                    qrc_counts,
                    values='count',
                    names='QUERY/REQUEST/COMPLAINT',
                    title='Distribution by Category'
                )
                st.plotly_chart(fig_qrc, use_container_width=True)
            
            st.divider()
            
            # Section 3: Top 5 Complaint Types
            st.subheader("🏆 Top 5 Complaint Types")
            col3, col4 = st.columns([1, 1])
            
            with col3:
                with st.spinner("Identifying top complaint types..."):
                    complaint_type_counts = get_complaint_type_value_counts_type(df)
                    st.dataframe(
                        complaint_type_counts,
                        use_container_width=True,
                        hide_index=True
                    )
            
            with col4:
                # Bar chart for top complaint types
                fig_complaints = px.bar(
                    complaint_type_counts,
                    x='COMPLAINT TYPE',
                    y='count',
                    title='Top 5 Complaint Types',
                    labels={'count': 'Number of Complaints'}
                )
                fig_complaints.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_complaints, use_container_width=True)
            
            st.divider()
            
            
            
            
            # Section 4: Aging Analysis for Open Complaints
            st.subheader("⏰ Aging Analysis - Open Complaints")

            with st.spinner("Analyzing aging buckets..."):
                aging_pivot = agging_all_open_pivot_table(df)
                
                # Display pivot table
                st.dataframe(
                    aging_pivot,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Summary metrics
                st.markdown("### 📊 Key Metrics")
                total_open = aging_pivot.loc[aging_pivot['COMPLAINT TYPE'] == 'Grand_Total', 'Grand_Total'].values[0]
                
                col5, col6, col7 = st.columns(3)
                with col5:
                    st.metric("Total Open Complaints", f"{total_open:,}")
                with col6:
                    overdue = aging_pivot.loc[aging_pivot['COMPLAINT TYPE'] == 'Grand_Total', '>180Days'].values[0]
                    pct_overdue = (overdue / total_open * 100) if total_open > 0 else 0
                    st.metric("Overdue (>180 Days)", f"{overdue:,}", f"{pct_overdue:.1f}%")
                with col7:
                    recent = aging_pivot.loc[aging_pivot['COMPLAINT TYPE'] == 'Grand_Total', '<15Days'].values[0]
                    pct_recent = (recent / total_open * 100) if total_open > 0 else 0
                    st.metric("Recent (<15 Days)", f"{recent:,}", f"{pct_recent:.1f}%")
                
                st.markdown("---")
                
                # Visualization Controls
                st.markdown("### 📈 Interactive Visualizations")
                
                # Filter options
                col_filter1, col_filter2 = st.columns(2)
                
                with col_filter1:
                    # Exclude Grand Total for visualizations
                    complaint_types = aging_pivot[aging_pivot['COMPLAINT TYPE'] != 'Grand_Total']['COMPLAINT TYPE'].tolist()
                    
                    # Multi-select for complaint types
                    selected_complaints = st.multiselect(
                        "Select Complaint Types to Display",
                        options=complaint_types,
                        default=complaint_types[:5] if len(complaint_types) > 5 else complaint_types,
                        help="Choose which complaint types to show in the charts"
                    )
                
                with col_filter2:
                    # Chart type selector
                    chart_view = st.radio(
                        "Select View",
                        options=["Both Charts", "Line Chart Only", "Bar Chart Only"],
                        horizontal=True
                    )
                
                # Filter data based on selection
                if selected_complaints:
                    filtered_data = aging_pivot[aging_pivot['COMPLAINT TYPE'].isin(selected_complaints)]
                else:
                    st.warning("⚠️ Please select at least one complaint type to display charts")
                    filtered_data = pd.DataFrame()
                
                if not filtered_data.empty:
                    # Prepare data for visualizations
                    age_columns = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
                    
                    # LINE CHART
                    if chart_view in ["Both Charts", "Line Chart Only"]:
                        if chart_view == "Both Charts":
                            viz_col1, viz_col2 = st.columns(2)
                            line_container = viz_col1
                        else:
                            line_container = st.container()
                        
                        with line_container:
                            st.markdown("#### 📉 Aging Trend by Complaint Type")
                            
                            # Prepare data for line chart
                            line_data = filtered_data.melt(
                                id_vars=['COMPLAINT TYPE'],
                                value_vars=age_columns,
                                var_name='Age Bucket',
                                value_name='Count'
                            )
                            
                            # Create interactive line chart
                            fig_line = px.line(
                                line_data,
                                x='Age Bucket',
                                y='Count',
                                color='COMPLAINT TYPE',
                                markers=True,
                                title='Complaint Distribution Across Age Buckets',
                                labels={'Count': 'Number of Complaints', 'Age Bucket': 'Age Range'},
                                hover_data={'Count': ':,'}
                            )
                            
                            fig_line.update_traces(
                                mode='lines+markers',
                                marker=dict(size=8),
                                line=dict(width=2.5)
                            )
                            
                            fig_line.update_layout(
                                hovermode='x unified',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(
                                    showgrid=True,
                                    gridcolor='lightgray',
                                    gridwidth=0.5
                                ),
                                yaxis=dict(
                                    showgrid=True,
                                    gridcolor='lightgray',
                                    gridwidth=0.5
                                ),
                                legend=dict(
                                    orientation="v",
                                    yanchor="top",
                                    y=1,
                                    xanchor="left",
                                    x=1.02
                                ),
                                height=500
                            )
                            
                            st.plotly_chart(fig_line, use_container_width=True)
                    
                    # HORIZONTAL BAR CHART
                    if chart_view in ["Both Charts", "Bar Chart Only"]:
                        if chart_view == "Both Charts":
                            # viz_col2 is already defined above
                            bar_container = viz_col2
                        else:
                            bar_container = st.container()
                        
                        with bar_container:
                            st.markdown("#### 📊 Total Complaints by Type")
                            
                            # Prepare data for horizontal bar chart
                            bar_data = filtered_data[['COMPLAINT TYPE', 'Grand_Total']].copy()
                            bar_data = bar_data.sort_values('Grand_Total', ascending=True)
                            
                            # Create horizontal bar chart
                            fig_bar = px.bar(
                                bar_data,
                                x='Grand_Total',
                                y='COMPLAINT TYPE',
                                orientation='h',
                                title='Total Open Complaints by Type',
                                labels={'Grand_Total': 'Total Count', 'COMPLAINT TYPE': 'Complaint Type'},
                                text='Grand_Total',
                                color='Grand_Total',
                                color_continuous_scale='RdYlGn_r'
                            )
                            
                            fig_bar.update_traces(
                                texttemplate='%{text:,}',
                                textposition='outside',
                                textfont=dict(size=11)
                            )
                            
                            fig_bar.update_layout(
                                showlegend=False,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(
                                    showgrid=True,
                                    gridcolor='lightgray',
                                    gridwidth=0.5
                                ),
                                yaxis=dict(
                                    showgrid=False
                                ),
                                height=500,
                                coloraxis_showscale=False
                            )
                            
                            st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # STACKED BAR CHART (Additional visualization)
                    st.markdown("#### 🎯 Detailed Age Distribution")
                    
                    # Toggle for stacked view
                    show_percentage = st.checkbox("Show as Percentage", value=False)
                    
                    # Prepare data for stacked bar
                    stacked_data = filtered_data.copy()
                    
                    if show_percentage:
                        # Calculate percentages
                        for col in age_columns:
                            stacked_data[col] = (stacked_data[col] / stacked_data['Grand_Total'] * 100).round(1)
                    
                    # Create stacked bar chart
                    fig_stacked = go.Figure()
                    
                    colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c', '#c0392b', '#8e44ad']
                    
                    for idx, age_col in enumerate(age_columns):
                        fig_stacked.add_trace(go.Bar(
                            name=age_col,
                            x=stacked_data['COMPLAINT TYPE'],
                            y=stacked_data[age_col],
                            marker_color=colors[idx],
                            text=stacked_data[age_col],
                            texttemplate='%{text:.1f}%' if show_percentage else '%{text:,}',
                            textposition='inside',
                            hovertemplate='<b>%{x}</b><br>' +
                                        f'{age_col}: ' + 
                                        ('%{y:.1f}%' if show_percentage else '%{y:,}') +
                                        '<extra></extra>'
                        ))
                    
                    fig_stacked.update_layout(
                        barmode='stack',
                        title='Age Bucket Distribution by Complaint Type',
                        xaxis_title='Complaint Type',
                        yaxis_title='Percentage (%)' if show_percentage else 'Number of Complaints',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=False,
                            tickangle=-45
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='lightgray',
                            gridwidth=0.5
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=500,
                        hovermode='closest'
                    )
                    
                    st.plotly_chart(fig_stacked, use_container_width=True)
                    
                    # Download options
                    st.markdown("---")
                    st.markdown("### 💾 Download Data")
                    
                    download_col1, download_col2 = st.columns(2)
                    
                    with download_col1:
                        # Download filtered data as CSV
                        csv_data = filtered_data.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Filtered Data (CSV)",
                            data=csv_data,
                            file_name="aging_analysis_filtered.csv",
                            mime="text/csv"
                        )
                    
                    with download_col2:
                        # Download full pivot table
                        csv_full = aging_pivot.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Full Data (CSV)",
                            data=csv_full,
                            file_name="aging_analysis_full.csv",
                            mime="text/csv"
                        )


        
            # ========================================
            # VISUALIZATIONS SECTION - FIXED
            # ========================================
            st.markdown("### 📊 Data Visualizations")
            
            # Tab layout for different visualizations
            viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                "📈 Time Series", 
                "🔵 Complaint Types", 
                "🌡️ Aging Analysis",
                "📊 Additional Insights"
            ])
            
            with viz_tab1:
                st.markdown("#### Time Series Analysis")
                
                # Map visualization type
                chart_type_map = {
                    "Line Chart": "line",
                    "Bar Chart": "bar",
                    "Area Chart": "area"
                }
                
                with st.spinner("Generating time series chart..."):
                    # FIXED: Pass DataFrame instead of dataset_path
                    create_time_series_chart(filtered_df, chart_type_map[viz_type])
                
                st.markdown("##### Monthly Trends")
                create_monthly_trend_chart(filtered_df)
            
            with viz_tab2:
                st.markdown("#### Complaint Type Distribution")
                
                complaint_chart_map = {
                    "Bar Chart": "bar",
                    "Pie Chart": "pie",
                    "Horizontal Bar": "horizontal_bar"
                }
                
                with st.spinner("Generating complaint type chart..."):
                    create_complaint_type_chart(filtered_df, complaint_chart_map[complaint_viz_type])
                
                st.markdown("##### Query/Request/Complaint Distribution")
                if 'QUERY/REQUEST/COMPLAINT' in filtered_df.columns:
                    create_qrc_chart(filtered_df)
            
            with viz_tab3:
                st.markdown("#### Aging Analysis for Open Complaints")
                
                with st.spinner("Generating aging analysis..."):
                    # FIXED: Pass DataFrame instead of dataset_path
                    create_aging_heatmap(filtered_df)
                
                st.markdown("##### Aging Pivot Table")
                # FIXED: Pass DataFrame instead of dataset_path
                aging_table = agging_all_open_pivot_table(filtered_df)
                st.dataframe(aging_table, use_container_width=True, height=400)
            
            with viz_tab4:
                st.markdown("#### Additional Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'CLOSED/OPEN' in filtered_df.columns:
                        st.markdown("##### Status Distribution")
                        status_counts = filtered_df['CLOSED/OPEN'].value_counts()
                        fig = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            title="Open vs Closed Status",
                            color_discrete_sequence=['#FF6B6B', '#4ECDC4']
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'DATE' in filtered_df.columns:
                        st.markdown("##### Complaints by Day of Week")
                        temp_df = filtered_df.copy()
                        temp_df['DAY_OF_WEEK'] = pd.to_datetime(temp_df['DATE']).dt.day_name()
                        day_counts = temp_df['DAY_OF_WEEK'].value_counts()
                        
                        # Reorder by weekday
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_counts = day_counts.reindex([d for d in day_order if d in day_counts.index])
                        
                        fig = px.bar(
                            x=day_counts.index,
                            y=day_counts.values,
                            labels={'x': 'Day of Week', 'y': 'Count'},
                            title="Complaints by Day of Week"
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # ========================================
            # DATA SUMMARY SECTION
            # ========================================
            st.markdown("### 📊 Detailed Data Summary")
            
            st.markdown("#### Column Statistics")
            
            # Display column info
            col_info = pd.DataFrame({
                'Column Name': filtered_df.columns,
                'Data Type': filtered_df.dtypes.values,
                'Non-Null Count': filtered_df.count().values,
                'Null Count': filtered_df.isnull().sum().values,
                'Unique Values': [filtered_df[col].nunique() for col in filtered_df.columns]
            })
            
            st.dataframe(col_info, use_container_width=True, height=400)
            
            st.markdown("#### Numeric Column Statistics")
            if not filtered_df.select_dtypes(include=[np.number]).empty:
                st.dataframe(filtered_df.describe(), use_container_width=True, height=400)
            else:
                st.info("No numeric columns available for statistical summary")
            
            # ========================================
            # FOOTER
            # ========================================
            st.markdown("---")
            st.markdown("""
                <div style='text-align: center; color: #666; padding: 2rem;'>
                    <p>📊 Complaint Analysis Dashboard | Built with Streamlit</p>
                    <p style='font-size: 0.8rem;'>Last updated: {}</p>
                </div>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)
            
            if logger:
                logger.info("Tab 4 analysis completed successfully")
    
    except Exception as e:
        error_msg = f"Error in Tab 4: {str(e)}"
        if logger:
            logger.error(error_msg)
        st.error(f"❌ An unexpected error occurred: {error_msg}")
        with st.expander("Show error details"):
            st.code(error_msg)