"""
Main Window for CSV Data Visualizer.

This module contains the MainWindow class for the CSV Data Visualizer application.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QSplitter, QTabWidget, 
                          QToolBar, QStatusBar, QMenu, QMenuBar, QFileDialog,
                          QMessageBox, QApplication, QVBoxLayout, QHBoxLayout,
                          QLabel, QComboBox, QPushButton, QToolButton)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.ui.widgets.file_browser import FileBrowserWidget
from csv_visualizer.ui.widgets.chart_view import ChartViewWidget
from csv_visualizer.ui.widgets.control_panel import ControlPanelWidget
from csv_visualizer.ui.widgets.info_panel import InfoPanelWidget
from csv_visualizer.ui.dialogs.date_range_dialog import DateRangeDialog
from csv_visualizer.ui.dialogs.about_dialog import AboutDialog


class MainWindow(QMainWindow):
    """Main Window for CSV Data Visualizer."""
    
    def __init__(self, app_controller):
        """
        Initialize the main window.
        
        Args:
            app_controller: Application controller instance
        """
        super().__init__()
        
        self.app_controller = app_controller
        self.logger = get_module_logger("MainWindow")
        
        # Initialize UI
        self._init_ui()
        
        self.logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("CSV Data Visualizer")
        self.resize(
            self.app_controller.settings.window_width,
            self.app_controller.settings.window_height
        )
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(4)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create file browser
        self.file_browser = FileBrowserWidget(self.app_controller)
        self.file_browser.file_selected.connect(self.on_file_selected)
        
        # Create dashboard container
        self.dashboard_container = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_container)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create control panel
        self.control_panel = ControlPanelWidget(self.app_controller)
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        
        # Create chart view
        self.chart_view = ChartViewWidget(self.app_controller)
        
        # Create info panel
        self.info_panel = InfoPanelWidget(self.app_controller)
        
        # Add widgets to dashboard layout
        self.dashboard_layout.addWidget(self.control_panel)
        self.dashboard_layout.addWidget(self.chart_view, 1)  # 1 = stretch factor
        self.dashboard_layout.addWidget(self.info_panel)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.file_browser)
        self.main_splitter.addWidget(self.dashboard_container)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes(self.app_controller.settings.splitter_sizes)
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.main_splitter)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        self.menu_bar = self.menuBar()
        
        # File menu
        self.file_menu = self.menu_bar.addMenu("&File")
        
        # Open File action
        self.open_action = QAction("&Open CSV File...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.on_open_file)
        self.file_menu.addAction(self.open_action)
        
        # Open Directory action
        self.open_dir_action = QAction("Open Directory...", self)
        self.open_dir_action.setShortcut("Ctrl+Shift+O")
        self.open_dir_action.triggered.connect(self.on_open_directory)
        self.file_menu.addAction(self.open_dir_action)
        
        self.file_menu.addSeparator()
        
        # Export submenu
        self.export_menu = self.file_menu.addMenu("&Export")
        
        # Export Image action
        self.export_image_action = QAction("Export as &Image...", self)
        self.export_image_action.triggered.connect(self.on_export_image)
        self.export_menu.addAction(self.export_image_action)
        
        # Export CSV action
        self.export_csv_action = QAction("Export as &CSV...", self)
        self.export_csv_action.triggered.connect(self.on_export_csv)
        self.export_menu.addAction(self.export_csv_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # View menu
        self.view_menu = self.menu_bar.addMenu("&View")
        
        # Chart Type submenu
        self.chart_type_menu = self.view_menu.addMenu("Chart &Type")
        
        # Line Chart action
        self.line_chart_action = QAction("&Line Chart", self)
        self.line_chart_action.triggered.connect(lambda: self.on_chart_type_selected("Line Chart"))
        self.chart_type_menu.addAction(self.line_chart_action)
        
        # Bar Chart action
        self.bar_chart_action = QAction("&Bar Chart", self)
        self.bar_chart_action.triggered.connect(lambda: self.on_chart_type_selected("Bar Chart"))
        self.chart_type_menu.addAction(self.bar_chart_action)
        
        # Pie Chart action
        self.pie_chart_action = QAction("&Pie Chart", self)
        self.pie_chart_action.triggered.connect(lambda: self.on_chart_type_selected("Pie Chart"))
        self.chart_type_menu.addAction(self.pie_chart_action)
        
        # Diverging Bar Chart action
        self.diverging_bar_action = QAction("&Diverging Bar Chart", self)
        self.diverging_bar_action.triggered.connect(lambda: self.on_chart_type_selected("Diverging Bar"))
        self.chart_type_menu.addAction(self.diverging_bar_action)
        
        # Time Period submenu
        self.time_period_menu = self.view_menu.addMenu("&Time Period")
        
        # 7 Days action
        self.seven_days_action = QAction("&7 Days", self)
        self.seven_days_action.triggered.connect(lambda: self.on_time_period_selected(7))
        self.time_period_menu.addAction(self.seven_days_action)
        
        # 30 Days action
        self.thirty_days_action = QAction("&30 Days", self)
        self.thirty_days_action.triggered.connect(lambda: self.on_time_period_selected(30))
        self.time_period_menu.addAction(self.thirty_days_action)
        
        # 60 Days action
        self.sixty_days_action = QAction("&60 Days", self)
        self.sixty_days_action.triggered.connect(lambda: self.on_time_period_selected(60))
        self.time_period_menu.addAction(self.sixty_days_action)
        
        # 90 Days action
        self.ninety_days_action = QAction("&90 Days", self)
        self.ninety_days_action.triggered.connect(lambda: self.on_time_period_selected(90))
        self.time_period_menu.addAction(self.ninety_days_action)
        
        # Custom Date Range action
        self.custom_date_action = QAction("&Custom Date Range...", self)
        self.custom_date_action.triggered.connect(self.on_custom_date_range)
        self.time_period_menu.addAction(self.custom_date_action)
        
        # Help menu
        self.help_menu = self.menu_bar.addMenu("&Help")
        
        # About action
        self.about_action = QAction("&About", self)
        self.about_action.triggered.connect(self.on_about)
        self.help_menu.addAction(self.about_action)
    
    def _create_toolbar(self):
        """Create the toolbar."""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Add open file action to toolbar
        self.toolbar.addAction(self.open_action)
        
        # Add open directory action to toolbar
        self.toolbar.addAction(self.open_dir_action)
        
        self.toolbar.addSeparator()
        
        # Add chart type selector to toolbar
        self.chart_type_label = QLabel("Chart Type:")
        self.toolbar.addWidget(self.chart_type_label)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Line Chart", "Bar Chart", "Pie Chart", "Diverging Bar"
        ])
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_selected)
        self.toolbar.addWidget(self.chart_type_combo)
        
        self.toolbar.addSeparator()
        
        # Add time period selector to toolbar
        self.time_period_label = QLabel("Time Period:")
        self.toolbar.addWidget(self.time_period_label)
        
        self.time_period_combo = QComboBox()
        self.time_period_combo.addItems([
            "7 Days", "30 Days", "60 Days", "90 Days", "Custom..."
        ])
        self.time_period_combo.setCurrentText("30 Days")  # Default
        self.time_period_combo.currentTextChanged.connect(self.on_time_period_changed)
        self.toolbar.addWidget(self.time_period_combo)
        
        # Add refresh button
        self.toolbar.addSeparator()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.on_refresh)
        self.toolbar.addWidget(self.refresh_button)
    
    def on_file_selected(self, file_info: Dict[str, Any]):
        """
        Handle file selection.
        
        Args:
            file_info: File information dictionary
        """
        self.logger.info(f"File selected: {file_info['name']}")
        
        try:
            # Update status bar
            self.status_bar.showMessage(f"Loading: {file_info['name']}")
            
            # Process the file
            self._load_and_visualize_file(file_info)
            
            # Update status bar
            self.status_bar.showMessage(f"Loaded: {file_info['name']}")
            
        except Exception as e:
            self.logger.error(f"Error loading file: {str(e)}", exc_info=True)
            self.status_bar.showMessage(f"Error loading file: {str(e)}")
            
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading file: {str(e)}"
            )
    
    def on_chart_type_selected(self, chart_type: str):
        """
        Handle chart type selection.
        
        Args:
            chart_type: Selected chart type
        """
        self.logger.info(f"Chart type selected: {chart_type}")
        
        # Update combo box if called from menu
        if self.chart_type_combo.currentText() != chart_type:
            self.chart_type_combo.setCurrentText(chart_type)
        
        # Update control panel
        self.control_panel.set_chart_type(chart_type)
        
        # Refresh visualization
        self.on_refresh()
    
    def on_time_period_changed(self, period: str):
        """
        Handle time period selection.
        
        Args:
            period: Selected time period
        """
        self.logger.info(f"Time period selected: {period}")
        
        if period == "Custom...":
            # Show custom date range dialog
            self.on_custom_date_range()
        else:
            # Parse days from period string
            days = int(period.split()[0])
            
            # Update control panel
            self.control_panel.set_time_period(days)
            
            # Refresh visualization
            self.on_refresh()
    
    def on_time_period_selected(self, days: int):
        """
        Handle time period selection from menu.
        
        Args:
            days: Number of days
        """
        self.logger.info(f"Time period selected: {days} days")
        
        # Update combo box
        self.time_period_combo.setCurrentText(f"{days} Days")
        
        # Update control panel
        self.control_panel.set_time_period(days)
        
        # Refresh visualization
        self.on_refresh()
    
    def on_custom_date_range(self):
        """Handle custom date range selection."""
        self.logger.info("Custom date range requested")
        
        # Show date range dialog
        dialog = DateRangeDialog(self.app_controller, self)
        
        if dialog.exec():
            # Get selected date range
            start_date, end_date = dialog.get_selected_range()
            
            self.logger.info(f"Custom date range selected: {start_date} to {end_date}")
            
            # Update control panel
            self.control_panel.set_custom_date_range(start_date, end_date)
            
            # Update combo box
            self.time_period_combo.setCurrentText("Custom...")
            
            # Refresh visualization
            self.on_refresh()
        else:
            # Restore previous selection
            current_config = self.control_panel.get_config()
            if 'date_range' in current_config and 'days' in current_config['date_range']:
                days = current_config['date_range']['days']
                self.time_period_combo.setCurrentText(f"{days} Days")
    
    def on_settings_changed(self):
        """Handle settings changes from control panel."""
        self.logger.info("Settings changed, refreshing visualization")
        
        # Refresh visualization
        self.on_refresh()
    
    def on_refresh(self):
        """Refresh the current visualization."""
        self.logger.info("Refreshing visualization")
        
        # Get current file info
        file_info = self.file_browser.get_selected_file_info()
        
        if file_info:
            self._load_and_visualize_file(file_info)
    
    def on_open_file(self):
        """Handle open file action."""
        self.logger.info("Open file requested")
        
        # Get initial directory
        initial_dir = self.app_controller.settings.data_directory
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            initial_dir,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.logger.info(f"Selected file: {file_path}")
            
            # Create file info
            file_name = os.path.basename(file_path)
            file_info = {
                'path': file_path,
                'name': file_name,
                'display_name': file_name.split('.')[0]
            }
            
            # Process the file
            self._load_and_visualize_file(file_info)
            
            # Add to recent files
            self.app_controller.settings.add_recent_file(file_path)
    
    def on_open_directory(self):
        """Handle open directory action."""
        self.logger.info("Open directory requested")
        
        # Get initial directory
        initial_dir = self.app_controller.settings.data_directory
        
        # Show directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            initial_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.logger.info(f"Selected directory: {directory}")
            
            # Update settings
            self.app_controller.settings.data_directory = directory
            self.app_controller.settings.save_settings()
            
            # Refresh file browser
            self.file_browser.refresh_directory()
    
    def on_export_image(self):
        """Handle export as image action."""
        self.logger.info("Export as image requested")
        
        # Get current visualization
        if not self.chart_view.has_figure():
            QMessageBox.warning(
                self,
                "Warning",
                "No visualization to export."
            )
            return
        
        # Get initial directory
        initial_dir = os.path.expanduser("~")
        
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as Image",
            initial_dir,
            "PNG Images (*.png);;JPEG Images (*.jpg *.jpeg);;All Files (*)"
        )
        
        if file_path:
            self.logger.info(f"Exporting to: {file_path}")
            
            # Export image
            success = self.chart_view.save_as_image(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to: {file_path}")
            else:
                self.status_bar.showMessage("Error exporting image")
    
    def on_export_csv(self):
        """Handle export as CSV action."""
        self.logger.info("Export as CSV requested")
        
        # Get current data
        file_info = self.file_browser.get_selected_file_info()
        
        if not file_info:
            QMessageBox.warning(
                self,
                "Warning",
                "No data to export."
            )
            return
        
        # Get initial directory
        initial_dir = os.path.expanduser("~")
        initial_name = os.path.splitext(file_info['name'])[0] + "_processed.csv"
        
        # Show save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as CSV",
            os.path.join(initial_dir, initial_name),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        self.logger.info(f"Exporting to: {file_path}")
        
        try:
            # Load data
            df = self.app_controller.data_manager.load_csv(file_info['path'])
            
            # Get current configuration
            config = self.control_panel.get_config()
            
            # Apply filters
            df = self._filter_data(df, config)
            
            # Export to CSV
            df.to_csv(file_path, index=False)
            
            self.status_bar.showMessage(f"Exported to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
            
            QMessageBox.critical(
                self,
                "Error",
                f"Error exporting CSV: {str(e)}"
            )
    
    def on_about(self):
        """Handle about action."""
        self.logger.info("About dialog requested")
        
        # Show about dialog
        dialog = AboutDialog(self)
        dialog.exec()
    
    def _load_and_visualize_file(self, file_info: Dict[str, Any]):
        """
        Load and visualize a file.
        
        Args:
            file_info: File information dictionary
        """
        try:
            # Get configuration from control panel
            config = self.control_panel.get_config()
            
            # Set title (if not already set)
            if 'title' not in config and 'metric' in file_info:
                config['title'] = file_info['metric']
            elif 'title' not in config and 'display_name' in file_info:
                config['title'] = file_info['display_name']
            
            # Create visualization
            fig = self.app_controller.create_visualization(file_info['path'], config)
            
            # Display visualization
            self.chart_view.set_figure(fig)
            
            # Calculate metrics
            metrics = self.app_controller.calculate_metrics(file_info['path'], config)
            
            # Update info panel
            self.info_panel.update_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"Error visualizing file: {str(e)}", exc_info=True)
            raise
    
    def _filter_data(self, df, config):
        """
        Filter data based on configuration.
        
        Args:
            df: DataFrame to filter
            config: Configuration dictionary
        
        Returns:
            Filtered DataFrame
        """
        # Get date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if not date_col:
            return df
        
        # Ensure date column is datetime type
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Apply date range filter if specified
        date_range = config.get('date_range', {})
        
        if 'start' in date_range and 'end' in date_range:
            # Custom date range
            start_date = pd.to_datetime(date_range['start'])
            end_date = pd.to_datetime(date_range['end'])
            
            df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
            
        elif 'days' in date_range:
            # Last N days
            days = date_range['days']
            end_date = df[date_col].max()
            start_date = end_date - pd.Timedelta(days=days)
            
            df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
        
        # Apply series filter if specified
        if 'Breakdown' in df.columns and 'series' in config and config['series']:
            df = df[df['Breakdown'].isin(config['series'])]
        
        return df
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        self.logger.info("Window closing")
        
        # Save window state
        self.app_controller.settings.window_width = self.width()
        self.app_controller.settings.window_height = self.height()
        self.app_controller.settings.splitter_sizes = self.main_splitter.sizes()
        self.app_controller.settings.save_settings()
        
        # Accept the close event
        event.accept()
