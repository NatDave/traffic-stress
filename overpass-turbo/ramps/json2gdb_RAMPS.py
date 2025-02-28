import arcpy
import json
import os

# Set up paths
json_path = r"C:\Users\natdave\Downloads\freeway_ramps.json"  # Input JSON file
output_gdb = r"C:\Users\natdave\Downloads\freeway_ramps.gdb"  # Output Geodatabase
output_fc = "freeway_ramps"  # Feature class name

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

# Extract ways tagged as freeway ramps (highway=motorway_link)
ways = [
    way for way in json_data.get('elements', [])
    if way.get("type") == "way" and "tags" in way and way["tags"].get("highway") == "motorway_link"
]

# Extract node coordinates from the JSON
nodes_dict = {
    node["id"]: (node["lon"], node["lat"])
    for node in json_data.get('elements', []) if node["type"] == "node"
}

# Check if ways and nodes exist
if not ways:
    raise ValueError("No freeway ramps (motorway_link) found in JSON. Check Overpass Turbo query!")
if not nodes_dict:
    raise ValueError("No nodes found in JSON! Ensure Overpass query includes (._; >;) to retrieve nodes.")

# Create feature class with POLYLINE geometry (EPSG:6491)
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POLYLINE",
    spatial_reference=arcpy.SpatialReference(6491)  # EPSG:6491
)

# Collect unique fields from OSM tags
unique_fields = set()
for way in ways:
    if "tags" in way:
        unique_fields.update(way["tags"].keys())

# Add fields to the feature class
for field in unique_fields:
    field_name = field.replace(":", "_")  # Ensure valid field names
    arcpy.AddField_management(feature_class_path, field_name, "TEXT")

# Insert data into the feature class
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@"] + [field.replace(":", "_") for field in unique_fields]) as cursor:
    for way in ways:
        try:
            # Extract node IDs and convert to coordinates
            node_ids = way.get("nodes", [])
            points = [arcpy.Point(*nodes_dict[node_id]) for node_id in node_ids if node_id in nodes_dict]

            # Only create polylines if there are at least two valid points
            if len(points) > 1:
                polyline_geometry = arcpy.Polyline(arcpy.Array(points), arcpy.SpatialReference(6491))

                # Prepare row data
                row = [polyline_geometry] + [way.get("tags", {}).get(field, None) for field in unique_fields]
                cursor.insertRow(row)
                print(f"Inserted Way {way['id']} with {len(points)} points.")  # Debug log
        except Exception as e:
            print(f"Error processing way {way['id']}: {e}")

print(f"Freeway ramps successfully converted to GDB at: {output_gdb}")
