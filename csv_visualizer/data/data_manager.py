"""
Data Manager for CSV Data Visualizer.

This module contains the DataManager class for loading and processing CSV data.
"""

import os
import re
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

import pandas as pd
import numpy as np
from dateutil import parser

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings
from csv_visualizer.data.file_scanner import FileScanner


class DataManager:
    """Data Manager for CSV Data Visualizer."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the data manager.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("DataManager")
        self.settings = settings
        self.file_scanner = FileScanner(logger, settings)
        
        # Initialize data cache
        self._data_cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_entries = 20
        self._cache_access_count = 0
    
    def scan_directory(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan a directory for CSV files.

        Args:
            directory: Directory to scan (default: data_directory from settings)

        Returns:
            List of file information dictionaries
        """
        # Use default directory if not specified
        if directory is None:
            directory = self.settings.data_directory
        
        self.logger.info(f"Scanning directory: {directory}")
        
        try:
            files = self.file_scanner.scan_directory(directory)
            self.logger.info(f"Found {len(files)} CSV files")
            return files
        except Exception as e:
            self.logger.error(f"Error scanning directory: {str(e)}", exc_info=True)
            raise
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load a CSV file with intelligent date handling.

        Args:
            file_path: Path to CSV file

        Returns:
            Pandas DataFrame
        """
        self.logger.info(f"Loading CSV file: {file_path}")
        
        # Check cache first
        cache_key = self._get_cache_key(file_path)
        if cache_key in self._data_cache:
            self.logger.info("Using cached data")
            self._data_cache[cache_key]["access_count"] = self._cache_access_count
            self._cache_access_count += 1
            return self._data_cache[cache_key]["data"].copy()
        
        try:
            # First pass to determine column types
            df = pd.read_csv(file_path, nrows=5)
            
            # Find date column
            date_col = self._find_date_column(df)
            
            # Define column types for efficiency
            dtypes = self._determine_column_types(df, date_col)
            
            # Second pass to load full CSV with optimized settings
            parse_dates = [date_col] if date_col else None
            df = pd.read_csv(file_path, parse_dates=parse_dates, dtype=dtypes)
            
            # Ensure numeric columns are properly typed
            df = self._convert_numeric_columns(df, date_col)
            
            # Cache the data
            self._cache_data(cache_key, df)
            
            # Add to recent files
            self.settings.add_recent_file(file_path)
            
            self.logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading CSV file: {str(e)}", exc_info=True)
            raise
    
    def load_combined_data(self, file_path: str, combine_similar: bool = True) -> pd.DataFrame:
        """
        Load a CSV file and optionally combine data from similar files.

        Args:
            file_path: Path to primary CSV file
            combine_similar: Whether to combine data from similar files

        Returns:
            Pandas DataFrame with combined data
        """
        self.logger.info(f"Loading {'combined' if combine_similar else 'single'} data from: {file_path}")
        
        # If not combining, just load the single file
        if not combine_similar:
            return self.load_csv(file_path)
        
        try:
            # Generate a cache key for the combined data
            base_name = self._extract_metric_name(os.path.basename(file_path))
            directory = os.path.dirname(file_path)
            combined_cache_key = f"combined_{directory}_{base_name}"
            cache_key = hashlib.md5(combined_cache_key.encode()).hexdigest()
            
            # Check cache first
            if cache_key in self._data_cache:
                self.logger.info("Using cached combined data")
                self._data_cache[cache_key]["access_count"] = self._cache_access_count
                self._cache_access_count += 1
                return self._data_cache[cache_key]["data"].copy()
            
            # Get all files in the directory
            all_files = self.scan_directory(directory)
            
            # Find files with the same metric
            similar_files = []
            for file_info in all_files:
                file_metric = self._extract_metric_name(file_info['name'])
                if file_metric == base_name:
                    similar_files.append(file_info['path'])
            
            self.logger.info(f"Found {len(similar_files)} files with similar metrics")
            
            if not similar_files:
                # If no similar files found, just load the original file
                return self.load_csv(file_path)
            
            # Load and combine all similar files
            combined_df = self._load_and_combine_files(similar_files)
            
            # Cache the combined data
            self._cache_data(cache_key, combined_df)
            
            self.logger.info(f"Successfully combined data with {len(combined_df)} rows")
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Error combining data: {str(e)}", exc_info=True)
            # Fall back to loading just the single file
            self.logger.info("Falling back to loading single file")
            return self.load_csv(file_path)
    
    def _load_and_combine_files(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Load multiple CSV files and combine them, removing duplicates.

        Args:
            file_paths: List of file paths to load and combine

        Returns:
            Combined Pandas DataFrame
        """
        dataframes = []
        
        for file_path in file_paths:
            try:
                df = self.load_csv(file_path)
                dataframes.append(df)
            except Exception as e:
                self.logger.warning(f"Error loading file {file_path}: {str(e)}")
        
        if not dataframes:
            raise ValueError("No data could be loaded from any of the files")
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Find date column
        date_col = self._find_date_column(combined_df)
        
        if date_col:
            # Sort by date
            combined_df = combined_df.sort_values(date_col)
            
            # Remove duplicates based on date and any breakdown column
            if 'Breakdown' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(subset=[date_col, 'Breakdown'], keep='last')
            else:
                combined_df = combined_df.drop_duplicates(subset=[date_col], keep='last')
        
        return combined_df
    
    def _extract_metric_name(self, filename: str) -> str:
        """
        Extract the metric name from a filename.

        Args:
            filename: Name of the file

        Returns:
            Extracted metric name
        """
        # Remove any date/time patterns from the filename
        # Example: "Session time- SessionDurationSeconds, 2025-03-22T08-30-00.000Z.csv"
        # should become "Session time- SessionDurationSeconds"
        
        # Match patterns like dates, times, and timestamps
        date_pattern = r', \d{4}-\d{2}-\d{2}.*?\.csv'
        
        # Remove the date part
        metric_name = re.sub(date_pattern, '', filename)
        
        # Remove any other common suffixes
        metric_name = re.sub(r' to \d{4}.*?\.csv', '', metric_name)
        
        # Remove file extension if it's still there
        metric_name = re.sub(r'\.csv$', '', metric_name)
        
        return metric_name.strip()
    
    def aggregate_time_series(
        self, df: pd.DataFrame, date_col: str, value_cols: List[str], 
        breakdown_col: Optional[str] = None, period: str = 'D'
    ) -> pd.DataFrame:
        """
        Aggregate time series data by specified period.

        Args:
            df: Input DataFrame
            date_col: Name of date column
            value_cols: List of value columns to aggregate
            breakdown_col: Name of breakdown/series column (if any)
            period: Aggregation period ('D'=daily, 'W'=weekly, 'M'=monthly)

        Returns:
            Aggregated DataFrame
        """
        self.logger.info(f"Aggregating time series by {period}")
        
        try:
            # Ensure date column is datetime type
            if df[date_col].dtype != 'datetime64[ns]':
                df[date_col] = pd.to_datetime(df[date_col])
            
            # Set date as index for resampling
            df = df.set_index(date_col)
            
            # Group by breakdown if specified
            if breakdown_col and breakdown_col in df.columns:
                result_dfs = []
                
                for name, group in df.groupby(breakdown_col):
                    # Resample and aggregate values
                    resampled = group[value_cols].resample(period).mean()
                    
                    # Add breakdown column back
                    resampled[breakdown_col] = name
                    
                    # Add to results
                    result_dfs.append(resampled.reset_index())
                
                # Combine all results
                if result_dfs:
                    result = pd.concat(result_dfs)
                    self.logger.info(f"Aggregated data has {len(result)} rows")
                    return result
                else:
                    self.logger.warning("No data after aggregation")
                    return pd.DataFrame()
            else:
                # Simple resampling without breakdown
                resampled = df[value_cols].resample(period).mean().reset_index()
                self.logger.info(f"Aggregated data has {len(resampled)} rows")
                return resampled
                
        except Exception as e:
            self.logger.error(f"Error aggregating time series: {str(e)}", exc_info=True)
            raise
    
    def calculate_period_metrics(
        self, df: pd.DataFrame, date_col: str, value_col: str, 
        breakdown_col: Optional[str] = None, periods_back: int = 1, 
        current_period_days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate period-over-period metrics.

        Args:
            df: Input DataFrame
            date_col: Name of date column
            value_col: Name of value column
            breakdown_col: Name of breakdown/series column (if any)
            periods_back: Number of periods to compare against
            current_period_days: Number of days in current period

        Returns:
            Dictionary of metrics by breakdown
        """
        self.logger.info(f"Calculating period metrics for {value_col}")
        
        try:
            # Ensure date column is datetime type
            if df[date_col].dtype != 'datetime64[ns]':
                df[date_col] = pd.to_datetime(df[date_col])
            
            # Sort by date
            df = df.sort_values(date_col)
            
            # Get end date (most recent date in data)
            end_date = df[date_col].max()
            
            # Calculate start dates for current and previous periods
            current_start = end_date - pd.Timedelta(days=current_period_days)
            previous_start = current_start - pd.Timedelta(days=current_period_days)
            
            # Filter for current and previous periods
            current_df = df[(df[date_col] >= current_start) & (df[date_col] <= end_date)]
            previous_df = df[(df[date_col] >= previous_start) & (df[date_col] < current_start)]
            
            # Group by breakdown if specified
            if breakdown_col and breakdown_col in df.columns:
                metrics = {}
                
                for name, group in df.groupby(breakdown_col):
                    # Get current and previous period data for this breakdown
                    curr_group = current_df[current_df[breakdown_col] == name]
                    prev_group = previous_df[previous_df[breakdown_col] == name]
                    
                    # Calculate metrics
                    curr_avg = curr_group[value_col].mean() if not curr_group.empty else None
                    prev_avg = prev_group[value_col].mean() if not prev_group.empty else None
                    
                    # Calculate percent change
                    if curr_avg is not None and prev_avg is not None and prev_avg != 0:
                        pct_change = ((curr_avg - prev_avg) / prev_avg) * 100
                    else:
                        pct_change = None
                        
                    metrics[name] = {
                        'current_avg': curr_avg,
                        'previous_avg': prev_avg,
                        'pct_change': pct_change,
                        'current_period': {
                            'start': current_start,
                            'end': end_date
                        },
                        'previous_period': {
                            'start': previous_start,
                            'end': current_start - pd.Timedelta(days=1)
                        }
                    }
                
                self.logger.info(f"Calculated metrics for {len(metrics)} breakdowns")
                return metrics
            else:
                # Calculate metrics without breakdown
                curr_avg = current_df[value_col].mean() if not current_df.empty else None
                prev_avg = previous_df[value_col].mean() if not previous_df.empty else None
                
                # Calculate percent change
                if curr_avg is not None and prev_avg is not None and prev_avg != 0:
                    pct_change = ((curr_avg - prev_avg) / prev_avg) * 100
                else:
                    pct_change = None
                
                metrics = {
                    'overall': {
                        'current_avg': curr_avg,
                        'previous_avg': prev_avg,
                        'pct_change': pct_change,
                        'current_period': {
                            'start': current_start,
                            'end': end_date
                        },
                        'previous_period': {
                            'start': previous_start,
                            'end': current_start - pd.Timedelta(days=1)
                        }
                    }
                }
                
                self.logger.info("Calculated overall metrics")
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error calculating period metrics: {str(e)}", exc_info=True)
            raise
    
    def sample_for_visualization(self, df: pd.DataFrame, max_points: int = 2000) -> pd.DataFrame:
        """
        Sample a DataFrame for interactive visualization.

        Args:
            df: DataFrame to sample
            max_points: Maximum number of points to include

        Returns:
            Sampled DataFrame
        """
        if len(df) <= max_points:
            return df
        
        self.logger.info(f"Sampling {len(df)} points down to {max_points} for visualization")
        
        try:
            # For time series data, use strategic sampling to preserve patterns
            date_col = self._find_date_column(df)
            
            if date_col:
                # If we have a breakdown column, sample within each group
                if 'Breakdown' in df.columns:
                    result_dfs = []
                    
                    for name, group in df.groupby('Breakdown'):
                        # Calculate sampling ratio for this group
                        group_size = len(group)
                        group_points = int(max_points * (group_size / len(df)))
                        
                        if group_points < 5:  # Ensure minimum points per group
                            group_points = min(5, group_size)
                            
                        # If group is small enough, keep all points
                        if group_size <= group_points:
                            result_dfs.append(group)
                        else:
                            # Sample with emphasis on newest data and extremes
                            # Sort by date
                            group = group.sort_values(date_col)
                            
                            # Always include first and last point
                            start_point = group.iloc[[0]]
                            end_point = group.iloc[[-1]]
                            
                            # Find min and max values for main metric
                            metric_col = [col for col in group.columns 
                                         if col not in [date_col, 'Breakdown']][0]
                            max_val_idx = group[metric_col].idxmax()
                            min_val_idx = group[metric_col].idxmin()
                            extremes = group.loc[[max_val_idx, min_val_idx]]
                            
                            # Sample remaining points
                            remaining_points = group_points - len(start_point) - len(end_point) - len(extremes)
                            
                            middle_group = group.drop(index=[0, len(group)-1, max_val_idx, min_val_idx])
                            
                            if remaining_points > 0 and not middle_group.empty:
                                sampled = middle_group.sample(min(remaining_points, len(middle_group)))
                                result = pd.concat([start_point, extremes, sampled, end_point])
                            else:
                                result = pd.concat([start_point, extremes, end_point])
                            
                            result_dfs.append(result)
                    
                    result = pd.concat(result_dfs)
                    self.logger.info(f"Sampled to {len(result)} points")
                    return result
                
                else:
                    # Simple sampling without groups
                    # Always include first and last point
                    sorted_df = df.sort_values(date_col)
                    start_point = sorted_df.iloc[[0]]
                    end_point = sorted_df.iloc[[-1]]
                    
                    # Find extremes
                    metric_col = [col for col in df.columns if col != date_col][0]
                    max_val_idx = df[metric_col].idxmax()
                    min_val_idx = df[metric_col].idxmin()
                    extremes = df.loc[[max_val_idx, min_val_idx]]
                    
                    # Sample remaining points
                    remaining_points = max_points - len(start_point) - len(end_point) - len(extremes)
                    middle_df = df.drop(index=[0, len(df)-1, max_val_idx, min_val_idx])
                    
                    if remaining_points > 0 and not middle_df.empty:
                        sampled = middle_df.sample(min(remaining_points, len(middle_df)))
                        result = pd.concat([start_point, extremes, sampled, end_point])
                    else:
                        result = pd.concat([start_point, extremes, end_point])
                    
                    self.logger.info(f"Sampled to {len(result)} points")
                    return result
            
            # For non-time series data, use simple random sampling
            result = df.sample(max_points)
            self.logger.info(f"Randomly sampled to {len(result)} points")
            return result
            
        except Exception as e:
            self.logger.error(f"Error sampling data: {str(e)}", exc_info=True)
            # Return original data in case of error
            return df
    
    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Find the date column in a DataFrame.

        Args:
            df: DataFrame

        Returns:
            Name of date column or None if not found
        """
        # First check if any column is already datetime
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            return datetime_cols[0]
            
        # Then try to find by name
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                return col
        
        # Then try to find by content
        for col in df.select_dtypes(include=['object']):
            # Check if at least 80% of the values can be parsed as dates
            try:
                date_count = pd.to_datetime(df[col], errors='coerce').notna().sum()
                if date_count >= 0.8 * len(df):
                    return col
            except:
                continue
        
        return None
    
    def _determine_column_types(self, df: pd.DataFrame, date_col: Optional[str]) -> Dict[str, str]:
        """
        Determine column types for efficient memory usage.

        Args:
            df: DataFrame
            date_col: Name of date column (to be excluded from type conversion)

        Returns:
            Dictionary of column types
        """
        dtypes = {}
        
        for col in df.columns:
            # Skip date column
            if col == date_col:
                continue
            
            # Check if column is categorical
            if df[col].dtype == 'object':
                nunique = df[col].nunique()
                if nunique / len(df) < 0.5:  # If less than 50% unique values
                    dtypes[col] = 'category'
        
        return dtypes
    
    def _convert_numeric_columns(self, df: pd.DataFrame, date_col: Optional[str]) -> pd.DataFrame:
        """
        Convert columns to numeric where possible.

        Args:
            df: DataFrame
            date_col: Name of date column (to be excluded from conversion)

        Returns:
            DataFrame with converted columns
        """
        for col in df.columns:
            if col != date_col and col != 'Breakdown' and df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
        
        return df
    
    def _get_cache_key(self, file_path: str) -> str:
        """
        Generate a cache key for a file path.

        Args:
            file_path: Path to file

        Returns:
            Cache key
        """
        # Use hash of file path and modification time for cache key
        try:
            mtime = os.path.getmtime(file_path)
            key = f"{file_path}_{mtime}"
            return hashlib.md5(key.encode()).hexdigest()
        except:
            # Fall back to just the file path if we can't get mtime
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _cache_data(self, cache_key: str, df: pd.DataFrame) -> None:
        """
        Cache DataFrame for future use.

        Args:
            cache_key: Cache key
            df: DataFrame to cache
        """
        # If cache is full, remove least recently used item
        if len(self._data_cache) >= self.max_cache_entries:
            lru_key = min(self._data_cache.items(), 
                         key=lambda x: x[1]["access_count"])[0]
            del self._data_cache[lru_key]
        
        # Store in cache
        self._data_cache[cache_key] = {
            "data": df,
            "access_count": self._cache_access_count,
            "timestamp": datetime.now()
        }
        self._cache_access_count += 1
