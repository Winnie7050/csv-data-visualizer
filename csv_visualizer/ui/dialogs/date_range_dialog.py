"""
Date Range Dialog for CSV Data Visualizer.

This module contains the DateRangeDialog class for selecting a date range.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                          QDateEdit, QPushButton, QDialogButtonBox,
                          QGroupBox, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon

from csv_visualizer.utils.logging_utils import get_module_logger


class DateRangeDialog(QDialog):
    """Dialog for selecting a date range."""
    
    def __init__(self, app_controller, parent=None):
        """
        Initialize the date range dialog.
        
        Args:
            app_controller: Application controller
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.app_controller = app_controller
        self.logger = get_module_logger("DateRangeDialog")
        
        # Initialize UI
        self._init_ui()
        
        # Set default date range
        self._set_default_date_range()
        
        self.logger.info("Date range dialog initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Select Date Range")
        self.setMinimumWidth(300)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        
        # Create date range group
        self.date_range_group = QGroupBox("Date Range")
        self.date_range_layout = QGridLayout(self.date_range_group)
        
        # Start date
        self.start_label = QLabel("Start Date:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.dateChanged.connect(self._validate_dates)
        
        # End date
        self.end_label = QLabel("End Date:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.dateChanged.connect(self._validate_dates)
        
        # Add widgets to layout
        self.date_range_layout.addWidget(self.start_label, 0, 0)
        self.date_range_layout.addWidget(self.start_date_edit, 0, 1)
        self.date_range_layout.addWidget(self.end_label, 1, 0)
        self.date_range_layout.addWidget(self.end_date_edit, 1, 1)
        
        # Create preset buttons
        self.preset_group = QGroupBox("Presets")
        self.preset_layout = QHBoxLayout(self.preset_group)
        
        self.last_7_button = QPushButton("Last 7 Days")
        self.last_30_button = QPushButton("Last 30 Days")
        self.last_90_button = QPushButton("Last 90 Days")
        
        self.last_7_button.clicked.connect(lambda: self._set_preset_range(7))
        self.last_30_button.clicked.connect(lambda: self._set_preset_range(30))
        self.last_90_button.clicked.connect(lambda: self._set_preset_range(90))
        
        self.preset_layout.addWidget(self.last_7_button)
        self.preset_layout.addWidget(self.last_30_button)
        self.preset_layout.addWidget(self.last_90_button)
        
        # Create button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Add widgets to main layout
        self.layout.addWidget(self.date_range_group)
        self.layout.addWidget(self.preset_group)
        self.layout.addWidget(self.button_box)
    
    def _set_default_date_range(self):
        """Set default date range (last 30 days)."""
        self._set_preset_range(30)
    
    def _set_preset_range(self, days: int):
        """
        Set a preset date range.
        
        Args:
            days: Number of days
        """
        self.logger.info(f"Setting preset range: {days} days")
        
        # Calculate dates
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days)
        
        # Update date edits
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
    
    def _validate_dates(self):
        """Validate date range."""
        # Get dates
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        # Check if start date is after end date
        if start_date > end_date:
            # Set start date to end date
            self.start_date_edit.setDate(end_date)
    
    def get_selected_range(self) -> Tuple[datetime, datetime]:
        """
        Get the selected date range.
        
        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        # Get dates
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        # Convert to datetime
        start = datetime(start_date.year(), start_date.month(), start_date.day())
        end = datetime(end_date.year(), end_date.month(), end_date.day(), 23, 59, 59)
        
        return start, end
