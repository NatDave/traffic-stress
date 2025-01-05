###############################
# Load the necessary libraries
###############################

import math
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from collections import defaultdict

############################################
# Set Directory Paths and File Name Strings
############################################

base_dir = r"C:\Users\natda\Desktop\NatDave\...........\boston_LTS"
roads_filename = "boston_streets.shp"
junctions_filename = "junctions.shp"
crossings_filename = "crossings.shp"

roads_path = f"{base_dir}\\{roads_filename}"
junctions_path = f"{base_dir}\\{junctions_filename}"
crossings_path = f"{base_dir}\\{crossings_filename}"

#############################
# Load the Road Network Data
#############################

roads_gdf = gpd.read_file(roads_path)

# Set 'unique_id' as index for faster lookups
if 'unique_id' in roads_gdf.columns and roads_gdf.index.name != 'unique_id':
    roads_gdf = roads_gdf.set_index('unique_id', drop=False)

print("Loaded roads_gdf with CRS:", roads_gdf.crs)

##############################
# Create Junctions from Roads
##############################

# Build a quick lookup: unique_id -> (qExclude, qNoAccess, geometry)
road_info = {}
for idx, row in roads_gdf.iterrows():
    u_id = row['unique_id']
    qExclude = row.get('qExclude', 0)    # Default to 0 if not present
    qNoAccess = row.get('qNoAccess', 0)  # Default to 0 if not present
    geom = row.geometry
    road_info[u_id] = (qExclude, qNoAccess, geom)

# Collect the endpoints in a dictionary
# Key = endpoint coords, Value = list of segment IDs that touch this endpoint
endpoints_dict = defaultdict(list)

for seg_id, (qExclude, qNoAccess, geom) in road_info.items():
    # Skip inaccessible roads
    if qExclude == 1 or qNoAccess == 1:
        continue

    if geom is None:
        continue

    if geom.geom_type == "LineString":
        coords = geom.coords
    elif geom.geom_type == "MultiLineString":
        if len(geom.geoms) > 0:
            coords = geom.geoms[0].coords
        else:
            continue
    else:
        continue

    if len(coords) < 2:
        continue

    start_coords = coords[0]        # first point
    end_coords = coords[-1]         # last point

    endpoints_dict[start_coords].append(seg_id)
    endpoints_dict[end_coords].append(seg_id)

# Build a list of junction records
junctions_list = []
junction_id = 1

for point_coords, seg_ids_at_pt in endpoints_dict.items():
    if len(seg_ids_at_pt) >= 3:  # 3+ segments => a potential junction
        seg_ids_filtered = []
        valid_junction = True
        for sid in seg_ids_at_pt:
            qExclude, qNoAccess, _ = road_info[sid]
            # Exclude if qExclude or qNoAccess is 1
            if qExclude == 1 or qNoAccess == 1:
                valid_junction = False
                break
            seg_ids_filtered.append(sid)

        if valid_junction:
            junctions_list.append({
                'JUNC_ID': junction_id,
                'INC_SEGS': seg_ids_filtered,   # Store segment IDs
                'NUM_LEGS': len(seg_ids_filtered),
                'geometry': Point(point_coords)
            })
            junction_id += 1

# Create a GeoDataFrame for the junctions
junctions_gdf = gpd.GeoDataFrame(junctions_list, crs=roads_gdf.crs)
junctions_gdf.to_file(junctions_path)
print(f"Identified {len(junctions_gdf)} junctions.")
print(f"Saved junctions to: {junctions_path}")


#########################
# Create Legs Dictionary
#########################

def calc_bearing(junction_xy, line_geom):
    """
    Calculate bearing (0-360 degrees) from the junction outward along the segment.
    0° = North, increases clockwise.
    """
    x_j, y_j = junction_xy

    # Extract coords from geometry
    if line_geom.geom_type == "LineString":
        coords = line_geom.coords
    elif line_geom.geom_type == "MultiLineString":
        if len(line_geom.geoms) > 0:
            coords = line_geom.geoms[0].coords
        else:
            return None
    else:
        return None

    if len(coords) < 2:
        return None

    start_pt = coords[0]
    end_pt = coords[-1]

    # Figure out which endpoint is closer to the junction
    dist_start = (start_pt[0] - x_j)**2 + (start_pt[1] - y_j)**2
    dist_end   = (end_pt[0] - x_j)**2 + (end_pt[1] - y_j)**2

    if dist_start < dist_end:
        # The line "starts" at the junction, so bearing is junction->end
        dx = end_pt[0] - x_j
        dy = end_pt[1] - y_j
    else:
        # The line "ends" at the junction, so bearing is junction->start
        dx = start_pt[0] - x_j
        dy = start_pt[1] - y_j

    angle_rad = math.atan2(dx, dy)
    bearing_deg = math.degrees(angle_rad)
    if bearing_deg < 0:
        bearing_deg += 360

    return bearing_deg

def point_from_bearing(junction_xy, bearing_deg, dist_m=6):
    """
    Return a point dist_m meters away from the junction_xy at the given bearing (deg).
    0° = North; angle increases clockwise.
    """
    x_j, y_j = junction_xy
    theta = math.radians(bearing_deg)
    dx = dist_m * math.sin(theta)
    dy = dist_m * math.cos(theta)
    return (x_j + dx, y_j + dy)

# Build a dictionary keyed by JUNC_ID, storing a DataFrame of legs
legs_dict = {}

