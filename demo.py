import pandas as pd
import numpy as np
from ml_project.utils.helper import load_data_from_yaml, load_data_yaml, read_yaml
import os
import sys
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
logger = get_logger(__name__)

try:
    df = load_data_from_yaml("ml_project/config/ml_project_config.yaml")
    logger.info("df is loaded successfully")
    print(df.shape)

    d = load_data_yaml()
    print(d.shape)

    config = read_yaml("ml_project/config/ml_project_config.yaml")
    raw_path = config["data"]["raw_path"]
    df = pd.read_excel(raw_path) 
    print(df.shape)
    logger.info("df is loaded successfully")

except Exception as e:
    logger.error(str(CustomException(e, sys)))







