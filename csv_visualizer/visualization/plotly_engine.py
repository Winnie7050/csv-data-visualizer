"""
Plotly Visualization Engine for CSV Data Visualizer.

This module contains the PlotlyEngine class for creating Plotly visualizations.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from csv_visualizer.utils.logging_utils import get_module_logger
from csv_visualizer.core.settings import Settings


class PlotlyEngine:
    """Plotly Visualization Engine for CSV Data Visualizer."""

    def __init__(self, logger: logging.Logger, settings: Settings):
        """
        Initialize the Plotly visualization engine.

        Args:
            logger: Logger instance
            settings: Application settings
        """
        self.logger = get_module_logger("PlotlyEngine")
        self.settings = settings
        
        # Get color scheme
        self.colors = settings.get_color_scheme()
    
    def create_line_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """
        Create a multi-series line chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly figure
        """
        self.logger.info("Creating line chart")
        
        try:
            # Create figure
            fig = go.Figure()
            
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
                    
                    fig.add_trace(go.Scatter(
                        x=group[date_col],
                        y=group[value_col],
                        mode='lines+markers',
                        name=name,
                        line=dict(color=color, width=2),
                        marker=dict(color=color, size=6),
                        hovertemplate=(
                            f"<b>{name}</b><br>"
                            f"Date: %{{x|%Y-%m-%d}}<br>"
                            f"{value_col}: %{{y:.2f}}<extra></extra>"
                        )
                    ))
            else:
                # Single series chart for each value column
                for i, col in enumerate(value_cols):
                    color = self.colors['chart_colors'][i % len(self.colors['chart_colors'])]
                    
                    fig.add_trace(go.Scatter(
                        x=df[date_col],
                        y=df[col],
                        mode='lines+markers',
                        name=col,
                        line=dict(color=color, width=2),
                        marker=dict(color=color, size=6),
                        hovertemplate=(
                            f"Date: %{{x|%Y-%m-%d}}<br>"
                            f"{col}: %{{y:.2f}}<extra></extra>"
                        )
                    ))
            
            # Set layout
            title = config.get('title', 'Time Series Data')
            
            fig.update_layout(
                title=dict(
                    text=title,
                    font=dict(size=18, color=self.colors['foreground'])
                ),
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font=dict(color=self.colors['foreground']),
                xaxis=dict(
                    title="Date",
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    zerolinecolor='rgba(255, 255, 255, 0.1)'
                ),
                yaxis=dict(
                    title=value_col,
                    gridcolor='rgba(255, 255, 255, 0.1)',
                    zerolinecolor='rgba(255, 255, 255, 0.1)'
                ),
                hovermode="closest",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            # Set x-axis to date type
            fig.update_xaxes(type='date')
            
            self.logger.info("Line chart created successfully")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating line chart: {str(e)}", exc_info=True)
            raise
    
    def create_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """
        Create a bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly figure
        """
        self.logger.info("Creating bar chart")
        
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
            
            # Prepare data
            if date_col and 'Breakdown' in df.columns:
                # For time series with breakdown, create stacked or grouped bar chart
                
                # Group by date (typically by month for bar charts)
                df = self._group_by_date_period(df, date_col, 'M')
                
                # Format dates for better display
                df['date_label'] = df[date_col].dt.strftime('%b %Y')
                
                # Create figure
                if stacked:
                    fig = px.bar(
                        df, 
                        x='date_label', 
                        y=value_col, 
                        color='Breakdown',
                        barmode='stack',
                        color_discrete_sequence=self.colors['chart_colors'],
                        title=config.get('title', 'Bar Chart')
                    )
                else:
                    fig = px.bar(
                        df, 
                        x='date_label', 
                        y=value_col, 
                        color='Breakdown',
                        barmode='group',
                        color_discrete_sequence=self.colors['chart_colors'],
                        title=config.get('title', 'Bar Chart')
                    )
                
                # Update to match theme
                fig.update_layout(
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Date",
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        categoryorder='array',
                        categoryarray=sorted(df['date_label'].unique())
                    ),
                    yaxis=dict(
                        title=value_col,
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.1)'
                    ),
                    hovermode="closest",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                
            elif 'Breakdown' in df.columns:
                # For non-time series data with breakdown, create bar chart by breakdown
                
                # Aggregate data by breakdown
                agg_df = df.groupby('Breakdown')[value_col].mean().reset_index()
                
                # Sort if requested
                if sort_by == 'value':
                    agg_df = agg_df.sort_values(value_col, ascending=(sort_order == 'ascending'))
                elif sort_by == 'category':
                    agg_df = agg_df.sort_values('Breakdown', ascending=(sort_order == 'ascending'))
                
                # Create figure
                fig = px.bar(
                    agg_df, 
                    x='Breakdown', 
                    y=value_col,
                    color='Breakdown',
                    color_discrete_sequence=self.colors['chart_colors'],
                    title=config.get('title', 'Bar Chart')
                )
                
                # Update to match theme
                fig.update_layout(
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Category",
                        gridcolor='rgba(255, 255, 255, 0.1)'
                    ),
                    yaxis=dict(
                        title=value_col,
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.1)'
                    ),
                    hovermode="closest",
                    showlegend=False,
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                
            elif date_col:
                # For time series without breakdown, create simple bar chart by date
                
                # Group by date (typically by month for bar charts)
                df = self._group_by_date_period(df, date_col, 'M')
                
                # Format dates for better display
                df['date_label'] = df[date_col].dt.strftime('%b %Y')
                
                # Create figure
                fig = px.bar(
                    df, 
                    x='date_label', 
                    y=value_col,
                    color_discrete_sequence=[self.colors['chart_colors'][0]],
                    title=config.get('title', 'Bar Chart')
                )
                
                # Update to match theme
                fig.update_layout(
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Date",
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        categoryorder='array',
                        categoryarray=sorted(df['date_label'].unique())
                    ),
                    yaxis=dict(
                        title=value_col,
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.1)'
                    ),
                    hovermode="closest",
                    showlegend=False,
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                
            else:
                # For non-time series, non-breakdown data, create bar chart by column
                
                # Create a bar for each value column
                data = []
                for col in value_cols:
                    data.append(df[col].mean())
                
                # Create figure
                fig = go.Figure(data=[
                    go.Bar(
                        x=value_cols,
                        y=data,
                        marker_color=self.colors['chart_colors']
                    )
                ])
                
                # Update layout
                fig.update_layout(
                    title=dict(
                        text=config.get('title', 'Bar Chart'),
                        font=dict(size=18, color=self.colors['foreground'])
                    ),
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Metric",
                        gridcolor='rgba(255, 255, 255, 0.1)'
                    ),
                    yaxis=dict(
                        title="Value",
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.1)'
                    ),
                    hovermode="closest",
                    margin=dict(l=40, r=40, t=60, b=40)
                )
            
            self.logger.info("Bar chart created successfully")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating bar chart: {str(e)}", exc_info=True)
            raise
    
    def create_pie_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """
        Create a pie chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly figure
        """
        self.logger.info("Creating pie chart")
        
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
            fig = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4 if donut else 0,
                    marker=dict(
                        colors=self.colors['chart_colors'],
                        line=dict(color=self.colors['background'], width=1)
                    ),
                    textinfo='percent+label',
                    insidetextfont=dict(color=self.colors['background']),
                    outsidetextfont=dict(color=self.colors['foreground']),
                    hoverinfo='label+percent+value',
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Value: %{value:.2f}<br>"
                        "Percentage: %{percent}<extra></extra>"
                    )
                )
            ])
            
            # Set layout
            fig.update_layout(
                title=dict(
                    text=config.get('title', 'Distribution'),
                    font=dict(size=18, color=self.colors['foreground'])
                ),
                plot_bgcolor=self.colors['background'],
                paper_bgcolor=self.colors['background'],
                font=dict(color=self.colors['foreground']),
                margin=dict(l=40, r=40, t=60, b=40),
                legend=dict(
                    font=dict(color=self.colors['foreground']),
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            
            self.logger.info("Pie chart created successfully")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating pie chart: {str(e)}", exc_info=True)
            raise
    
    def create_diverging_bar_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """
        Create a diverging bar chart.

        Args:
            df: DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly figure
        """
        self.logger.info("Creating diverging bar chart")
        
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
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=agg_df['Breakdown'],
                    y=agg_df['deviation'],
                    marker_color=[
                        self.colors['chart_colors'][0] if x < 0 else self.colors['chart_colors'][1]
                        for x in agg_df['deviation']
                    ],
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{value_col}: %{{text:.2f}}<br>"
                        "Deviation from mean: %{y:.2f}<extra></extra>"
                    ),
                    text=agg_df[value_col]
                ))
                
                # Add zero line
                fig.add_shape(
                    type="line",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=0,
                    line=dict(
                        color="rgba(255, 255, 255, 0.5)",
                        width=2,
                        dash="dash"
                    )
                )
                
                # Add mean line annotation
                fig.add_annotation(
                    xref="paper",
                    yref="y",
                    x=1.01,
                    y=0,
                    text=f"Mean: {mean_value:.2f}",
                    showarrow=False,
                    font=dict(color="rgba(255, 255, 255, 0.7)")
                )
                
                # Update layout
                fig.update_layout(
                    title=dict(
                        text=config.get('title', 'Deviation from Average'),
                        font=dict(size=18, color=self.colors['foreground'])
                    ),
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Category",
                        gridcolor='rgba(255, 255, 255, 0.1)'
                    ),
                    yaxis=dict(
                        title=f"Deviation from mean {value_col}",
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.5)',
                        zerolinewidth=2
                    ),
                    hovermode="closest",
                    margin=dict(l=40, r=40, t=60, b=40)
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
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=labels,
                    y=data,
                    marker_color=[
                        self.colors['chart_colors'][0] if x < 0 else self.colors['chart_colors'][1]
                        for x in data
                    ],
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Deviation from average: %{y:.2f}<extra></extra>"
                    )
                ))
                
                # Add zero line
                fig.add_shape(
                    type="line",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=0,
                    line=dict(
                        color="rgba(255, 255, 255, 0.5)",
                        width=2,
                        dash="dash"
                    )
                )
                
                # Update layout
                fig.update_layout(
                    title=dict(
                        text=config.get('title', 'Deviation from Average'),
                        font=dict(size=18, color=self.colors['foreground'])
                    ),
                    plot_bgcolor=self.colors['background'],
                    paper_bgcolor=self.colors['background'],
                    font=dict(color=self.colors['foreground']),
                    xaxis=dict(
                        title="Metric",
                        gridcolor='rgba(255, 255, 255, 0.1)'
                    ),
                    yaxis=dict(
                        title="Deviation from average",
                        gridcolor='rgba(255, 255, 255, 0.1)',
                        zerolinecolor='rgba(255, 255, 255, 0.5)',
                        zerolinewidth=2
                    ),
                    hovermode="closest",
                    margin=dict(l=40, r=40, t=60, b=40)
                )
            
            self.logger.info("Diverging bar chart created successfully")
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating diverging bar chart: {str(e)}", exc_info=True)
            raise
    
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
