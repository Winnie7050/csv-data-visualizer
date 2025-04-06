#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV Data Visualizer - Main Entry Point

A Python-based application for visualizing time-series CSV data with PyQt6, Pandas, and Plotly.
"""

import sys
import os

# Store original argv for QtWebEngine
original_argv = sys.argv.copy()

# Ensure application name is passed to QCoreApplication
if not sys.argv[0]:
    sys.argv[0] = "CSV_Data_Visualizer"

# Add required imports
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
        exit_code = app.run(original_argv)
        
        # Clean up resources
        try:
            app.cleanup()
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {str(cleanup_error)}")
            
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
