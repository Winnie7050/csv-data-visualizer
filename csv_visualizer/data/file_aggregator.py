"""
File Aggregator for CSV Data Visualizer.

This module contains the FileAggregator class for combining related CSV files.
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
from dateutil import parser

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings


class FileAggregator:
    """File Aggregator for combining related CSV files."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the file aggregator.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("FileAggregator")
        self.settings = settings
        
        # Regex patterns for file name parsing
        self.metric_pattern = re.compile(r'(.+) - (.+), (.+) to (.+)')
        self.date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
        
    def group_files_by_metric(self, files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group files by metric name.

        Args:
            files: List of file information dictionaries

        Returns:
            Dictionary of files grouped by metric name
        """
        self.logger.info(f"Grouping {len(files)} files by metric")
        
        metric_groups = {}
        
        for file_info in files:
            # Skip files without metric information
            if 'metric' not in file_info:
                continue
                
            metric = file_info['metric']
            
            # Create group if it doesn't exist
            if metric not in metric_groups:
                metric_groups[metric] = []
                
            # Add file to group
            metric_groups[metric].append(file_info)
        
        # Sort each group by date
        for metric, group_files in metric_groups.items():
            metric_groups[metric] = sorted(
                group_files,
                key=lambda x: x.get('start_date_obj', datetime.min)
            )
        
        # Remove single-file groups if desired
        if not self.settings.show_single_file_groups:
            metric_groups = {
                metric: files for metric, files in metric_groups.items() 
                if len(files) > 1
            }
        
        self.logger.info(f"Grouped files into {len(metric_groups)} metric groups")
        return metric_groups
    
    def create_group_info(self, metric: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create group information for a metric group.

        Args:
            metric: Metric name
            files: List of file information dictionaries for this metric

        Returns:
            Group information dictionary
        """
        # Calculate the overall date range for the group
        start_dates = [
            file_info.get('start_date_obj') 
            for file_info in files 
            if 'start_date_obj' in file_info
        ]
        
        end_dates = [
            file_info.get('end_date_obj') 
            for file_info in files 
            if 'end_date_obj' in file_info
        ]
        
        start_date_obj = min(start_dates) if start_dates else None
        end_date_obj = max(end_dates) if end_dates else None
        
        # Format dates for display
        start_date = start_date_obj.strftime('%Y-%m-%d') if start_date_obj else None
        end_date = end_date_obj.strftime('%Y-%m-%d') if end_date_obj else None
        
        # Create a display name for the group
        if start_date and end_date:
            display_name = f"{metric}, {start_date} to {end_date}"
        else:
            display_name = f"{metric} (multiple files)"
        
        # Get total file count and size
        total_size = sum(file_info.get('size', 0) for file_info in files)
        
        # Create group info dictionary
        group_info = {
            'is_group': True,
            'metric': metric,
            'display_name': display_name,
            'start_date': start_date,
            'end_date': end_date,
            'start_date_obj': start_date_obj,
            'end_date_obj': end_date_obj,
            'file_count': len(files),
            'total_size': total_size,
            'files': files,
            # Set the first file's path as the primary path for the group
            'path': files[0]['path'] if files else None,
            'name': display_name,
        }
        
        return group_info
    
    def combine_data(self, files: List[Dict[str, Any]], data_manager) -> pd.DataFrame:
        """
        Combine data from multiple files.

        Args:
            files: List of file information dictionaries
            data_manager: DataManager instance for loading files

        Returns:
            Combined DataFrame
        """
        self.logger.info(f"Combining data from {len(files)} files")
        
        # Sort files by date to ensure chronological order
        sorted_files = sorted(
            files,
            key=lambda x: x.get('start_date_obj', datetime.min)
        )
        
        dataframes = []
        file_count = 0
        
        for file_info in sorted_files:
            try:
                # Load data
                df = data_manager.load_csv(file_info['path'])
                
                # Add file metadata as columns if needed for debugging or tracking
                if self.settings.add_file_metadata_columns:
                    df['_source_file'] = file_info.get('name', '')
                    if 'start_date' in file_info:
                        df['_file_start_date'] = file_info['start_date']
                    if 'end_date' in file_info:
                        df['_file_end_date'] = file_info['end_date']
                
                dataframes.append(df)
                file_count += 1
                self.logger.info(f"Loaded file {file_count}/{len(sorted_files)}: {file_info.get('name', 'Unknown')}")
            except Exception as e:
                self.logger.error(f"Error loading file {file_info.get('path', 'Unknown')}: {str(e)}", exc_info=True)
        
        if not dataframes:
            self.logger.error("No data could be loaded from any files")
            raise ValueError("No data could be loaded from any files")
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Find date column
        date_col = None
        for col in combined_df.columns:
            if col.lower().find('date') >= 0 or col.lower().find('time') >= 0:
                date_col = col
                break
        
        if date_col:
            # Convert date column to datetime if needed
            if combined_df[date_col].dtype != 'datetime64[ns]':
                combined_df[date_col] = pd.to_datetime(combined_df[date_col], errors='coerce')
            
            # Sort by date
            combined_df = combined_df.sort_values(date_col)
            
            # Handle duplicates based on date and any breakdown column
            if 'Breakdown' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(subset=[date_col, 'Breakdown'], keep='last')
            else:
                combined_df = combined_df.drop_duplicates(subset=[date_col], keep='last')
        
        self.logger.info(f"Combined data has {len(combined_df)} rows and {len(combined_df.columns)} columns")
        return combined_df
