##ARCHIVE FUNCTION - Lines to points
## *** Requirement: Shapefile with attribute station 
##Returns: Shape file of points set interval

##This alogrithm is improved on the Version - not fully functional, bugs include upadates to assigned stations.
##Use version A 

print('''Programmer:
  John Worrall

Version:
  1.0

Last Update:
   18/04/2013
       
  Batch spliting polylines enter interval
  
  NOTE:.
  
''')

# if digitising error occurs, ensure min distance appx 50m
#Create point of line

import sys, arcgisscripting, string, os
arcpy.env.overwriteOutput = True

gp = arcgisscripting.create(9.3)
gp.Workspace = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb"
gp.OverWriteOutput = 1

Interval = 100

print "Setting Parameters"
# set parameters
inputFC = "SAMPLE_StateWide_MetrageRoads_MGA56"
outputFC = "EventTableFC"
outputTable = "EventTable"
FC_View = "FCView"

print "Creating FCs"
# create FCs as neccessary
if not gp.Exists(outputFC):
    gp.FeatureclassToFeatureclass_conversion (inputFC, gp.Workspace, outputFC) 
if not gp.Exists(outputTable):
    gp.CreateTable (gp.Workspace, outputTable)
print "adding fields"

# add fields as neccessary
gp.AddField_management (outputFC, "NMBR_STATIONS", "LONG")
gp.AddField_management (outputFC, "STATION", "LONG")

print "caculating number of stations"
# calculate the number of stations needed and the position of the last station
gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length]/Interval) - 0.5) + 1")
gp.CalculateField_management (outputFC, "STATION", "[Shape_Length] - 1")

#gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length] * 100000 /100) - 0.5) + 1")
#gp.CalculateField_management (outputFC, "STATION", "[Shape_Length] * 100000- 1")

print "add more fields"
# add more fields to the event table...
gp.AddField_management (outputTable, "STATION", "LONG")
gp.AddField_management (outputTable, "PREFIX", "Text")
#gp.AddField_management (outputTable, "ProjectID", "Text")


print "Make a table of FC"
# make a table of the FC that contains the position of the last station (STATION) that can later be appended...
if not gp.Exists(FC_View):
    gp.TableToTable_conversion(outputFC, gp.Workspace, FC_View)

# start with the cursors...
# search cursor gets the number of stations needed for each ProjectID (NMBR_STATIONS)
# insert cursor is for adding new rows to Event Table
curID = gp.SearchCursor(outputFC)
rowID = curID.Next()
rows = gp.InsertCursor(outputTable)

print "Enter Station"
while rowID:
    numStations = rowID.NMBR_STATIONS
    projID = rowID.PREFIX
    x = 0
    while x+1 < numStations: # insert a row for each station until X = NumStations.  populate with station location along line.
        row = rows.NewRow()
        row.STATION = x * Interval + 70 #plus 70 here to as the start point 0, gives error.
        row.PREFIX = projID
        rows.InsertRow(row)
        x = x + 1
    rowID = curID.Next() # when x = numStations, go to top of loop and start for next ProjectID.

print "create points throgh linear M" 
#rt = outputFC
rid = "PREFIX"
tbl = outputTable
props = "PREFIX POINT STATION"
lyr = "LinesToPoint"

arcpy.MakeRouteEventLayer_lr (inputFC, rid, tbl, props, lyr, "#",  "ERROR_FIELD")

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#BUG HERE -> Unable to export route to shp file, required to extract coords
#Work around is manually data export function in gui
outfclass = "tsdfasfda"
lyr = "LinesToPoint"
#Save feature layer to feature class on disk
arcpy.CopyFeatures_management(lyr, outfclass)

