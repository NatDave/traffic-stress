###############################
# Load the necessary libraries
###############################

import math
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from collections import defaultdict

############################################
# Set Directory Paths and File Name Strings
############################################

base_dir = r"C:\Users\NatDave\Desktop\------------"
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
if 'unique_id' in roads_gdf.columns and roads_gdf.index.name != 'unique_id':
    roads_gdf = roads_gdf.set_index('unique_id', drop=False)

print("Loaded roads_gdf with CRS:", roads_gdf.crs)

#######################
# Create Intersections
#######################

roads_dict = {}
for idx, row in roads_gdf.iterrows():
    roads_dict[idx] = {
        'qExclude': row.get('qExclude', 0),
        'qNoAccess': row.get('qNoAccess', 0),
        'geometry': row.geometry,
        'StOperNEU': row.get('StOperNEU', 0),
        'STREETNAME': row.get('STREETNAME', "")
    }

endpoints_dict = defaultdict(list)
for sid, data in roads_dict.items():
    qExclude, qNoAccess = data['qExclude'], data['qNoAccess']
    geom = data['geometry']
    if qExclude == 1 or qNoAccess == 1 or geom is None:
        continue

    # Handle geometry to get start/end coords
    if geom.geom_type == "LineString":
        coords = geom.coords
    elif geom.geom_type == "MultiLineString" and len(geom.geoms) > 0:
        coords = geom.geoms[0].coords
    else:
        continue

    if len(coords) < 2:
        continue

    endpoints_dict[coords[0]].append(sid)
    endpoints_dict[coords[-1]].append(sid)

# Identify potential intersections
junctions_list = []
junction_id = 1

for pt, seg_ids in endpoints_dict.items():
    if len(seg_ids) >= 3:
        seg_ids_filtered = []
        valid = True
        for sid in seg_ids:
            rd = roads_dict[sid]
            if rd['qExclude'] == 1 or rd['qNoAccess'] == 1:
                valid = False
                break
            seg_ids_filtered.append(sid)
        if valid:
            junctions_list.append({
                'JUNC_ID': junction_id,
                'INC_LINKS': seg_ids_filtered,
                'NUM_LINKS': len(seg_ids_filtered),
                'geometry': Point(pt)
            })
            junction_id += 1

def merge_close_nodes_and_add_standalones(junctions, roads, threshold):
    """
    Merge nodes within 'threshold' distance if they're on a divided highway.
    Exclude nodes in prevent_merge_ids from being part of any merging cluster.
    Otherwise, keep them as separate intersections.
    """
    merged_junctions = []
    standalone_junctions = []
    processed = set()

    # Define IDs to prevent from merging
    prevent_merge_ids = {7718, 10131, 4837}

    for idx, junc in junctions.iterrows():
        # Skip processing if node ID is in prevention list
        if junc['JUNC_ID'] in prevent_merge_ids:
            standalone_junctions.append({
                'INTER_ID': junc['JUNC_ID'],
                'INC_LINKS': junc['INC_LINKS'],
                'NUM_LINKS': junc['NUM_LINKS'],
                'geometry': junc.geometry,
                'WAS_MERGED': False
            })
            processed.add(idx)
            continue

        if idx in processed:
            continue

        # Find nodes within threshold, excluding those in prevention list
        close_nodes = junctions[
            (junctions.geometry.distance(junc.geometry) <= threshold) & 
            (~junctions['JUNC_ID'].isin(prevent_merge_ids))
        ]
        inc_links = []
        valid_merge = False

        for cn in close_nodes.itertuples():
            for sid in cn.INC_LINKS:
                rd = roads[sid]
                geom = rd['geometry']
                if rd['StOperNEU'] == 11:
                    valid_merge = True
                if geom.geom_type == "LineString" and geom.length > threshold:
                    inc_links.append(sid)
                elif geom.geom_type == "MultiLineString":
                    if any(line.length > threshold for line in geom.geoms):
                        inc_links.append(sid)

        # Check if merging will result in at least three legs
        if valid_merge and len(close_nodes) > 1 and len(set(inc_links)) >= 3:
            mg = unary_union(close_nodes.geometry)
            merged_junctions.append({
                'INTER_ID': junc['JUNC_ID'],
                'INC_LINKS': list(set(inc_links)),
                'NUM_LINKS': len(set(inc_links)),
                'geometry': mg.centroid,
                'WAS_MERGED': True
            })
            processed.update(close_nodes.index)
        else:
            standalone_junctions.append({
                'INTER_ID': junc['JUNC_ID'],
                'INC_LINKS': junc['INC_LINKS'],
                'NUM_LEGS': len(junc['INC_LINKS']),
                'geometry': junc.geometry,
                'WAS_MERGED': False
            })
            processed.add(idx)

    mgdf = gpd.GeoDataFrame(merged_junctions, geometry='geometry', crs=junctions.crs)
    sgdf = gpd.GeoDataFrame(standalone_junctions, geometry='geometry', crs=junctions.crs)
    return pd.concat([mgdf, sgdf], ignore_index=True)

