#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup script for CSV Data Visualizer."""

from setuptools import setup, find_packages

# Read version from package
with open("csv_visualizer/__init__.py", "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break
    else:
        version = "0.1.0"

# Read requirements from file
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip()]

setup(
    name="csv-data-visualizer",
    version=version,
    description="A Python-based application for visualizing time-series CSV data",
    author="MCP Team",
    url="https://github.com/Winnie7050/csv-data-visualizer",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "csv-visualizer=csv_visualizer.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.9",
)
