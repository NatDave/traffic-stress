import arcpy
import json
import os

# Set up paths
json_path = r"C:\Users\natdave\Downloads\refuge_islands.json"  # Input JSON file
output_gdb = r"C:\Users\natdave\Downloads\refuge_islands.gdb"  # Output Geodatabase
output_fc = "pedestrian_refuge_islands"  # Feature class name

# Create a geodatabase if it doesn't exist
if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Delete existing feature class if it exists
feature_class_path = os.path.join(output_gdb, output_fc)
if arcpy.Exists(feature_class_path):
    arcpy.Delete_management(feature_class_path)

# Read JSON data
with open(json_path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Extract nodes with pedestrian refuge islands (crossing:island=yes)
nodes = [
    node for node in json_data.get('elements', [])
    if node.get("type") == "node" and "lat" in node and "lon" in node
    and node.get("tags", {}).get("crossing:island") == "yes"
]

# Create feature class with POINT geometry (WGS84)
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POINT",
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84 CRS
)

# Collect unique fields from OSM tags
unique_fields = set()
for node in nodes:
    if "tags" in node:
        unique_fields.update(node["tags"].keys())

# Add fields to the feature class
for field in unique_fields:
    field_name = field.replace(":", "_")  # Ensure valid field names
    arcpy.AddField_management(feature_class_path, field_name, "TEXT")

# Insert data into the feature class
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@"] + [field.replace(":", "_") for field in unique_fields]) as cursor:
    for node in nodes:
        try:
            # Create geometry from lat/lon
            point_geometry = arcpy.PointGeometry(
                arcpy.Point(float(node["lon"]), float(node["lat"])),
                arcpy.SpatialReference(4326)
            )

            # Prepare row data
            row = [point_geometry]  # First value is geometry
            for field in unique_fields:
                field_value = node.get("tags", {}).get(field, None)
                row.append(field_value)

            # Insert the row
            cursor.insertRow(row)
        except Exception as e:
            print(f"Error processing node {node['id']}: {e}")

print(f"Pedestrian refuge islands successfully converted to GDB at: {output_gdb}")
