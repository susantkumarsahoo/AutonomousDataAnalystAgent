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
    style_dataframe,
    create_download_link,


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
            # LOAD DATA
            # ========================================
            with st.spinner("Loading data..."):
                df = load_excel_data(dataset_path)
            
            if df.empty:
                st.error("❌ No data available. Please check the dataset path.")
                return
            
            # ========================================
            # KEY METRICS
            # ========================================
            st.markdown("### 📈 Key Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_complaints = len(df)
                st.metric(
                    label="Total Complaints",
                    value=f"{total_complaints:,}"
                )
            
            with col2:
                if 'CLOSED/OPEN' in df.columns:
                    open_complaints = len(df[df['CLOSED/OPEN'].str.lower().str.strip() == 'open'])
                    st.metric(
                        label="Open Complaints",
                        value=f"{open_complaints:,}",
                        delta=f"{(open_complaints/total_complaints*100):.1f}%"
                    )
            
            with col3:
                if 'COMPLAINT TYPE' in df.columns:
                    # Clean text data and apply title case
                    df['COMPLAINT TYPE'] = (
                        df['COMPLAINT TYPE']
                        .str.strip()          # remove leading/trailing spaces
                        .str.title()          # convert to title case
                        .str.replace(r'\s+', ' ', regex=True)  # normalize spaces
                    )

                    # Count unique complaint types
                    unique_types = df['COMPLAINT TYPE'].nunique()

                    st.metric(
                        label="Complaint Types",
                        value=f"{unique_types}",
                    )
            
            with col4:
                if 'DATE' in df.columns:
                    df['DATE'] = pd.to_datetime(df['DATE'])
                    avg_age = (datetime.now() - df['DATE']).dt.days.mean()
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
                        • Rows: {len(df):,}<br>
                        • Columns: {len(df.columns)}<br>
                        • Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if 'DATE' in df.columns:
                    min_date = df['DATE'].min()
                    max_date = df['DATE'].max()
                    st.markdown(f"""
                        <div class="success-box">
                            <strong>Date Range:</strong><br>
                            • From: {min_date.strftime('%Y-%m-%d')}<br>
                            • To: {max_date.strftime('%Y-%m-%d')}<br>
                            • Duration: {(max_date - min_date).days} days
                        </div>
                    """, unsafe_allow_html=True)
            
            # Dataframe display
            st.markdown("#### 🔍 Data Table")
            
            display_df = df.head(100)
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Download button
            csv = create_download_link(df)
            st.download_button(
                label="📥 Download Data (CSV)",
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
                        title='Distribution by Category',
                        hole=0.4,  # Makes it a donut chart for better readability
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_qrc.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_qrc, use_container_width=True)
                
                st.divider()
                
                # Section 3: Top 6 Multitype User Interactions
                st.subheader("📊 Top Multitype User Interactions")
                
                # Check what columns are available in your dataframe
                # Replace 'MULTITYPE' with the actual column name from your dataset
                multitype_column = None
                
                # Check for possible column names
                possible_columns = ['MULTITYPE', 'MultiType', 'Type', 'Interaction Type', 'QUERY/REQUEST/COMPLAINT']
                for col in possible_columns:
                    if col in df.columns:
                        multitype_column = col
                        break
                
                if multitype_column:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        with st.spinner("Analyzing multitype interactions..."):
                            # Get top 6 multitype combinations
                            multitype_counts = df[multitype_column].value_counts().head(6).reset_index()
                            multitype_counts.columns = ['Interaction Type', 'Count']
                            
                            # Horizontal bar chart
                            fig_multi_bar = px.bar(
                                multitype_counts,
                                y='Interaction Type',
                                x='Count',
                                orientation='h',
                                title='Top 6 Interaction Types',
                                color='Count',
                                color_continuous_scale='Blues',
                                text='Count'
                            )
                            fig_multi_bar.update_traces(texttemplate='%{text}', textposition='outside')
                            fig_multi_bar.update_layout(
                                showlegend=False,
                                yaxis={'categoryorder': 'total ascending'},
                                height=400
                            )
                            st.plotly_chart(fig_multi_bar, use_container_width=True)
                    
                    with col2:
                        # Treemap visualization for better visual hierarchy
                        fig_multi_tree = px.treemap(
                            multitype_counts,
                            path=['Interaction Type'],
                            values='Count',
                            title='Interaction Type Hierarchy',
                            color='Count',
                            color_continuous_scale='Viridis',
                            hover_data={'Count': True}
                        )
                        fig_multi_tree.update_traces(
                            textinfo='label+value',
                            textposition='middle center',
                            marker=dict(line=dict(width=2, color='white'))
                        )
                        fig_multi_tree.update_layout(height=400)
                        st.plotly_chart(fig_multi_tree, use_container_width=True)
                else:
                    st.warning("⚠️ Multitype column not found in the dataset. Please check your column names.")
                    st.write("Available columns:", df.columns.tolist())




            # Section 3: Top 5 Complaint Types
            st.subheader("🏆 Top 5 Complaint Types")

            with st.spinner("Identifying top complaint types..."):
                complaint_type_counts = get_complaint_type_value_counts_type(df)

            # Create three columns for better layout
            col3, col4, col5 = st.columns([1, 1, 1])

            with col3:
                # Display dataframe with enhanced styling
                st.markdown("##### 📊 Complaint Data")
                st.dataframe(
                    complaint_type_counts,
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )
                
                # Add a donut chart below the dataframe
                st.markdown("##### 🍩 Distribution Overview")
                fig_donut = px.pie(
                    complaint_type_counts,
                    values='count',
                    names='COMPLAINT TYPE',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_donut.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                fig_donut.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            with col4:
                # Horizontal bar chart
                st.markdown("##### 📊 Horizontal Bar Chart")
                fig_hbar = px.bar(
                    complaint_type_counts,
                    y='COMPLAINT TYPE',
                    x='count',
                    orientation='h',
                    color='count',
                    color_continuous_scale='Blues',
                    text='count'
                )
                fig_hbar.update_traces(
                    texttemplate='%{text:,}',
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
                )
                fig_hbar.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20),
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig_hbar, use_container_width=True)
                
                # Lollipop chart
                st.markdown("##### 🍭 Lollipop Chart")
                fig_lollipop = go.Figure()
                
                # Add stems
                for idx, row in complaint_type_counts.iterrows():
                    fig_lollipop.add_trace(go.Scatter(
                        x=[0, row['count']],
                        y=[row['COMPLAINT TYPE'], row['COMPLAINT TYPE']],
                        mode='lines',
                        line=dict(color='lightblue', width=2),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                
                # Add dots
                fig_lollipop.add_trace(go.Scatter(
                    x=complaint_type_counts['count'],
                    y=complaint_type_counts['COMPLAINT TYPE'],
                    mode='markers',
                    marker=dict(size=15, color='#1f77b4'),
                    text=complaint_type_counts['count'],
                    textposition='middle right',
                    texttemplate='%{text:,}',
                    showlegend=False,
                    hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
                ))
                
                fig_lollipop.update_layout(
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=60),
                    yaxis={'categoryorder': 'total ascending'},
                    xaxis_title='Number of Complaints'
                )
                st.plotly_chart(fig_lollipop, use_container_width=True)

            with col5:
                # Treemap
                st.markdown("##### 🗺️ Treemap Visualization")
                fig_treemap = px.treemap(
                    complaint_type_counts,
                    path=['COMPLAINT TYPE'],
                    values='count',
                    color='count',
                    color_continuous_scale='Viridis',
                    hover_data={'count': ':,'}
                )
                fig_treemap.update_traces(
                    texttemplate='<b>%{label}</b><br>%{value:,}',
                    hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percentRoot:.1%}<extra></extra>'
                )
                fig_treemap.update_layout(
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_treemap, use_container_width=True)
                
                # Waffle-style chart (using scatter plot)
                st.markdown("##### 🧇 Waffle Chart")
                
                # Calculate waffle chart data
                total = complaint_type_counts['count'].sum()
                waffle_data = []
                colors = px.colors.qualitative.Set2[:len(complaint_type_counts)]
                
                current_pos = 0
                for idx, (_, row) in enumerate(complaint_type_counts.iterrows()):
                    percentage = (row['count'] / total) * 100
                    boxes = int(percentage)
                    for i in range(boxes):
                        waffle_data.append({
                            'x': current_pos % 10,
                            'y': current_pos // 10,
                            'type': row['COMPLAINT TYPE'],
                            'color': colors[idx],
                            'count': row['count']
                        })
                        current_pos += 1
                
                waffle_df = pd.DataFrame(waffle_data)
                
                fig_waffle = go.Figure()
                
                for complaint_type in complaint_type_counts['COMPLAINT TYPE']:
                    subset = waffle_df[waffle_df['type'] == complaint_type]
                    if not subset.empty:
                        fig_waffle.add_trace(go.Scatter(
                            x=subset['x'],
                            y=subset['y'],
                            mode='markers',
                            marker=dict(
                                size=20,
                                color=subset['color'].iloc[0],
                                symbol='square',
                                line=dict(width=1, color='white')
                            ),
                            name=complaint_type,
                            text=complaint_type,
                            hovertemplate='<b>%{text}</b><extra></extra>'
                        ))
                
                fig_waffle.update_layout(
                    height=300,
                    showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    margin=dict(t=20, b=80, l=20, r=20),
                    plot_bgcolor='white'
                )
                st.plotly_chart(fig_waffle, use_container_width=True)

            st.divider()

            # Optional: Add a heatmap if you have temporal data
            st.markdown("##### 🔥 Heatmap Analysis")
            col6, col7 = st.columns([2, 1])

            with col6:
                # Try to find the date column with different possible names
                date_column = None
                possible_date_columns = ['Created Date', 'CREATED_DATE', 'created_date', 'Date', 'DATE', 
                                        'Created_Date', 'CreatedDate', 'Complaint Date', 'COMPLAINT_DATE']
                
                for col_name in possible_date_columns:
                    if col_name in df.columns:
                        date_column = col_name
                        break
                
                # Also try to find complaint type column
                complaint_column = None
                possible_complaint_columns = ['Complaint Type', 'COMPLAINT TYPE', 'complaint_type', 
                                            'Complaint_Type', 'ComplaintType', 'Type']
                
                for col_name in possible_complaint_columns:
                    if col_name in df.columns:
                        complaint_column = col_name
                        break
                
                if date_column and complaint_column:
                    try:
                        df_temp = df.copy()
                        df_temp['Date'] = pd.to_datetime(df_temp[date_column], errors='coerce')
                        
                        # Remove rows with invalid dates
                        df_temp = df_temp.dropna(subset=['Date'])
                        
                        if len(df_temp) > 0:
                            df_temp['Hour'] = df_temp['Date'].dt.hour
                            df_temp['DayOfWeek'] = df_temp['Date'].dt.day_name()
                            
                            # Get top 5 complaint types
                            top_types = complaint_type_counts['COMPLAINT TYPE'].tolist()
                            df_temp = df_temp[df_temp[complaint_column].isin(top_types)]
                            
                            if len(df_temp) > 0:
                                # Create pivot table
                                heatmap_data = df_temp.groupby(['DayOfWeek', complaint_column]).size().unstack(fill_value=0)
                                
                                # Reorder days
                                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                                heatmap_data = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])
                                
                                fig_heatmap = px.imshow(
                                    heatmap_data.T,
                                    labels=dict(x="Day of Week", y="Complaint Type", color="Count"),
                                    color_continuous_scale='YlOrRd',
                                    aspect='auto',
                                    text_auto=True
                                )
                                fig_heatmap.update_layout(
                                    height=400,
                                    margin=dict(t=40, b=20, l=20, r=20),
                                    xaxis_title="Day of Week",
                                    yaxis_title="Complaint Type"
                                )
                                fig_heatmap.update_traces(
                                    hovertemplate='<b>%{y}</b><br>%{x}<br>Count: %{z}<extra></extra>'
                                )
                                st.plotly_chart(fig_heatmap, use_container_width=True)
                            else:
                                st.warning("No data available for top complaint types in the date range.")
                        else:
                            st.warning("No valid date data found. Please check your date column format.")
                    except Exception as e:
                        st.error(f"Error creating heatmap: {str(e)}")
                        st.info(f"Available columns: {', '.join(df.columns.tolist())}")
                else:
                    # Show available columns to help debug
                    st.info("📋 Heatmap requires datetime data.")
                    st.write("**Available columns in your dataset:**")
                    st.write(df.columns.tolist())
                    
                    if not date_column:
                        st.warning("⚠️ No date column found. Looking for columns like: 'Created Date', 'CREATED_DATE', 'Date', etc.")
                    if not complaint_column:
                        st.warning("⚠️ No complaint type column found. Looking for columns like: 'Complaint Type', 'COMPLAINT TYPE', etc.")

            with col7:
                # Summary metrics
                st.markdown("##### 📈 Key Metrics")
                total_complaints = complaint_type_counts['count'].sum()
                avg_complaints = complaint_type_counts['count'].mean()
                max_complaint = complaint_type_counts.iloc[0]
                
                st.metric("Total Complaints", f"{total_complaints:,}")
                st.metric("Average per Type", f"{avg_complaints:,.0f}")
                st.metric("Top Complaint", max_complaint['COMPLAINT TYPE'], 
                        f"{max_complaint['count']:,} cases")
                
                # Percentage breakdown
                st.markdown("##### 📊 Percentage Breakdown")
                for _, row in complaint_type_counts.iterrows():
                    percentage = (row['count'] / total_complaints) * 100
                    st.progress(percentage / 100, text=f"{row['COMPLAINT TYPE'][:20]}...: {percentage:.1f}%")

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
                    create_time_series_chart(df, "line")
                
                st.markdown("##### Monthly Trends")
                create_monthly_trend_chart(df)
            
            with viz_tab2:
                st.markdown("#### Complaint Type Distribution")
                
                complaint_chart_map = {
                    "Bar Chart": "bar",
                    "Pie Chart": "pie",
                    "Horizontal Bar": "horizontal_bar"
                }
                
                with st.spinner("Generating complaint type chart..."):
                    create_complaint_type_chart(df, "bar")
                
                st.markdown("##### Query/Request/Complaint Distribution")
                if 'QUERY/REQUEST/COMPLAINT' in df.columns:
                    create_qrc_chart(df)
            
            with viz_tab3:
                st.markdown("#### Aging Analysis for Open Complaints")
                
                with st.spinner("Generating aging analysis..."):
                    # FIXED: Pass DataFrame instead of dataset_path
                    create_aging_heatmap(df)
                
                st.markdown("##### Aging Pivot Table")
                # FIXED: Pass DataFrame instead of dataset_path
                aging_table = agging_all_open_pivot_table(df)
                st.dataframe(aging_table, use_container_width=True, height=400)
            
            with viz_tab4:
                st.markdown("#### Additional Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'CLOSED/OPEN' in df.columns:
                        st.markdown("##### Status Distribution")
                        status_counts = df['CLOSED/OPEN'].value_counts()
                        fig = px.pie(
                            values=status_counts.values,
                            names=status_counts.index,
                            title="Open vs Closed Status",
                            color_discrete_sequence=['#FF6B6B', '#4ECDC4']
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'DATE' in df.columns:
                        st.markdown("##### Complaints by Day of Week")
                        temp_df = df.copy()
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
                'Column Name': df.columns,
                'Data Type': df.dtypes.values,
                'Non-Null Count': df.count().values,
                'Null Count': df.isnull().sum().values,
                'Unique Values': [df[col].nunique() for col in df.columns]
            })
            
            st.dataframe(col_info, use_container_width=True, height=400)
            
            st.markdown("#### Numeric Column Statistics")
            if not df.select_dtypes(include=[np.number]).empty:
                st.dataframe(df.describe(), use_container_width=True, height=400)
            else:
                st.info("No numeric columns available for statistical summary")
            
            st.markdown("---")
            
            # ========================================
            # CONTROL PANEL (MOVED TO BOTTOM)
            # ========================================
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