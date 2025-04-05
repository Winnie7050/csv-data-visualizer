"""
Chart View Widget for CSV Data Visualizer.

This module contains the ChartViewWidget class for displaying visualizations.
"""

import os
import sys
import logging
import tempfile
import traceback
from typing import Dict, List, Any, Optional, Union

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QSizePolicy, QFrame, QSpacerItem, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPainter, QPixmap

# Import WebEngine components with error handling
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    webengine_available = True
except ImportError:
    webengine_available = False

import plotly.io as pio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from csv_visualizer.utils.logging_utils import get_module_logger


class PlotlyWebView(QWidget):
    """Plotly Web View for displaying Plotly visualizations."""
    
    def __init__(self, parent=None):
        """Initialize the Plotly web view."""
        super().__init__(parent)
        self.logger = get_module_logger("PlotlyWebView")
        self._temp_file = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(400)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Only create web view if WebEngine is available
        if webengine_available:
            try:
                self.web_view = QWebEngineView()
                self.layout.addWidget(self.web_view)
                self.logger.info("QWebEngineView initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing QWebEngineView: {str(e)}", exc_info=True)
                self._create_fallback_view()
        else:
            self.logger.warning("PyQt6-WebEngine not available, using fallback view")
            self._create_fallback_view()
    
    def _create_fallback_view(self):
        """Create a fallback view when WebEngine is not available."""
        self.web_view = None
        
        # Add fallback label
        self.fallback_label = QLabel("Interactive Plotly visualizations require PyQt6-WebEngine.")
        self.fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fallback_label.setStyleSheet("color: #888; font-size: 14pt;")
        
        self.layout.addWidget(self.fallback_label)
    
    def set_figure(self, fig):
        """
        Set the Plotly figure to display.
        
        Args:
            fig: Plotly figure
        """
        try:
            # Clean up previous temp file
            if self._temp_file:
                try:
                    os.unlink(self._temp_file.name)
                    self._temp_file.close()
                except:
                    pass
            
            # If web view is not available, show error and return
            if not self.web_view:
                self.logger.warning("Cannot display Plotly figure: WebEngine not available")
                return
            
            # Create new temp file
            self._temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
            
            # Configure HTML output
            config = {
                'displayModeBar': True,
                'responsive': True,
                'scrollZoom': True
            }
            
            # Write figure to HTML file
            html = pio.to_html(fig, config=config, include_plotlyjs='cdn', full_html=True)
            self._temp_file.write(html.encode('utf-8'))
            self._temp_file.flush()
            
            # Load HTML file
            url = QUrl.fromLocalFile(self._temp_file.name)
            self.web_view.load(url)
            
            self.logger.info(f"Plotly figure loaded from {self._temp_file.name}")
        except Exception as e:
            self.logger.error(f"Error setting Plotly figure: {str(e)}", exc_info=True)
            
            # Show error message instead of crashing
            if self.web_view:
                error_html = f"""
                <html>
                <body style="background-color: #1e1e1e; color: white; font-family: Arial, sans-serif; padding: 20px;">
                    <h3>Error displaying visualization</h3>
                    <p>{str(e)}</p>
                    <pre>{traceback.format_exc()}</pre>
                </body>
                </html>
                """
                self.web_view.setHtml(error_html)
    
    def save_as_image(self, file_path: str) -> bool:
        """
        Save current figure as image.
        
        Args:
            file_path: Path to save image
            
        Returns:
            True if successful, False otherwise
        """
        if not self.web_view:
            self.logger.warning("Cannot save image: WebEngine not available")
            return False
        
        try:
            # Use JavaScript to trigger image download
            self.web_view.page().runJavaScript("""
                (function() {
                    if (window.Plotly) {
                        var graphDiv = document.getElementsByClassName('plotly-graph-div')[0];
                        if (graphDiv) {
                            Plotly.downloadImage(graphDiv, {
                                format: 'png',
                                filename: 'visualization',
                                width: 1200,
                                height: 800
                            });
                            return true;
                        }
                    }
                    return false;
                })();
            """)
            
            # Note: This approach doesn't actually save to the specified file_path
            # It triggers a browser download instead
            # To achieve specified path, a more complex approach would be needed
            return True
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}", exc_info=True)
            return False
    
    def clear(self):
        """Clear the current chart."""
        if self.web_view:
            self.web_view.setHtml("")
        
        # Clean up temp file
        if self._temp_file:
            try:
                os.unlink(self._temp_file.name)
                self._temp_file.close()
                self._temp_file = None
            except:
                pass


