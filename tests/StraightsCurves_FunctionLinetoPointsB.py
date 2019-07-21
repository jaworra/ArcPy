##ARCHIVE FUNCTION - Lines to points
## *** Requirement: Shapefile with attribute station 
##Returns: Shape file of points set interval


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
gp.Workspace = r"C:\Documents and Settings\jaworra\My Documents\ArcGIS\Default.gdb" # remove this gdb
gp.OverWriteOutput = 1

print "Setting Parameters"
# set parameters
inputFC = "SAMPLE_StateWide_MetrageRoads_MGA56"#"SAMPLETEST_StateWide_MetrageRoads_MGA56"
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
gp.CalculateField_management (outputFC, "NMBR_STATIONS", "ROUND(( [Shape_Length]/100) - 0.5) + 1")
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
        row.STATION = x * 100 + 70 #plus 70 here to as the start point 0, gives error.
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


print 'make layer'
gp.MakeRouteEventLayer_lr(inputFC, rid, tbl, props, lyr, "#",  "ERROR_FIELD")
#Assign points to list
rows = arcpy.SearchCursor(lyr, '', '', '', 'Station A') #set pointer and sort by col station in ascending
points = []
pointNo = 0

for row in rows:
    IDXY = [row.getValue("STATION"),pnt.x, pnt.y 

print row.Shape.getPart()

gp.MakeRouteEventLayer_lr("SAMPLE_StateWide_MetrageRoads_MGA56","PREFIX", "EventTable", "PREFIX POINT STATION","LinesToPoint18")
#polyArray = arcpy.Array()
inputPts = 'LinesToPoint18'
rows = arcpy.SearchCursor(inputPts, '', '', '', 'Station A')

words = []
points = []            
for row in rows:
     #print row.Shape.getPart()           
     words = str(row.Shape.getPart()).split()          
     stringinput = words[3:4],(words[0:1]),(words[1:2]) # concatination of lists
     print stringinput





(['70'], ['-13109.4666314314'], ['7780245.81232602'])
(['170'], ['-13154.3852138297'], ['7780341.80322597'])
(['270'], ['-13216.2909310983'], ['7780426.64533495'])
(['370'], ['-13291.3546615332'], ['7780498.79510232'])
(['470'], ['-13368.7708444156'], ['7780568.19485117'])
(['570'], ['-13446.2506885376'], ['7780637.51904881'])
(['670'], ['-13523.6499943127'], ['7780706.94490273'])
(['770'], ['-13601.095549373'], ['7780776.31273919'])

[70, -13109.466599999927, 7780245.8123000003]
[170, -13154.385200000368, 7780341.8032]
[270, -13216.290900000371, 7780426.6453]
[370, -13291.354700000025, 7780498.7950999998]
[470, -13368.770800000057, 7780568.1948999995]
[570, -13446.250699999742, 7780637.5190000003]