junctions_gdf = gpd.GeoDataFrame(junctions_list, crs=roads_gdf.crs)
junctions_gdf = merge_close_nodes_and_add_standalones(junctions_gdf, roads_dict, threshold=27)
junctions_gdf.to_file(junctions_path)
print(f"Intersections saved: {len(junctions_gdf)} total.")

#########################
# Create Legs Dictionary
#########################

def calc_bearing(jxy, geom):
    """Compute bearing (0 to 360°, north=0) from intersection jxy outward."""
    if geom.geom_type == "LineString":
        coords = geom.coords
    elif geom.geom_type == "MultiLineString" and len(geom.geoms) > 0:
        coords = geom.geoms[0].coords
    else:
        return None

    if len(coords) < 2:
        return None

    sx, sy = coords[0]
    ex, ey = coords[-1]

    ds = (sx - jxy[0])**2 + (sy - jxy[1])**2
    de = (ex - jxy[0])**2 + (ey - jxy[1])**2

    if ds < de:
        dx, dy = ex - jxy[0], ey - jxy[1]
    else:
        dx, dy = sx - jxy[0], sy - jxy[1]

    angle_rad = math.atan2(dx, dy)
    deg = math.degrees(angle_rad)
    return deg + 360 if deg < 0 else deg

def point_from_bearing(jxy, bearing_deg, dist_m=6):
    """Compute a point dist_m away from jxy at bearing_deg (0=North, clockwise)."""
    theta = math.radians(bearing_deg)
    return (
        jxy[0] + dist_m * math.sin(theta),
        jxy[1] + dist_m * math.cos(theta)
    )

legs_dict = {}
for _, row in junctions_gdf.iterrows():
    j_id = row['INTER_ID']
    jxy = (row.geometry.x, row.geometry.y)
    INC_LINKS = row['INC_LINKS']

    # 1) Build raw_legs
    raw_legs = []
    for sid in INC_LINKS:
        rd = roads_dict[sid]
        geom    = rd['geometry']
        st_name = rd['STREETNAME']
        divided = (rd['StOperNEU'] == 11)

        brg = calc_bearing(jxy, geom)
        if brg is not None:
            raw_legs.append({
                'LINKS': [sid],
                'ST_NAME': st_name,
                'AVG_BRG': brg,
                'DIVIDED': divided
            })

    # 2) Sort by bearing if not empty
    df = pd.DataFrame(raw_legs)
    if not df.empty and 'AVG_BRG' in df.columns:
        df = df.sort_values('AVG_BRG', ascending=False).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=['LINKS','ST_NAME','AVG_BRG','DIVIDED'])

    # 3) Merge adjacent divided links if n>3
    combined_legs = []
    used = set()
    n = len(df)

    if n > 3:
        for i in range(n):
            if i in used:
                continue
            leg_i = df.iloc[i].to_dict()
            j = (i + 1) % n
            if j not in used and n > 1:
                leg_j = df.iloc[j].to_dict()
                if leg_i['DIVIDED'] and leg_j['DIVIDED'] and leg_i['ST_NAME'] == leg_j['ST_NAME']:
                    combined_legs.append({
                        'LINKS': leg_i['LINKS'] + leg_j['LINKS'],
                        'ST_NAME': leg_i['ST_NAME'],
                        'AVG_BRG': (leg_i['AVG_BRG'] + leg_j['AVG_BRG']) / 2.0,
                        'DIVIDED': True
                    })
                    used.update([i, j])
                    continue
            combined_legs.append(leg_i)
            used.add(i)
    else:
        combined_legs = [df.iloc[k].to_dict() for k in range(n)]

    # 4) Re-sort final & assign rank
    if combined_legs:
        final_df = pd.DataFrame(combined_legs)
        if not final_df.empty and 'AVG_BRG' in final_df.columns:
            final_df = final_df.sort_values('AVG_BRG', ascending=False).reset_index(drop=True)
            final_df['CC_RANK'] = final_df.index + 1
        else:
            final_df = pd.DataFrame(columns=['LINKS','ST_NAME','AVG_BRG','DIVIDED','CC_RANK'])
    else:
        final_df = pd.DataFrame(columns=['LINKS','ST_NAME','AVG_BRG','DIVIDED','CC_RANK'])

    legs_dict[j_id] = {
        'INTERSECTION_XY': jxy,
        'J_NODES': [j_id],
        'LEGS_DF': final_df
    }

