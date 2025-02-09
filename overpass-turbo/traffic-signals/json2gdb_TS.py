import arcpy
import json
import os

# Set up the JSON file path
json_path = r"C:\Users\.............\boston_signals.json"
output_gdb = r"C:\Users\.............\boston_signals.gdb"
output_fc = "boston_signals"

# Create a geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read JSON
with open(json_path, 'r') as file:
    json_data = json.load(file)

# Extract node data
nodes = json_data.get('elements', [])

# Define fields to map from tags
field_mapping = {
    "highway": "highway",
    "crossing": "crossing",
    "button_operated": "button_operated",
    "tactile_paving": "tactile_paving",
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
    for node in nodes:
        # Process only nodes with latitude, longitude
        if node.get("type") == "node" and "lat" in node and "lon" in node:
            try:
                # Extract geometry as a point
                lat = float(node["lat"])
                lon = float(node["lon"])
                point_geometry = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))

                # Extract the properties/tags
                tags = node.get("tags", {})
                row = [point_geometry]  # Geometry comes first
                for key in field_mapping.keys():
                    row.append(tags.get(key, None))  # Map tag data into respective fields

                # Insert the row into the feature class
                cursor.insertRow(row)
            except Exception as e:
                print(f"Error processing node {node['id']}: {e}")
