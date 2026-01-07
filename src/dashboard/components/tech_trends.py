"""
Technology trends visualization components for dashboard.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_top_technologies(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """
    Create bar chart of most popular technologies.

    Args:
        df: DataFrame with technology data
        top_n: Number of top technologies to show

    Returns:
        Plotly figure
    """
    if df.empty or 'technology' not in df.columns:
        return _empty_figure("No technology data available")

    # Group by technology and sum job counts
    tech_counts = df.groupby('technology')['job_count'].sum().reset_index()
    tech_counts = tech_counts.nlargest(top_n, 'job_count')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=tech_counts['job_count'],
        y=tech_counts['technology'],
        orientation='h',
        text=tech_counts['job_count'],
        textposition='auto',
        marker=dict(
            color=tech_counts['job_count'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Job Count")
        ),
        hovertemplate='<b>%{y}</b><br>' +
                      'Jobs: %{x}<br>' +
                      '<extra></extra>'
    ))

    fig.update_layout(
        title=f'Top {top_n} Most In-Demand Technologies',
        xaxis_title='Number of Job Postings',
        yaxis_title='Technology',
        height=max(500, top_n * 25),
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )

    return fig


def plot_technology_trends(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create line chart showing technology popularity trends over time.

    Args:
        df: DataFrame with technology, snapshot_date, and job_count
        top_n: Number of top technologies to show

    Returns:
        Plotly figure
    """
    if df.empty or 'snapshot_date' not in df.columns:
        return _empty_figure("No technology trend data available")

    # Get top N technologies by total job count
    top_techs = df.groupby('technology')['job_count'].sum().nlargest(top_n).index

    # Filter to only top technologies
    df_top = df[df['technology'].isin(top_techs)].copy()

    if df_top.empty:
        return _empty_figure("Insufficient data for trends")

    fig = px.line(
        df_top,
        x='snapshot_date',
        y='job_count',
        color='technology',
        title=f'Technology Popularity Trends (Top {top_n})',
        labels={'snapshot_date': 'Date', 'job_count': 'Number of Jobs', 'technology': 'Technology'},
        markers=True
    )

    fig.update_layout(
        hovermode='x unified',
        height=500,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    return fig


def plot_technology_categories(df: pd.DataFrame) -> go.Figure:
    """
    Create pie chart of technology distribution by category.

    Args:
        df: DataFrame with category and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'category' not in df.columns:
        return _empty_figure("No category data available")

    # Group by category
    category_counts = df.groupby('category')['job_count'].sum().reset_index()
    category_counts = category_counts[category_counts['job_count'] > 0]

    if category_counts.empty:
        return _empty_figure("No valid category data")

    fig = px.pie(
        category_counts,
        values='job_count',
        names='category',
        title='Technology Distribution by Category',
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                      'Jobs: %{value}<br>' +
                      'Percentage: %{percent}<br>' +
                      '<extra></extra>'
    )

    fig.update_layout(height=400)

    return fig


def plot_technology_by_category(df: pd.DataFrame, top_per_category: int = 5) -> go.Figure:
    """
    Create grouped bar chart of top technologies per category.

    Args:
        df: DataFrame with technology, category, and job_count
        top_per_category: Number of top technologies to show per category

    Returns:
        Plotly figure
    """
    if df.empty:
        return _empty_figure("No technology data available")

    # Get top technologies per category
    top_techs = []

    for category in df['category'].unique():
        if pd.notna(category):
            cat_df = df[df['category'] == category].groupby('technology')['job_count'].sum().reset_index()
            cat_top = cat_df.nlargest(top_per_category, 'job_count')
            cat_top['category'] = category
            top_techs.append(cat_top)

    if not top_techs:
        return _empty_figure("No valid category data")

    df_top = pd.concat(top_techs, ignore_index=True)

    fig = px.bar(
        df_top,
        x='technology',
        y='job_count',
        color='category',
        title=f'Top {top_per_category} Technologies per Category',
        labels={'job_count': 'Number of Jobs', 'technology': 'Technology', 'category': 'Category'},
        barmode='group'
    )

    fig.update_layout(
        height=500,
        xaxis_tickangle=-45
    )

    return fig


def plot_technology_co_occurrence(df: pd.DataFrame, technology: str, top_n: int = 10) -> go.Figure:
    """
    Show which technologies most commonly appear with a given technology.

    Args:
        df: DataFrame with job technologies
        technology: The technology to analyze
        top_n: Number of co-occurring technologies to show

    Returns:
        Plotly figure
    """
    # This requires a different query structure - simplified version
    # In practice, you'd need to query job_technologies for co-occurrence
    return _empty_figure(f"Co-occurrence analysis for {technology} - Feature coming soon")


def create_technology_summary_table(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Create summary table of top technologies.

    Args:
        df: DataFrame with technology data
        top_n: Number of technologies to include

    Returns:
        Summary DataFrame
    """
    if df.empty:
        return pd.DataFrame()

    # Group by technology
    summary = df.groupby(['technology', 'category']).agg({
        'job_count': 'sum'
    }).reset_index()

    summary = summary.nlargest(top_n, 'job_count')
    summary = summary.rename(columns={
        'technology': 'Technology',
        'category': 'Category',
        'job_count': 'Job Count'
    })

    summary = summary.reset_index(drop=True)
    summary.index = summary.index + 1

    return summary


def plot_skill_demand_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create heatmap of skill demand over time.

    Args:
        df: DataFrame with technology, snapshot_date, and job_count

    Returns:
        Plotly figure
    """
    if df.empty or 'snapshot_date' not in df.columns:
        return _empty_figure("No temporal data available for heatmap")

    # Get top 15 technologies
    top_techs = df.groupby('technology')['job_count'].sum().nlargest(15).index

    # Filter and pivot
    df_top = df[df['technology'].isin(top_techs)]

    if df_top.empty:
        return _empty_figure("Insufficient data for heatmap")

    # Pivot to create heatmap data
    heatmap_data = df_top.pivot_table(
        index='technology',
        columns='snapshot_date',
        values='job_count',
        fill_value=0
    )

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[str(col) for col in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale='YlOrRd',
        hovertemplate='Technology: %{y}<br>Date: %{x}<br>Jobs: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title='Technology Demand Heatmap Over Time',
        xaxis_title='Date',
        yaxis_title='Technology',
        height=600
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
