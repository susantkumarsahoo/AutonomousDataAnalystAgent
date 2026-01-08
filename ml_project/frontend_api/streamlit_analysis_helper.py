import time
from ml_project.utils.helper import read_yaml
import pandas as pd
import numpy as np


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



