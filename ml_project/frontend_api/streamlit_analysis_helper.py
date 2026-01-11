import time
from ml_project.utils.helper import read_yaml
import pandas as pd
import numpy as np
import streamlit as st


config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]



def style_dataframe_headers(df):
    """Apply styling to highlight column headers (top heading) for any dataframe"""
    styled_df = df.style.set_table_styles([
        {
            'selector': 'th',
            'props': [
                ('background-color', '#4CAF50'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('padding', '10px'),
                ('border', '1px solid white')
            ]
        }
    ], overwrite=False)
    
    return styled_df


def style_grand_total_dataframe(df_pivot):
    """Apply styling to highlight Grand_Total row"""
    if 'Grand_Total' in df_pivot['COMPLAINT TYPE'].values:
        def highlight_grand_total(row):
            if row['COMPLAINT TYPE'] == 'Grand_Total':
                return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        return df_pivot.style.apply(highlight_grand_total, axis=1)
    else:
        return df_pivot


def generate_all_agging_complaint_report(dataset_path: str) -> dict:
    """
    Load complaint dataset, clean data, calculate age buckets,
    build pivot table, and return as dictionary report.
    """

    # Load dataset
    df = pd.read_excel(dataset_path)

    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])

    # Clean string columns
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    df['DEPT'] = df['DEPT'].astype(str).str.strip().str.title()
    df['CLOSED/OPEN'] = df['CLOSED/OPEN'].astype(str).str.strip().str.title()

    # Calculate age in days
    today = pd.Timestamp.today()
    df['Age_Days'] = (today - df['DATE']).dt.days

    # Define age buckets
    bins = [0, 15, 30, 60, 90, 180, float('inf')]
    labels = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
    df['Age_Bucket'] = pd.cut(df['Age_Days'], bins=bins, labels=labels, right=True, include_lowest=True)

    # Pivot table with complaint type + age bucket + dept + open/close
    pivot_data_df = pd.pivot_table(
        df,
        values='SL.NO',
        index=['COMPLAINT TYPE'],              # rows
        columns=['Age_Bucket','DEPT','CLOSED/OPEN'],  # include CLOSED/OPEN in columns
        aggfunc='count',
        fill_value=0
    )

    # Add Grand Total column (row-wise sum)
    pivot_data_df['Grand_Total'] = pivot_data_df.sum(axis=1)

    # Add Grand Total row (column-wise sum)
    pivot_data_df.loc['Grand_Total'] = pivot_data_df.sum(axis=0)



    return pivot_data_df



import pandas as pd
from datetime import datetime, time

@st.cache_data
def close_power_outage_duration(dataset_path):
    # Read dataset
    main_df = pd.read_excel(dataset_path)
    df = main_df.copy()
    
    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Filter for specific day
    day_filter_data = df[df['DATE'].dt.date == pd.to_datetime("2025-06-25").date()]
    
    # Filter complaint types
    power_outage_data = day_filter_data[
        (day_filter_data['COMPLAINT TYPE'] == 'Power Outage') | 
        (day_filter_data['COMPLAINT TYPE'] == 'No Power Supply')
    ]
    
    # Convert time objects into datetime for subtraction
    def to_datetime(t):
        if pd.isnull(t):
            return None
        if isinstance(t, datetime):
            return t
        if isinstance(t, time):
            return datetime.combine(datetime.today(), t)
        return pd.to_datetime(t)
    
    # Apply conversion
    start = power_outage_data['COMPLAINT RECEIVED TIME'].apply(to_datetime)
    end   = power_outage_data['FINAL RESPONSE TIME'].apply(to_datetime)
    
    # Calculate difference in hours
    power_outage_data['DURATION_HOURS'] = (end - start).dt.total_seconds() / 3600
    
    # Round to nearest whole hour
    power_outage_data['DURATION_HOURS_ROUNDED'] = power_outage_data['DURATION_HOURS'].round()
    
    # Integer hours (floor)
    power_outage_data['DURATION_HOURS_INT'] = power_outage_data['DURATION_HOURS'].fillna(0).astype(int)
    
    # Select relevant columns
    close_open_hour = power_outage_data[['DIVISION','SUB-DIVISION', 'SHIFT DUTY', 'CLOSED/OPEN', 'DURATION_HOURS_INT']].copy()
    
    # Define classification function
    def classify_duration(x):
        if x <= 2:
            return "<2"
        elif 2 < x <= 4:
            return "2<4"
        elif 4 < x <= 8:
            return "4<8"
        elif x >= 8:
            return ">8"
        else:
            return None
    
    # Apply classification
    close_open_hour["DURATION_RANGE"] = close_open_hour["DURATION_HOURS_INT"].apply(classify_duration)

    pivot_df = pd.pivot_table(
        close_open_hour,
        values='DURATION_HOURS_INT',
        index=['DIVISION','SUB-DIVISION','SHIFT DUTY'],
        columns=['DURATION_RANGE','CLOSED/OPEN'],
        aggfunc='count',
        fill_value=0,
        margins=True,          
        margins_name='Grand Total'
    )
    
    return pivot_df



