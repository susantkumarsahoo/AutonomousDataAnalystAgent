"""
Main FastAPI Application - Alternative Approach Using APIRouter
Better organization with proper routing separation
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

from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

logger = get_logger(__name__)


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

# ============================================================================
# Create Main FastAPI Application
# ============================================================================
app = FastAPI(
    title="Twitter Analytics & AI Chatbot Platform",
    description="Unified API for Twitter analytics, data visualization, and AI-powered chatbot",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# Custom Middleware
# ============================================================================
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

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# ============================================================================
# Add Middleware
# ============================================================================
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Import and Include Routers
# ============================================================================

# Create routers for each module
from fastapi import APIRouter

# Analytics Router
analytics_router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Chatbot Router  
chatbot_router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# Import routes from the original files and add them to routers
# We need to extract the route handlers from the original apps

# For Analytics - import all the endpoint functions
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
    
    # Add analytics routes
    analytics_router.add_api_route("/", analytics_root, methods=["GET"])
    analytics_router.add_api_route("/healthcheck", analytics_health, methods=["GET"])
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

# For Chatbot - import all the endpoint functions
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
    chatbot_router.add_api_route("/chatbot_health", chatbot_health, methods=["GET"])
    chatbot_router.add_api_route("/initialize", initialize_chatbot, methods=["POST"])
    chatbot_router.add_api_route("/chat", chat, methods=["POST"])
    chatbot_router.add_api_route("/reset", reset_conversation, methods=["POST"])
    chatbot_router.add_api_route("/session/{session_id}", delete_session, methods=["DELETE"])
    
    logger.info("Chatbot routes registered successfully")
    
except Exception as e:
    logger.error(f"Error importing chatbot routes: {str(CustomException(e, sys))}")

# Include routers in main app
app.include_router(analytics_router)
app.include_router(chatbot_router)

# ============================================================================
# Root Endpoints
# ============================================================================
@app.get("/", tags=["Root"])
def read_root():
    """Main root endpoint with complete API information"""
    try:
        logger.info("Root endpoint accessed")
        return {
            "message": "Twitter Analytics & AI Chatbot Platform",
            "status": "running",
            "version": "2.0.0",
            "architecture": "Microservices with APIRouter",
            "services": {
                "analytics": {
                    "base_path": "/api/analytics",
                    "description": "Twitter complaint analytics and reporting",
                    "endpoints": [
                        "GET /api/analytics/",
                        "GET /api/analytics/healthcheck",
                        "GET /api/analytics/open_complaint_pivot",
                        "GET /api/analytics/open_close_complaint_pivot",
                        "GET /api/analytics/agging_open_pivot_dict",
                        "GET /api/analytics/agging_open_close_pivot_dict",
                        "GET /api/analytics/open_close_complaint_report",
                        "GET /api/analytics/all_agging_complaint_report",
                        "GET /api/analytics/month_wise_open_close_pivot_report?selected_month=YYYY-MM",
                        "GET /api/analytics/quarter_wise_open_close_report?start_year=YYYY&start_quarter=Q1&end_year=YYYY&end_quarter=Q4",
                        "GET /api/analytics/year_wise_open_close_pivot_report?start_year=YYYY&start_date=MM-DD&end_year=YYYY&end_date=MM-DD"
                    ]
                },
                "chatbot": {
                    "base_path": "/api/chatbot",
                    "description": "AI-powered conversational chatbot",
                    "endpoints": [
                        "GET /api/chatbot/",
                        "GET /api/chatbot/chatbot_health",
                        "POST /api/chatbot/initialize",
                        "POST /api/chatbot/chat",
                        "POST /api/chatbot/reset",
                        "DELETE /api/chatbot/session/{session_id}"
                    ]
                }
            },
            "documentation": {
                "swagger_ui": "http://localhost:8000/docs",
                "openapi_json": "http://localhost:8000/openapi.json"
            },
            "example_usage": {
                "analytics": "curl http://localhost:8000/api/analytics/healthcheck",
                "chatbot": "curl http://localhost:8000/api/chatbot/chatbot_health"
            }
        }
    except Exception as e:
        logger.error(f"Root endpoint error | error={str(CustomException(e, sys))}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

@app.get("/healthcheck", tags=["Health"])
def global_health_check():
    """Global health check for entire platform"""
    try:
        logger.info("Global health check accessed")
        
        return {
            "platform_status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {
                "analytics": {
                    "status": "available",
                    "path": "/api/analytics"
                },
                "chatbot": {
                    "status": "available",
                    "path": "/api/chatbot"
                }
            },
            "version": "2.0.0",
            "uptime": "system_active"
        }
        
    except Exception as e:
        logger.error(f"Health check error | error={str(CustomException(e, sys))}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

# ============================================================================
# Startup & Shutdown Events
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        logger.info("=" * 80)
        logger.info("UNIFIED FASTAPI APPLICATION STARTING")
        logger.info("=" * 80)
        logger.info("Application: %s", app.title)
        logger.info("Version: %s", app.version)
        logger.info("Server: http://localhost:8000")
        logger.info("=" * 80)

    except Exception as e:
        logger.exception(
            "Startup initialization failed",
            exc_info=CustomException(e, sys)
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        logger.info("=" * 80)
        logger.info("UNIFIED FASTAPI APPLICATION SHUTTING DOWN")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"Shutdown error | error={str(e)}")

# ============================================================================
# Development Server
# ============================================================================
if __name__ == "__main__":
    logger.info("Starting Unified FastAPI Server with APIRouter Architecture")
    
    try:
        uvicorn.run(
            "main:app",  # Point to this file
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True,
            access_log=True,
            workers=1
        )
    except Exception as e:
        logger.error(f"Failed to start server | error={str(e)}")
        sys.exit(1)