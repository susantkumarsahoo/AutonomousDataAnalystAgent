import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np


class DatasetNotFoundError(Exception):
    """Custom exception for when dataset is not found"""
    pass

def get_dataset_path(base_path="data/raw_path"):
    """
    Get the dataset file path (Excel or CSV).
    
    Args:
        base_path (str): The base path for the dataset directory
        
    Returns:
        str: The full path to the dataset file
        
    Raises:
        DatasetNotFoundError: If the dataset path or file doesn't exist
    """
    dataset_dir = os.path.abspath(base_path)
    
    if not os.path.exists(dataset_dir):
        raise DatasetNotFoundError(
            f"Dataset directory not available: '{dataset_dir}' does not exist. "
            f"Please create the directory or check the path."
        )
    
    # Look for Excel files first, then CSV files
    excel_files = [f for f in os.listdir(dataset_dir) if f.endswith(('.xlsx', '.xls'))]
    csv_files = [f for f in os.listdir(dataset_dir) if f.endswith('.csv')]
    
    if excel_files:
        dataset_file = os.path.join(dataset_dir, excel_files[0])
    elif csv_files:
        dataset_file = os.path.join(dataset_dir, csv_files[0])
    else:
        raise DatasetNotFoundError(
            f"No Excel or CSV files found in '{dataset_dir}'. "
            f"Please add a dataset file to this directory."
        )
    
    return dataset_file


def load_excel_data(file_path):
    """
    Load and cache Excel data from an Excel file.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        pd.DataFrame: DataFrame with parsed DATE column
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If DATE column is missing or invalid
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load Excel file
        df = pd.read_excel(file_path)
        
        # Validate DATE column exists
        if 'DATE' not in df.columns:
            raise ValueError("'DATE' column not found in Excel file")
        
        # Convert DATE column to datetime
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        
        # Check for invalid dates
        if df['DATE'].isna().any():
            invalid_count = df['DATE'].isna().sum()
            print(f"Warning: {invalid_count} invalid date(s) found and converted to NaT")
        
        return df
        
    except Exception as e:
        print(f"Error loading Excel data: {str(e)}")
        raise