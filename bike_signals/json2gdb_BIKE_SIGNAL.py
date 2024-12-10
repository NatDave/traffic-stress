import arcpy
import json
import os

# Set up the JSON file path
json_path = r"C:\Users\................\signal.geojson"
output_gdb = r"C:\Users\...............\signal.gdb"
output_fc = "signals"

# Create a geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read JSON
with open(json_path, 'r') as file:
    json_data = json.load(file)

# Extract features (nodes) from GeoJSON
features = json_data.get('features', [])

# Define fields to map from tags in the GeoJSON
field_mapping = {
    "highway": "highway",
    "crossing": "crossing",
    "button_operated": "button_operated",
    "tactile_paving": "tactile_paving",
    "traffic_signals": "traffic_signals",
    "traffic_signals:direction": "traffic_signals_direction",
}

# Create feature class with the specified geometry type (POINT)
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POINT",
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84 coordinate system
)

# Path to the created feature class
feature_class_path = os.path.join(output_gdb, output_fc)

# Add fields to the feature class for each mapped field
for key in field_mapping.keys():
    arcpy.AddField_management(feature_class_path, field_mapping[key], "TEXT")

# Insert data into the feature class
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@", *field_mapping.values()]) as cursor:
    for feature in features:
        try:
            # Extract geometry (coordinates) for each feature
            coords = feature['geometry']['coordinates']
            lat = coords[1]
            lon = coords[0]
            
            # Create point geometry
            point_geometry = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))
            
            # Extract the properties/tags (if available) from the feature's properties
            properties = feature.get("properties", {})
            row = [point_geometry]  # Geometry comes first

            for key in field_mapping.keys():
                row.append(properties.get(key, None))  # Get field value or None if not present

            # Insert the row into the feature class
            cursor.insertRow(row)
        except Exception as e:
            print(f"Error processing feature {feature['id']}: {e}")
