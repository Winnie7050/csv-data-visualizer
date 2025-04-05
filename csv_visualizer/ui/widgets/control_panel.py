"""
Control Panel Widget for CSV Data Visualizer.

This module contains the ControlPanelWidget class for configuring visualizations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QComboBox, QCheckBox, QGroupBox, QGridLayout,
                          QSizePolicy, QScrollArea, QFrame, QListWidget,
                          QListWidgetItem, QDateEdit, QToolButton, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QDate
from PyQt6.QtGui import QIcon

from csv_visualizer.utils.logging_utils import get_module_logger


class SeriesSelectorWidget(QWidget):
    """Widget for selecting data series to display."""
    
    # Signal emitted when selection changes
    selection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the series selector widget."""
        super().__init__(parent)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        # Create header
        self.header_layout = QHBoxLayout()
        self.header_label = QLabel("Data Series:")
        self.header_layout.addWidget(self.header_label)
        self.header_layout.addStretch()
        
        # Create select/deselect buttons
        self.select_all_button = QToolButton()
        self.select_all_button.setText("All")
        self.select_all_button.setToolTip("Select all series")
        self.select_all_button.clicked.connect(self._select_all)
        
        self.deselect_all_button = QToolButton()
        self.deselect_all_button.setText("None")
        self.deselect_all_button.setToolTip("Deselect all series")
        self.deselect_all_button.clicked.connect(self._deselect_all)
        
        self.header_layout.addWidget(self.select_all_button)
        self.header_layout.addWidget(self.deselect_all_button)
        
        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemChanged.connect(self._item_changed)
        
        # Add widgets to layout
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.list_widget)
    
    def set_series(self, series: List[str]):
        """
        Set available series.
        
        Args:
            series: List of series names
        """
        # Block signals to prevent multiple calls to _item_changed
        self.list_widget.blockSignals(True)
        
        # Clear list
        self.list_widget.clear()
        
        # Add items
        for s in series:
            item = QListWidgetItem(s)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)
        
        # Unblock signals
        self.list_widget.blockSignals(False)
        
        # Emit signal for initial selection
        self.selection_changed.emit()
    
    def get_selected_series(self) -> List[str]:
        """
        Get selected series.
        
        Returns:
            List of selected series names
        """
        selected = []
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        
        return selected
    
    def _item_changed(self, item: QListWidgetItem):
        """
        Handle item check state change.
        
        Args:
            item: Changed item
        """
        # Emit signal
        self.selection_changed.emit()
    
    def _select_all(self):
        """Select all series."""
        # Block signals to prevent multiple calls to _item_changed
        self.list_widget.blockSignals(True)
        
        # Check all items
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        
        # Unblock signals
        self.list_widget.blockSignals(False)
        
        # Emit signal
        self.selection_changed.emit()
    
    def _deselect_all(self):
        """Deselect all series."""
        # Block signals to prevent multiple calls to _item_changed
        self.list_widget.blockSignals(True)
        
        # Uncheck all items
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        
        # Unblock signals
        self.list_widget.blockSignals(False)
        
        # Emit signal
        self.selection_changed.emit()


class DateRangeWidget(QWidget):
    """Widget for selecting a date range."""
    
    # Signal emitted when date range changes
    date_range_changed = pyqtSignal(QDate, QDate)
    
    def __init__(self, parent=None):
        """Initialize the date range widget."""
        super().__init__(parent)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        # Create labels
        self.start_label = QLabel("Start Date:")
        self.end_label = QLabel("End Date:")
        
        # Create date edits
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.dateChanged.connect(self._date_changed)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.dateChanged.connect(self._date_changed)
        
        # Add widgets to layout
        self.layout.addWidget(self.start_label, 0, 0)
        self.layout.addWidget(self.start_date_edit, 0, 1)
        self.layout.addWidget(self.end_label, 1, 0)
        self.layout.addWidget(self.end_date_edit, 1, 1)
    
    def set_date_range(self, start_date: datetime, end_date: datetime):
        """
        Set the date range.
        
        Args:
            start_date: Start date
            end_date: End date
        """
        # Block signals to prevent multiple calls to _date_changed
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        
        # Set dates
        self.start_date_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))
        self.end_date_edit.setDate(QDate(end_date.year, end_date.month, end_date.day))
        
        # Unblock signals
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        
        # Emit signal
        self._date_changed()
    
    def get_date_range(self) -> tuple:
        """
        Get the selected date range.
        
        Returns:
            Tuple of (start_date, end_date) as QDate objects
        """
        return (self.start_date_edit.date(), self.end_date_edit.date())
    
    def _date_changed(self):
        """Handle date change."""
        # Ensure start date is not after end date
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        if start_date > end_date:
            # If start date is after end date, set end date to start date
            self.end_date_edit.blockSignals(True)
            self.end_date_edit.setDate(start_date)
            self.end_date_edit.blockSignals(False)
            end_date = start_date
        
        # Emit signal
        self.date_range_changed.emit(start_date, end_date)


