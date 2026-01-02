from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
import pandas as pd
import os
import sys
import io
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

logger = get_logger(__name__)

from ml_project.utils.helper import read_yaml

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