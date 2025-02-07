##############################
# Load the necessary libraries
##############################

import os
import geopandas as gpd
from shapely.geometry import Point
from collections import defaultdict


###########################################
# Set Directory Paths and File Name Strings
###########################################

base_dir = r"C:\Users\natda\Desktop\NatDave\Academics\PhD_NU\RESEARCH\Traffic_Stress\Boston"

roads_filename = "street_network.shp"
nodes_filename = "nodes.shp"

roads_path = os.path.join(base_dir, roads_filename)
nodes_path = os.path.join(base_dir, nodes_filename)

############################
# Load the Road Network Data
############################

roads_gdf = gpd.read_file(roads_path)
if 'unique_id' in roads_gdf.columns and roads_gdf.index.name != 'unique_id':
    roads_gdf = roads_gdf.set_index('unique_id', drop=False)

print("Loaded roads_gdf with CRS:", roads_gdf.crs)

##############
# Create Nodes
##############

# Filter and create a dict for valid road segments
roads_dict = {}
for idx, row in roads_gdf.iterrows():
    qExclude = row.get('qExclude', 0)
    qNoAccess = row.get('qNoAccess', 0)
    geom = row.geometry

    # Only include valid segments in roads_dict
    if qExclude not in {1, 5} and qNoAccess != 1 and geom is not None:
        roads_dict[idx] = {
            'geometry': geom,
            'StOperNEU': row.get('StOperNEU', 0),
            'STREETNAME': row.get('STREETNAME', "")
        }

# Collect start and end points of valid road segments
endpoints_dict = defaultdict(list)
for sid, data in roads_dict.items():
    geom = data['geometry']

    # Handle geometry to get the very first and very last coordinates
    if geom.geom_type == "LineString":
        first_point = geom.coords[0]
        last_point = geom.coords[-1]
    elif geom.geom_type == "MultiLineString":
        first_point = geom.geoms[0].coords[0]     # Start of the first LineString
        last_point = geom.geoms[-1].coords[-1]    # End of the last LineString
    else:
        continue                                  # Skip unsupported geometries

    # Record the start and end points
    endpoints_dict[first_point].append(sid)
    endpoints_dict[last_point].append(sid)

# Identify potential intersections
nodes_list = []
node_id = 1

for pt, seg_ids in endpoints_dict.items():
    if len(seg_ids) >= 3:
        nodes_list.append({
            'NODE_ID': node_id,
            'INC_LINKS': seg_ids,
            'NUM_LINKS': len(seg_ids),
            'geometry': Point(pt)
        })
        node_id += 1

nodes_gdf = gpd.GeoDataFrame(nodes_list, crs=roads_gdf.crs)
nodes_gdf.to_file(nodes_path)
print(f"Saved {len(nodes_gdf)} nodes in total.")