import os
import sys
import io
import json
import time
import pandas as pd
import numpy as np
import requests
import datetime
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.utils.helper import read_yaml
from ml_project.backend_api.fastapi_analysis_helper import (
    open_complaint_pivot,
    open_close_complaint_pivot,
    agging_open_pivot_dict,
    agging_open_close_pivot_dict,
    open_close_complaint_report )

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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# -----------------------------------------------------------------------------
# Custom Middleware - Request Logging & Timing
# -----------------------------------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with timing"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Incoming request | method={request.method} | "
            f"path={request.url.path} | client={request.client.host}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed | method={request.method} | "
                f"path={request.url.path} | status={response.status_code} | "
                f"duration={duration:.3f}s"
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)
            response.headers["X-API-Version"] = "1.0.0"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed | method={request.method} | "
                f"path={request.url.path} | duration={duration:.3f}s | "
                f"error={str(e)}"
            )
            raise

# -----------------------------------------------------------------------------
# Security Headers Middleware
# -----------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# -----------------------------------------------------------------------------
# Add Middleware to App
# -----------------------------------------------------------------------------
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP exception | path={request.url.path} | "
        f"status={exc.status_code} | detail={exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    error_msg = str(CustomException(exc, sys))
    logger.error(f"Unhandled exception | path={request.url.path} | error={error_msg}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": error_msg if app.debug else None,
            "path": str(request.url.path)
        }
    )

# -----------------------------------------------------------------------------
# Startup & Shutdown Events
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("=" * 60)
        logger.info("FastAPI Application Starting")
        logger.info(f"API Title: {app.title}")
        logger.info(f"API Version: {app.version}")
        logger.info(f"Dataset Path: {dataset_path}")
        logger.info(f"Dataset Exists: {os.path.exists(dataset_path)}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Startup error | error={str(CustomException(e, sys))}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        logger.info("FastAPI Application Shutting Down")
    except Exception as e:
        logger.error(f"Shutdown error | error={str(e)}")

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint with API information"""
    try:
        logger.info("Root endpoint accessed")
        return {
            "message": "Twitter Flow Analysis API",
            "status": "running",
            "version": "1.0.0",
            "endpoints": {
                "healthcheck": "/healthcheck",
                "open_complaint_pivot": "/open_complaint_pivot",
                "open_close_complaint_pivot": "/open_close_complaint_pivot",
                "agging_open_pivot": "/agging_open_pivot_dict",
                "agging_open_close_pivot": "/agging_open_close_pivot_dict",
                "docs": "/docs",
                "redoc": "/redoc"
            },
        }
    except Exception as e:
        logger.error(f"Root endpoint error | error={str(CustomException(e, sys))}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/healthcheck", tags=["Health"])
async def get_healthcheck():
    """Health check endpoint with system status"""
    try:
        logger.info("Healthcheck endpoint accessed")
        dataset_exists = os.path.exists(dataset_path)

        return {
            "status": "healthy" if dataset_exists else "degraded",
            "timestamp": datetime.datetime.now().isoformat(),
            "dataset_available": dataset_exists,
            "dataset_path": dataset_path,
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Healthcheck error | error={str(CustomException(e, sys))}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/open_complaint_pivot", tags=["Analytics"])
async def get_open_complaint_pivot():
    """Get open complaints pivot table"""
    try:
        logger.info("Open complaint pivot endpoint accessed")
        
        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found | path={dataset_path}")
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get pivot table
        pivot_df = open_complaint_pivot(dataset_path)
        
        # Convert to JSON-serializable format
        response_dict = json.loads(pivot_df.to_json(orient="records"))
        
        logger.info(f"Open complaint pivot generated | records={len(response_dict)}")
        return JSONResponse(content=response_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Open complaint pivot error | error={error_msg}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/open_close_complaint_pivot", tags=["Analytics"])
async def get_open_close_complaint_pivot():
    """Get open/close complaints pivot table"""
    try:
        logger.info("Open/Close complaint pivot endpoint accessed")

        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found | path={dataset_path}")
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get pivot data
        response_dict = open_close_complaint_pivot(dataset_path)

        logger.info(f"Open/Close pivot generated | records={len(response_dict)}")
        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Open/Close complaint pivot error | error={error_msg}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/agging_open_pivot_dict", tags=["Analytics"])
async def get_agging_open_pivot_dict():
    """Get aging open complaints pivot table"""
    try:
        logger.info("Aging open pivot endpoint accessed")

        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found | path={dataset_path}")
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get pivot data
        response_dict = agging_open_pivot_dict(dataset_path)

        logger.info(f"Aging open pivot generated | records={len(response_dict)}")
        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Aging open pivot error | error={error_msg}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/agging_open_close_pivot_dict", tags=["Analytics"])
async def get_agging_open_close_pivot_dict():
    """Get aging open/close complaints pivot table"""
    try:
        logger.info("Aging open/close pivot endpoint accessed")

        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found | path={dataset_path}")
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get pivot data
        response_dict = agging_open_close_pivot_dict(dataset_path)

        logger.info(f"Aging open/close pivot generated | records={len(response_dict)}")
        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Aging open/close pivot error | error={error_msg}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

@app.get("/open_close_complaint_report", tags=["Analytics"])    
async def get_open_close_complaint_report():
    """Get open/close complaints report"""
    try:
        logger.info("Open/Close complaint report endpoint accessed")

        if not os.path.exists(dataset_path):
            logger.warning(f"Dataset not found | path={dataset_path}")
            raise HTTPException(status_code=404, detail="Dataset not found")

        # Get report data
        response_dict = open_close_complaint_report(dataset_path)

        logger.info(f"Open/Close report generated | records={len(response_dict)}")
        return JSONResponse(content=response_dict)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Open/Close report error | error={error_msg}")
        raise HTTPException(status_code=500, detail="Internal server error")




# -----------------------------------------------------------------------------
# Development Server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server in development mode")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True,  # Enable auto-reload in development
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server | error={str(e)}")
        sys.exit(1)