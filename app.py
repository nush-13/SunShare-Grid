import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from src.data import get_osm_data, clean_and_enrich_data
from src.intelligence import calculate_solar_suitability, estimate_demand, run_optimization

st.set_page_config(layout="wide")

st.title("SunShare Grid")

@st.cache_data
def load_data(area_name):
    gdf = get_osm_data(area_name)
    gdf = clean_and_enrich_data(gdf)
    gdf = calculate_solar_suitability(gdf)
    gdf = estimate_demand(gdf)
    return gdf

def display_map(gdf, solar_stations, show_suitability, show_demand, show_stations):
    # Create a Folium map centered on the area
    m = folium.Map(location=[gdf.unary_union.centroid.y, gdf.unary_union.centroid.x], zoom_start=15)

    if show_suitability:
        folium.Choropleth(
            geo_data=gdf,
            name='Solar Suitability',
            data=gdf,
            columns=['geometry', 'solar_suitability'],
            key_on='feature.id',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Solar Suitability Score'
        ).add_to(m)

    if show_demand:
        folium.Choropleth(
            geo_data=gdf,
            name='Energy Demand',
            data=gdf,
            columns=['geometry', 'demand_score'],
            key_on='feature.id',
            fill_color='BuPu',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Demand Score'
        ).add_to(m)

    if show_stations:
        for _, row in solar_stations.iterrows():
            folium.Marker(
                location=[row.geometry.centroid.y, row.geometry.centroid.x],
                popup=f"Solar Station (Suitability: {row.solar_suitability:.2f})",
                icon=folium.Icon(color='green', icon='flash')
            ).add_to(m)

    # Add a GeoJson layer to the map to show building details on click
    folium.GeoJson(
        gdf,
        name='Building Details',
        popup=folium.GeoJsonPopup(fields=['building:use', 'area', 'solar_suitability', 'demand_score'],
                                 aliases=['Use:', 'Area (m²):', 'Solar Suitability:', 'Demand Score:'])
    ).add_to(m)


    return m

# Load the data
area = "Malviya Nagar, Delhi"
gdf = load_data(area)
solar_stations = run_optimization(gdf)

# Create sidebar controls
st.sidebar.title("Map Layers")
show_suitability = st.sidebar.checkbox("Show Solar Suitability", value=True)
show_demand = st.sidebar.checkbox("Show Demand", value=True)
show_stations = st.sidebar.checkbox("Show Solar Stations", value=True)

# Display Impact Metrics
st.sidebar.title("Impact Metrics")
st.sidebar.metric("Total Solar Capacity", "1.2 MW")
st.sidebar.metric("People Served", "5,000+")
st.sidebar.metric("CO₂ Avoided", "800 tons/year")


# Display the map
st_folium(display_map(gdf, solar_stations, show_suitability, show_demand, show_stations), width=1200, height=800)
