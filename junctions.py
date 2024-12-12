import geopandas as gpd
from collections import defaultdict
from shapely.geometry import Point
import math

# Function to calculate bearing between two points
def calculate_bearing(point1, point2):
    lon1, lat1 = map(math.radians, point1)
    lon2, lat2 = map(math.radians, point2)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

# Read the shapefile to get the road network data
roads_gdf = gpd.read_file(r"C:\Users\..............\boston_streets.shp")

# Extract segment endpoints (start and end coordinates)
endpoints_dict = defaultdict(list)

# Loop through each road segment and store start/end points
for idx, row in roads_gdf.iterrows():
    start_point = (row['Start_Lon'], row['Start_Lat'])
    end_point = (row['End_Lon'], row['End_Lat'])
    endpoints_dict[start_point].append(row['unique_id'])
    endpoints_dict[end_point].append(row['unique_id'])

# Identify junctions where 3 or more segments meet
junctions = {}
j_id = 1

for point, segments in endpoints_dict.items():
    if len(segments) >= 3:
        legs_data = []  # Store data for ccw_junclegs_df
        for seg_id in segments:
            segment = roads_gdf.loc[roads_gdf['unique_id'] == seg_id].iloc[0]
            other_point = (segment['End_Lon'], segment['End_Lat']) if (segment['Start_Lon'], segment['Start_Lat']) == point else (segment['Start_Lon'], segment['Start_Lat'])
            bearing = calculate_bearing(point, other_point)
            legs_data.append({
                'ccw_rank': None,  # Placeholder for now
                'avg_bearing': bearing,
                'links': [seg_id]
            })
        
        # Sort legs by bearing in descending order (for CCW sorting) and assign ccw_rank
        legs_data.sort(key=lambda leg: -leg['avg_bearing'])  # Descending order for CCW
        for rank, leg in enumerate(legs_data, start=1):
            leg['ccw_rank'] = rank
        
        # Store junction details
        junctions[j_id] = {
            'coordinates': point,
            'segments': segments,
            'ccw_junclegs_df': legs_data
        }
        j_id += 1

# Create a GeoDataFrame for junctions
junction_rows = []
for jid, data in junctions.items():
    point = data['coordinates']
    junction_rows.append({
        'j_id': jid,
        'geometry': Point(point)
    })

junctions_gdf = gpd.GeoDataFrame(junction_rows, crs=roads_gdf.crs)

# Save the junctions as a shapefile
junctions_gdf.to_file(r"C:\Users\.............\junctions_ccw.shp")

print(f"Identified {len(junctions)} junctions.")
