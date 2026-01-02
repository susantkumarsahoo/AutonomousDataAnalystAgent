import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

logger = get_logger(__name__)

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    try:
        logger.info("Home endpoint hit (Flask)")
        return jsonify(
            {
                "message": "Welcome to the Twitter Flow Analysis API",
                "version": "1.0.0",
            }
        ), 200
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        return jsonify({"error": "Internal server error"}), 500


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    try:
        logger.info("Health check endpoint hit (Flask)")
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(str(CustomException(e, sys)))
        return jsonify({"error": "Internal server error"}), 500


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Flask API Server")
    logger.info("=" * 60)

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )