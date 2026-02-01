import os
import sys
import time
import io
from io import BytesIO
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import streamlit as st
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
from ml_project.frontend_api.streamlit_analysis_tab5_helper import (
    get_remarks_df,
    get_remarks_counts,
)
from ml_project.frontend_api.streamlit_cache_data import(
    load_excel_data,
)

# ================================================================
# CONFIGURATION AND SETUP
# ================================================================

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
        pass

logger = get_logger(__name__)


# ================================================================
# HELPER FUNCTION 1: DATA PROCESSING AND VISUALIZATION
# ================================================================

def process_and_visualize_remarks(
    remarks_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    logger=None
) -> Tuple[go.Figure, go.Figure, go.Figure, pd.DataFrame]:
    """
    Process remarks data and create comprehensive visualizations.
    
    Parameters:
    -----------
    remarks_df : pd.DataFrame
        Processed remarks DataFrame with all flags and categories
    summary_df : pd.DataFrame
        Summary counts DataFrame
    logger : Logger, optional
        Logger instance for tracking operations
        
    Returns:
    --------
    Tuple[go.Figure, go.Figure, go.Figure, pd.DataFrame]
        - Bar chart of category counts
        - Pie chart of top categories
        - Time series analysis chart
        - Filtered DataFrame based on user selections
    """
    try:
        if logger:
            logger.info("Starting remarks data visualization process")
        
        # ============================================================
        # CREATE INTERACTIVE BAR CHART FOR CATEGORY COUNTS
        # ============================================================
        
        # load excel data
        df = load_excel_data(dataset_path)
        
        
        
        remarks_df = get_remarks_df(df)
        summary_df = get_remarks_counts(remarks_df)
        
        # Exclude total row for visualization
        viz_summary = summary_df[summary_df['Category'] != 'Total Data Length Records'].copy()
        
        # Create color scheme based on count magnitude
        colors = px.colors.sequential.Blues_r
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            x=viz_summary['Category'],
            y=viz_summary['Count'],
            text=viz_summary['Count'],
            textposition='outside',
            marker=dict(
                color=viz_summary['Count'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Count"),
                line=dict(color='rgb(8,48,107)', width=1.5)
            ),
            hovertemplate='<b>%{x}</b><br>Count: %{y}<br><extra></extra>'
        ))
        
        fig_bar.update_layout(
            title={
                'text': '📊 Remarks Category Analysis',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#1f77b4', 'family': 'Arial Black'}
            },
            xaxis_title='Category',
            yaxis_title='Count',
            xaxis={'tickangle': -45, 'tickfont': {'size': 10}},
            template='plotly_white',
            height=500,
            showlegend=False,
            hovermode='x unified'
        )
        
        # ============================================================
        # CREATE PIE CHART FOR TOP CATEGORIES
        # ============================================================
        
        # Get top 6 categories
        top_categories = viz_summary.nlargest(6, 'Count')
        
        fig_pie = go.Figure()
        
        fig_pie.add_trace(go.Pie(
            labels=top_categories['Category'],
            values=top_categories['Count'],
            hole=0.4,
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textfont_size=12,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        ))
        
        fig_pie.update_layout(
            title={
                'text': '🥧 Top 6 Categories Distribution',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#1f77b4', 'family': 'Arial Black'}
            },
            template='plotly_white',
            height=450,
            annotations=[dict(
                text=f'Total<br>{viz_summary["Count"].sum()}',
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )]
        )
        
        # ============================================================
        # CREATE TIME SERIES ANALYSIS
        # ============================================================
        
        # Convert DATE column to datetime
        remarks_df_copy = remarks_df.copy()
        remarks_df_copy['DATE'] = pd.to_datetime(remarks_df_copy['DATE'], errors='coerce')
        
        # Group by date and count records
        daily_counts = remarks_df_copy.groupby('DATE').size().reset_index(name='Count')
        daily_counts = daily_counts.sort_values('DATE')
        
        fig_time = go.Figure()
        
        fig_time.add_trace(go.Scatter(
            x=daily_counts['DATE'],
            y=daily_counts['Count'],
            mode='lines+markers',
            name='Daily Complaints',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8, color='#FF6B6B', line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)',
            hovertemplate='<b>Date: %{x|%Y-%m-%d}</b><br>Count: %{y}<extra></extra>'
        ))
        
        # Add trend line
        if len(daily_counts) > 1:
            z = np.polyfit(range(len(daily_counts)), daily_counts['Count'], 1)
            p = np.poly1d(z)
            
            fig_time.add_trace(go.Scatter(
                x=daily_counts['DATE'],
                y=p(range(len(daily_counts))),
                mode='lines',
                name='Trend',
                line=dict(color='rgba(0, 0, 0, 0.5)', width=2, dash='dash'),
                hovertemplate='Trend: %{y:.1f}<extra></extra>'
            ))
        
        fig_time.update_layout(
            title={
                'text': '📈 Daily Complaints Trend Analysis',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#1f77b4', 'family': 'Arial Black'}
            },
            xaxis_title='Date',
            yaxis_title='Number of Complaints',
            template='plotly_white',
            height=450,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        if logger:
            logger.info("Visualizations created successfully")
        
        return fig_bar, fig_pie, fig_time, remarks_df_copy
        
    except Exception as e:
        error_msg = f"Error in visualization process: {str(e)}"
        if logger:
            logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        raise CustomException(e, sys)


# ================================================================
# HELPER FUNCTION 2: INTERACTIVE FILTERING AND ANALYSIS
# ================================================================

def create_interactive_filters_and_analysis(
    remarks_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    logger=None
) -> Dict[str, any]:
    """
    Create interactive filters and perform detailed analysis on remarks data.
    
    Parameters:
    -----------
    remarks_df : pd.DataFrame
        Processed remarks DataFrame with all flags and categories
    summary_df : pd.DataFrame
        Summary counts DataFrame
    logger : Logger, optional
        Logger instance for tracking operations
        
    Returns:
    --------
    Dict[str, any]
        Dictionary containing filtered DataFrames and analysis results
    """
    try:
        if logger:
            logger.info("Creating interactive filters and analysis")
        
        results = {}
        
        # ============================================================
        # SIDEBAR FILTERS
        # ============================================================
        
        st.sidebar.header("🔍 Filter Options")
        
        # Date range filter
        remarks_df['DATE'] = pd.to_datetime(remarks_df['DATE'], errors='coerce')
        
        if not remarks_df['DATE'].isna().all():
            min_date = remarks_df['DATE'].min().date()
            max_date = remarks_df['DATE'].max().date()
            
            date_range = st.sidebar.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (remarks_df['DATE'].dt.date >= start_date) & (remarks_df['DATE'].dt.date <= end_date)
                filtered_df = remarks_df[mask].copy()
            else:
                filtered_df = remarks_df.copy()
        else:
            filtered_df = remarks_df.copy()
        
        # Division filter
        if 'DIVISION' in filtered_df.columns:
            divisions = ['All'] + sorted(filtered_df['DIVISION'].dropna().unique().tolist())
            selected_division = st.sidebar.selectbox("Select Division", divisions)
            
            if selected_division != 'All':
                filtered_df = filtered_df[filtered_df['DIVISION'] == selected_division]
        
        # Circle filter
        if 'CIRCLE' in filtered_df.columns:
            circles = ['All'] + sorted(filtered_df['CIRCLE'].dropna().unique().tolist())
            selected_circle = st.sidebar.selectbox("Select Circle", circles)
            
            if selected_circle != 'All':
                filtered_df = filtered_df[filtered_df['CIRCLE'] == selected_circle]
        
        # Complaint type filter
        if 'COMPLAINT TYPE' in filtered_df.columns:
            complaint_types = ['All'] + sorted(filtered_df['COMPLAINT TYPE'].dropna().unique().tolist())
            selected_complaint = st.sidebar.selectbox("Select Complaint Type", complaint_types)
            
            if selected_complaint != 'All':
                filtered_df = filtered_df[filtered_df['COMPLAINT TYPE'] == selected_complaint]
        
        # Category-based filters
        st.sidebar.subheader("📋 Category Filters")
        
        show_duplicates = st.sidebar.checkbox("Show Duplicate Cases Only", value=False)
        if show_duplicates:
            filtered_df = filtered_df[filtered_df['Duplicate Case'] != 'NA']
        
        show_appreciation = st.sidebar.checkbox("Show Appreciation Tweets Only", value=False)
        if show_appreciation:
            filtered_df = filtered_df[filtered_df['Appreciation Tweet'] != 'NA']
        
        show_weather = st.sidebar.checkbox("Show Weather Events Only", value=False)
        if show_weather:
            filtered_df = filtered_df[filtered_df['Weather Event'] == 'Yes']
        
        show_elephant = st.sidebar.checkbox("Show Elephant Movement Only", value=False)
        if show_elephant:
            filtered_df = filtered_df[filtered_df['Elephant Movement'] == 'Yes']
        
        results['filtered_df'] = filtered_df
        
        # ============================================================
        # ADDITIONAL ANALYSIS
        # ============================================================
        
        # Division-wise analysis
        if 'DIVISION' in filtered_df.columns:
            division_counts = filtered_df.groupby('DIVISION').size().reset_index(name='Count')
            division_counts = division_counts.sort_values('Count', ascending=False)
            results['division_analysis'] = division_counts
        
        # Complaint type distribution
        if 'COMPLAINT TYPE' in filtered_df.columns:
            complaint_dist = filtered_df.groupby('COMPLAINT TYPE').size().reset_index(name='Count')
            complaint_dist = complaint_dist.sort_values('Count', ascending=False)
            results['complaint_analysis'] = complaint_dist
        
        # X User engagement analysis
        x_user_available = (filtered_df['X User Id'] != 'NA').sum()
        x_user_not_available = (filtered_df['X User Id'] == 'NA').sum()
        
        results['x_user_stats'] = {
            'available': x_user_available,
            'not_available': x_user_not_available,
            'total': len(filtered_df)
        }
        
        # Weather event impact analysis
        weather_events = filtered_df[filtered_df['Weather Event'] == 'Yes']
        results['weather_impact'] = {
            'total_weather_events': len(weather_events),
            'percentage': (len(weather_events) / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        }
        
        if logger:
            logger.info(f"Filters applied. Filtered records: {len(filtered_df)}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error in filtering and analysis: {str(e)}"
        if logger:
            logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        raise CustomException(e, sys)


# ================================================================
# MAIN STREAMLIT APP FOR TAB 5
# ================================================================

def streamlit_analysis_tab5(tab5, dataset_path, logger=None):
    """
    Main function for Tab 5: Comprehensive Remarks Analysis Dashboard
    
    Parameters:
    -----------
    tab5 : streamlit.tab
        Streamlit tab container
    dataset_path : str
        Path to the dataset file
    logger : Logger, optional
        Logger instance for tracking operations
    """
    try:
        with tab5:
            st.title("🔍 Comprehensive Remarks Analysis Dashboard")
            st.markdown("---")
            
            # ============================================================
            # LOAD AND PROCESS DATA
            # ============================================================
            
            with st.spinner("Loading and processing data..."):
                # Load data
                df = load_excel_data(dataset_path)
                
                if df is None or df.empty:
                    st.error("❌ No data found. Please check the dataset path.")
                    return
                
                # Process remarks
                remarks_df = get_remarks_df(df)
                summary_df = get_remarks_counts(remarks_df)
                
                if logger:
                    logger.info(f"Data loaded successfully. Total records: {len(remarks_df)}")
            
            st.success(f"✅ Data loaded successfully! Total records: {len(remarks_df)}")
            
            # ============================================================
            # DISPLAY KEY METRICS
            # ============================================================
            
            st.header("📊 Key Metrics Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_records = len(remarks_df)
                st.metric(
                    label="Total Records",
                    value=f"{total_records:,}",
                    delta=None
                )
            
            with col2:
                duplicate_cases = (remarks_df['Duplicate Case'] != 'NA').sum()
                st.metric(
                    label="Duplicate Cases",
                    value=f"{duplicate_cases:,}",
                    delta=f"{(duplicate_cases/total_records*100):.1f}%"
                )
            
            with col3:
                appreciation_tweets = (remarks_df['Appreciation Tweet'] != 'NA').sum()
                st.metric(
                    label="Appreciation Tweets",
                    value=f"{appreciation_tweets:,}",
                    delta=f"{(appreciation_tweets/total_records*100):.1f}%"
                )
            
            with col4:
                weather_events = (remarks_df['Weather Event'] == 'Yes').sum()
                st.metric(
                    label="Weather Events",
                    value=f"{weather_events:,}",
                    delta=f"{(weather_events/total_records*100):.1f}%"
                )
            
            st.markdown("---")
            
            # ============================================================
            # CREATE VISUALIZATIONS
            # ============================================================
            
            st.header("📈 Visual Analytics")
            
            with st.spinner("Generating visualizations..."):
                fig_bar, fig_pie, fig_time, processed_df = process_and_visualize_remarks(
                    remarks_df, summary_df, logger
                )
            
            # Display charts in tabs
            viz_tab1, viz_tab2, viz_tab3 = st.tabs([
                "📊 Category Counts",
                "🥧 Distribution",
                "📈 Time Trends"
            ])
            
            with viz_tab1:
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with viz_tab2:
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with viz_tab3:
                st.plotly_chart(fig_time, use_container_width=True)
            
            st.markdown("---")
            
            # ============================================================
            # INTERACTIVE FILTERS AND ANALYSIS
            # ============================================================
            
            st.header("🔍 Interactive Analysis")
            
            analysis_results = create_interactive_filters_and_analysis(
                remarks_df, summary_df, logger
            )
            
            filtered_df = analysis_results['filtered_df']
            
            # Display filtered results
            st.subheader(f"📋 Filtered Results ({len(filtered_df)} records)")
            
            # Additional metrics for filtered data
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'division_analysis' in analysis_results:
                    st.metric(
                        "Unique Divisions",
                        len(analysis_results['division_analysis'])
                    )
            
            with col2:
                if 'x_user_stats' in analysis_results:
                    engagement_rate = (
                        analysis_results['x_user_stats']['available'] / 
                        analysis_results['x_user_stats']['total'] * 100
                        if analysis_results['x_user_stats']['total'] > 0 else 0
                    )
                    st.metric(
                        "X User Engagement",
                        f"{engagement_rate:.1f}%"
                    )
            
            with col3:
                if 'weather_impact' in analysis_results:
                    st.metric(
                        "Weather Impact",
                        f"{analysis_results['weather_impact']['percentage']:.1f}%"
                    )
            
            # ============================================================
            # DETAILED DATA TABLES
            # ============================================================
            
            st.subheader("📊 Detailed Data Analysis")
            
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
                "Summary Table",
                "Division Analysis",
                "Filtered Data"
            ])
            
            with analysis_tab1:
                st.dataframe(
                    summary_df.style.background_gradient(
                        subset=['Count'],
                        cmap='YlOrRd'
                    ),
                    use_container_width=True,
                    height=400
                )
            
            with analysis_tab2:
                if 'division_analysis' in analysis_results:
                    # Create division visualization
                    fig_division = px.bar(
                        analysis_results['division_analysis'],
                        x='DIVISION',
                        y='Count',
                        title='Division-wise Complaint Distribution',
                        color='Count',
                        color_continuous_scale='Blues'
                    )
                    fig_division.update_layout(
                        xaxis_tickangle=-45,
                        height=400
                    )
                    st.plotly_chart(fig_division, use_container_width=True)
                    
                    st.dataframe(
                        analysis_results['division_analysis'],
                        use_container_width=True
                    )
            
            with analysis_tab3:
                # Display options
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    search_term = st.text_input(
                        "🔍 Search in remarks",
                        placeholder="Enter search term..."
                    )
                
                with col2:
                    show_all_columns = st.checkbox("Show all columns", value=False)
                
                # Apply search filter
                display_df = filtered_df.copy()
                
                if search_term:
                    mask = display_df['REMARKS'].astype(str).str.contains(
                        search_term,
                        case=False,
                        na=False
                    )
                    display_df = display_df[mask]
                
                # Select columns to display
                if not show_all_columns:
                    display_columns = [
                        'SL.NO', 'DATE', 'DIVISION', 'CIRCLE',
                        'COMPLAINT TYPE', 'REMARKS', 'Duplicate Case',
                        'Appreciation Tweet', 'Weather Event'
                    ]
                    display_df = display_df[[col for col in display_columns if col in display_df.columns]]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=500
                )
                
                # Download button
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Filtered Data (CSV)",
                    data=csv,
                    file_name=f"filtered_remarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            st.markdown("---")
            
            # ============================================================
            # INSIGHTS AND RECOMMENDATIONS
            # ============================================================
            
            st.header("💡 Key Insights & Recommendations")
            
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                st.subheader("🎯 Top Insights")
                
                top_category = summary_df.iloc[0]
                st.info(
                    f"**Highest Category:** {top_category['Category']} "
                    f"with {top_category['Count']} cases"
                )
                
                if (remarks_df['Duplicate Case'] != 'NA').sum() > 0:
                    dup_pct = (remarks_df['Duplicate Case'] != 'NA').sum() / len(remarks_df) * 100
                    if dup_pct > 10:
                        st.warning(
                            f"⚠️ High duplicate case rate: {dup_pct:.1f}%. "
                            "Consider implementing better case tracking."
                        )
                
                weather_pct = (remarks_df['Weather Event'] == 'Yes').sum() / len(remarks_df) * 100
                if weather_pct > 15:
                    st.warning(
                        f"🌦️ Weather events account for {weather_pct:.1f}% of cases. "
                        "Consider preparing weather contingency plans."
                    )
            
            with insights_col2:
                st.subheader("📋 Recommendations")
                
                recommendations = []
                
                # Check for high awaited consumer IDs
                awaited_pct = (remarks_df['Awaited Consumer Id'] == 'Yes').sum() / len(remarks_df) * 100
                if awaited_pct > 20:
                    recommendations.append(
                        f"🔴 {awaited_pct:.1f}% cases await consumer details. "
                        "Improve data collection process."
                    )
                
                # Check for X user engagement
                x_user_na_pct = (remarks_df['X User Id'] == 'NA').sum() / len(remarks_df) * 100
                if x_user_na_pct > 30:
                    recommendations.append(
                        f"🔴 {x_user_na_pct:.1f}% cases lack X user IDs. "
                        "Enhance social media tracking."
                    )
                
                # Check for non-TPWODL cases
                non_tpwodl_pct = (remarks_df['Streetlight And Not TPWODL'] == 'Yes').sum() / len(remarks_df) * 100
                if non_tpwodl_pct > 5:
                    recommendations.append(
                        f"🔴 {non_tpwodl_pct:.1f}% cases outside jurisdiction. "
                        "Improve case routing system."
                    )
                
                if recommendations:
                    for rec in recommendations:
                        st.warning(rec)
                else:
                    st.success("✅ All metrics are within acceptable ranges!")
            
            if logger:
                logger.info("Tab 5 analysis completed successfully")
    
    except Exception as e:
        error_msg = f"Error in Tab 5: {str(e)}"
        if logger:
            logger.error(error_msg)
        st.error(f"❌ An unexpected error occurred: {error_msg}")
        
        with st.expander("🔍 Show error details"):
            st.code(error_msg)
            import traceback
            st.code(traceback.format_exc())