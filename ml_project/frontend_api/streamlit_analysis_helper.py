import time
from ml_project.utils.helper import read_yaml
import pandas as pd
import numpy as np


config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]






