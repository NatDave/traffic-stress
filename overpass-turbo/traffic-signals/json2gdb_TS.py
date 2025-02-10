import arcpy
import json
import os

# Set up paths
json_path = r"C:\Users\natda\Downloads\export.json"
output_gdb = r"C:\Users\natda\Downloads\osm_signals.gdb"
output_fc = "osm_signals"

# Create a geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Delete existing feature class if it exists
feature_class_path = os.path.join(output_gdb, output_fc)
if arcpy.Exists(feature_class_path):
    arcpy.Delete_management(feature_class_path)

# Read JSON
with open(json_path, 'r') as file:
    json_data = json.load(file)

# Extract node data
nodes = json_data.get('elements', [])

# Create feature class with POINT geometry (WGS84)
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POINT",
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84 CRS
)

# Collect unique fields from all node tags
unique_fields = set()
for node in nodes:
    if "tags" in node:
        unique_fields.update(node["tags"].keys())

# Add unique fields to the feature class
for field in unique_fields:
    field_name = field.replace(":", "_")  # Replace colon for valid field names
    arcpy.AddField_management(feature_class_path, field_name, "TEXT")

# Insert data into the feature class
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@"] + [field.replace(":", "_") for field in unique_fields]) as cursor:
    for node in nodes:
        if node.get("type") == "node" and "lat" in node and "lon" in node:
            try:
                # Geometry setup
                point_geometry = arcpy.PointGeometry(
                    arcpy.Point(float(node["lon"]), float(node["lat"])),
                    arcpy.SpatialReference(4326)
                )

                # Prepare row data
                row = [point_geometry]  # Geometry as the first field
                for field in unique_fields:
                    field_value = node.get("tags", {}).get(field, None)
                    row.append(field_value)

                # Insert the row
                cursor.insertRow(row)
            except Exception as e:
                print(f"Error processing node {node['id']}: {e}")

print(f"GeoJSON data successfully converted to GDB at: {output_gdb}")
