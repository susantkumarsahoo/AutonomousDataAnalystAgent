import os
import sys
import io
import pandas as pd
import numpy as np
import requests
import datetime
import time
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.utils.helper import read_yaml
from ml_project.backend_api.fastapi_analysis_helper import open_complaint_pivot,open_close_complaint_pivot,agging_open_pivot_dict,agging_open_close_pivot_dict



logger = get_logger(__name__)



config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Twitter Flow Analysis API",
    description="API for Twitter analytics and data visualization",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("API started")
    except Exception as e:
        logger.error(str(CustomException(e, sys)))

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/")
def read_root():
    try:
        return {
            "message": "Twitter Flow Analysis API",
            "status": "running",
            "version": "1.0.0",
            "endpoints": {
                "healthcheck": "/healthcheck",
                "report": "/report_missing_values",
                "docs": "/docs",
            },
        }
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/healthcheck")
def get_healthcheck():
    try:
        dataset_exists = os.path.exists(dataset_path)

        return {
            "status": "healthy" if dataset_exists else "degraded",
            "dataset_available": dataset_exists,
            "dataset_path": dataset_path,
        }
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail="Internal server error")
    
from fastapi import HTTPException

from fastapi.responses import JSONResponse
import json

@app.get("/open_complaint_pivot")
def get_open_complaint_pivot():
    try:
        logger.info("Open complaint pivot endpoint hit")
        
        if not os.path.exists(dataset_path):
            logger.warning("Dataset not found | path=%s", dataset_path)
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get pivot table
        pivot_df = open_complaint_pivot(dataset_path)
        
        # **SIMPLE FIX: Convert to dict and handle types automatically**
        response_dict = json.loads(
            pivot_df.to_json(orient="records")
        )
        
        logger.info("Open Pivot table generated successfully | records=%d", len(response_dict))
        return JSONResponse(content=response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail=" open_complaint_pivot url Internal server error")


@app.get("/open_close_complaint_pivot")
def get_open_close_complaint_pivot():
    try:
        logger.info("Open/Close complaint pivot endpoint hit")

        if not os.path.exists(dataset_path):
            logger.warning("Dataset not found | path=%s", dataset_path)
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Function already returns dict, use it directly
        response_dict = open_close_complaint_pivot(dataset_path)

        logger.info(
            "Open/Close Pivot table generated successfully | records=%d",
            len(response_dict)
        )

        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/agging_open_pivot_dict")
def get_agging_open_pivot_dict():
    try:
        logger.info("Agging open pivot endpoint hit")

        if not os.path.exists(dataset_path):
            logger.warning("Dataset not found | path=%s", dataset_path)
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Function already returns dict, use it directly
        response_dict = agging_open_pivot_dict(dataset_path)

        logger.info(
            "Agging open Pivot table generated successfully | records=%d",
            len(response_dict)
        )

        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/agging_open_close_pivot_dict")
def get_agging_open_close_pivot_dict():
    try:
        logger.info("Agging open/close pivot endpoint hit")

        if not os.path.exists(dataset_path):
            logger.warning("Dataset not found | path=%s", dataset_path)
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Function already returns dict, use it directly
        response_dict = agging_open_close_pivot_dict(dataset_path)

        logger.info(
            "Agging open/close Pivot table generated successfully | records=%d",
            len(response_dict)
        )

        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------------------------------------------------------------
# Local run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )