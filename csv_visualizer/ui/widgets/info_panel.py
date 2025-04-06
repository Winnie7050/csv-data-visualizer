"""
Info Panel Widget for CSV Data Visualizer.

This module contains the InfoPanelWidget class for displaying data metrics.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QGridLayout, QGroupBox, QScrollArea, QFrame,
                          QSizePolicy, QTableWidget, QTableWidgetItem,
                          QHeaderView, QTabWidget)
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
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
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


class GroupInfoWidget(QWidget):
    """Widget for displaying file group information."""
    
    def __init__(self, group_info: Dict[str, Any], parent=None):
        """
        Initialize the group info widget.
        
        Args:
            group_info: Group information dictionary
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize UI
        self._init_ui(group_info)
    
    def _init_ui(self, group_info: Dict[str, Any]):
        """
        Initialize the user interface.
        
        Args:
            group_info: Group information dictionary
        """
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)
        
        # Create header
        self.header = QLabel("File Group Information")
        self.header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        
        # Create metrics grid
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setColumnStretch(1, 1)
        
        # Add metrics
        row = 0
        
        # Metric name
        if 'metric' in group_info:
            self.metrics_grid.addWidget(QLabel("Metric:"), row, 0)
            self.metrics_grid.addWidget(QLabel(group_info['metric']), row, 1)
            row += 1
        
        # Date range
        if 'start_date' in group_info and 'end_date' in group_info:
            start_date = group_info['start_date']
            end_date = group_info['end_date']
            
            self.metrics_grid.addWidget(QLabel("Date Range:"), row, 0)
            self.metrics_grid.addWidget(QLabel(f"{start_date} to {end_date}"), row, 1)
            row += 1
        
        # File count
        if 'file_count' in group_info:
            self.metrics_grid.addWidget(QLabel("Files Combined:"), row, 0)
            self.metrics_grid.addWidget(QLabel(str(group_info['file_count'])), row, 1)
            row += 1
        
        # Total size
        if 'total_size' in group_info:
            size_mb = group_info['total_size'] / (1024 * 1024)
            self.metrics_grid.addWidget(QLabel("Total Size:"), row, 0)
            self.metrics_grid.addWidget(QLabel(f"{size_mb:.2f} MB"), row, 1)
            row += 1
        
        # Add header and metrics grid to layout
        self.layout.addWidget(self.header)
        self.layout.addLayout(self.metrics_grid)
        self.layout.addStretch()
    
    def update_info(self, group_info: Dict[str, Any]):
        """
        Update the displayed group information.
        
        Args:
            group_info: New group information dictionary
        """
        # Clear layout
        for i in reversed(range(self.layout.count())):
            layout_item = self.layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().setParent(None)
            elif layout_item.layout():
                # Clear sub-layout
                sub_layout = layout_item.layout()
                for j in reversed(range(sub_layout.count())):
                    sub_item = sub_layout.itemAt(j)
                    if sub_item.widget():
                        sub_item.widget().setParent(None)
        
        # Recreate UI
        self._init_ui(group_info)


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
        
        # Date range
        if col > 0:
            row += 1
            col = 0
        
        if 'first_date' in metrics:
            self.layout.addWidget(MetricWidget("First Date", metrics['first_date']), row, col)
            col += 1
        
        if 'last_date' in metrics:
            self.layout.addWidget(MetricWidget("Last Date", metrics['last_date']), row, col)
            col += 1
        
        # Trend information
        if 'trend' in metrics and metrics['trend']:
            if col > 0:
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
        
        # Current file or group info
        self.current_file_info = None
        
        # Initialize UI
        self._init_ui()
        
        self.logger.info("Info panel widget initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create metrics tab
        self.metrics_tab = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_tab)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(0)
        
        # Create metrics scroll area
        self.metrics_scroll = QScrollArea()
        self.metrics_scroll.setWidgetResizable(True)
        self.metrics_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create metrics container widget
        self.metrics_container = QWidget()
        self.metrics_container_layout = QVBoxLayout(self.metrics_container)
        self.metrics_container_layout.setContentsMargins(6, 6, 6, 6)
        self.metrics_container_layout.setSpacing(6)
        
        # Set metrics scroll area widget
        self.metrics_scroll.setWidget(self.metrics_container)
        
        # Add metrics scroll area to metrics layout
        self.metrics_layout.addWidget(self.metrics_scroll)
        
        # Create file info tab
        self.file_info_tab = QWidget()
        self.file_info_layout = QVBoxLayout(self.file_info_tab)
        self.file_info_layout.setContentsMargins(6, 6, 6, 6)
        self.file_info_layout.setSpacing(6)
        
        # Create file info scroll area
        self.file_info_scroll = QScrollArea()
        self.file_info_scroll.setWidgetResizable(True)
        self.file_info_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create file info container widget
        self.file_info_container = QWidget()
        self.file_info_container_layout = QVBoxLayout(self.file_info_container)
        self.file_info_container_layout.setContentsMargins(0, 0, 0, 0)
        self.file_info_container_layout.setSpacing(6)
        
        # Create group info widget (initially empty)
        self.group_info_widget = GroupInfoWidget({})
        self.file_info_container_layout.addWidget(self.group_info_widget)
        self.group_info_widget.hide()  # Hide until needed
        
        # Set file info scroll area widget
        self.file_info_scroll.setWidget(self.file_info_container)
        
        # Add file info scroll area to file info layout
        self.file_info_layout.addWidget(self.file_info_scroll)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.metrics_tab, "Metrics")
        self.tab_widget.addTab(self.file_info_tab, "File Info")
        
        # Add tab widget to layout
        self.layout.addWidget(self.tab_widget)
        
        # Set fixed height
        self.setFixedHeight(200)
    
    def update_metrics(self, metrics: Dict[str, Dict[str, Any]]):
        """
        Update the displayed metrics.
        
        Args:
            metrics: Dictionary of metrics by series
        """
        self.logger.info(f"Updating metrics: {len(metrics)} series")
        
        try:
            # Clear metrics container layout
            for i in reversed(range(self.metrics_container_layout.count())): 
                widget = self.metrics_container_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            # Clear series widgets
            self.series_widgets = {}
            
            # Check for error
            if 'error' in metrics:
                error_label = QLabel(f"Error: {metrics['error']}")
                error_label.setStyleSheet("color: red;")
                self.metrics_container_layout.addWidget(error_label)
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
                    self.metrics_container_layout.addWidget(widget)
            
            # Add stretch to bottom
            self.metrics_container_layout.addStretch()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {str(e)}", exc_info=True)
            
            # Show error message
            error_label = QLabel(f"Error updating metrics: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.metrics_container_layout.addWidget(error_label)
    
    def update_file_info(self, file_info: Dict[str, Any]):
        """
        Update the displayed file information.
        
        Args:
            file_info: File information dictionary
        """
        self.logger.info(f"Updating file info: {file_info.get('name', 'Unknown')}")
        
        # Store current file info
        self.current_file_info = file_info
        
        try:
            # Check if this is a file group
            is_group = file_info.get('is_group', False)
            
            if is_group:
                # Show group info
                self.group_info_widget.update_info(file_info)
                self.group_info_widget.show()
                
                # Switch to the file info tab
                self.tab_widget.setCurrentWidget(self.file_info_tab)
            else:
                # Hide group info
                self.group_info_widget.hide()
                
                # Switch to the metrics tab
                self.tab_widget.setCurrentWidget(self.metrics_tab)
            
        except Exception as e:
            self.logger.error(f"Error updating file info: {str(e)}", exc_info=True)
            
            # Hide group info widget
            self.group_info_widget.hide()
            
            # Show error message
            error_label = QLabel(f"Error updating file info: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.file_info_container_layout.addWidget(error_label)
