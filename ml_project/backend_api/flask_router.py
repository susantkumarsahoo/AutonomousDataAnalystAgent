import os
import sys
import time
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from functools import wraps
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

logger = get_logger(__name__)

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# -----------------------------------------------------------------------------
# Middleware - Request Logging
# -----------------------------------------------------------------------------
@app.before_request
def before_request():
    """Log incoming requests and track timing"""
    g.start_time = time.time()
    logger.info(
        f"Incoming request | method={request.method} | "
        f"path={request.path} | ip={request.remote_addr}"
    )


@app.after_request
def after_request(response):
    """Log response and add security headers"""
    # Calculate request duration
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(
            f"Request completed | method={request.method} | "
            f"path={request.path} | status={response.status_code} | "
            f"duration={duration:.3f}s"
        )
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response


# -----------------------------------------------------------------------------
# Middleware - Error Handler
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 Error | path={request.path}")
    return jsonify({
        "error": "Resource not found",
        "path": request.path,
        "status": 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 Error | path={request.path} | error={str(error)}")
    return jsonify({
        "error": "Internal server error",
        "status": 500
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Global exception handler"""
    error_msg = str(CustomException(error, sys))
    logger.error(f"Unhandled exception | error={error_msg}")
    return jsonify({
        "error": "An unexpected error occurred",
        "details": error_msg if app.debug else None,
        "status": 500
    }), 500


# -----------------------------------------------------------------------------
# Decorator - Route Error Handler
# -----------------------------------------------------------------------------
def handle_errors(f):
    """Decorator to handle errors in routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Route error | endpoint={f.__name__} | error={error_msg}")
            return jsonify({
                "error": "Internal server error",
                "endpoint": f.__name__,
                "details": error_msg if app.debug else None
            }), 500
    return decorated_function


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@handle_errors
def home():
    """Home endpoint with API information"""
    logger.info("Home endpoint accessed")
    return jsonify({
        "message": "Welcome to the Twitter Flow Analysis API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "health": "/healthcheck",
            "home": "/"
        }
    }), 200


@app.route("/healthcheck", methods=["GET"])
@handle_errors
def healthcheck():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return jsonify({
        "status": "healthy",
        "service": "Flask API",
        "timestamp": time.time()
    }), 200


@app.route("/api/status", methods=["GET"])
@handle_errors
def api_status():
    """API status endpoint with detailed information"""
    logger.info("API status endpoint accessed")
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "uptime": "active",
        "environment": os.getenv("FLASK_ENV", "production"),
        "debug_mode": app.debug
    }), 200


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Flask API Server")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"Debug Mode: {app.debug}")
    logger.info(f"Host: 0.0.0.0")
    logger.info(f"Port: 5000")
    logger.info("=" * 60)

    try:
        app.run(
            debug=True,
            host="0.0.0.0",
            port=5000,
            threaded=True  # Enable multi-threading for better performance
        )
    except Exception as e:
        logger.error(f"Failed to start Flask server | error={str(e)}")
        sys.exit(1)