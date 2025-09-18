import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def load_california_wildfires(db_path='../data/wild_fires.sqlite'):
    """
    Load California wildfire data for 2000-2015 with specific columns only
    """
    
    # Define the columns we want
    columns = [
        'FIRE_NAME',
        'STATE', 
        'FIRE_YEAR',
        'LATITUDE',
        'LONGITUDE',
        'FIRE_SIZE',
        'FIRE_SIZE_CLASS',
        'STAT_CAUSE_CODE',
        'STAT_CAUSE_DESCR'
    ]
    
    # SQL query to get exactly what we need
    query = f"""
    SELECT {', '.join(columns)}
    FROM Fires 
    WHERE STATE = 'CA' 
      AND FIRE_YEAR >= 2000 
      AND FIRE_YEAR <= 2015
    ORDER BY FIRE_YEAR, FIRE_SIZE DESC
    """
    
    try:
        print("Loading California wildfire data (2000-2015)...")
        
        # Connect and load data
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✓ Successfully loaded {len(df):,} California fires")
        print(f"✓ Years: {df['FIRE_YEAR'].min()}-{df['FIRE_YEAR'].max()}")
        print(f"✓ Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def explore_ca_data(df):
    """
    Quick exploration of California wildfire data
    """
    if df is None:
        return
    
    print("\n" + "="*50)
    print("CALIFORNIA WILDFIRE DATA SUMMARY")
    print("="*50)
    
    print(f"\nDataset Info:")
    print(f"  Total fires: {len(df):,}")
    print(f"  Years covered: {df['FIRE_YEAR'].min()}-{df['FIRE_YEAR'].max()}")
    print(f"  Total acres burned: {df['FIRE_SIZE'].sum():,.0f}")
    print(f"  Average fire size: {df['FIRE_SIZE'].mean():.1f} acres")
    
    print(f"\nFires by Year:")
    yearly_counts = df['FIRE_YEAR'].value_counts().sort_index()
    for year, count in yearly_counts.items():
        print(f"  {year}: {count:,} fires")
    
    print(f"\nFire Size Classes:")
    size_class_counts = df['FIRE_SIZE_CLASS'].value_counts()
    for size_class, count in size_class_counts.items():
        print(f"  Class {size_class}: {count:,} fires")
    
    print(f"\nTop 10 Fire Causes:")
    cause_counts = df['STAT_CAUSE_DESCR'].value_counts().head(10)
    for cause, count in cause_counts.items():
        print(f"  {cause}: {count:,} fires")
    
    print(f"\nLargest Fires (Top 5):")
    largest_fires = df.nlargest(5, 'FIRE_SIZE')
    for _, fire in largest_fires.iterrows():
        name = fire['FIRE_NAME'] if pd.notna(fire['FIRE_NAME']) else 'Unknown'
        print(f"  {fire['FIRE_YEAR']} - {name}: {fire['FIRE_SIZE']:,.0f} acres")
    
    print(f"\nMissing Data:")
    missing = df.isnull().sum()
    for col, missing_count in missing.items():
        if missing_count > 0:
            pct = (missing_count / len(df)) * 100
            print(f"  {col}: {missing_count:,} ({pct:.1f}%)")
    
    print(f"\nFirst 3 records:")
    print(df.head(3).to_string())

def create_fire_choropleth(df, metric='fire_count', year=None):
    """
    Create a choropleth map of California wildfire data
    
    Parameters:
    - df: DataFrame with wildfire data
    - metric: 'fire_count', 'total_acres', or 'avg_fire_size'
    - year: specific year to visualize (None for all years)
    """
    if df is None:
        print("No data available for visualization")
        return None
    
    # Filter by year if specified
    plot_df = df.copy()
    if year:
        plot_df = plot_df[plot_df['FIRE_YEAR'] == year]
        title_year = f" ({year})"
    else:
        title_year = " (2000-2015)"
    
    # Create latitude/longitude bins for choropleth-like effect
    # California roughly spans: 32.5°N to 42°N, -124.4°W to -114.1°W
    lat_bins = 20  # Number of latitude divisions
    lon_bins = 20  # Number of longitude divisions
    
    # Create bins
    plot_df['lat_bin'] = pd.cut(plot_df['LATITUDE'], bins=lat_bins, labels=False)
    plot_df['lon_bin'] = pd.cut(plot_df['LONGITUDE'], bins=lon_bins, labels=False)
    
    # Calculate bin centers for plotting
    lat_centers = pd.cut(plot_df['LATITUDE'], bins=lat_bins).apply(lambda x: x.mid)
    lon_centers = pd.cut(plot_df['LONGITUDE'], bins=lon_bins).apply(lambda x: x.mid)
    plot_df['lat_center'] = lat_centers
    plot_df['lon_center'] = lon_centers
    
    # Aggregate data by bins
    if metric == 'fire_count':
        agg_data = plot_df.groupby(['lat_bin', 'lon_bin', 'lat_center', 'lon_center']).size().reset_index(name='value')
        title = f"California Wildfire Count by Region{title_year}"
        colorbar_title = "Number of Fires"
    elif metric == 'total_acres':
        agg_data = plot_df.groupby(['lat_bin', 'lon_bin', 'lat_center', 'lon_center'])['FIRE_SIZE'].sum().reset_index(name='value')
        title = f"California Total Acres Burned by Region{title_year}"
        colorbar_title = "Total Acres Burned"
    elif metric == 'avg_fire_size':
        agg_data = plot_df.groupby(['lat_bin', 'lon_bin', 'lat_center', 'lon_center'])['FIRE_SIZE'].mean().reset_index(name='value')
        title = f"California Average Fire Size by Region{title_year}"
        colorbar_title = "Average Fire Size (Acres)"
    else:
        print("Invalid metric. Use 'fire_count', 'total_acres', or 'avg_fire_size'")
        return None
    
    # Create the choropleth-style map using scatter_mapbox
    fig = px.scatter_mapbox(
        agg_data,
        lat='lat_center',
        lon='lon_center',
        color='value',
        size='value',
        hover_data={'lat_center': ':.2f', 'lon_center': ':.2f'},
        color_continuous_scale='Reds',
        size_max=30,
        zoom=4.5,
        center=dict(lat=36.7, lon=-119.7),  # Center of California
        mapbox_style='open-street-map',
        title=title,
        labels={'value': colorbar_title}
    )
    
    fig.update_layout(
        height=700,
        title_font_size=16,
        coloraxis_colorbar=dict(title=colorbar_title)
    )
    
    return fig

def create_time_series_map(df):
    """
    Create an animated choropleth showing fire activity over time
    """
    if df is None:
        print("No data available for visualization")
        return None
    
    # Create bins for mapping
    lat_bins = 15
    lon_bins = 15
    
    df_viz = df.copy()
    df_viz['lat_bin'] = pd.cut(df_viz['LATITUDE'], bins=lat_bins, labels=False)
    df_viz['lon_bin'] = pd.cut(df_viz['LONGITUDE'], bins=lon_bins, labels=False)
    
    lat_centers = pd.cut(df_viz['LATITUDE'], bins=lat_bins).apply(lambda x: x.mid)
    lon_centers = pd.cut(df_viz['LONGITUDE'], bins=lon_bins).apply(lambda x: x.mid)
    df_viz['lat_center'] = lat_centers
    df_viz['lon_center'] = lon_centers
    
    # Aggregate by year and location
    yearly_data = df_viz.groupby(['FIRE_YEAR', 'lat_bin', 'lon_bin', 'lat_center', 'lon_center']).agg({
        'FIRE_SIZE': ['count', 'sum']
    }).reset_index()
    
    yearly_data.columns = ['FIRE_YEAR', 'lat_bin', 'lon_bin', 'lat_center', 'lon_center', 'fire_count', 'total_acres']
    
    # Create animated scatter plot
    fig = px.scatter_mapbox(
        yearly_data,
        lat='lat_center',
        lon='lon_center',
        color='fire_count',
        size='total_acres',
        animation_frame='FIRE_YEAR',
        hover_data={'fire_count': True, 'total_acres': ':.0f'},
        color_continuous_scale='Reds',
        size_max=25,
        zoom=4.5,
        center=dict(lat=36.7, lon=-119.7),
        mapbox_style='open-street-map',
        title='California Wildfire Activity Over Time (2000-2015)',
        labels={'fire_count': 'Number of Fires', 'total_acres': 'Total Acres Burned'}
    )
    
    fig.update_layout(
        height=700,
        title_font_size=16
    )
    
    return fig

def create_cause_bar_chart(df, top_n_causes=10):
    """
    Create a bar chart showing the top fire causes.
    """
    if df is None:
        print("No data available for visualization")
        return None
    
    # Get top N causes and their counts
    cause_counts = df['STAT_CAUSE_DESCR'].value_counts().head(top_n_causes)
    causes = cause_counts.index.tolist()
    counts = cause_counts.values.tolist()

    fig = go.Figure(go.Bar(
        x=causes,
        y=counts,
        text=counts,
        textposition='auto',
        marker_color='orangered'
    ))
    fig.update_layout(
        title="Top Fire Causes",
        xaxis_title="Cause",
        yaxis_title="Number of Fires",
        title_font_size=16,
        bargap=0.3,
        height=500
    )
    
    return fig
def save_data(df, filename='california_wildfires_2000_2015.csv'):
    """
    Save the data to CSV
    """
    if df is None:
        print("No data to save")
        return
    
    try:
        df.to_csv(filename, index=False)
        print(f"\n✓ Data saved to: {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def get_fires_by_year(df, year):
    """
    Get fires for a specific year
    """
    if df is None:
        return None
    
    year_data = df[df['FIRE_YEAR'] == year].copy()
    print(f"\n{year}: {len(year_data):,} fires, {year_data['FIRE_SIZE'].sum():,.0f} acres burned")
    return year_data

def get_large_fires(df, min_acres=1000):
    """
    Get fires larger than specified acres
    """
    if df is None:
        return None
    
    large_fires = df[df['FIRE_SIZE'] >= min_acres].copy()
    print(f"\nFires ≥{min_acres:,} acres: {len(large_fires):,}")
    return large_fires

# Main execution
if __name__ == "__main__":
    
    # Load the data
    df = load_california_wildfires()
    
    if df is not None:
        # Explore the data
        explore_ca_data(df)
        
        # Save to CSV
        # save_data(df)
        
        # Create visualizations
        print(f"\n" + "="*50)
        print("CREATING VISUALIZATIONS...")
        print("="*50)
        
        # Fire count choropleth
        # print("Creating fire count choropleth...")
        # fig1 = create_fire_choropleth(df, metric='fire_count')
        # if fig1:
        #     fig1.show()
        
        # Total acres choropleth
        print("Creating total acres burned choropleth...")
        fig2 = create_fire_choropleth(df, metric='total_acres')
        if fig2:
            fig2.show()
        
        # Time series animation
        # print("Creating time series animation...")
        # fig3 = create_time_series_map(df)
        # if fig3:
        #     fig3.show()
        
        # Fire causes map
        print("Creating fire causes comparison...")
        fig4 = create_cause_bar_chart(df)
        if fig4:
            fig4.show()
        
    else:
        print("Failed to load data. Check the database path.")
