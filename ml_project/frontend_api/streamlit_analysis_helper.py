import time
from ml_project.utils.helper import read_yaml
import pandas as pd
import numpy as np
import streamlit as st


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path
try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")

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


def close_power_outage_duration(dataset_path: str, selected_day: str) -> pd.DataFrame:
    main_df = pd.read_excel(dataset_path)
    df = main_df.copy()
    
    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Filter for specific day
    day_filter_data = df[df['DATE'].dt.date == pd.to_datetime(selected_day).date()].copy()
    
    # Normalize complaint type text
    day_filter_data['COMPLAINT TYPE'] = (
        day_filter_data['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    )

    # Filter complaint types
    power_outage_data = day_filter_data[
        day_filter_data['COMPLAINT TYPE'].isin(['Power Outage', 'No Power Supply'])
    ].copy()

    
    # Convert time objects into datetime for subtraction
    def to_datetime(t):
        if pd.isnull(t):
            return pd.NaT
        if isinstance(t, datetime):
            return t
        if isinstance(t, time):
            return datetime.combine(datetime.today(), t)
        return pd.to_datetime(t)
    
    # Apply conversion first
    power_outage_data['COMPLAINT_RECEIVED_DT'] = power_outage_data['COMPLAINT RECEIVED TIME'].apply(to_datetime)
    power_outage_data['FINAL_RESPONSE_DT'] = power_outage_data['FINAL RESPONSE TIME'].apply(to_datetime)
    
    # Fill missing FINAL RESPONSE TIME with current timestamp AFTER conversion
    power_outage_data['FINAL_RESPONSE_DT'] = power_outage_data['FINAL_RESPONSE_DT'].fillna(pd.Timestamp.now())
    
    # Calculate difference in hours
    power_outage_data['DURATION_HOURS'] = (
        power_outage_data['FINAL_RESPONSE_DT'] - power_outage_data['COMPLAINT_RECEIVED_DT']
    ).dt.total_seconds() / 3600
    
    # Round to nearest whole hour
    power_outage_data['DURATION_HOURS_ROUNDED'] = power_outage_data['DURATION_HOURS'].round()
    
    # Integer hours (floor)
    power_outage_data['DURATION_HOURS_INT'] = power_outage_data['DURATION_HOURS'].fillna(0).astype(int)
    
    # Select relevant columns
    close_open_hour = power_outage_data[['DIVISION', 'SUB-DIVISION', 'SHIFT DUTY', 'CLOSED/OPEN', 'DURATION_HOURS_INT']].copy()
    
    # Define classification function
    def classify_duration(x):
        if x < 2:
            return "<2"
        elif 2 <= x < 4:
            return "2<4"
        elif 4 <= x < 8:
            return "4<8"
        else:
            return ">8"

    # Apply classification
    close_open_hour["DURATION_RANGE"] = close_open_hour["DURATION_HOURS_INT"].apply(classify_duration)

    # Pivot table
    pivot = pd.pivot_table(
        close_open_hour,
        values='DURATION_HOURS_INT',
        index=['DIVISION', 'SUB-DIVISION', 'SHIFT DUTY'],
        columns=['DURATION_RANGE', 'CLOSED/OPEN'],
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='Grand Total',
        observed=False
    )

    
    pivot_df = pivot.reset_index()
    pivot_df.columns = ['_'.join([str(c) for c in col if c]) for col in pivot_df.columns.values]

    # Fix: Use the correct column name after pivot (it keeps the space)
    pivot_df_siftA = pivot_df[pivot_df['SHIFT DUTY'] == 'A']
    pivot_df_siftB = pivot_df[pivot_df['SHIFT DUTY'] == 'B']
    pivot_df_siftC = pivot_df[pivot_df['SHIFT DUTY'] == 'C']

    # Concatenate properly
    merge_df = pd.concat([pivot_df_siftA, pivot_df_siftB, pivot_df_siftC], axis=0)
    
    # Sum duration range columns correctly
    duration_cols = [col for col in merge_df.columns if any(dur in col for dur in ['<2_', '2<4_', '4<8_', '>8_'])]
    merge_df["Total Complaint Count (A+B+C)"] = merge_df[duration_cols].sum(axis=1)
    
    # Separate numeric and categorical columns
    numeric_cols = merge_df.select_dtypes(include='number').columns
    categorical_cols = merge_df.select_dtypes(exclude='number').columns

    # Create totals for numeric columns
    totals = merge_df[numeric_cols].sum().astype(int)

    # Fill categorical columns with a label
    for col in categorical_cols:
        totals[col] = "Grand Total"

    # Append totals row
    merge_df.loc['Grand Total'] = totals
    
    # Select final columns
    final_cols = ['DIVISION', 'SUB-DIVISION', 'SHIFT DUTY', 'Total Complaint Count (A+B+C)']
    final_cols.extend([col for col in merge_df.columns if 'Grand Total' in col or col in duration_cols])
    
    final_df = merge_df[final_cols]
    
    return final_df


import pandas as pd

def generate_month_wise_open_clode_pivot_report(dataset_path: str,selected_month: str) -> dict:
    # Load dataset
    new_df = pd.read_excel(dataset_path)

    # Clean and format columns
    new_df['DATE'] = pd.to_datetime(new_df['DATE'])
    df = new_df[new_df['DATE'].dt.to_period('M') == selected_month]
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    df['DEPT'] = df['DEPT'].astype(str).str.strip().str.title()
    df['CLOSED/OPEN'] = df['CLOSED/OPEN'].astype(str).str.strip().str.title()

    pivot = pd.pivot_table(
        df,
        values='DATE',
        index=['COMPLAINT TYPE'],          # keep this index
        columns=['DEPT','CLOSED/OPEN'],
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='Grand Total',
        observed=False
    )

    # Flatten MultiIndex columns into single strings
    pivot.columns = [f"{dept}_{status}" for dept, status in pivot.columns]

    # Convert pivot table to dictionary format, preserving index
    pivot_dict = pivot.to_dict()

    return pivot_dict


import pandas as pd

import pandas as pd

def generate_complaint_report(dataset_path: str, selected_month: str) -> pd.Series:
    """
    Reads an Excel file from the given dataset path and 
    returns a report of complaint type counts.

    Parameters:
    dataset_path (str): Path to the Excel dataset file.

    Returns:
    pd.Series: Complaint type counts.
    """
    df = pd.read_excel(dataset_path)
    df['DATE'] = pd.to_datetime(df['DATE'])
    month_fd = df[df['DATE'].dt.to_period('M') == selected_month]
    complainttype_df = month_fd['COMPLAINT TYPE'].value_counts()
    return complainttype_df


def generate_date_report(dataset_path: str, selected_month: str) -> pd.Series:
    """
    Reads an Excel file from the given dataset path and 
    returns a report of date counts.

    Parameters:
    dataset_path (str): Path to the Excel dataset file.

    Returns:
    pd.Series: Date counts.
    """
    df = pd.read_excel(dataset_path)
    df['DATE'] = pd.to_datetime(df['DATE'])
    month_fd = df[df['DATE'].dt.to_period('M') == selected_month]
    date_df = month_fd['DATE'].value_counts()
    return date_df


def generate_shift_duty_report(dataset_path: str, selected_month: str) -> pd.Series:
    """
    Reads an Excel file from the given dataset path and 
    returns a report of shift duty counts.

    Parameters:
    dataset_path (str): Path to the Excel dataset file.

    Returns:
    pd.Series: Shift duty counts.
    """
    df = pd.read_excel(dataset_path)
    df['DATE'] = pd.to_datetime(df['DATE'])
    month_fd = df[df['DATE'].dt.to_period('M') == selected_month]
    shift_duty_df = month_fd['SHIFT DUTY'].value_counts()
    return shift_duty_df

import pandas as pd

import pandas as pd

def get_monthly_qrc_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning QRC value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of QUERY/REQUEST/COMPLAINT for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for QUERY/REQUEST/COMPLAINT column
    qrc_df = month_df['QUERY/REQUEST/COMPLAINT'].value_counts()
    
    return qrc_df

def get_monthly_section_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning SECTION value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of SECTION for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for SECTION column
    section_df = month_df['SECTION'].value_counts()
    
    return section_df

def get_monthly_subdivision_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning SUB-DIVISION value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of SUB-DIVISION for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for SUB-DIVISION column
    subdivision_df = month_df['SUB-DIVISION'].value_counts()
    
    return subdivision_df

def get_monthly_circle_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning CIRCLE value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of CIRCLE for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for CIRCLE column
    circle_df = month_df['CIRCLE'].value_counts()
    
    return circle_df

def get_monthly_consumer_number_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning CONSUMER NUMBER value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of CONSUMER NUMBER for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for CONSUMER NUMBER column
    consumer_number_df = month_df['CONSUMER NUMBER'].value_counts()
    
    return consumer_number_df

def get_monthly_mobile_number_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning MOBILE NUMB value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of MOBILE NUMB for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for MOBILE NUMB column
    mobile_number_df = month_df['MOBILE NUMB'].value_counts()
    
    return mobile_number_df


def get_monthly_dept_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning DEPT value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of DEPT for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for DEPT column
    dept_df = month_df['DEPT'].value_counts()
    
    return dept_df


def get_monthly_status_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning CLOSED/OPEN value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of CLOSED/OPEN for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for CLOSED/OPEN column
    status_df = month_df['CLOSED/OPEN'].value_counts()
    
    return status_df


def get_monthly_pscc_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning PSCC/FG/TO value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of PSCC/FG/TO for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for PSCC/FG/TO column
    pscc_df = month_df['PSCC/FG/TO'].value_counts()
    
    return pscc_df


def get_monthly_minute_data(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning MINUTE value counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    pd.Series
        Value counts of MINUTE for the selected month
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Get value counts for MINUTE column
    minute_df = month_df['MINUTE'].value_counts()
    
    return minute_df

def get_monthly_remarks_analysis(dataset_path, selected_month):
    """
    Read Excel data and filter by selected month, returning REMARKS analysis counts.
    
    Parameters:
    -----------
    dataset_path : str
        Path to the Excel file
    selected_month : str or pd.Period
        Month to filter (e.g., '2024-01' or pd.Period('2024-01', 'M'))
    
    Returns:
    --------
    dict
        Dictionary containing counts of different remark categories
    """
    # Read the Excel file
    df = pd.read_excel(dataset_path)
    
    # Convert DATE column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Convert selected_month to Period if it's a string
    if isinstance(selected_month, str):
        selected_month = pd.Period(selected_month, freq='M')
    
    # Filter data for the selected month
    month_df = df[df['DATE'].dt.to_period('M') == selected_month]
    
    # Ensure REMARKS column is string type
    month_df['REMARKS'] = month_df['REMARKS'].astype(str)
    
    # Count different categories
    appreciation_count = month_df['REMARKS'].str.contains("Appreciation Tweet", case=False, na=False).sum()
    awaited_consumer_count = month_df['REMARKS'].str.contains("Awaited consumer", case=False, na=False).sum()
    number_count = month_df['REMARKS'].str.contains(r"\b\d{5}\b", na=False).sum()
    
    # Return results as dictionary
    results = {
        'Appreciation Tweets': appreciation_count,
        'Awaited Consumer': awaited_consumer_count,
        '5-digit Numbers': number_count,
        'Total Remarks': len(month_df)
    }
    
    return results




