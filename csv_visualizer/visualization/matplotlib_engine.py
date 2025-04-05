"""
Matplotlib Visualization Engine for CSV Data Visualizer.

This module contains the MatplotlibEngine class for creating Matplotlib visualizations.
Used as a fallback option when Plotly is not suitable.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import io
import base64

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings


class MatplotlibEngine:
    """Matplotlib Visualization Engine for CSV Data Visualizer."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the Matplotlib visualization engine.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("MatplotlibEngine")
        self.settings = settings
        
        # Get color scheme
        self.colors = settings.get_color_scheme()
        
        # Set up matplotlib style
        self._setup_matplotlib_style()
    
    def _setup_matplotlib_style(self) -> None:
        """Set up matplotlib style for dark theme."""
        plt.style.use('dark_background')
        
        mpl.rcParams['figure.facecolor'] = self.colors['background']
        mpl.rcParams['axes.facecolor'] = self.colors['background']
        mpl.rcParams['axes.edgecolor'] = 'white'
        mpl.rcParams['axes.labelcolor'] = 'white'
        mpl.rcParams['xtick.color'] = 'white'
        mpl.rcParams['ytick.color'] = 'white'
        mpl.rcParams['text.color'] = 'white'
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['grid.alpha'] = 0.3
    
    def create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """
        Create a multi-series line chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Matplotlib figure
        """
        self.logger.info("Creating line chart (Matplotlib)")
        
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            # Get date column
            date_col = self._find_date_column(df)
            if not date_col:
                self.logger.error("No date column found")
                raise ValueError("No date column found in data")
            
            # Get value columns (excluding date and breakdown)
            value_cols = [col for col in df.columns 
                         if col != date_col and col != 'Breakdown']
            
            if not value_cols:
                self.logger.error("No value columns found")
                raise ValueError("No value columns found in data")
            
            # Default value column is the first one
            value_col = value_cols[0]
            
            # Create traces
            if 'Breakdown' in df.columns:
                # Multi-series chart grouped by Breakdown
                for i, (name, group) in enumerate(df.groupby('Breakdown')):
                    color = self.colors['chart_colors'][i % len(self.colors['chart_colors'])]
                    
                    ax.plot(group[date_col], group[value_col], 
                           marker='o', linestyle='-', linewidth=2, 
                           label=name, color=color)
            else:
                # Single series chart for each value column
                for i, col in enumerate(value_cols):
                    color = self.colors['chart_colors'][i % len(self.colors['chart_colors'])]
                    
                    ax.plot(df[date_col], df[col], 
                           marker='o', linestyle='-', linewidth=2, 
                           label=col, color=color)
            
            # Set title and labels
            title = config.get('title', 'Time Series Data')
            ax.set_title(title, fontsize=14)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel(value_col, fontsize=12)
            
            # Format x-axis as date
            fig.autofmt_xdate()
            
            # Add legend
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                     fancybox=True, shadow=True, ncol=3)
            
            # Grid
            ax.grid(True, alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            self.logger.info("Line chart created successfully (Matplotlib)")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating line chart: {str(e)}", exc_info=True)
            raise
    
    def create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """
        Create a bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Matplotlib figure
        """
        self.logger.info("Creating bar chart (Matplotlib)")
        
        try:
            # Get configuration options
            stacked = config.get('stacked', False)
            sort_by = config.get('sort_by', None)
            sort_order = config.get('sort_order', 'descending')
            
            # Get date column
            date_col = self._find_date_column(df)
            
            # Get value columns (excluding date and breakdown)
            value_cols = [col for col in df.columns 
                         if col != date_col and col != 'Breakdown']
            
            if not value_cols:
                self.logger.error("No value columns found")
                raise ValueError("No value columns found in data")
            
            # Default value column is the first one
            value_col = value_cols[0]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            # Prepare data
            if date_col and 'Breakdown' in df.columns:
                # For time series with breakdown, create stacked or grouped bar chart
                
                # Group by date (typically by month for bar charts)
                df = self._group_by_date_period(df, date_col, 'M')
                
                # Format dates for better display
                df['date_label'] = df[date_col].dt.strftime('%b %Y')
                
                # Get unique categories and dates
                categories = df['Breakdown'].unique()
                dates = sorted(df['date_label'].unique())
                
                # For grouped bars
                bar_width = 0.8 / len(categories) if len(categories) > 0 else 0.8
                
                # Create bars
                if stacked:
                    bottom = np.zeros(len(dates))
                    
                    for i, category in enumerate(categories):
                        # Filter data for this category
                        cat_data = df[df['Breakdown'] == category]
                        
                        # Prepare values for each date
                        values = []
                        for date in dates:
                            date_data = cat_data[cat_data['date_label'] == date]
                            if not date_data.empty:
                                values.append(date_data[value_col].values[0])
                            else:
                                values.append(0)
                        
                        # Plot stacked bar
                        ax.bar(dates, values, bottom=bottom, 
                              label=category, 
                              color=self.colors['chart_colors'][i % len(self.colors['chart_colors'])])
                        
                        # Update bottom for next stack
                        bottom += np.array(values)
                else:
                    # Grouped bars
                    x = np.arange(len(dates))
                    
                    for i, category in enumerate(categories):
                        # Filter data for this category
                        cat_data = df[df['Breakdown'] == category]
                        
                        # Prepare values for each date
                        values = []
                        for date in dates:
                            date_data = cat_data[cat_data['date_label'] == date]
                            if not date_data.empty:
                                values.append(date_data[value_col].values[0])
                            else:
                                values.append(0)
                        
                        # Plot grouped bar
                        ax.bar(x + i * bar_width - (len(categories) - 1) * bar_width / 2, 
                              values, bar_width, 
                              label=category, 
                              color=self.colors['chart_colors'][i % len(self.colors['chart_colors'])])
                    
                    # Set x-ticks at the middle of the groups
                    ax.set_xticks(x)
                    ax.set_xticklabels(dates)
                
            elif 'Breakdown' in df.columns:
                # For non-time series data with breakdown, create bar chart by breakdown
                
                # Aggregate data by breakdown
                agg_df = df.groupby('Breakdown')[value_col].mean().reset_index()
                
                # Sort if requested
                if sort_by == 'value':
                    agg_df = agg_df.sort_values(value_col, ascending=(sort_order == 'ascending'))
                elif sort_by == 'category':
                    agg_df = agg_df.sort_values('Breakdown', ascending=(sort_order == 'ascending'))
                
                # Create bars
                ax.bar(agg_df['Breakdown'], agg_df[value_col], 
                      color=self.colors['chart_colors'])
                
            elif date_col:
                # For time series without breakdown, create simple bar chart by date
                
                # Group by date (typically by month for bar charts)
                df = self._group_by_date_period(df, date_col, 'M')
                
                # Format dates for better display
                df['date_label'] = df[date_col].dt.strftime('%b %Y')
                
                # Sort by date
                df = df.sort_values(date_col)
                
                # Create bars
                ax.bar(df['date_label'], df[value_col], 
                      color=self.colors['chart_colors'][0])
                
            else:
                # For non-time series, non-breakdown data, create bar chart by column
                
                # Create a bar for each value column
                ax.bar(value_cols, [df[col].mean() for col in value_cols], 
                      color=self.colors['chart_colors'])
            
            # Set title and labels
            title = config.get('title', 'Bar Chart')
            ax.set_title(title, fontsize=14)
            ax.set_xlabel('Category', fontsize=12)
            ax.set_ylabel(value_col, fontsize=12)
            
            # Rotate x-tick labels if needed
            if len(ax.get_xticklabels()) > 5:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add legend if needed
            if 'Breakdown' in df.columns:
                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
                         fancybox=True, shadow=True, ncol=3)
            
            # Grid
            ax.grid(True, axis='y', alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            self.logger.info("Bar chart created successfully (Matplotlib)")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating bar chart: {str(e)}", exc_info=True)
            raise
    
    def create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """
        Create a pie chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Matplotlib figure
        """
        self.logger.info("Creating pie chart (Matplotlib)")
        
        try:
            # Get configuration options
            donut = config.get('donut', False)
            
            # Get date column (for filtering if needed)
            date_col = self._find_date_column(df)
            
            # Get value columns (excluding date and breakdown)
            value_cols = [col for col in df.columns 
                         if col != date_col and col != 'Breakdown']
            
            if not value_cols:
                self.logger.error("No value columns found")
                raise ValueError("No value columns found in data")
            
            # Default value column is the first one
            value_col = value_cols[0]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
            
            # Prepare data for pie chart
            if 'Breakdown' in df.columns:
                # Use breakdown column for categories
                agg_df = df.groupby('Breakdown')[value_col].sum().reset_index()
                labels = agg_df['Breakdown']
                values = agg_df[value_col]
            else:
                # Use value columns as categories
                labels = value_cols
                values = [df[col].sum() for col in value_cols]
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=None,  # We'll add a legend instead
                autopct='%1.1f%%',
                startangle=90,
                colors=self.colors['chart_colors'],
                wedgeprops=dict(width=0.5 if donut else 0)  # For donut chart
            )
            
            # Enhance text visibility
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Set title
            title = config.get('title', 'Distribution')
            ax.set_title(title, fontsize=14)
            
            # Add legend
            ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
            
            # Adjust layout
            plt.tight_layout()
            
            self.logger.info("Pie chart created successfully (Matplotlib)")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating pie chart: {str(e)}", exc_info=True)
            raise
    
    def create_diverging_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Figure:
        """
        Create a diverging bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Matplotlib figure
        """
        self.logger.info("Creating diverging bar chart (Matplotlib)")
        
        try:
            # Get configuration options
            sort_by = config.get('sort_by', 'value')
            
            # Get date column
            date_col = self._find_date_column(df)
            
            # Get value columns (excluding date and breakdown)
            value_cols = [col for col in df.columns 
                         if col != date_col and col != 'Breakdown']
            
            if not value_cols:
                self.logger.error("No value columns found")
                raise ValueError("No value columns found in data")
            
            # Default value column is the first one
            value_col = value_cols[0]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            # Prepare data
            if 'Breakdown' in df.columns:
                # Use breakdown column for categories
                agg_df = df.groupby('Breakdown')[value_col].mean().reset_index()
                
                # Calculate deviation from mean
                mean_value = agg_df[value_col].mean()
                agg_df['deviation'] = agg_df[value_col] - mean_value
                
                # Sort if requested
                if sort_by == 'value':
                    agg_df = agg_df.sort_values('deviation')
                elif sort_by == 'category':
                    agg_df = agg_df.sort_values('Breakdown')
                
                # Create diverging bar chart
                bars = ax.bar(
                    agg_df['Breakdown'],
                    agg_df['deviation'],
                    color=[self.colors['chart_colors'][0] if x < 0 else self.colors['chart_colors'][1]
                          for x in agg_df['deviation']]
                )
                
                # Add value annotations
                for bar, value, deviation in zip(bars, agg_df[value_col], agg_df['deviation']):
                    height = bar.get_height()
                    if height < 0:
                        ha = 'center'
                        va = 'top'
                        y = height - 0.1 * abs(height)
                    else:
                        ha = 'center'
                        va = 'bottom'
                        y = height + 0.1 * abs(height)
                    
                    ax.annotate(
                        f'{value:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, y),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha=ha, va=va,
                        color='white',
                        fontsize=8
                    )
                
                # Add zero line
                ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
                
                # Add mean line annotation
                ax.annotate(
                    f'Mean: {mean_value:.2f}',
                    xy=(1, 0),
                    xytext=(8, 0),
                    xycoords=('axes fraction', 'data'),
                    textcoords='offset points',
                    ha='left',
                    va='center',
                    color='white',
                    alpha=0.7
                )
                
            else:
                # Use value columns as categories
                data = []
                labels = []
                
                # Calculate mean for each column
                for col in value_cols:
                    mean_val = df[col].mean()
                    dev = mean_val - df[value_cols].mean().mean()
                    data.append(dev)
                    labels.append(col)
                
                # Sort if requested
                if sort_by == 'value':
                    # Sort by deviation
                    sorted_indices = np.argsort(data)
                    data = [data[i] for i in sorted_indices]
                    labels = [labels[i] for i in sorted_indices]
                
                # Create diverging bar chart
                bars = ax.bar(
                    labels,
                    data,
                    color=[self.colors['chart_colors'][0] if x < 0 else self.colors['chart_colors'][1]
                          for x in data]
                )
                
                # Add value annotations
                for bar, value in zip(bars, data):
                    height = bar.get_height()
                    if height < 0:
                        ha = 'center'
                        va = 'top'
                        y = height - 0.1 * abs(height)
                    else:
                        ha = 'center'
                        va = 'bottom'
                        y = height + 0.1 * abs(height)
                    
                    ax.annotate(
                        f'{value:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, y),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha=ha, va=va,
                        color='white',
                        fontsize=8
                    )
                
                # Add zero line
                ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
            
            # Set title and labels
            title = config.get('title', 'Deviation from Average')
            ax.set_title(title, fontsize=14)
            ax.set_xlabel('Category', fontsize=12)
            ax.set_ylabel(f"Deviation from mean {value_col}", fontsize=12)
            
            # Rotate x-tick labels if needed
            if len(ax.get_xticklabels()) > 5:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Grid (only horizontal)
            ax.grid(True, axis='y', alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            self.logger.info("Diverging bar chart created successfully (Matplotlib)")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating diverging bar chart: {str(e)}", exc_info=True)
            raise
    
    def figure_to_image(self, fig: Figure) -> bytes:
        """
        Convert a Matplotlib figure to a PNG image.

        Args:
            fig: Matplotlib figure

        Returns:
            PNG image as bytes
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        return buf.getvalue()
    
    def figure_to_base64(self, fig: Figure) -> str:
        """
        Convert a Matplotlib figure to a base64-encoded PNG image.

        Args:
            fig: Matplotlib figure

        Returns:
            Base64-encoded PNG image
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
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
    
    def _group_by_date_period(
        self, df: pd.DataFrame, date_col: str, period: str = 'M'
    ) -> pd.DataFrame:
        """
        Group DataFrame by date period.

        Args:
            df: DataFrame
            date_col: Date column name
            period: Period to group by ('D'=daily, 'W'=weekly, 'M'=monthly)

        Returns:
            Grouped DataFrame
        """
        # Ensure date column is datetime type
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Create period column
        if period == 'D':
            df['period'] = df[date_col].dt.date
        elif period == 'W':
            df['period'] = df[date_col].dt.to_period('W').dt.start_time
        elif period == 'M':
            df['period'] = df[date_col].dt.to_period('M').dt.start_time
        else:
            df['period'] = df[date_col]
        
        # Group by period and breakdown if available
        if 'Breakdown' in df.columns:
            agg_df = df.groupby(['period', 'Breakdown']).mean().reset_index()
        else:
            agg_df = df.groupby('period').mean().reset_index()
        
        # Rename period column to original date column
        agg_df[date_col] = agg_df['period']
        agg_df = agg_df.drop('period', axis=1)
        
        return agg_df
