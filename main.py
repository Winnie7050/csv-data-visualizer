#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV Data Visualizer - Main Entry Point

A Python-based application for visualizing time-series CSV data with PyQt6, Pandas, and Plotly.
"""

import sys

# Add QtWebEngine initialization before importing any Qt modules
# This ensures proper initialization with command line args
sys.argv = [arg for arg in sys.argv if not arg.startswith('--single-process')]
if '--disable-gpu' not in sys.argv:
    sys.argv.append('--disable-gpu')  # Helps with certain rendering issues
if '--disable-software-rasterizer' not in sys.argv:
    sys.argv.append('--disable-software-rasterizer')  # Helps with rendering issues

# Ensure application name is passed to QCoreApplication
if not sys.argv[0]:
    sys.argv[0] = "CSV_Data_Visualizer"

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
