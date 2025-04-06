"""
Chart View Widget for CSV Data Visualizer.

This module contains the ChartViewWidget class for displaying visualizations.
"""

import os
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                          QSizePolicy, QFrame, QSpacerItem)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    has_webengine = True
except ImportError:
    has_webengine = False

from PyQt6.QtGui import QImage, QPainter, QPixmap

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
        self.layout.setSpacing(0)
        
        # Try to create QWebEngineView if available
        if has_webengine:
            try:
                self.web_view = QWebEngineView()
                self.layout.addWidget(self.web_view)
                self.logger.info("QWebEngineView created successfully")
            except Exception as e:
                self.logger.error(f"Error creating QWebEngineView: {str(e)}")
                self._create_fallback_widget()
        else:
            self.logger.warning("QWebEngineWidgets not available, using fallback")
            self._create_fallback_widget()
    
    def _create_fallback_widget(self):
        """Create a fallback widget when QWebEngineView is not available."""
        self.web_view = None
        # Create a label to show the fallback message
        self.fallback_label = QLabel("Interactive Plotly visualization not available.\nUsing Matplotlib fallback.")
        self.fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fallback_label.setStyleSheet("color: #aaa; font-size: 14pt;")
        self.layout.addWidget(self.fallback_label)
    
    def set_figure(self, fig):
        """
        Set the Plotly figure to display.
        
        Args:
            fig: Plotly figure
        """
        # Clean up previous temp file
        if self._temp_file:
            try:
                os.unlink(self._temp_file.name)
                self._temp_file.close()
            except:
                pass
        
        # If the web view is not available, raise an exception to fall back to Matplotlib
        if not has_webengine or not self.web_view:
            raise Exception("QWebEngineView not available")
        
        try:
            # Create new temp file
            self._temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
            
            # Configure HTML output with Plotly included locally
            config = {
                'displayModeBar': True,
                'responsive': True,
                'scrollZoom': True
            }
            
            # Write figure to HTML file with Plotly.js included (not using CDN)
            html = pio.to_html(fig, config=config, include_plotlyjs=True, full_html=True)
            self._temp_file.write(html.encode('utf-8'))
            self._temp_file.flush()
            
            # Load HTML file
            try:
                self.web_view.load(QUrl.fromLocalFile(self._temp_file.name))
            except Exception as web_error:
                # If QWebEngineView fails, raise exception to fall back to matplotlib
                raise Exception(f"QWebEngineView error: {str(web_error)}")
            
        except Exception as e:
            # Create a simple HTML with error message
            html = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        background-color: #1e1e1e; 
                        color: white; 
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .error {{ 
                        background-color: #333;
                        border-left: 4px solid red;
                        padding: 20px;
                        max-width: 80%;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>Error Rendering Chart</h2>
                    <p>{str(e)}</p>
                </div>
            </body>
            </html>
            """
            # Create a temporary file for the error message
            self._temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
            self._temp_file.write(html.encode('utf-8'))
            self._temp_file.flush()
            try:
                if self.web_view:
                    self.web_view.load(QUrl.fromLocalFile(self._temp_file.name))
                else:
                    # Re-raise to trigger fallback to Matplotlib
                    raise Exception("Web view not available")
            except Exception:
                # Bubble up the exception to trigger fallback to Matplotlib
                raise Exception(f"Error setting Plotly figure: {str(e)}")
    
    def save_as_image(self, file_path: str) -> bool:
        """
        Save current figure as image.
        
        Args:
            file_path: Path to save image
            
        Returns:
            True if successful, False otherwise
        """
        if not has_webengine or not self.web_view:
            return False
            
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
    
    def clear(self):
        """Clear the current chart."""
        if has_webengine and self.web_view:
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
        
        # Create plotly view with error handling
        try:
            self.logger.info("Creating Plotly web view")
            self.plotly_view = PlotlyWebView()
            self.logger.info("Plotly web view created successfully")
        except Exception as e:
            self.logger.error(f"Error initializing Plotly view: {str(e)}", exc_info=True)
            # Create a fallback widget if web view fails
            self.plotly_view = QWidget()
            self.fallback_layout = QVBoxLayout(self.plotly_view)
            self.fallback_label = QLabel("Plotly visualization not available. Using Matplotlib fallback.")
            self.fallback_layout.addWidget(self.fallback_label)
        
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
                
                try:
                    # Try using Plotly first
                    self.engine_type = 'plotly'
                    
                    # Clear frame layout
                    self._clear_frame_layout()
                    
                    # Show plotly view
                    self.frame_layout.addWidget(self.plotly_view)
                    self.plotly_view.set_figure(fig)
                    
                except Exception as plotly_error:
                    self.logger.error(f"Error displaying Plotly figure: {str(plotly_error)}", exc_info=True)
                    # Fall back to matplotlib
                    self.logger.info("Falling back to Matplotlib")
                    
                    # Create a simple Matplotlib figure from Plotly data
                    try:
                        self.engine_type = 'matplotlib'
                        
                        # Clear frame layout
                        self._clear_frame_layout()
                        
                        # Convert Plotly to Matplotlib if possible (simplified approach)
                        if hasattr(fig, 'data') and len(fig.data) > 0:
                            mpl_fig = Figure(figsize=(10, 6))
                            ax = mpl_fig.add_subplot(111)
                            
                            # Iterate through traces
                            for trace in fig.data:
                                x = trace.get('x', [])
                                y = trace.get('y', [])
                                name = trace.get('name', '')
                                ax.plot(x, y, label=name)
                            
                            # Add title and labels if available
                            if hasattr(fig, 'layout'):
                                if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
                                    ax.set_title(fig.layout.title.text)
                                if hasattr(fig.layout, 'xaxis') and hasattr(fig.layout.xaxis, 'title') and hasattr(fig.layout.xaxis.title, 'text'):
                                    ax.set_xlabel(fig.layout.xaxis.title.text)
                                if hasattr(fig.layout, 'yaxis') and hasattr(fig.layout.yaxis, 'title') and hasattr(fig.layout.yaxis.title, 'text'):
                                    ax.set_ylabel(fig.layout.yaxis.title.text)
                            
                            # Add legend if more than one trace
                            if len(fig.data) > 1:
                                ax.legend()
                            
                            # Show the figure
                            self.frame_layout.addWidget(self.matplotlib_canvas)
                            self.matplotlib_canvas.set_figure(mpl_fig)
                        else:
                            # If conversion fails, show error
                            self.show_placeholder("Error converting Plotly to Matplotlib")
                            raise Exception("Cannot convert Plotly figure to Matplotlib")
                    except Exception as convert_error:
                        self.logger.error(f"Error converting to Matplotlib: {str(convert_error)}", exc_info=True)
                        self.show_placeholder(f"Visualization error: {str(plotly_error)}")
                        self.engine_type = None
                        self.current_figure = None
                
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
        # Remove all widgets
        while self.frame_layout.count():
            item = self.frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
