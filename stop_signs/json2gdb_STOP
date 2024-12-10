import arcpy
import json
import os

# Set up the JSON (GeoJSON) file path
json_path = r"C:\Users\------------\boston_stop_signs.geojson"
output_gdb = r"C:\Users\-----------\boston_stop_signs.gdb"
output_fc = "boston_stop_signs"

# Create a geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read GeoJSON data
with open(json_path, 'r') as file:
    json_data = json.load(file)

# Extract features from GeoJSON
features = json_data.get('features', [])

# Define the fields to map from the properties in the GeoJSON
field_mapping = {
    "highway": "highway",
    "direction": "direction",
    "stop": "stop"
}

# Create a feature class with the specified geometry type (POINT) in the geodatabase
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
            # Extract latitude and longitude from the GeoJSON coordinates
            coordinates = feature['geometry']['coordinates']
            if coordinates and len(coordinates) == 2:
                lon, lat = float(coordinates[0]), float(coordinates[1])  # GeoJSON uses [lon, lat]
                point_geometry = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))

                # Extract relevant properties from the feature's properties
                properties = feature.get('properties', {})
                row = [point_geometry]  # Geometry comes first
                for key in field_mapping.keys():
                    row.append(properties.get(key, None))  # Map tag data into respective fields

                # Insert the row into the feature class
                cursor.insertRow(row)
            else:
                print(f"Skipping invalid coordinates for feature: {feature}")
        except Exception as e:
            print(f"Error processing feature {feature}: {e}")