for idx, junc_row in junctions_gdf.iterrows():
    j_id = junc_row['JUNC_ID']
    j_geom = junc_row.geometry
    j_xy = (j_geom.x, j_geom.y)
    incident_segs = junc_row['INC_SEGS']

    leg_records = []
    for seg_id in incident_segs:
        if seg_id in roads_gdf.index:
            st_name = roads_gdf.loc[seg_id, 'STREETNAME']
            seg_geom = roads_gdf.loc[seg_id, 'geometry']
            brg = calc_bearing(j_xy, seg_geom)
            if brg is not None:
                leg_records.append({
                    'LINKS': [seg_id],      # list of segment IDs
                    'ST_NAME': st_name,     # street name
                    'AVG_BRG': brg          # bearing of the segmenmt
                })

    if len(leg_records) > 0:
        legs_df = pd.DataFrame(leg_records)
        # Sort by bearing descending, so 360 deg (North) is first, going counterclockwise
        legs_df = legs_df.sort_values('AVG_BRG', ascending=False).reset_index(drop=True)
        # Create a rank
        legs_df['CC_RANK'] = legs_df.index + 1

        legs_dict[j_id] = {
            'JUNC_XY': j_xy,
            'J_NODES': [j_id],  # single node for simplicity
            'LEGS_DF': legs_df
        }
    else:
        # Empty DataFrame if no legs
        legs_dict[j_id] = {
            'JUNC_XY': j_xy,
            'J_NODES': [j_id],
            'LEGS_DF': pd.DataFrame(columns=['LINKS', 'ST_NAME', 'AVG_BRG', 'CC_RANK'])
        }

print("legs_dict created with bearing info for each junction.")

#############################
# Create Crossing Geometries
#############################

def create_crossings(legs_dictionary, roads_geo_df, out_path):
    """
    Identify pairs of legs forming valid crossings (Montreal logic),
    create line geometries, and offset for visualization.
    """
    cross_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries())
    cross_gdf['geometry'] = None
    row_idx = 0

    # Offsets in meters
    offset_multi = 8
    offset_singl = 5

    for j_id, j_data in legs_dictionary.items():
        legs_df = j_data['LEGS_DF']
        junc_xy = j_data['JUNC_XY']

        # We only create crossings if 3+ legs
        if len(legs_df) >= 3:
            n_legs = len(legs_df)
            for i_ in range(n_legs):
                for j_ in range(n_legs):
                    if i_ == j_:
                        continue

                    from_leg = legs_df.iloc[[i_]]
                    to_leg   = legs_df.iloc[[j_]]

                    from_rank = from_leg['CC_RANK'].values[0]
                    to_rank   = to_leg['CC_RANK'].values[0]

                    # Determine how many legs are between them
                    num_between = ((to_rank - from_rank) % n_legs) - 1

                    # If there's exactly 1 leg between => crossing
                    if num_between == 1:
                        # Identify the crossed leg
                        crossed_rank = ((from_rank + num_between - 1) % n_legs) + 1
                        crossed_leg = legs_df.loc[legs_df['CC_RANK'] == crossed_rank]

                        from_brg = from_leg['AVG_BRG'].values[0]
                        to_brg   = to_leg['AVG_BRG'].values[0]

                        # Build the line geometry
                        start_pt = point_from_bearing(junc_xy, from_brg, dist_m=6)
                        end_pt   = point_from_bearing(junc_xy, to_brg,   dist_m=6)
                        cross_line = LineString([start_pt, end_pt])

                        # Offset line for visualization
                        # If multiple junction nodes, offset a bit more
                        if len(j_data['J_NODES']) > 1:
                            offset_dist = offset_multi
                        else:
                            offset_dist = offset_singl

                        try:
                            cross_line_off = cross_line.parallel_offset(offset_dist, 'right', join_style=2, mitre_limit=2)
                        except:
                            cross_line_off = cross_line

                        # Extract segment IDs
                        from_links = from_leg['LINKS'].values[0]  # e.g. [seg_id]
                        to_links   = to_leg['LINKS'].values[0]
                        xcd_links  = crossed_leg['LINKS'].values[0]

                        from_seg = from_links[0]
                        to_seg   = to_links[0]
                        xcd_seg  = xcd_links[0]

                        # Extract street names
                        from_stnm = from_leg['ST_NAME'].values[0]
                        to_stnm   = to_leg['ST_NAME'].values[0]
                        xcd_stnm  = crossed_leg['ST_NAME'].values[0]

                        # Populate cross_gdf
                        cross_gdf.at[row_idx, 'geometry']   = cross_line_off
                        cross_gdf.at[row_idx, 'JUNC_ID']    = j_id
                        cross_gdf.at[row_idx, 'FRM_RANK']   = from_rank
                        cross_gdf.at[row_idx, 'TO_RANK']    = to_rank
                        cross_gdf.at[row_idx, 'CRS_RANK']   = crossed_rank
                        cross_gdf.at[row_idx, 'FRM_SEG']    = from_seg
                        cross_gdf.at[row_idx, 'TO_SEG']     = to_seg
                        cross_gdf.at[row_idx, 'CRS_SEG']    = xcd_seg
                        cross_gdf.at[row_idx, 'FRM_STNM']   = from_stnm
                        cross_gdf.at[row_idx, 'TO_STNM']    = to_stnm
                        cross_gdf.at[row_idx, 'CRS_STNM']   = xcd_stnm

                        row_idx += 1

    # Match the CRS of roads
    cross_gdf.crs = roads_geo_df.crs
    cross_gdf.to_file(out_path)
    print(f"Saved {len(cross_gdf)} crossings to {out_path}")


#########################
# Run Crossing Creation
#########################

create_crossings(legs_dict, roads_gdf, crossings_path)