print("legs_dict created successfully.")

#############################
# Create Crossing Geometries
#############################

def create_crossings(legs_dictionary, roads_geo_df, out_path):
    cross_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries())
    cross_gdf['geometry'] = None
    offset = 5
    row_idx = 0

    for j_id, j_data in legs_dictionary.items():
        df = j_data['LEGS_DF']
        jxy = j_data['INTERSECTION_XY']

        if len(df) >= 3:
            n_legs = len(df)
            for i_ in range(n_legs):
                for j_ in range(n_legs):
                    if i_ == j_:
                        continue

                    leg_from = df.iloc[i_].to_dict()
                    leg_to   = df.iloc[j_].to_dict()
                    fr_rank  = leg_from.get('CC_RANK', 9999)
                    to_rank  = leg_to.get('CC_RANK', 9999)
                    num_between = ((to_rank - fr_rank) % n_legs) - 1

                    if num_between == 1:
                        x_rank = ((fr_rank + num_between - 1) % n_legs) + 1
                        leg_x  = df.loc[df['CC_RANK'] == x_rank]
                        if leg_x.empty:
                            continue
                        leg_xd = leg_x.iloc[0].to_dict()

                        fb, tb = leg_from['AVG_BRG'], leg_to['AVG_BRG']
                        if not (isinstance(fb, (int, float)) and isinstance(tb, (int, float))):
                            continue

                        sp = point_from_bearing(jxy, fb, 6)
                        ep = point_from_bearing(jxy, tb, 6)
                        line = LineString([sp, ep])

                        try:
                            line_off = line.parallel_offset(offset, 'right', join_style=2, mitre_limit=2)
                        except:
                            line_off = line

                        cross_gdf.at[row_idx, 'geometry']  = line_off
                        cross_gdf.at[row_idx, 'JUNC_ID']   = j_id
                        cross_gdf.at[row_idx, 'FRM_RANK']  = fr_rank
                        cross_gdf.at[row_idx, 'TO_RANK']   = to_rank
                        cross_gdf.at[row_idx, 'CRS_RANK']  = x_rank
                        cross_gdf.at[row_idx, 'FRM_LEG']   = str(leg_from['LINKS'])
                        cross_gdf.at[row_idx, 'TO_LEG']    = str(leg_to['LINKS'])
                        cross_gdf.at[row_idx, 'CRS_LEG']   = str(leg_xd['LINKS'])
                        cross_gdf.at[row_idx, 'FRM_STNM']  = leg_from['ST_NAME']
                        cross_gdf.at[row_idx, 'TO_STNM']   = leg_to['ST_NAME']
                        cross_gdf.at[row_idx, 'CRS_STNM']  = leg_xd['ST_NAME']
                        row_idx += 1

    cross_gdf.crs = roads_geo_df.crs
    cross_gdf.to_file(out_path)
    print(f"Saved {len(cross_gdf)} crossings to base directory.")

#########################
# Run Crossing Creation
#########################

create_crossings(legs_dict, roads_gdf, crossings_path)
