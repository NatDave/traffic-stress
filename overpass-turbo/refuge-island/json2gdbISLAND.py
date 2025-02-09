import arcpy
import json
import os

# Set up the file paths
geojson_path = r"C:\Users\............\ped_refuge_island.geojson"
output_gdb = r"C:\Users\..............\ped_refuge_island.gdb"
output_fc = "ped_refuge_islands"

# Create a file geodatabase if it doesn't exist
if not os.path.exists(output_gdb):
    arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

# Read the GeoJSON file
with open(geojson_path, 'r') as file:
    geojson_data = json.load(file)

# Extract the features
features = geojson_data.get('features', [])

# Create the feature class
arcpy.CreateFeatureclass_management(
    output_gdb,
    output_fc,
    "POINT",
    spatial_reference=arcpy.SpatialReference(4326)  # WGS84 coordinate system
)

# Path to the created feature class
feature_class_path = os.path.join(output_gdb, output_fc)

# Define the fields to add to the feature class
fields_to_add = [
    "crossing",
    "highway",
    "tactile_paving",
    "crossing_markings"
]

# Add fields to the feature class for each mapped attribute
for field in fields_to_add:
    arcpy.AddField_management(feature_class_path, field, "TEXT")

# Insert data into the feature class
with arcpy.da.InsertCursor(feature_class_path, ["SHAPE@", *fields_to_add]) as cursor:
    for feature in features:
        try:
            # Extract geometry coordinates
            coords = feature['geometry']['coordinates']
            lon, lat = coords[0], coords[1]
            point_geometry = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))

            # Extract properties safely
            properties = feature['properties']
            row = [
                point_geometry,
                properties.get('crossing', None),
                properties.get('highway', None),
                properties.get('tactile_paving', None),
                properties.get('crossing:markings', None)  # Map special field safely
            ]
            # Insert the data row
            cursor.insertRow(row)
        except Exception as e:
            print(f"Error processing feature {feature}: {e}")
