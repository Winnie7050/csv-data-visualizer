"""
Settings Class for CSV Data Visualizer.

This module contains the Settings class that manages application settings.
"""

import os
import json
from typing import Dict, Any, Optional, List


class Settings:
    """Settings class for CSV Data Visualizer."""

    def __init__(self):
        """Initialize default settings."""
        # Application info
        self.version = "0.1.0"
        self.app_name = "CSV Data Visualizer"
        
        # Data settings
        self.data_directory = self._get_default_data_dir()
        self.recent_files: List[str] = []
        self.max_recent_files = 10
        
        # File aggregation settings
        self.enable_file_aggregation = True
        self.show_single_file_groups = False
        self.add_file_metadata_columns = False
        self.auto_combine_same_metric = True
        self.duplicate_handling_strategy = "last"  # Options: "last", "first", "average"
        
        # Visualization settings
        self.default_chart_type = "Line Chart"
        self.default_time_period = 30  # days
        
        # UI settings
        self.window_width = 1200
        self.window_height = 800
        self.splitter_sizes = [300, 900]  # Initial sizes for file browser and dashboard
        
        # Theme settings
        self.theme = "dark"
        self.color_schemes = {
            "dark": {
                "background": "#1e1e1e",
                "foreground": "#ffffff",
                "accent": "#0078d4",
                "secondary": "#3d3d3d",
                "chart_colors": [
                    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
                ]
            }
        }
        
        # Try to load settings from file
        self._load_settings()
    
    def _get_default_data_dir(self) -> str:
        """
        Get the default data directory.

        Returns:
            Default data directory path
        """
        # Try to find the specified data directory
        default_dir = r"D:\1GameDev\Frankfurt Response\Statistics"
        if os.path.exists(default_dir):
            return default_dir
        
        # Fall back to Documents folder
        try:
            import platform
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    documents_dir = winreg.QueryValueEx(key, "Personal")[0]
                return os.path.join(documents_dir, "CSV Data")
        except:
            pass
        
        # Last resort: user's home directory
        return os.path.join(os.path.expanduser("~"), "CSV Data")
    
    def _get_settings_path(self) -> str:
        """
        Get the settings file path.

        Returns:
            Settings file path
        """
        app_data_dir = self._get_app_data_dir()
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, "settings.json")
    
    def _get_app_data_dir(self) -> str:
        """
        Get the application data directory.

        Returns:
            Application data directory path
        """
        # For Windows
        if os.name == "nt":
            app_data = os.environ.get("APPDATA")
            if app_data:
                return os.path.join(app_data, self.app_name)
        
        # For Linux/Mac
        return os.path.join(os.path.expanduser("~"), f".{self.app_name.lower().replace(' ', '_')}")
    
    def _load_settings(self) -> None:
        """Load settings from file."""
        settings_path = self._get_settings_path()
        
        if not os.path.exists(settings_path):
            return
        
        try:
            with open(settings_path, 'r') as f:
                settings_dict = json.load(f)
            
            # Update settings
            for key, value in settings_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
    
    def save_settings(self) -> None:
        """Save settings to file."""
        settings_path = self._get_settings_path()
        
        try:
            # Create settings dictionary
            settings_dict = {
                "data_directory": self.data_directory,
                "recent_files": self.recent_files,
                "default_chart_type": self.default_chart_type,
                "default_time_period": self.default_time_period,
                "window_width": self.window_width,
                "window_height": self.window_height,
                "splitter_sizes": self.splitter_sizes,
                "theme": self.theme,
                "enable_file_aggregation": self.enable_file_aggregation,
                "show_single_file_groups": self.show_single_file_groups,
                "add_file_metadata_columns": self.add_file_metadata_columns,
                "auto_combine_same_metric": self.auto_combine_same_metric,
                "duplicate_handling_strategy": self.duplicate_handling_strategy,
            }
            
            # Save to file
            with open(settings_path, 'w') as f:
                json.dump(settings_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
    
    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the file
        """
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Add to the beginning
        self.recent_files.insert(0, file_path)
        
        # Trim list if needed
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        # Save settings
        self.save_settings()
    
    def get_color_scheme(self) -> Dict[str, Any]:
        """
        Get the current color scheme.

        Returns:
            Color scheme dictionary
        """
        return self.color_schemes.get(self.theme, self.color_schemes["dark"])
