import os
import sys
from pathlib import Path


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