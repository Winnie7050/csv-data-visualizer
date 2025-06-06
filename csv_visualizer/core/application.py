"""
Main Application Class for CSV Data Visualizer.

This module contains the main Application class that orchestrates the application.
"""

import sys
import traceback
from typing import List, Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
try:
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    has_webengine = True
except ImportError:
    has_webengine = False

from csv_visualizer.ui.main_window import MainWindow
from csv_visualizer.data.data_manager import DataManager
from csv_visualizer.core.settings import Settings
from csv_visualizer.visualization.visualization_manager import VisualizationManager


class Application:
    """Main application class for CSV Data Visualizer."""

    def __init__(self, logger):
        """
        Initialize the application.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.logger.info("Initializing application")
        
        # Settings
        self.settings = Settings()
        
        # Filter command line args to remove visualization-specific flags
        filtered_args = [arg for arg in sys.argv if not arg.startswith('--')]
        
        # Qt application - Make sure to pass filtered args
        self.qt_app = QApplication(filtered_args)
        self.qt_app.setApplicationName("CSV Data Visualizer")
        self.qt_app.setApplicationVersion(self.settings.version)
        self.qt_app.setOrganizationName("MCP")
        
        # Initialize QWebEngine if available
        if has_webengine:
            try:
                dummy_web_view = QWebEngineView()  # Create a dummy view to initialize QWebEngine
                self.logger.info("QWebEngineView successfully initialized")
                
                # Try to configure WebEngine settings directly on the instance
                try:
                    # Set settings directly on the web view instance
                    dummy_web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                    dummy_web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
                    dummy_web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
                    self.logger.info("WebEngine settings configured on instance")
                except Exception as settings_error:
                    self.logger.warning(f"Could not configure WebEngine settings: {str(settings_error)}")
            except Exception as e:
                self.logger.warning(f"Error initializing QWebEngineView: {str(e)}. Proceeding with fallback options.")
        else:
            self.logger.warning("PyQt6-WebEngine is not available. Will use Matplotlib for visualizations.")
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Data manager
        self.data_manager = DataManager(self.logger, self.settings)
        
        # Visualization manager
        self.viz_manager = VisualizationManager(self.logger, self.settings)
        
        # Main window
        self.main_window = None
        
        # Set up exception handling
        sys.excepthook = self._handle_uncaught_exception
        
        self.logger.info("Application initialized")

    def run(self, argv: List[str]) -> int:
        """
        Run the application.

        Args:
            argv: Command line arguments

        Returns:
            Exit code
        """
        try:
            self.logger.info("Starting application")
            
            # Parse command line arguments (filtering out flags)
            filtered_args = [arg for arg in argv if not arg.startswith('--')]
            self._parse_arguments(filtered_args)
            
            # Create main window
            self.main_window = MainWindow(self)
            self.main_window.show()
            
            # Run application
            return self.qt_app.exec()
            
        except Exception as e:
            self.logger.critical(f"Error running application: {str(e)}", exc_info=True)
            self._show_error_dialog("Critical Error", f"An error occurred while starting the application:\n{str(e)}")
            return 1
    
    def _apply_dark_theme(self) -> None:
        """Apply the dark theme to the application."""
        self.logger.info("Applying dark theme")
        
        # Set stylesheet
        self.qt_app.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            QMenuBar {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            
            QToolBar {
                background-color: #2d2d2d;
                border: none;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDateEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 4px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #1e1e1e;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
            }
            
            QSplitter::handle {
                background-color: #2d2d2d;
            }
            
            QStatusBar {
                background-color: #2d2d2d;
                color: #cccccc;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #5d5d5d;
                min-height: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #2d2d2d;
                height: 12px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #5d5d5d;
                min-width: 20px;
                border-radius: 6px;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QTableView, QTreeView, QListView {
                background-color: #1e1e1e;
                alternate-background-color: #262626;
                selection-background-color: #0078d4;
                selection-color: white;
                border: 1px solid #3d3d3d;
            }
            
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 4px;
                border: 1px solid #3d3d3d;
            }
            
            /* File group items styling */
            QTreeView::item:has-children {
                color: #0078d4;
                font-weight: bold;
            }
            
            /* Tag labels styling */
            QLabel[tag="true"] {
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
                padding: 2px 4px;
                margin: 2px;
            }
        """)
    
    def _parse_arguments(self, argv: List[str]) -> None:
        """
        Parse command line arguments.

        Args:
            argv: Command line arguments
        """
        # Simple argument parsing for now
        if len(argv) > 1:
            data_path = argv[1]
            if data_path and not data_path.startswith('--'):
                self.settings.data_directory = data_path
                self.logger.info(f"Data directory set to {data_path}")
    
    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """
        Handle uncaught exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Log the exception
        self.logger.critical("Uncaught exception", 
                           exc_info=(exc_type, exc_value, exc_traceback))
        
        # Format the traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)
        
        # Show error dialog
        error_msg = f"{exc_type.__name__}: {str(exc_value)}\n\nTraceback:\n{tb_text}"
        self._show_error_dialog("Uncaught Exception", error_msg)
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """
        Show an error dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle(title)
        error_box.setText("An error has occurred:")
        error_box.setDetailedText(message)
        error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_box.exec()
        
    def show_error(self, title: str, message: str) -> None:
        """
        Show an error dialog to the user.

        Args:
            title: Dialog title
            message: Error message
        """
        self.logger.error(f"Error: {title} - {message}")
        self._show_error_dialog(title, message)
    
    def create_visualization(self, file_info: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """
        Create a visualization for a CSV file or grouped files.

        Args:
            file_info: File or group information dictionary
            config: Visualization configuration

        Returns:
            Plotly figure object
        """
        try:
            # Check if this is a file group or an individual file
            is_group = file_info.get('is_group', False)
            
            if is_group:
                self.logger.info(f"Creating visualization for file group: {file_info.get('metric', 'Unknown')}")
                # Load combined data from file group
                df = self.data_manager.load_combined_data(file_info)
            else:
                # Load data from individual file
                self.logger.info(f"Creating visualization for file: {file_info.get('name', 'Unknown')}")
                df = self.data_manager.load_csv(file_info['path'])
            
            # Create visualization
            return self.viz_manager.create_visualization(df, config)
        except Exception as e:
            self.logger.error(f"Error creating visualization: {str(e)}", exc_info=True)
            raise
    
    def calculate_metrics(self, file_info: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for a CSV file or grouped files.

        Args:
            file_info: File or group information dictionary
            config: Configuration

        Returns:
            Dictionary of metrics
        """
        try:
            # Check if this is a file group or an individual file
            is_group = file_info.get('is_group', False)
            
            if is_group:
                self.logger.info(f"Calculating metrics for file group: {file_info.get('metric', 'Unknown')}")
                # Load combined data from file group
                df = self.data_manager.load_combined_data(file_info)
            else:
                # Load data from individual file
                self.logger.info(f"Calculating metrics for file: {file_info.get('name', 'Unknown')}")
                df = self.data_manager.load_csv(file_info['path'])
            
            # Calculate metrics
            return self.viz_manager.calculate_metrics(df, config)
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}", exc_info=True)
            raise
            
    def cleanup(self):
        """Clean up resources before exit."""
        # Clean up web engine resources
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'chart_view') and self.main_window.chart_view:
                if hasattr(self.main_window.chart_view, 'plotly_view'):
                    try:
                        self.main_window.chart_view.plotly_view.setHtml("")
                        self.main_window.chart_view.plotly_view.close()
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up web resources: {str(e)}")
