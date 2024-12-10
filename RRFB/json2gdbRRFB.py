import arcpy
import json
import os

# File paths
geojson_path = r"C:\Users\..............\rrfb.geojson"
output_gdb = r"C:\Users\................\rrfb.gdb"
output_fc = "RRFB"

# Create a file geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read GeoJSON
with open(geojson_path, 'r') as file:
    geojson_data = json.load(file)

# Extract features
features = geojson_data.get('features', [])

# Create the feature class
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POINT",
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84
)

# Path to feature class
feature_class_path = os.path.join(output_gdb, output_fc)

# Add fields
fields_to_add = [
    "bicycle", "crossing", "crossing_island", "crossing_markings",
    "crossing_signals", "flashing_lights", "highway",
    "kerb", "tactile_paving", "traffic_calming"
]

for field in fields_to_add:
    arcpy.AddField_management(feature_class_path, field, "TEXT")

# Insert data
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@", *fields_to_add]) as cursor:
    for feature in features:
        try:
            # Get geometry
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            point_geometry = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))

            # Get properties
            properties = feature.get('properties', {})
            row = [point_geometry]
            for field in fields_to_add:
                # Replace ':' in field names to match the property keys
                key = field.replace("_", ":") if ":" in properties else field
                row.append(properties.get(key, None))

            # Insert row
            cursor.insertRow(row)
        except Exception as e:
            print(f"Error processing feature {feature['id']}: {e}")
