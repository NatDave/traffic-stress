import arcpy

# Define the input feature class (road segments)
road_fc = r"C:\Users\............S\boston_streets.shp"

# Add new fields for start and end latitude and longitude
arcpy.AddField_management(road_fc, "Start_Lat", "DOUBLE")
arcpy.AddField_management(road_fc, "Start_Lon", "DOUBLE")
arcpy.AddField_management(road_fc, "End_Lat", "DOUBLE")
arcpy.AddField_management(road_fc, "End_Lon", "DOUBLE")

# Create a search cursor to iterate through each road segment
with arcpy.da.UpdateCursor(road_fc, ['SHAPE@', 'Start_Lat', 'Start_Lon', 'End_Lat', 'End_Lon']) as cursor:
    for row in cursor:
        # Get the start and end points of the road segment
        start_point = row[0].firstPoint
        end_point = row[0].lastPoint
        
        # Assign the latitude and longitude values
        row[1] = start_point.Y  # Latitude of the start point
        row[2] = start_point.X  # Longitude of the start point
        row[3] = end_point.Y    # Latitude of the end point
        row[4] = end_point.X    # Longitude of the end point
        
        # Update the row
        cursor.updateRow(row)