class ControlPanelWidget(QWidget):
    """Control Panel Widget for configuring visualizations."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal()
    
    def __init__(self, app_controller):
        """
        Initialize the control panel widget.
        
        Args:
            app_controller: Application controller
        """
        super().__init__()
        
        self.app_controller = app_controller
        self.logger = get_module_logger("ControlPanelWidget")
        
        # Initialize state
        self.chart_type = self.app_controller.settings.default_chart_type
        self.time_period = self.app_controller.settings.default_time_period
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Initialize UI
        self._init_ui()
        
        self.logger.info("Control panel widget initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(10)
        
        # Create chart type group
        self.chart_type_group = QGroupBox("Chart Type")
        self.chart_type_layout = QVBoxLayout(self.chart_type_group)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Line Chart", "Bar Chart", "Pie Chart", "Diverging Bar"
        ])
        self.chart_type_combo.setCurrentText(self.chart_type)
        self.chart_type_combo.currentTextChanged.connect(self._chart_type_changed)
        
        self.chart_type_layout.addWidget(self.chart_type_combo)
        
        # Create time period group
        self.time_period_group = QGroupBox("Time Period")
        self.time_period_layout = QVBoxLayout(self.time_period_group)
        
        self.time_period_combo = QComboBox()
        self.time_period_combo.addItems([
            "7 Days", "30 Days", "60 Days", "90 Days", "Custom..."
        ])
        self.time_period_combo.setCurrentText(f"{self.time_period} Days")
        self.time_period_combo.currentTextChanged.connect(self._time_period_changed)
        
        self.time_period_layout.addWidget(self.time_period_combo)
        
        # Create date range widget (initially hidden)
        self.date_range_widget = DateRangeWidget()
        self.date_range_widget.date_range_changed.connect(self._custom_date_range_changed)
        self.date_range_widget.setVisible(False)
        
        self.time_period_layout.addWidget(self.date_range_widget)
        
        # Create series selector
        self.series_selector = SeriesSelectorWidget()
        self.series_selector.selection_changed.connect(self._series_selection_changed)
        
        # Add widgets to layout
        self.layout.addWidget(self.chart_type_group)
        self.layout.addWidget(self.time_period_group)
        self.layout.addWidget(self.series_selector, 1)  # 1 = stretch factor
    
    def set_chart_type(self, chart_type: str):
        """
        Set the chart type.
        
        Args:
            chart_type: Chart type
        """
        self.logger.info(f"Setting chart type: {chart_type}")
        
        # Update state
        self.chart_type = chart_type
        
        # Update combo box
        self.chart_type_combo.setCurrentText(chart_type)
    
    def set_time_period(self, days: int):
        """
        Set the time period.
        
        Args:
            days: Number of days
        """
        self.logger.info(f"Setting time period: {days} days")
        
        # Update state
        self.time_period = days
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Update combo box
        self.time_period_combo.setCurrentText(f"{days} Days")
        
        # Hide date range widget
        self.date_range_widget.setVisible(False)
    
    def set_custom_date_range(self, start_date: datetime, end_date: datetime):
        """
        Set a custom date range.
        
        Args:
            start_date: Start date
            end_date: End date
        """
        self.logger.info(f"Setting custom date range: {start_date} to {end_date}")
        
        # Update state
        self.custom_start_date = start_date
        self.custom_end_date = end_date
        
        # Update combo box
        self.time_period_combo.setCurrentText("Custom...")
        
        # Update date range widget
        self.date_range_widget.set_date_range(start_date, end_date)
        
        # Show date range widget
        self.date_range_widget.setVisible(True)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Configuration dictionary
        """
        config = {
            'chart_type': self.chart_type,
            'series': self.series_selector.get_selected_series()
        }
        
        # Add date range
        if self.custom_start_date and self.custom_end_date:
            config['date_range'] = {
                'start': self.custom_start_date,
                'end': self.custom_end_date
            }
        else:
            config['date_range'] = {
                'days': self.time_period
            }
        
        return config
    
    def _chart_type_changed(self, chart_type: str):
        """
        Handle chart type change.
        
        Args:
            chart_type: New chart type
        """
        self.logger.info(f"Chart type changed: {chart_type}")
        
        # Update state
        self.chart_type = chart_type
        
        # Emit signal
        self.settings_changed.emit()
    
    def _time_period_changed(self, period: str):
        """
        Handle time period change.
        
        Args:
            period: New time period
        """
        self.logger.info(f"Time period changed: {period}")
        
        if period == "Custom...":
            # Show date range widget
            self.date_range_widget.setVisible(True)
            
            # Set default date range if not already set
            if not self.custom_start_date or not self.custom_end_date:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                self.custom_start_date = start_date
                self.custom_end_date = end_date
                
                self.date_range_widget.set_date_range(start_date, end_date)
        else:
            # Parse days from period string
            try:
                days = int(period.split()[0])
                
                # Update state
                self.time_period = days
                self.custom_start_date = None
                self.custom_end_date = None
                
                # Hide date range widget
                self.date_range_widget.setVisible(False)
                
                # Emit signal
                self.settings_changed.emit()
                
            except ValueError:
                self.logger.error(f"Invalid time period: {period}")
    
    def _custom_date_range_changed(self, start_date: QDate, end_date: QDate):
        """
        Handle custom date range change.
        
        Args:
            start_date: New start date
            end_date: New end date
        """
        self.logger.info(f"Custom date range changed: {start_date.toString()} to {end_date.toString()}")
        
        # Update state
        self.custom_start_date = datetime(start_date.year(), start_date.month(), start_date.day())
        self.custom_end_date = datetime(end_date.year(), end_date.month(), end_date.day())
        
        # Emit signal
        self.settings_changed.emit()
    
    def _series_selection_changed(self):
        """Handle series selection change."""
        self.logger.info("Series selection changed")
        
        # Emit signal
        self.settings_changed.emit()
