import geopandas as gpd
import pandas as pd

def calculate_solar_suitability(gdf):
    """
    Calculates the solar suitability of each building.
    """
    # Placeholder logic: suitability is proportional to area
    gdf['solar_suitability'] = gdf['area'] / gdf['area'].max()
    return gdf

def estimate_demand(gdf):
    """
    Estimates the energy demand for each building.
    """
    # Placeholder logic: demand is proportional to area, with weights for usage
    weights = {'commercial': 1.5, 'residential': 1.0, 'school': 1.2, 'hospital': 1.5}
    
    # Ensure 'building:use' column exists and has a default value
    if 'building:use' not in gdf.columns:
        gdf['building:use'] = 'residential'
    gdf['building:use'].fillna('residential', inplace=True)
    
    # Calculate demand score
    gdf['demand_score'] = gdf.apply(
        lambda row: row['area'] * weights.get(row['building:use'], 1.0), 
        axis=1
    )
    return gdf

def run_optimization(gdf):
    """
    Runs the optimization algorithm to select solar stations and connect them.
    """
    # Placeholder logic: select top 10% of buildings with highest solar suitability
    num_stations = int(len(gdf) * 0.1)
    gdf_sorted = gdf.sort_values(by='solar_suitability', ascending=False)
    solar_stations = gdf_sorted.head(num_stations)
    
    # For now, just return the selected solar stations
    return solar_stations
