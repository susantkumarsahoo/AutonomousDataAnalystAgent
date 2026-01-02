import yaml
import pandas as pd

def load_data_from_yaml(yaml_file: str, key: str = "data", subkey: str = "raw_path") -> pd.DataFrame:
    """
    Reads a YAML file, extracts the Excel path, and loads it into a DataFrame.

    Parameters
    ----------
    yaml_file : str
        Path to the YAML configuration file.
    key : str, optional
        Top-level key in YAML (default is "data").
    subkey : str, optional
        Sub-key under the top-level key (default is "raw_path").

    Returns
    -------
    pd.DataFrame
        DataFrame loaded from the Excel file.
    """
    # Step 1: Load YAML
    with open(yaml_file, "r") as file:
        config = yaml.safe_load(file)

    # Step 2: Extract path
    data_path = config[key][subkey]

    # Step 3: Load Excel into DataFrame
    df = pd.read_excel(data_path)

    return df

import yaml
import pandas as pd
import os

import yaml
import pandas as pd
import os


def load_data_yaml(
    yaml_file: str = os.path.join("ml_project", "config", "ml_project_config.yaml")
) -> pd.DataFrame:
    """
    Reads YAML config and loads an Excel file into a pandas DataFrame.

    Expected YAML structure:
    data:
      raw_path: path/to/file.xlsx
    """

    # 1. Validate YAML file existence
    if not os.path.exists(yaml_file):
        raise FileNotFoundError(f"Config file not found at: {yaml_file}")

    # 2. Load YAML safely
    with open(yaml_file, "r") as file:
        config = yaml.safe_load(file)

    # 3. Validate YAML structure
    if "data" not in config or "raw_path" not in config["data"]:
        raise KeyError("Missing 'data.raw_path' in YAML configuration")

    data_path = config["data"]["raw_path"]

    # 4. Validate Excel file existence
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at: {data_path}")

    # 5. Load Excel file
    df = pd.read_excel(data_path)

    return df

import yaml

def read_yaml(yaml_file: str) -> dict:
    """
    Reads a YAML file and returns its contents as a dictionary.
    
    Args:
        yaml_file (str): Path to the YAML file.
    
    Returns:
        dict: Parsed YAML content.
    """
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)


    