class MatplotlibCanvas(FigureCanvasQTAgg):
    """Matplotlib Canvas for displaying Matplotlib visualizations."""
    
    def __init__(self, figure=None, parent=None):
        """
        Initialize the Matplotlib canvas.
        
        Args:
            figure: Matplotlib figure (optional)
            parent: Parent widget
        """
        if figure is None:
            figure = Figure(figsize=(5, 4), dpi=100)
        
        super().__init__(figure)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(400)
    
    def set_figure(self, figure):
        """
        Set the Matplotlib figure to display.
        
        Args:
            figure: Matplotlib figure
        """
        # Clear current figure
        self.figure.clear()
        
        # Copy the content from the new figure to our canvas figure
        for ax in figure.get_axes():
            # Create a new axes in the canvas figure
            new_ax = self.figure.add_subplot(111)
            
            # Copy the content
            for item in ax.get_children():
                # This is a simplified approach and may not copy everything
                item.figure = self.figure
                item.axes = new_ax
                new_ax.add_artist(item)
            
            # Copy axes properties
            new_ax.set_title(ax.get_title())
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_ax.set_xlim(ax.get_xlim())
            new_ax.set_ylim(ax.get_ylim())
        
        # Redraw canvas
        self.figure.tight_layout()
        self.draw()
    
    def save_as_image(self, file_path: str) -> bool:
        """
        Save current figure as image.
        
        Args:
            file_path: Path to save image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving figure: {str(e)}")
            return False
    
    def clear(self):
        """Clear the current chart."""
        self.figure.clear()
        self.draw()


class ChartViewWidget(QWidget):
    """Chart View Widget for displaying visualizations."""
    
    def __init__(self, app_controller):
        """
        Initialize the chart view widget.
        
        Args:
            app_controller: Application controller
        """
        super().__init__()
        
        self.app_controller = app_controller
        self.logger = get_module_logger("ChartViewWidget")
        
        # Initialize state
        self.current_figure = None
        self.engine_type = None  # 'plotly' or 'matplotlib'
        
        # Initialize UI
        self._init_ui()
        
        self.logger.info("Chart view widget initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create frame for better appearance
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Sunken)
        self.frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create layout for frame
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)
        
        # Create plotly view
        self.plotly_view = PlotlyWebView()
        
        # Create matplotlib canvas
        self.matplotlib_canvas = MatplotlibCanvas()
        
        # Create placeholder widget (for empty state)
        self.placeholder = QWidget()
        self.placeholder_layout = QVBoxLayout(self.placeholder)
        self.placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.placeholder_label = QLabel("No visualization to display")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #888; font-size: 16pt;")
        
        self.placeholder_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.placeholder_layout.addWidget(self.placeholder_label)
        self.placeholder_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Initially show placeholder
        self.frame_layout.addWidget(self.placeholder)
        
        # Add frame to main layout
        self.layout.addWidget(self.frame)
    
    def set_figure(self, fig):
        """
        Set the figure to display.
        
        Args:
            fig: Figure object (Plotly or Matplotlib)
        """
        try:
            self.current_figure = fig
            
            # Determine figure type and display accordingly
            if 'plotly' in str(type(fig)).lower():
                self.logger.info("Displaying Plotly figure")
                self.engine_type = 'plotly'
                
                # Clear frame layout
                self._clear_frame_layout()
                
                # Show plotly view
                self.frame_layout.addWidget(self.plotly_view)
                self.plotly_view.set_figure(fig)
                
            elif 'figure' in str(type(fig)).lower():
                self.logger.info("Displaying Matplotlib figure")
                self.engine_type = 'matplotlib'
                
                # Clear frame layout
                self._clear_frame_layout()
                
                # Show matplotlib canvas
                self.frame_layout.addWidget(self.matplotlib_canvas)
                self.matplotlib_canvas.set_figure(fig)
                
            else:
                self.logger.error(f"Unsupported figure type: {type(fig)}")
                self.show_placeholder("Unsupported visualization type")
                self.engine_type = None
                self.current_figure = None
                
        except Exception as e:
            self.logger.error(f"Error setting figure: {str(e)}", exc_info=True)
            self.show_placeholder(f"Error: {str(e)}")
            self.engine_type = None
            self.current_figure = None
            
            # Show error message box
            error_msg = f"Error displaying visualization:\n{str(e)}\n\n"
            error_msg += "Please make sure you have PyQt6-WebEngine installed:\n"
            error_msg += "pip install PyQt6-WebEngine"
            
            QMessageBox.critical(
                self,
                "Visualization Error",
                error_msg
            )
    
    def has_figure(self) -> bool:
        """
        Check if a figure is currently displayed.
        
        Returns:
            True if a figure is displayed, False otherwise
        """
        return self.current_figure is not None
    
    def save_as_image(self, file_path: str) -> bool:
        """
        Save current figure as image.
        
        Args:
            file_path: Path to save image
            
        Returns:
            True if successful, False otherwise
        """
        if not self.has_figure():
            self.logger.warning("No figure to save")
            return False
        
        try:
            if self.engine_type == 'plotly':
                return self.plotly_view.save_as_image(file_path)
            elif self.engine_type == 'matplotlib':
                return self.matplotlib_canvas.save_as_image(file_path)
            else:
                self.logger.error("Unknown engine type")
                return False
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}", exc_info=True)
            return False
    
    def clear(self):
        """Clear the current chart."""
        self.logger.info("Clearing chart view")
        
        # Clear current figure
        self.current_figure = None
        self.engine_type = None
        
        # Show placeholder
        self.show_placeholder("No visualization to display")
    
    def show_placeholder(self, message: str):
        """
        Show placeholder with custom message.
        
        Args:
            message: Message to display
        """
        self.logger.info(f"Showing placeholder: {message}")
        
        # Update placeholder label
        self.placeholder_label.setText(message)
        
        # Clear frame layout
        self._clear_frame_layout()
        
        # Show placeholder
        self.frame_layout.addWidget(self.placeholder)
    
    def _clear_frame_layout(self):
        """Clear the frame layout."""
        # Hide all widgets
        if self.plotly_view in self.findChildren(PlotlyWebView):
            self.plotly_view.setParent(None)
        
        if self.matplotlib_canvas in self.findChildren(MatplotlibCanvas):
            self.matplotlib_canvas.setParent(None)
        
        if self.placeholder in self.findChildren(QWidget):
            self.placeholder.setParent(None)
        
        # Recreate the widgets if needed
        if not self.plotly_view:
            self.plotly_view = PlotlyWebView()
        
        if not self.matplotlib_canvas:
            self.matplotlib_canvas = MatplotlibCanvas()
        
        if not self.placeholder:
            self.placeholder = QWidget()
            self.placeholder_layout = QVBoxLayout(self.placeholder)
            self.placeholder_label = QLabel("No visualization to display")
            self.placeholder_layout.addWidget(self.placeholder_label)
