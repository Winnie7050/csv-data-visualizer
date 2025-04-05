"""
Info Panel Widget for CSV Data Visualizer.

This module contains the InfoPanelWidget class for displaying data metrics.
"""

import logging
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QGridLayout, QGroupBox, QScrollArea, QFrame,
                          QSizePolicy, QTableWidget, QTableWidgetItem,
                          QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from csv_visualizer.utils.logging_utils import get_module_logger


class MetricWidget(QWidget):
    """Widget for displaying a single metric."""
    
    def __init__(self, name: str, value: Any, parent=None):
        """
        Initialize the metric widget.
        
        Args:
            name: Metric name
            value: Metric value
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize UI
        self._init_ui(name, value)
    
    def _init_ui(self, name: str, value: Any):
        """
        Initialize the user interface.
        
        Args:
            name: Metric name
            value: Metric value
        """
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(2)
        
        # Create labels
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold; color: #aaa;")
        
        self.value_label = QLabel(str(self._format_value(value)))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        
        # Add widgets to layout
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.value_label)
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for display.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted value string
        """
        if isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, int):
            return f"{value:,}"
        elif value is None:
            return "N/A"
        else:
            return str(value)
    
    def update_value(self, value: Any):
        """
        Update the displayed value.
        
        Args:
            value: New value
        """
        self.value_label.setText(self._format_value(value))


class SeriesMetricsWidget(QGroupBox):
    """Widget for displaying metrics for a data series."""
    
    def __init__(self, series_name: str, metrics: Dict[str, Any], parent=None):
        """
        Initialize the series metrics widget.
        
        Args:
            series_name: Series name
            metrics: Metrics dictionary
            parent: Parent widget
        """
        super().__init__(series_name, parent)
        
        # Initialize UI
        self._init_ui(metrics)
    
    def _init_ui(self, metrics: Dict[str, Any]):
        """
        Initialize the user interface.
        
        Args:
            metrics: Metrics dictionary
        """
        # Create layout
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(6, 12, 6, 6)
        self.layout.setSpacing(6)
        
        # Add metrics
        self._add_metrics(metrics)
    
    def _add_metrics(self, metrics: Dict[str, Any]):
        """
        Add metrics to the layout.
        
        Args:
            metrics: Metrics dictionary
        """
        # Clear layout
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
        
        # Add basic metrics
        row = 0
        col = 0
        
        # Basic statistics
        if 'mean' in metrics:
            self.layout.addWidget(MetricWidget("Average", metrics['mean']), row, col)
            col += 1
        
        if 'median' in metrics:
            self.layout.addWidget(MetricWidget("Median", metrics['median']), row, col)
            col += 1
        
        if 'std' in metrics:
            self.layout.addWidget(MetricWidget("Std Dev", metrics['std']), row, col)
            col += 1
        
        if col > 0:
            row += 1
            col = 0
        
        if 'min' in metrics:
            self.layout.addWidget(MetricWidget("Minimum", metrics['min']), row, col)
            col += 1
        
        if 'max' in metrics:
            self.layout.addWidget(MetricWidget("Maximum", metrics['max']), row, col)
            col += 1
        
        if 'count' in metrics:
            self.layout.addWidget(MetricWidget("Count", metrics['count']), row, col)
            col += 1
        
        # Trend information
        if 'trend' in metrics and metrics['trend']:
            row += 1
            col = 0
            
            trend = metrics['trend']
            
            # Trend direction
            if 'direction' in trend:
                direction = trend['direction']
                direction_text = direction.capitalize()
                self.layout.addWidget(MetricWidget("Trend", direction_text), row, col)
                col += 1
            
            # Percent change
            if 'percent_change' in trend:
                pct_change = trend['percent_change']
                self.layout.addWidget(MetricWidget("Change %", pct_change), row, col)
                col += 1
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """
        Update the displayed metrics.
        
        Args:
            metrics: New metrics dictionary
        """
        self._add_metrics(metrics)


class InfoPanelWidget(QWidget):
    """Info Panel Widget for displaying data metrics."""
    
    def __init__(self, app_controller):
        """
        Initialize the info panel widget.
        
        Args:
            app_controller: Application controller
        """
        super().__init__()
        
        self.app_controller = app_controller
        self.logger = get_module_logger("InfoPanelWidget")
        
        # Series metrics widgets
        self.series_widgets = {}
        
        # Initialize UI
        self._init_ui()
        
        self.logger.info("Info panel widget initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create container widget
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(6, 6, 6, 6)
        self.container_layout.setSpacing(6)
        
        # Set scroll area widget
        self.scroll_area.setWidget(self.container)
        
        # Add scroll area to layout
        self.layout.addWidget(self.scroll_area)
        
        # Set fixed height
        self.setFixedHeight(150)
    
    def update_metrics(self, metrics: Dict[str, Dict[str, Any]]):
        """
        Update the displayed metrics.
        
        Args:
            metrics: Dictionary of metrics by series
        """
        self.logger.info(f"Updating metrics: {len(metrics)} series")
        
        try:
            # Clear container layout
            for i in reversed(range(self.container_layout.count())): 
                widget = self.container_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            # Clear series widgets
            self.series_widgets = {}
            
            # Check for error
            if 'error' in metrics:
                error_label = QLabel(f"Error: {metrics['error']}")
                error_label.setStyleSheet("color: red;")
                self.container_layout.addWidget(error_label)
                return
            
            # Add metrics for each series
            for series_name, series_metrics in metrics.items():
                if series_name in self.series_widgets:
                    # Update existing widget
                    self.series_widgets[series_name].update_metrics(series_metrics)
                else:
                    # Create new widget
                    widget = SeriesMetricsWidget(series_name, series_metrics)
                    self.series_widgets[series_name] = widget
                    self.container_layout.addWidget(widget)
            
            # Add stretch to bottom
            self.container_layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}", exc_info=True)
            
            # Show error message
            error_label = QLabel(f"Error updating metrics: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.container_layout.addWidget(error_label)
