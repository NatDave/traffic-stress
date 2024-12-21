###############################
# Load the necessary libraries
###############################

import math
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from collections import defaultdict
import pyproj

#############################
# Load the Road Network Data
#############################

roads_path = r"C:\Users\................\boston_streets.shp"
roads_gdf = gpd.read_file(roads_path)
# Set 'unique_id' as index for faster lookups later
if 'unique_id' in roads_gdf.columns and roads_gdf.index.name != 'unique_id':
    roads_gdf = roads_gdf.set_index('unique_id', drop=False)

##############################
# Create Junctions from Roads
##############################

exclude_terms = ["turnpike", "interstate", "i-", "express", "highway", "alley"]

# Build a quick lookup: unique_id -> (streetname, geometry)
road_info = {
    row['unique_id']: (row['STREETNAME'] or "", row.geometry)
    for idx, row in roads_gdf.iterrows()
}

endpoints_dict = defaultdict(list)

for uid, (streetname, geom) in road_info.items():
    if geom.geom_type == "LineString":
        start_coords = geom.coords[0]
        end_coords = geom.coords[-1]
    elif geom.geom_type == "MultiLineString":
        first_line = geom.geoms[0]
        start_coords = first_line.coords[0]
        end_coords = first_line.coords[-1]
    else:
        continue

    endpoints_dict[start_coords].append(uid)
    endpoints_dict[end_coords].append(uid)

junctions = []
j_id = 1

for point, segments in endpoints_dict.items():
    if len(segments) >= 3:  # 3+ segments form a junction
        seg_ids = []
        valid_junction = True
        for seg_id in segments:
            streetname, _ = road_info[seg_id]
            if any(term.lower() in streetname.lower() for term in exclude_terms):
                valid_junction = False
                break
            seg_ids.append(seg_id)

        if valid_junction:
            junctions.append({
                'Junc_ID': j_id,
                'Inc_Segs': seg_ids,
                'Num_Legs': len(seg_ids),
                'geometry': Point(point)
            })
            j_id += 1

junctions_gdf = gpd.GeoDataFrame(junctions, crs=roads_gdf.crs)
junctions_path = r"C:\Users\................\junctions.shp"
junctions_gdf.to_file(junctions_path)
print(f"Identified {len(junctions)} junctions.")

#########################
# Create Legs Dictionary
#########################

def calculate_bearing(junc_coord, line_geom):
    """
    Calculate bearing (0-360 degrees) from junction point along the segment.
    0° = North, increases clockwise.
    """
    x_j, y_j = junc_coord
    if line_geom.geom_type == "LineString":
        coords = line_geom.coords
    elif line_geom.geom_type == "MultiLineString":
        # Use first line
        coords = line_geom.geoms[0].coords
    else:
        return None

    start = coords[0]
    end = coords[-1]

    dist_to_start = (start[0] - x_j)**2 + (start[1] - y_j)**2
    dist_to_end = (end[0] - x_j)**2 + (end[1] - y_j)**2

    if dist_to_start < dist_to_end:
        dx = end[0] - x_j
        dy = end[1] - y_j
    else:
        dx = start[0] - x_j
        dy = start[1] - y_j

    angle_radians = math.atan2(dx, dy)
    bearing_degrees = math.degrees(angle_radians)
    if bearing_degrees < 0:
        bearing_degrees += 360
    return bearing_degrees

def point_from_bearing(junc_point, bearing_, radii=6):
    """
    Given a junction coordinate and a bearing, returns a point radii away in that direction.
    """
    x_j, y_j = junc_point
    point_x = x_j + radii * np.sin(math.radians(bearing_))
    point_y = y_j + radii * np.cos(math.radians(bearing_))
    return (point_x, point_y)

# Create legs_dict similar to Montreal code
legs_dict = {}

for idx, junc_row in junctions_gdf.iterrows():
    junc_id = junc_row['Junc_ID']
    junc_geom = junc_row.geometry
    junc_coord = (junc_geom.x, junc_geom.y)
    inc_segs = junc_row['Inc_Segs']

    legs_data = []
    for seg_id in inc_segs:
        if seg_id in roads_gdf.index:
            seg_streetname = roads_gdf.loc[seg_id, 'STREETNAME']
            seg_geom = roads_gdf.loc[seg_id, 'geometry']
            bearing = calculate_bearing(junc_coord, seg_geom)
            if bearing is not None:
                legs_data.append({
                    'links': [seg_id],
                    'STREETNAME': seg_streetname,
                    'avg_bearing': bearing
                })

    if len(legs_data) > 0:
        legs_df = pd.DataFrame(legs_data)
        legs_df = legs_df.sort_values('avg_bearing').reset_index(drop=True)
        legs_df['cc_rank'] = legs_df.index + 1
        legs_dict[junc_id] = {
            '_jcoord': junc_coord,
            '_jnodes': [junc_id],  # simplifying to single node
            'cc_junclegs_df': legs_df
        }
    else:
        legs_dict[junc_id] = {
            '_jcoord': junc_coord,
            '_jnodes': [junc_id],
            'cc_junclegs_df': pd.DataFrame(columns=['links', 'STREETNAME', 'avg_bearing', 'cc_rank'])
        }

