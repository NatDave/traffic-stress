import arcpy
import json
import os

# Set up the JSON (GeoJSON) file path
json_path = r"C:\Users\................\asl.geojson"
output_gdb = r"C:\Users\...............\asl.gdb"
output_fc = "asl_features"

# Create a geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read GeoJSON data with explicit encoding
with open(json_path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Extract features from GeoJSON
features = json_data.get('features', [])

# Define the fields to map from the properties in the GeoJSON
field_mapping = {
    "cycleway": "cycleway",
    "highway": "highway",
    "lanes": "lanes",
    "lanes:backward": "lanes_backward",
    "lanes:forward": "lanes_forward",
    "maxspeed": "maxspeed",
    "surface": "surface",
    "oneway": "oneway",
    "name": "name",
    "ref": "ref",
    "direction": "direction",
    "footway": "footway",
    "bicycle": "bicycle",
    "lit": "lit",
    "note": "note",
}

# Create a feature class with the specified geometry type (POLYLINE) in the geodatabase
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POLYLINE",
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
            # Extract coordinates from the GeoJSON feature
            coordinates = feature['geometry']['coordinates']
            if coordinates:
                # Convert coordinates to PointGeometry (for POLYLINE geometry)
                line_geometry = arcpy.Array([arcpy.Point(*coord) for coord in coordinates])
                polyline = arcpy.Polyline(line_geometry, arcpy.SpatialReference(4326))

                # Extract relevant properties from the feature's properties
                properties = feature.get('properties', {})
                row = [polyline]  # Geometry comes first
                for key in field_mapping.keys():
                    row.append(properties.get(key, None))  # Map tag data into respective fields

                # Insert the row into the feature class
                cursor.insertRow(row)
            else:
                print(f"Skipping feature with invalid coordinates: {feature}")
        except Exception as e:
            print(f"Error processing feature {feature}: {e}")
