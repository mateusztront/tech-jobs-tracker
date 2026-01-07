"""
Geographic visualization components for dashboard.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_jobs_by_city(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Create bar chart of jobs by city.

    Args:
        df: DataFrame with city and job_count
        top_n: Number of top cities to show

    Returns:
        Plotly figure
    """
    if df.empty or 'city' not in df.columns:
        return _empty_figure("No city data available")

    # Filter out nulls and group by city
    df_clean = df[df['city'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid city data")

    city_counts = df_clean.groupby('city')['job_count'].sum().reset_index()
    city_counts = city_counts.nlargest(top_n, 'job_count')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=city_counts['city'],
        y=city_counts['job_count'],
        text=city_counts['job_count'],
        textposition='auto',
        marker=dict(
            color=city_counts['job_count'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Job Count")
        ),
        hovertemplate='<b>%{x}</b><br>' +
                      'Jobs: %{y}<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title=f'Job Distribution by City (Top {top_n})',
        xaxis_title='City',
        yaxis_title='Number of Jobs',
        height=450,
        showlegend=False,
        xaxis_tickangle=-45
    )

    return fig


def plot_location_type_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Create pie chart of location type distribution.

    Args:
        df: DataFrame with location_type and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'location_type' not in df.columns:
        return _empty_figure("No location type data available")

    # Filter out nulls and group by location type
    df_clean = df[df['location_type'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid location type data")

    location_counts = df_clean.groupby('location_type')['job_count'].sum().reset_index()

    # Define colors for location types
    color_map = {
        'remote': '#2ca02c',
        'hybrid': '#ff7f0e',
        'office': '#1f77b4'
    }

    colors = [color_map.get(loc, '#gray') for loc in location_counts['location_type']]

    fig = go.Figure(data=[go.Pie(
        labels=location_counts['location_type'].str.title(),
        values=location_counts['job_count'],
        marker=dict(colors=colors),
        hole=0.3,
        hovertemplate='<b>%{label}</b><br>' +
                      'Jobs: %{value}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>'
    )])

    fig.update_layout(
        title='Job Distribution by Location Type',
        height=400,
        annotations=[dict(text='Location<br>Type', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )

    return fig


def plot_location_type_trend(df: pd.DataFrame) -> go.Figure:
    """
    Create stacked area chart of location type trends over time.

    Args:
        df: DataFrame with snapshot_date, location_type, and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'snapshot_date' not in df.columns or 'location_type' not in df.columns:
        return _empty_figure("No temporal location data available")

    # Group by date and location type
    trend_data = df.groupby(['snapshot_date', 'location_type'])['job_count'].sum().reset_index()

    if trend_data.empty:
        return _empty_figure("Insufficient data for trend analysis")

    # Pivot for area chart
    trend_pivot = trend_data.pivot(
        index='snapshot_date',
        columns='location_type',
        values='job_count'
    ).fillna(0)

    fig = go.Figure()

    colors = {
        'remote': '#2ca02c',
        'hybrid': '#ff7f0e',
        'office': '#1f77b4'
    }

    for col in trend_pivot.columns:
        fig.add_trace(go.Scatter(
            x=trend_pivot.index,
            y=trend_pivot[col],
            name=col.title(),
            mode='lines',
            stackgroup='one',
            fillcolor=colors.get(col, '#gray'),
            line=dict(width=0.5, color=colors.get(col, '#gray'))
        ))

    fig.update_layout(
        title='Location Type Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Jobs',
        hovermode='x unified',
        height=400
    )

    return fig


def plot_regional_comparison(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart comparing job counts by region.

    Args:
        df: DataFrame with region and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'region' not in df.columns:
        return _empty_figure("No region data available")

    # Filter out nulls and group by region
    df_clean = df[df['region'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid region data")

    region_counts = df_clean.groupby('region')['job_count'].sum().reset_index()
    region_counts = region_counts.sort_values('job_count', ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=region_counts['region'],
        x=region_counts['job_count'],
        orientation='h',
        text=region_counts['job_count'],
        textposition='auto',
        marker=dict(
            color=region_counts['job_count'],
            colorscale='Greens',
            showscale=True,
            colorbar=dict(title="Job Count")
        ),
        hovertemplate='<b>%{y}</b><br>' +
                      'Jobs: %{x}<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title='Job Distribution by Region',
        xaxis_title='Number of Jobs',
        yaxis_title='Region',
        height=max(400, len(region_counts) * 30),
        showlegend=False
    )

    return fig


def plot_city_by_location_type(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create grouped bar chart showing location types by city.

    Args:
        df: DataFrame with city, location_type, and job_count
        top_n: Number of top cities to show

    Returns:
        Plotly figure
    """
    if df.empty or 'city' not in df.columns or 'location_type' not in df.columns:
        return _empty_figure("No city/location type data available")

    # Filter valid data
    df_clean = df[df['city'].notna() & df['location_type'].notna()].copy()

    if df_clean.empty:
        return _empty_figure("No valid city/location data")

    # Get top cities by total job count
    top_cities = df_clean.groupby('city')['job_count'].sum().nlargest(top_n).index

    # Filter to top cities
    df_top = df_clean[df_clean['city'].isin(top_cities)]

    # Group by city and location type
    city_location = df_top.groupby(['city', 'location_type'])['job_count'].sum().reset_index()

    fig = px.bar(
        city_location,
        x='city',
        y='job_count',
        color='location_type',
        title=f'Location Types in Top {top_n} Cities',
        labels={'job_count': 'Number of Jobs', 'city': 'City', 'location_type': 'Location Type'},
        barmode='group',
        color_discrete_map={
            'remote': '#2ca02c',
            'hybrid': '#ff7f0e',
            'office': '#1f77b4'
        }
    )

    fig.update_layout(
        height=450,
        xaxis_tickangle=-45
    )

    return fig


def create_location_summary_table(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Create summary table of locations.

    Args:
        df: DataFrame with location data
        top_n: Number of locations to include

    Returns:
        Summary DataFrame
    """
    if df.empty or 'city' not in df.columns:
        return pd.DataFrame()

    # Filter valid cities
    df_clean = df[df['city'].notna()].copy()

    if df_clean.empty:
        return pd.DataFrame()

    # Group by city and region
    summary = df_clean.groupby(['city', 'region']).agg({
        'job_count': 'sum'
    }).reset_index()

    summary = summary.nlargest(top_n, 'job_count')
    summary = summary.rename(columns={
        'city': 'City',
        'region': 'Region',
        'job_count': 'Job Count'
    })

    summary = summary.reset_index(drop=True)
    summary.index = summary.index + 1

    return summary


def plot_remote_percentage_trend(df: pd.DataFrame) -> go.Figure:
    """
    Create line chart showing percentage of remote jobs over time.

    Args:
        df: DataFrame with snapshot_date, location_type, and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'snapshot_date' not in df.columns or 'location_type' not in df.columns:
        return _empty_figure("No temporal location data available")

    # Calculate total jobs and remote jobs per date
    total_by_date = df.groupby('snapshot_date')['job_count'].sum().reset_index()
    total_by_date.columns = ['snapshot_date', 'total_jobs']

    remote_by_date = df[df['location_type'] == 'remote'].groupby('snapshot_date')['job_count'].sum().reset_index()
    remote_by_date.columns = ['snapshot_date', 'remote_jobs']

    # Merge and calculate percentage
    trend = total_by_date.merge(remote_by_date, on='snapshot_date', how='left')
    trend['remote_jobs'] = trend['remote_jobs'].fillna(0)
    trend['remote_pct'] = (trend['remote_jobs'] / trend['total_jobs'] * 100).round(1)

    if trend.empty:
        return _empty_figure("Insufficient data for trend")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend['snapshot_date'],
        y=trend['remote_pct'],
        mode='lines+markers',
        name='Remote %',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(44, 160, 44, 0.2)',
        hovertemplate='Date: %{x}<br>Remote: %{y:.1f}%<extra></extra>'
    ))

    fig.update_layout(
        title='Remote Work Trend',
        xaxis_title='Date',
        yaxis_title='Percentage of Remote Jobs (%)',
        hovermode='x unified',
        height=400
    )

    return fig


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