print("legs_dict created.")

#############################
# Create Crossing Geometries
#############################

def create_crossings(legs_dict, roads_gdf, output_path):
    """
    Similar logic to Montreal code:
    Identify pairs of legs that form a valid crossing and create line geometries.
    """
    crossings_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries())
    crossings_gdf['geometry'] = None
    row_idx = 0

    # Offsets
    multi_junction_offset = 8
    single_junction_offset = 5

    for junc_id, junc_data in legs_dict.items():
        cc_junclegs_df = junc_data['cc_junclegs_df']
        via_coords = junc_data['_jcoord']

        if len(cc_junclegs_df) >= 3:
            num_legs = len(cc_junclegs_df)
            for i_ in range(num_legs):
                for j_ in range(num_legs):
                    if j_ != i_:
                        from_df = cc_junclegs_df.iloc[[i_]]
                        to_df = cc_junclegs_df.iloc[[j_]]
                        from_cc_ = from_df['cc_rank'].values[0]
                        to_cc_ = to_df['cc_rank'].values[0]

                        # Determine legs in between
                        num_leg_bein_crossed_ = ((to_cc_ - from_cc_) % num_legs) - 1

                        if num_leg_bein_crossed_ == 1:
                            # Identify crossed leg
                            crossed_cc_ = ((from_cc_ + num_leg_bein_crossed_ - 1) % num_legs) + 1
                            crossed_df = cc_junclegs_df.loc[cc_junclegs_df['cc_rank'] == crossed_cc_]

                            from_bear = from_df['avg_bearing'].values[0]
                            to_bear = to_df['avg_bearing'].values[0]
                            start_point = point_from_bearing(via_coords, from_bear, radii=6)
                            end_point = point_from_bearing(via_coords, to_bear, radii=6)
                            rels_geom = LineString([start_point, end_point])

                            offset_dist = multi_junction_offset if len(junc_data['_jnodes']) > 1 else single_junction_offset
                            try:
                                rels_geom_right_offset = rels_geom.parallel_offset(offset_dist, 'right', join_style=2, mitre_limit=2)
                            except:
                                rels_geom_right_offset = rels_geom

                            from_seg_ids = from_df['links'].values[0]
                            to_seg_ids = to_df['links'].values[0]
                            crossed_seg_ids = crossed_df['links'].values[0]

                            from_seg_id = from_seg_ids[0]
                            to_seg_id = to_seg_ids[0]
                            crossed_seg_id = crossed_seg_ids[0]

                            from_street = from_df['STREETNAME'].values[0]
                            to_street = to_df['STREETNAME'].values[0]
                            crossed_street = crossed_df['STREETNAME'].values[0]

                            # Populate GDF
                            crossings_gdf.at[row_idx, 'geometry'] = rels_geom_right_offset
                            crossings_gdf.at[row_idx, 'Junc_ID'] = junc_id
                            crossings_gdf.at[row_idx, 'from_rank'] = from_cc_
                            crossings_gdf.at[row_idx, 'to_rank'] = to_cc_
                            crossings_gdf.at[row_idx, 'xx_rank'] = crossed_cc_
                            crossings_gdf.at[row_idx, 'from_seg'] = from_seg_id
                            crossings_gdf.at[row_idx, 'to_seg'] = to_seg_id
                            crossings_gdf.at[row_idx, 'xx_seg'] = crossed_seg_id
                            crossings_gdf.at[row_idx, 'from_str'] = from_street
                            crossings_gdf.at[row_idx, 'to_str'] = to_street
                            crossings_gdf.at[row_idx, 'xx_str'] = crossed_street

                            row_idx += 1

    # Set CRS to match roads_gdf
    crossings_gdf.crs = roads_gdf.crs
    crossings_gdf.to_file(output_path)
    print(f"Saved {len(crossings_gdf)} crossings")

# Specify output path for crossings
crossings_path = r"C:\Users\................\crossings.shp"
create_crossings(legs_dict, roads_gdf, crossings_path)
