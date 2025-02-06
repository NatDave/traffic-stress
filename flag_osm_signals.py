import geopandas as gpd
import os

import warnings
warnings.filterwarnings('ignore')

# Base directory path
base_path = r"C:\Users\natdave\...........\"

# File paths
city_boston_path = os.path.join(base_path, "traffic_signals.shp")
osm_gdb_path = os.path.join(base_path, "boston_signals.gdb")
output_path = os.path.join(base_path, "flagged_osm_signal.shp")

# Load the shapefile and gdb as GeoDataFrames
city_boston_signals = gpd.read_file(city_boston_path)
osm_signals = gpd.read_file(osm_gdb_path)

# Reproject to EPSG:6491 (Massachusetts Mainland CRS)
city_boston_signals = city_boston_signals.to_crs(epsg=6491)
osm_signals = osm_signals.to_crs(epsg=6491)

# Perform a spatial join to find OSM signals within 25 meters of City of Boston signals
join_result = gpd.sjoin_nearest(
    osm_signals, 
    city_boston_signals, 
    how='left', 
    max_distance=xx,
    distance_col='distance'
)

# Filter out points where no nearby City of Boston signal was found (NaN means no match within xx meters)
flagged_osm_signal = join_result[join_result['index_right'].isna()]

# Save the flagged points as a new shapefile
flagged_osm_signal.to_file(output_path, driver='ESRI Shapefile')

print(f"Flagged OSM signals saved.")
print(f"Number of flagged OSM signals: {len(flagged_osm_signal)}")
