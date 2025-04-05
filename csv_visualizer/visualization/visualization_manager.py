"""
Visualization Manager for CSV Data Visualizer.

This module contains the VisualizationManager class for creating visualizations.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

import pandas as pd
import numpy as np

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings
from csv_visualizer.visualization.plotly_engine import PlotlyEngine
from csv_visualizer.visualization.matplotlib_engine import MatplotlibEngine


class VisualizationManager:
    """Visualization Manager for CSV Data Visualizer."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the visualization manager.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("VisualizationManager")
        self.settings = settings
        
        # Initialize visualization engines
        self.plotly_engine = PlotlyEngine(logger, settings)
        self.matplotlib_engine = MatplotlibEngine(logger, settings)
        
        # Chart type mapping
        self.chart_types = {
            "Line Chart": self._create_line_chart,
            "Bar Chart": self._create_bar_chart,
            "Pie Chart": self._create_pie_chart,
            "Diverging Bar": self._create_diverging_bar_chart,
        }
        
        # Try importing required modules to determine which engine to use as primary
        try:
            import plotly
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            self.primary_engine = 'plotly'
            self.logger.info("Using Plotly as primary visualization engine")
        except ImportError:
            self.primary_engine = 'matplotlib'
            self.logger.info("Using Matplotlib as primary visualization engine (PyQt6-WebEngine not available)")
    
    def create_visualization(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """
        Create a visualization based on the provided configuration.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly or Matplotlib figure object
        """
        self.logger.info(f"Creating visualization: {config.get('chart_type', 'Unknown')}")
        
        try:
            # Apply date range filter if specified
            df = self._filter_by_date_range(df, config)
            
            # Apply series filter if specified
            df = self._filter_by_series(df, config)
            
            # Sample data for better performance if needed
            if len(df) > 2000:
                df = self._sample_data(df)
            
            # Create the visualization based on chart type
            chart_type = config.get('chart_type', self.settings.default_chart_type)
            
            # Get the appropriate chart creation function
            create_func = self.chart_types.get(chart_type)
            
            if create_func:
                fig = create_func(df, config)
                self.logger.info(f"Visualization created successfully: {chart_type}")
                return fig
            else:
                self.logger.error(f"Unknown chart type: {chart_type}")
                # Fall back to line chart
                return self._create_line_chart(df, config)
                
        except Exception as e:
            self.logger.error(f"Error creating visualization: {str(e)}", exc_info=True)
            raise
    
    def calculate_metrics(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for the data.

        Args:
            df: DataFrame with data
            config: Configuration

        Returns:
            Dictionary of metrics
        """
        self.logger.info("Calculating metrics")
        
        try:
            # Apply date range filter if specified
            df = self._filter_by_date_range(df, config)
            
            # Apply series filter if specified
            df = self._filter_by_series(df, config)
            
            # Get the date column
            date_col = self._find_date_column(df)
            if not date_col:
                self.logger.warning("No date column found, metrics may be incomplete")
                return {'error': 'No date column found'}
            
            # Get value columns (excluding date and breakdown columns)
            value_cols = [col for col in df.columns 
                         if col != date_col and col != 'Breakdown']
            
            if not value_cols:
                self.logger.warning("No value columns found, metrics may be incomplete")
                return {'error': 'No value columns found'}
            
            # Calculate basic metrics
            metrics = {}
            
            # If we have a breakdown column, calculate metrics for each series
            if 'Breakdown' in df.columns and 'series' in config and config['series']:
                for series in config['series']:
                    series_df = df[df['Breakdown'] == series]
                    
                    if not series_df.empty:
                        series_metrics = self._calculate_series_metrics(
                            series_df, date_col, value_cols[0])
                        metrics[series] = series_metrics
            else:
                # Calculate overall metrics
                overall_metrics = self._calculate_series_metrics(
                    df, date_col, value_cols[0])
                metrics['overall'] = overall_metrics
            
            self.logger.info("Metrics calculated successfully")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def _calculate_series_metrics(self, df: pd.DataFrame, 
                                date_col: str, value_col: str) -> Dict[str, Any]:
        """
        Calculate metrics for a data series.

        Args:
            df: DataFrame for the series
            date_col: Date column name
            value_col: Value column name

        Returns:
            Dictionary of metrics
        """
        # Ensure date column is datetime type
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Basic statistics
        metrics = {
            'count': len(df),
            'min': df[value_col].min() if not df.empty else None,
            'max': df[value_col].max() if not df.empty else None,
            'mean': df[value_col].mean() if not df.empty else None,
            'median': df[value_col].median() if not df.empty else None,
            'std': df[value_col].std() if not df.empty else None,
            'first_date': df[date_col].min() if not df.empty else None,
            'last_date': df[date_col].max() if not df.empty else None,
        }
        
        # Calculate period metrics if enough data
        if len(df) > 2:
            # Calculate trend (simple linear regression)
            x = np.arange(len(df))
            y = df[value_col].values
            
            try:
                slope, intercept = np.polyfit(x, y, 1)
                metrics['trend'] = {
                    'slope': slope,
                    'intercept': intercept,
                    'direction': 'up' if slope > 0 else 'down' if slope < 0 else 'flat',
                    'percent_change': (slope * len(df) / df[value_col].mean()) * 100 
                                     if df[value_col].mean() != 0 else 0
                }
            except:
                metrics['trend'] = None
        
        return metrics
    
    def _filter_by_date_range(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter DataFrame by date range.

        Args:
            df: DataFrame to filter
            config: Configuration with date range

        Returns:
            Filtered DataFrame
        """
        date_col = self._find_date_column(df)
        
        if not date_col:
            self.logger.warning("No date column found, cannot filter by date range")
            return df
        
        # Ensure date column is datetime type
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Get date range from config
        date_range = config.get('date_range', {})
        
        if 'start' in date_range and 'end' in date_range:
            # Custom date range
            start_date = pd.to_datetime(date_range['start'])
            end_date = pd.to_datetime(date_range['end'])
            
            self.logger.info(f"Filtering by custom date range: {start_date} to {end_date}")
            return df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
            
        elif 'days' in date_range:
            # Last N days
            days = date_range['days']
            end_date = df[date_col].max()
            start_date = end_date - pd.Timedelta(days=days)
            
            self.logger.info(f"Filtering by last {days} days: {start_date} to {end_date}")
            return df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
        
        # No date range specified, return all data
        return df
    
    def _filter_by_series(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter DataFrame by selected series.

        Args:
            df: DataFrame to filter
            config: Configuration with series selection

        Returns:
            Filtered DataFrame
        """
        if 'Breakdown' not in df.columns:
            self.logger.info("No Breakdown column found, cannot filter by series")
            return df
        
        # Get selected series from config
        selected_series = config.get('series', [])
        
        if selected_series:
            self.logger.info(f"Filtering by selected series: {selected_series}")
            return df[df['Breakdown'].isin(selected_series)]
        
        # No series specified, return all data
        return df
    
    def _sample_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sample data for better visualization performance.

        Args:
            df: DataFrame to sample

        Returns:
            Sampled DataFrame
        """
        self.logger.info(f"Sampling data from {len(df)} points")
        
        # Find date column
        date_col = self._find_date_column(df)
        
        if date_col:
            # If we have a breakdown column, sample within each group
            if 'Breakdown' in df.columns:
                result_dfs = []
                
                for name, group in df.groupby('Breakdown'):
                    # Get sample size based on proportion of data
                    sample_size = max(100, min(1000, int(len(group) / 2)))
                    
                    # Sort by date
                    group = group.sort_values(date_col)
                    
                    # Always include first and last point
                    first = group.iloc[:1]
                    last = group.iloc[-1:]
                    
                    # Sample middle points
                    middle = group.iloc[1:-1]
                    if len(middle) > sample_size - 2:
                        middle = middle.sample(sample_size - 2)
                    
                    # Combine and sort
                    sampled = pd.concat([first, middle, last]).sort_values(date_col)
                    result_dfs.append(sampled)
                
                result = pd.concat(result_dfs)
                self.logger.info(f"Sampled to {len(result)} points")
                return result
            else:
                # Sample without groups
                sample_size = min(2000, int(len(df) / 2))
                
                # Sort by date
                df = df.sort_values(date_col)
                
                # Always include first and last point
                first = df.iloc[:1]
                last = df.iloc[-1:]
                
                # Sample middle points
                middle = df.iloc[1:-1]
                if len(middle) > sample_size - 2:
                    middle = middle.sample(sample_size - 2)
                
                # Combine and sort
                result = pd.concat([first, middle, last]).sort_values(date_col)
                self.logger.info(f"Sampled to {len(result)} points")
                return result
        
        # If no date column, use simple random sampling
        sample_size = min(2000, int(len(df) / 2))
        result = df.sample(sample_size)
        self.logger.info(f"Randomly sampled to {len(result)} points")
        return result
    
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
            # Check if column contains date-like strings
            try:
                if pd.to_datetime(df[col], errors='coerce').notna().mean() > 0.8:
                    return col
            except:
                continue
        
        return None
    
    def _create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """
        Create a line chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly or Matplotlib figure object
        """
        if self.primary_engine == 'plotly':
            try:
                return self.plotly_engine.create_line_chart(df, config)
            except Exception as e:
                self.logger.warning(f"Plotly engine failed, falling back to Matplotlib: {str(e)}")
                return self.matplotlib_engine.create_line_chart(df, config)
        else:
            return self.matplotlib_engine.create_line_chart(df, config)
    
    def _create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """
        Create a bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly or Matplotlib figure object
        """
        if self.primary_engine == 'plotly':
            try:
                return self.plotly_engine.create_bar_chart(df, config)
            except Exception as e:
                self.logger.warning(f"Plotly engine failed, falling back to Matplotlib: {str(e)}")
                return self.matplotlib_engine.create_bar_chart(df, config)
        else:
            return self.matplotlib_engine.create_bar_chart(df, config)
    
    def _create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """
        Create a pie chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly or Matplotlib figure object
        """
        if self.primary_engine == 'plotly':
            try:
                return self.plotly_engine.create_pie_chart(df, config)
            except Exception as e:
                self.logger.warning(f"Plotly engine failed, falling back to Matplotlib: {str(e)}")
                return self.matplotlib_engine.create_pie_chart(df, config)
        else:
            return self.matplotlib_engine.create_pie_chart(df, config)
    
    def _create_diverging_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """
        Create a diverging bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly or Matplotlib figure object
        """
        if self.primary_engine == 'plotly':
            try:
                return self.plotly_engine.create_diverging_bar_chart(df, config)
            except Exception as e:
                self.logger.warning(f"Plotly engine failed, falling back to Matplotlib: {str(e)}")
                return self.matplotlib_engine.create_diverging_bar_chart(df, config)
        else:
            return self.matplotlib_engine.create_diverging_bar_chart(df, config)
