import arcpy
import json
import os

# File paths
geojson_path = r"C:\Users\.............\bike_infrastructure.geojson"
output_gdb = r"C:\Users\...............\bike_infrastructure.gdb"
output_fc = "Bike_Infrastructure"

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
    "POLYLINE",  # Since the data is in LineString geometry
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84
)

# Path to feature class
feature_class_path = os.path.join(output_gdb, output_fc)

# Add fields for relevant properties
fields_to_add = [
    "cycleway", "highway", "lanes", "name", "surface", "width", "maxheight", 
    "condition", "maxspeed", "lit", "parking_lane", "postal_code", "smoothness", "source"
]

for field in fields_to_add:
    arcpy.AddField_management(feature_class_path, field, "TEXT")

# Insert data
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@", *fields_to_add]) as cursor:
    for feature in features:
        try:
            # Get geometry (LineString)
            coords = feature['geometry']['coordinates']
            points = [arcpy.Point(*coord) for coord in coords]
            polyline_geometry = arcpy.Polyline(arcpy.Array(points), arcpy.SpatialReference(4326))

            # Get properties
            properties = feature.get('properties', {})
            row = [polyline_geometry]
            for field in fields_to_add:
                # Get field value from properties
                row.append(properties.get(field, None))

            # Insert row
            cursor.insertRow(row)
        except Exception as e:
            print(f"Error processing feature {feature['id']}: {e}")
