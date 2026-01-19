import osmnx as ox
import geopandas as gpd

def get_osm_data(area_name):
    """
    Downloads building footprint data for a given area from OpenStreetMap.
    """
    tags = {"building": True}
    gdf = ox.features_from_place(area_name, tags)
    return gdf

def clean_and_enrich_data(gdf):
    """
    Cleans and enriches the GeoDataFrame with building data.
    """
    # Fill missing building:levels with a default value
    if 'building:levels' not in gdf.columns:
        gdf['building:levels'] = 2
    else:
        gdf['building:levels'].fillna(2, inplace=True)

    # Calculate building area
    gdf['area'] = gdf['geometry'].to_crs(epsg=3857).area

    # Classify buildings without usage tags based on area
    if 'building:use' not in gdf.columns:
        gdf['building:use'] = 'residential'
        gdf.loc[gdf['area'] > 200, 'building:use'] = 'commercial'

    return gdf
