"""
Settings Dialog for CSV Data Visualizer.

This module contains the SettingsDialog class for configuring application settings.
"""

import os
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                          QLineEdit, QPushButton, QFileDialog, QCheckBox,
                          QComboBox, QTabWidget, QWidget, QGroupBox,
                          QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal

from csv_visualizer.utils.logging_utils import get_module_logger


class SettingsDialog(QDialog):
    """Settings Dialog for configuring application settings."""
    
    # Signal emitted when settings are saved
    settings_saved = pyqtSignal()
    
    def __init__(self, app_controller, parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            app_controller: Application controller
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.app_controller = app_controller
        self.logger = get_module_logger("SettingsDialog")
        
        # Initialize UI
        self._init_ui()
        
        # Load current settings
        self._load_settings()
        
        self.logger.info("Settings dialog initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create general settings tab
        self.general_tab = QWidget()
        self.general_layout = QVBoxLayout(self.general_tab)
        
        # Create data directory group
        self.dir_group = QGroupBox("Data Directory")
        self.dir_layout = QHBoxLayout(self.dir_group)
        
        self.dir_edit = QLineEdit()
        self.dir_button = QPushButton("Browse...")
        self.dir_button.clicked.connect(self._browse_directory)
        
        self.dir_layout.addWidget(self.dir_edit)
        self.dir_layout.addWidget(self.dir_button)
        
        # Create visualization settings group
        self.viz_group = QGroupBox("Visualization Settings")
        self.viz_layout = QFormLayout(self.viz_group)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Line Chart", "Bar Chart", "Pie Chart", "Diverging Bar"])
        
        self.time_period_spin = QSpinBox()
        self.time_period_spin.setMinimum(1)
        self.time_period_spin.setMaximum(365)
        
        self.viz_layout.addRow("Default Chart Type:", self.chart_type_combo)
        self.viz_layout.addRow("Default Time Period (days):", self.time_period_spin)
        
        # Add groups to general tab
        self.general_layout.addWidget(self.dir_group)
        self.general_layout.addWidget(self.viz_group)
        self.general_layout.addStretch()
        
        # Create file aggregation tab
        self.aggregation_tab = QWidget()
        self.aggregation_layout = QVBoxLayout(self.aggregation_tab)
        
        # Create aggregation settings group
        self.agg_group = QGroupBox("File Aggregation Settings")
        self.agg_layout = QVBoxLayout(self.agg_group)
        
        # Create checkboxes
        self.enable_agg_checkbox = QCheckBox("Enable File Aggregation")
        self.show_single_file_checkbox = QCheckBox("Show Single File Groups")
        self.add_metadata_checkbox = QCheckBox("Add File Metadata Columns")
        self.auto_combine_checkbox = QCheckBox("Auto-Combine Same Metric")
        
        # Create duplicate handling group
        self.dup_layout = QHBoxLayout()
        self.dup_label = QLabel("Duplicate Handling Strategy:")
        self.dup_combo = QComboBox()
        self.dup_combo.addItems(["Last", "First", "Average"])
        
        self.dup_layout.addWidget(self.dup_label)
        self.dup_layout.addWidget(self.dup_combo)
        self.dup_layout.addStretch()
        
        # Add widgets to aggregation layout
        self.agg_layout.addWidget(self.enable_agg_checkbox)
        self.agg_layout.addWidget(self.show_single_file_checkbox)
        self.agg_layout.addWidget(self.add_metadata_checkbox)
        self.agg_layout.addWidget(self.auto_combine_checkbox)
        self.agg_layout.addLayout(self.dup_layout)
        
        # Add description label
        self.agg_desc = QLabel(
            "File aggregation combines multiple CSV files containing the same metric "
            "but covering different time periods into a single continuous timeline. "
            "This allows you to visualize data spanning across multiple files."
        )
        self.agg_desc.setWordWrap(True)
        self.agg_desc.setStyleSheet("color: #888888; font-style: italic;")
        
        # Add widgets to aggregation tab
        self.aggregation_layout.addWidget(self.agg_group)
        self.aggregation_layout.addWidget(self.agg_desc)
        self.aggregation_layout.addStretch()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.aggregation_tab, "File Aggregation")
        
        # Add tab widget to main layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Create button layout
        self.button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        
        # Add button layout to main layout
        self.main_layout.addLayout(self.button_layout)
    
    def _load_settings(self):
        """Load current settings."""
        # Load data directory
        self.dir_edit.setText(self.app_controller.settings.data_directory)
        
        # Load visualization settings
        self.chart_type_combo.setCurrentText(self.app_controller.settings.default_chart_type)
        self.time_period_spin.setValue(self.app_controller.settings.default_time_period)
        
        # Load file aggregation settings
        self.enable_agg_checkbox.setChecked(self.app_controller.settings.enable_file_aggregation)
        self.show_single_file_checkbox.setChecked(self.app_controller.settings.show_single_file_groups)
        self.add_metadata_checkbox.setChecked(self.app_controller.settings.add_file_metadata_columns)
        self.auto_combine_checkbox.setChecked(self.app_controller.settings.auto_combine_same_metric)
        
        # Load duplicate handling strategy
        strategy = self.app_controller.settings.duplicate_handling_strategy
        self.dup_combo.setCurrentText(strategy.capitalize())
    
    def _save_settings(self):
        """Save settings and close dialog."""
        # Get data directory
        data_dir = self.dir_edit.text()
        
        # Validate directory
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Error creating directory: {str(e)}")
                # Continue anyway, as it might be a network path or other valid location
        
        # Update settings
        self.app_controller.settings.data_directory = data_dir
        self.app_controller.settings.default_chart_type = self.chart_type_combo.currentText()
        self.app_controller.settings.default_time_period = self.time_period_spin.value()
        
        # Update file aggregation settings
        self.app_controller.settings.enable_file_aggregation = self.enable_agg_checkbox.isChecked()
        self.app_controller.settings.show_single_file_groups = self.show_single_file_checkbox.isChecked()
        self.app_controller.settings.add_file_metadata_columns = self.add_metadata_checkbox.isChecked()
        self.app_controller.settings.auto_combine_same_metric = self.auto_combine_checkbox.isChecked()
        self.app_controller.settings.duplicate_handling_strategy = self.dup_combo.currentText().lower()
        
        # Save settings
        self.app_controller.settings.save_settings()
        
        # Log settings saved
        self.logger.info("Settings saved")
        
        # Emit signal
        self.settings_saved.emit()
        
        # Close dialog
        self.accept()
    
    def _browse_directory(self):
        """Open directory browser dialog."""
        # Get current directory
        current_dir = self.dir_edit.text()
        
        # Show directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Data Directory",
            current_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        # Update directory if selected
        if directory:
            self.dir_edit.setText(directory)
