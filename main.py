#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV Data Visualizer - Main Entry Point

A Python-based application for visualizing time-series CSV data with PyQt6, Pandas, and Plotly.
"""

import sys
import os
from csv_visualizer.core.application import Application
from csv_visualizer.utils.logging_utils import setup_logging


def main():
    """Main entry point for the application."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting CSV Data Visualizer")
    
    try:
        # Create and start application
        app = Application(logger)
        exit_code = app.run(sys.argv)
        
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
