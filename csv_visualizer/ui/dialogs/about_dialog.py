"""
About Dialog for CSV Data Visualizer.

This module contains the AboutDialog class for displaying application information.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                          QPushButton, QDialogButtonBox, QTabWidget,
                          QTextBrowser, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont

from csv_visualizer import __version__


class AboutDialog(QDialog):
    """Dialog for displaying application information."""
    
    def __init__(self, parent=None):
        """
        Initialize the about dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("About CSV Data Visualizer")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        
        # Create header
        self.header_layout = QHBoxLayout()
        
        # Add icon (placeholder)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("background-color: #0078d4; border-radius: 8px;")
        
        # Add title and version
        self.title_layout = QVBoxLayout()
        
        self.title_label = QLabel("CSV Data Visualizer")
        self.title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        
        self.version_label = QLabel(f"Version {__version__}")
        self.version_label.setStyleSheet("font-size: 10pt; color: #888;")
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.version_label)
        
        self.header_layout.addWidget(self.icon_label)
        self.header_layout.addLayout(self.title_layout)
        self.header_layout.addStretch()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # About tab
        self.about_widget = QWidget()
        self.about_layout = QVBoxLayout(self.about_widget)
        
        self.about_text = QTextBrowser()
        self.about_text.setOpenExternalLinks(True)
        self.about_text.setHtml(
            "<p>CSV Data Visualizer is a powerful tool for visualizing time-series CSV data.</p>"
            "<p>Features include:</p>"
            "<ul>"
            "<li>Interactive visualization of time-series data</li>"
            "<li>Multiple chart types (Line, Bar, Pie, Diverging Bar)</li>"
            "<li>Time period selection and data filtering</li>"
            "<li>Efficient handling of large datasets</li>"
            "</ul>"
            f"<p>Build Date: {datetime.now().strftime('%Y-%m-%d')}</p>"
        )
        
        self.about_layout.addWidget(self.about_text)
        
        # Credits tab
        self.credits_widget = QWidget()
        self.credits_layout = QVBoxLayout(self.credits_widget)
        
        self.credits_text = QTextBrowser()
        self.credits_text.setOpenExternalLinks(True)
        self.credits_text.setHtml(
            "<p><strong>Created by:</strong> MCP Team</p>"
            "<p><strong>Technologies:</strong></p>"
            "<ul>"
            "<li><a href='https://www.python.org/'>Python</a></li>"
            "<li><a href='https://www.riverbankcomputing.com/software/pyqt/'>PyQt6</a></li>"
            "<li><a href='https://pandas.pydata.org/'>Pandas</a></li>"
            "<li><a href='https://plotly.com/python/'>Plotly</a></li>"
            "<li><a href='https://matplotlib.org/'>Matplotlib</a></li>"
            "</ul>"
        )
        
        self.credits_layout.addWidget(self.credits_text)
        
        # Add tabs
        self.tab_widget.addTab(self.about_widget, "About")
        self.tab_widget.addTab(self.credits_widget, "Credits")
        
        # Create button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)
        
        # Add widgets to main layout
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.button_box)
