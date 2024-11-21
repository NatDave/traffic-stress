from pyrosm import OSM
import geopandas as gpd

# Load the .osm.pbf file
osm = OSM("massachusetts.osm.pbf")

# Get all roads and their tags (no filtering)
roads = osm.get_data_by_custom_criteria(
    custom_filter={"highway": ["*"]},  # Capture all highway types
    filter_type="keep",                # Keep all attributes of roads
    keep_nodes=True                    # Keep intersection points as well
)

# Save as Shapefile for later use
roads.to_file("massachusetts_roads.shp")

# Inspect data
roads.head()