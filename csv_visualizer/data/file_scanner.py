"""
File Scanner for CSV Data Visualizer.

This module contains the FileScanner class for scanning directories for CSV files.
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from dateutil import parser

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings


class FileScanner:
    """File Scanner for CSV Data Visualizer."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the file scanner.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("FileScanner")
        self.settings = settings
        
        # Regex patterns for file name parsing
        self.metric_pattern = re.compile(r'(.+) - (.+), (.+) to (.+)')
        self.date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        self.week_pattern = re.compile(r'Week\d+\[(\d{4}-\d{1,2}-\d{1,2})_(\d{4}-\d{1,2}-\d{1,2})\]')
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        Scan a directory for CSV files.

        Args:
            directory: Directory to scan

        Returns:
            List of file information dictionaries
        """
        self.logger.info(f"Scanning directory: {directory}")
        
        if not os.path.exists(directory):
            self.logger.error(f"Directory does not exist: {directory}")
            raise FileNotFoundError(f"Directory does not exist: {directory}")
        
        all_files = []
        
        # Walk through the directory
        for root, dirs, files in os.walk(directory):
            # Check if this is a weekly folder
            week_info = self._parse_week_folder(os.path.basename(root))
            
            # Process each file
            for file in files:
                if file.lower().endswith('.csv'):
                    file_path = os.path.join(root, file)
                    file_info = self._parse_file_info(file_path, file, week_info)
                    all_files.append(file_info)
        
        # Sort files by start date (newest first)
        all_files.sort(key=lambda x: x.get('start_date_obj', datetime.min), reverse=True)
        
        self.logger.info(f"Found {len(all_files)} CSV files")
        return all_files
    
    def _parse_file_info(self, file_path: str, file_name: str, 
                        week_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse file information from a file name.

        Args:
            file_path: Path to file
            file_name: File name
            week_info: Week folder information (if available)

        Returns:
            File information dictionary
        """
        file_info = {
            'path': file_path,
            'name': file_name,
            'size': os.path.getsize(file_path),
            'modified': os.path.getmtime(file_path),
            'display_name': file_name.split('.')[0]  # Remove extension
        }
        
        # Try to parse the metric and date range
        match = self.metric_pattern.search(file_name)
        if match:
            metric = match.group(1).strip()
            identifier = match.group(2).strip()
            start_date = match.group(3).strip()
            end_date = match.group(4).strip()
            
            file_info['metric'] = metric
            file_info['identifier'] = identifier
            file_info['start_date'] = start_date
            file_info['end_date'] = end_date
            
            # Parse dates for sorting
            try:
                file_info['start_date_obj'] = parser.parse(start_date)
                file_info['end_date_obj'] = parser.parse(end_date)
            except:
                # If date parsing fails, try to find dates in the name
                dates = self.date_pattern.findall(file_name)
                if len(dates) >= 2:
                    try:
                        file_info['start_date_obj'] = parser.parse(dates[0])
                        file_info['end_date_obj'] = parser.parse(dates[1])
                    except:
                        pass
        else:
            # Try to extract any dates from the filename
            dates = self.date_pattern.findall(file_name)
            if dates:
                try:
                    file_info['start_date'] = dates[0]
                    file_info['start_date_obj'] = parser.parse(dates[0])
                    if len(dates) > 1:
                        file_info['end_date'] = dates[-1]
                        file_info['end_date_obj'] = parser.parse(dates[-1])
                except:
                    pass
            
            # Use the filename as the metric
            file_info['metric'] = file_name.split('.')[0]
        
        # If we have week info from the folder, add it
        if week_info:
            if 'week_number' in week_info:
                file_info['week_number'] = week_info['week_number']
            
            # Use folder dates if file dates not available
            if 'start_date_obj' not in file_info and 'folder_start_date' in week_info:
                file_info['start_date_obj'] = week_info['folder_start_date']
                file_info['start_date'] = week_info['folder_start_date'].strftime('%Y-%m-%d')
            
            if 'end_date_obj' not in file_info and 'folder_end_date' in week_info:
                file_info['end_date_obj'] = week_info['folder_end_date']
                file_info['end_date'] = week_info['folder_end_date'].strftime('%Y-%m-%d')
        
        return file_info
    
    def _parse_week_folder(self, folder_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse week information from a folder name.

        Args:
            folder_name: Folder name

        Returns:
            Dictionary of week information or None if not a week folder
        """
        match = self.week_pattern.search(folder_name)
        if match:
            week_num = re.search(r'Week(\d+)', folder_name)
            week_number = int(week_num.group(1)) if week_num else None
            
            start_date_str = match.group(1)
            end_date_str = match.group(2)
            
            try:
                folder_start_date = parser.parse(start_date_str)
                folder_end_date = parser.parse(end_date_str)
                
                return {
                    'week_number': week_number,
                    'folder_start_date': folder_start_date,
                    'folder_end_date': folder_end_date
                }
            except:
                self.logger.warning(f"Failed to parse dates from folder name: {folder_name}")
        
        return None
