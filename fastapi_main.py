"""
Main FastAPI Application - Fixed Version
"""

import os
import sys
import time
import uvicorn
import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import APIRouter

from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

logger = get_logger(__name__)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Create Main FastAPI Application
app = FastAPI(
    title="Twitter Analytics & AI Chatbot Platform",
    description="Unified API for Twitter analytics, data visualization, and AI-powered chatbot",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Custom Middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with timing"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        logger.info(
            f"Incoming request | method={request.method} | "
            f"path={request.url.path} | client={request.client.host}"
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                f"Request completed | method={request.method} | "
                f"path={request.url.path} | status={response.status_code} | "
                f"duration={duration:.3f}s"
            )
            
            response.headers["X-Process-Time"] = str(duration)
            response.headers["X-API-Version"] = "2.0.0"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed | method={request.method} | "
                f"path={request.url.path} | duration={duration:.3f}s | "
                f"error={str(e)}"
            )
            raise

# Add Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Analytics Router - NO PREFIX (FIX FOR 404 ISSUE)
analytics_router = APIRouter(prefix="", tags=["Analytics"])

# Chatbot Router  
chatbot_router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# Import analytics routes
try:
    from ml_project.backend_api.fastapi_router import (
        read_root as analytics_root,
        get_healthcheck as analytics_health,
        get_open_complaint_pivot,
        get_open_close_complaint_pivot,
        get_agging_open_pivot_dict,
        get_agging_open_close_pivot_dict,
        get_open_close_complaint_report,
        get_generate_all_agging_complaint_report,
        get_generate_month_wise_open_close_pivot_report,
        get_generate_quarter_wise_open_close_pivot_report,
        get_generate_finance_year_wise_open_close_pivot_report
    )
    
    # Add analytics routes WITHOUT prefix
    analytics_router.add_api_route("/analytics", analytics_root, methods=["GET"])
    analytics_router.add_api_route("/analytics/healthcheck", analytics_health, methods=["GET"])
    analytics_router.add_api_route("/open_complaint_pivot", get_open_complaint_pivot, methods=["GET"])
    analytics_router.add_api_route("/open_close_complaint_pivot", get_open_close_complaint_pivot, methods=["GET"])
    analytics_router.add_api_route("/agging_open_pivot_dict", get_agging_open_pivot_dict, methods=["GET"])
    analytics_router.add_api_route("/agging_open_close_pivot_dict", get_agging_open_close_pivot_dict, methods=["GET"])
    analytics_router.add_api_route("/open_close_complaint_report", get_open_close_complaint_report, methods=["GET"])
    analytics_router.add_api_route("/all_agging_complaint_report", get_generate_all_agging_complaint_report, methods=["GET"])
    analytics_router.add_api_route("/month_wise_open_close_pivot_report", get_generate_month_wise_open_close_pivot_report, methods=["GET"])
    analytics_router.add_api_route("/quarter_wise_open_close_report", get_generate_quarter_wise_open_close_pivot_report, methods=["GET"])
    analytics_router.add_api_route("/year_wise_open_close_pivot_report", get_generate_finance_year_wise_open_close_pivot_report, methods=["GET"])
    
    logger.info("Analytics routes registered successfully")
    
except Exception as e:
    logger.error(f"Error importing analytics routes: {str(CustomException(e, sys))}")

# Import chatbot routes
try:
    from ml_project.backend_api.chatbot_api import (
        root as chatbot_root,
        health_check as chatbot_health,
        initialize_chatbot,
        chat,
        reset_conversation,
        delete_session
    )
    
    # Add chatbot routes
    chatbot_router.add_api_route("/", chatbot_root, methods=["GET"])
    chatbot_router.add_api_route("/health", chatbot_health, methods=["GET"])
    chatbot_router.add_api_route("/initialize", initialize_chatbot, methods=["POST"])
    chatbot_router.add_api_route("/chat", chat, methods=["POST"])
    chatbot_router.add_api_route("/reset", reset_conversation, methods=["POST"])
    chatbot_router.add_api_route("/session/{session_id}", delete_session, methods=["DELETE"])
    
    logger.info("Chatbot routes registered successfully")
    
except Exception as e:
    logger.error(f"Error importing chatbot routes: {str(CustomException(e, sys))}")

# Include routers
app.include_router(analytics_router)
app.include_router(chatbot_router)

# Root Endpoints
@app.get("/", tags=["Root"])
def read_root():
    """Main root endpoint"""
    try:
        logger.info("Root endpoint accessed")
        return {
            "status": "success",
            "message": "Twitter Analytics & AI Chatbot Platform",
            "version": "2.0.0",
            "endpoints": {
                "healthcheck": "GET /healthcheck",
                "analytics": "GET /open_complaint_pivot",
                "chatbot": "POST /api/chatbot/chat",
                "docs": "GET /docs"
            }
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@app.get("/healthcheck", tags=["Health"])
def global_health_check():
    """Global health check - FIXED VERSION"""
    try:
        logger.info("Global health check accessed")
        
        # Re-check for dataset on each healthcheck
        current_dataset_path = None
        dataset_exists = False
        
        try:
            from ml_project.configs.config import get_dataset_path, DatasetNotFoundError
            current_dataset_path = get_dataset_path("data/raw_path")
            dataset_exists = os.path.exists(current_dataset_path) if current_dataset_path else False
        except:
            current_dataset_path = None
            dataset_exists = False
        
        return {
            "status": "healthy",  # This was missing in analytics endpoint
            "message": "FastAPI is healthy",
            "platform_status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "2.0.0",
            "dataset_available": dataset_exists,
            "dataset_path": current_dataset_path if current_dataset_path else "Not available"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("=" * 80)
        logger.info("FASTAPI APPLICATION STARTING")
        logger.info("=" * 80)
        logger.info("Server: http://localhost:8000")
        logger.info("Docs: http://localhost:8000/docs")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting FastAPI Server")
    
    try:
        uvicorn.run(
            "fastapi_main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True,
            access_log=True,
            workers=1
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)