"""
Salary visualization components for dashboard.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_salary_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Create histogram of salary distribution.

    Args:
        df: DataFrame with salary data

    Returns:
        Plotly figure
    """
    if df.empty or 'salary_avg' not in df.columns:
        return _empty_figure("No salary data available")

    # Filter out nulls
    df_clean = df[df['salary_avg'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid salary data")

    fig = px.histogram(
        df_clean,
        x='salary_avg',
        nbins=30,
        title='Salary Distribution (PLN)',
        labels={'salary_avg': 'Average Salary (PLN)', 'count': 'Number of Jobs'},
        color_discrete_sequence=['#1f77b4']
    )

    # Add median line
    median_salary = df_clean['salary_avg'].median()
    fig.add_vline(
        x=median_salary,
        line_dash='dash',
        line_color='red',
        annotation_text=f"Median: {median_salary:,.0f} PLN",
        annotation_position="top right"
    )

    fig.update_layout(
        showlegend=False,
        height=400,
        hovermode='x unified'
    )

    return fig


def plot_salary_by_technology(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Create box plot of salaries by technology.

    Args:
        df: DataFrame with technology and salary data
        top_n: Number of top technologies to show

    Returns:
        Plotly figure
    """
    if df.empty:
        return _empty_figure("No technology salary data available")

    # Sort by job count and take top N
    df_sorted = df.nlargest(top_n, 'job_count')

    fig = go.Figure()

    # Create horizontal bar chart showing salary ranges
    fig.add_trace(go.Bar(
        y=df_sorted['technology'],
        x=df_sorted['avg_salary'],
        orientation='h',
        text=[f"{val:,.0f} PLN" for val in df_sorted['avg_salary']],
        textposition='auto',
        marker=dict(
            color=df_sorted['avg_salary'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Avg Salary (PLN)")
        ),
        hovertemplate='<b>%{y}</b><br>' +
                      'Avg Salary: %{x:,.0f} PLN<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title=f'Average Salary by Technology (Top {top_n})',
        xaxis_title='Average Salary (PLN)',
        yaxis_title='Technology',
        height=max(400, top_n * 25),
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )

    return fig


def plot_salary_trends(df: pd.DataFrame) -> go.Figure:
    """
    Create time series of salary trends.

    Args:
        df: DataFrame with snapshot_date and salary_avg

    Returns:
        Plotly figure
    """
    if df.empty or 'snapshot_date' not in df.columns or 'salary_avg' not in df.columns:
        return _empty_figure("No salary trend data available")

    # Group by date and calculate statistics
    df_trend = df.groupby('snapshot_date').agg({
        'salary_avg': ['mean', 'median', 'count']
    }).reset_index()

    df_trend.columns = ['snapshot_date', 'mean_salary', 'median_salary', 'count']

    # Filter dates with enough data points
    df_trend = df_trend[df_trend['count'] >= 5]

    if df_trend.empty:
        return _empty_figure("Insufficient data for trend analysis")

    fig = go.Figure()

    # Add mean salary line
    fig.add_trace(go.Scatter(
        x=df_trend['snapshot_date'],
        y=df_trend['mean_salary'],
        mode='lines+markers',
        name='Average',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))

    # Add median salary line
    fig.add_trace(go.Scatter(
        x=df_trend['snapshot_date'],
        y=df_trend['median_salary'],
        mode='lines+markers',
        name='Median',
        line=dict(color='#2ca02c', width=2, dash='dash'),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title='Salary Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Salary (PLN)',
        hovermode='x unified',
        height=400,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    return fig


def plot_salary_by_seniority(df: pd.DataFrame) -> go.Figure:
    """
    Create box plot of salaries by seniority level.

    Args:
        df: DataFrame with seniority_level and salary data

    Returns:
        Plotly figure
    """
    if df.empty or 'seniority_level' not in df.columns or 'salary_avg' not in df.columns:
        return _empty_figure("No seniority salary data available")

    # Filter valid data
    df_clean = df[df['seniority_level'].notna() & df['salary_avg'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid seniority data")

    # Order seniority levels (only include levels that exist in data)
    seniority_order = ['junior', 'mid', 'senior']
    existing_levels = [level for level in seniority_order if level in df_clean['seniority_level'].values]

    if existing_levels:
        df_clean['seniority_level'] = pd.Categorical(
            df_clean['seniority_level'],
            categories=existing_levels,
            ordered=True
        )

    fig = px.box(
        df_clean,
        x='seniority_level',
        y='salary_avg',
        title='Salary Distribution by Seniority Level',
        labels={'seniority_level': 'Seniority', 'salary_avg': 'Salary (PLN)'},
        color='seniority_level',
        color_discrete_map={
            'junior': '#ff7f0e',
            'mid': '#2ca02c',
            'senior': '#1f77b4'
        }
    )

    fig.update_layout(
        showlegend=False,
        height=400
    )

    return fig


def plot_salary_by_location_type(df: pd.DataFrame) -> go.Figure:
    """
    Create box plot comparing salaries by location type.

    Args:
        df: DataFrame with location and salary data

    Returns:
        Plotly figure
    """
    if df.empty:
        return _empty_figure("No location salary data available")

    # Merge location and salary data
    # This assumes df already has both location_type and salary_avg
    df_clean = df[df['location_type'].notna() & df['salary_avg'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid location data")

    fig = px.box(
        df_clean,
        x='location_type',
        y='salary_avg',
        title='Salary Distribution by Location Type',
        labels={'location_type': 'Location Type', 'salary_avg': 'Salary (PLN)'},
        color='location_type',
        color_discrete_map={
            'remote': '#2ca02c',
            'hybrid': '#ff7f0e',
            'office': '#1f77b4'
        }
    )

    fig.update_layout(
        showlegend=False,
        height=400
    )

    return fig


def create_salary_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary statistics table for salaries.

    Args:
        df: DataFrame with salary data

    Returns:
        Summary DataFrame
    """
    if df.empty or 'salary_avg' not in df.columns:
        return pd.DataFrame()

    df_clean = df[df['salary_avg'].notna()]

    if df_clean.empty:
        return pd.DataFrame()

    summary = pd.DataFrame({
        'Metric': ['Mean', 'Median', 'Min', 'Max', '25th Percentile', '75th Percentile'],
        'Value (PLN)': [
            f"{df_clean['salary_avg'].mean():,.0f}",
            f"{df_clean['salary_avg'].median():,.0f}",
            f"{df_clean['salary_avg'].min():,.0f}",
            f"{df_clean['salary_avg'].max():,.0f}",
            f"{df_clean['salary_avg'].quantile(0.25):,.0f}",
            f"{df_clean['salary_avg'].quantile(0.75):,.0f}"
        ]
    })

    return summary


def _empty_figure(message: str) -> go.Figure:
    """
    Create an empty figure with a message.

    Args:
        message: Message to display

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray")
    )

    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        height=400
    )

    return fig
